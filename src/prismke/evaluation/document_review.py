"""Evidence-aware review tables for partially annotated real documents, not full-text F1."""

from __future__ import annotations

import csv
import json
import math
from collections import Counter
from pathlib import Path
from typing import Any
from urllib.parse import quote

from prismke.domain import DocumentIR
from prismke.parsing.visual_assets import select_analysis_assets


def document_coverage(state: dict[str, Any]) -> dict[str, Any]:
    """Report structural coverage, not extraction accuracy or evidence truth."""
    raw = state.get("document")
    if not raw:
        return {"document_available": False, "processing_complete": False}
    document = DocumentIR.model_validate(raw)
    selected = {asset.id for asset in select_analysis_assets(document)}
    called = {
        call["operation_id"]
        for call in state.get("provider_calls", [])
        if call.get("provider") == "vlm" and call.get("status") == "succeeded"
    }
    missing = selected - called
    invalid: list[str] = []
    boxes = 0
    for ref in document.evidence:
        if ref.bbox is None:
            continue
        boxes += 1
        width = 1.0 if ref.coordinate_space == "normalized" else ref.canvas_width
        height = 1.0 if ref.coordinate_space == "normalized" else ref.canvas_height
        b = ref.bbox
        valid = width is not None and height is not None
        valid &= all(math.isfinite(v) for v in (b.x0, b.y0, b.x1, b.y1))
        if not valid or not (
            0 <= b.x0 <= b.x1 <= (width or 0) and 0 <= b.y0 <= b.y1 <= (height or 0)
        ):
            invalid.append(ref.id)
    warnings = state.get("warnings", [])
    failures = [w for w in warnings if w.startswith(("ocr_failed:", "vlm_failed:"))]
    return {
        "document_available": True,
        "source_hash": document.source_hash,
        "pages": len(document.pages),
        "text_blocks_by_modality": dict(Counter(b.modality.value for b in document.text_blocks)),
        "media_assets": len(document.media_assets),
        "selected_visual_assets": len(selected),
        "called_visual_assets": len(selected & called),
        "missing_visual_asset_ids": sorted(missing),
        "analysis_failures": failures,
        "bbox_count": boxes,
        "invalid_bbox_ids": invalid,
        "alignment_decisions": dict(
            Counter(a["decision"] for a in state.get("alignment_records", []))
        ),
        "batch_provenance": [w for w in warnings if w.startswith("evaluation_")],
        "processing_complete": state.get("status") in {"completed", "awaiting_review"}
        and not missing
        and not failures,
    }


def _normalized(text: str) -> str:
    return " ".join(text.split()).casefold()


def _joined(mentions: list[dict[str, Any]], key: str) -> str:
    return "; ".join(sorted({str(item[key]) for item in mentions if item.get(key) is not None}))


def evidence_match(gold: dict[str, Any], actual: dict[str, Any], context: str) -> str:
    position = gold.get("evidence") or {}
    if position.get("coordinate_system") == "pdf_points":
        if actual.get("coordinate_space") != "pdf_points":
            return "not_verified"
        if actual.get("page_number") != position.get("page"):
            return "different_page"
        expected = position.get("bbox")
        bbox = actual.get("bbox")
        if expected and bbox:
            overlap = min(expected[2], bbox["x1"]) > max(expected[0], bbox["x0"])
            overlap &= min(expected[3], bbox["y1"]) > max(expected[1], bbox["y0"])
            return "pdf_block_overlap" if overlap else "different_region"
        return "not_verified"
    expected_context = _normalized(gold.get("context", ""))
    if (
        gold.get("modality", "text") == "text"
        and len(expected_context) >= 20
        and expected_context in _normalized(context)
    ):
        return "context_overlap_requires_manual_span_check"
    return "not_verified"


def review_document_state(
    state: dict[str, Any], annotations: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    document = state.get("document") or {}
    refs = {ref["id"]: ref for ref in document.get("evidence", [])}
    blocks = {block["evidence_id"]: block["text"] for block in document.get("text_blocks", [])}
    decisions = {row["mention_id"]: row for row in state.get("entity_resolution_decisions", [])}
    mentions: dict[str, dict[str, Any]] = {}
    for claim in state.get("candidates", []):
        for role in ("subject", "object"):
            mention = claim.get(role)
            if isinstance(mention, dict) and "name" in mention:
                mentions[mention["id"]] = mention
    rows = []
    for gold in annotations:
        observed = []
        for mention in mentions.values():
            if _normalized(mention["name"]) != _normalized(gold["name"]):
                continue
            matches = [
                {
                    "evidence_id": eid,
                    "position_match": evidence_match(gold, refs.get(eid, {}), blocks.get(eid, "")),
                }
                for eid in mention.get("evidence_ids", [])
            ]
            decision = decisions.get(mention["id"], {})
            observed.append(
                {
                    "mention_id": mention["id"],
                    "entity_type": mention.get("entity_type"),
                    "type_matches": mention.get("entity_type") == gold["entity_type"],
                    "evidence": matches,
                    "method": decision.get("method"),
                    "selected_entity_id": decision.get("selected_entity_id"),
                    "requires_review": decision.get("requires_review"),
                    "candidates": decision.get("candidates", []),
                    "reasons": decision.get("reasons", []),
                }
            )
        rows.append(
            {
                "mention_id": gold["id"],
                "document_id": gold["document_id"],
                "name": gold["name"],
                "gold_type": gold["entity_type"],
                "gold_cluster_id": gold["cluster_id"],
                "expected_seed_entity_id": gold.get("expected_entity_id"),
                "gold_evidence": gold.get("evidence"),
                "run_status": state.get("status"),
                "surface_found": bool(observed),
                "observed_mentions": observed,
                "automatic_link_correctness": "requires_evidence_and_identity_review",
            }
        )
    return rows


def export_document_review(
    reports: list[Path], annotations_path: Path, output: Path, *, prefer_latest: bool = False
) -> list[dict[str, Any]]:
    annotations = json.loads(annotations_path.read_text(encoding="utf-8"))["mentions"]
    if len({row["id"] for row in annotations}) != len(annotations):
        raise ValueError("duplicate annotated mention IDs")
    rows: list[dict[str, Any]] = []
    seen_documents: set[str] = set()
    for report_path in reversed(reports) if prefer_latest else reports:
        report = json.loads(report_path.read_text(encoding="utf-8"))
        for case in report["cases"]:
            if case["id"] in seen_documents:
                if prefer_latest:
                    continue
                raise ValueError("duplicate document reports; select the intended final attempt")
            seen_documents.add(case["id"])
            gold = [row for row in annotations if row["document_id"] == case["id"]]
            if "run_id" not in case:
                rows.extend(review_document_state({"status": case.get("status", "failed")}, gold))
                continue
            path = report_path.parent / "runs" / f"{quote(case['run_id'], safe='')}.json"
            state = json.loads(path.read_text(encoding="utf-8"))
            rows.extend(review_document_state(state, gold))
    missing = [row for row in annotations if row["document_id"] not in seen_documents]
    rows.extend(review_document_state({"status": "not_started"}, missing))
    output.mkdir(parents=True, exist_ok=True)
    (output / "annotated-mention-review.json").write_text(
        json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8", newline="\n"
    )
    with (output / "annotated-mention-review.csv").open(
        "w", encoding="utf-8-sig", newline=""
    ) as stream:
        fields = [
            "提及ID",
            "文档ID",
            "标注名称",
            "标注类型",
            "原答案ID",
            "原证据位置",
            "名称出现",
            "证据位置核验",
            "系统选择或草稿ID",
            "链接方式",
            "待审核",
            "第一候选",
            "说明",
        ]
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            observed = row["observed_mentions"]
            positions = {
                ref["position_match"] for mention in observed for ref in mention["evidence"]
            }

            top = {
                mention["candidates"][0]["entity_id"]
                for mention in observed
                if mention["candidates"]
            }
            writer.writerow(
                {
                    "提及ID": row["mention_id"],
                    "文档ID": row["document_id"],
                    "标注名称": row["name"],
                    "标注类型": row["gold_type"],
                    "原答案ID": row["gold_cluster_id"],
                    "原证据位置": json.dumps(row["gold_evidence"], ensure_ascii=False),
                    "名称出现": "是" if row["surface_found"] else "否",
                    "证据位置核验": "; ".join(sorted(positions)) or "未找到提及证据",
                    "系统选择或草稿ID": _joined(observed, "selected_entity_id"),
                    "链接方式": _joined(observed, "method"),
                    "待审核": "是" if any(item["requires_review"] for item in observed) else "否",
                    "第一候选": "; ".join(sorted(top)),
                    "说明": "名称出现不等于位置正确或身份确认；草稿ID不代表已入图",
                }
            )
    return rows
