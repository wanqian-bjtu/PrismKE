"""Read-only conversion of reviewed workbooks into isolated evaluation inputs."""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any

from bs4 import BeautifulSoup
from PIL import Image

from src.domain import CanonicalEntity


def _read(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _local(root: Path, name: str) -> Path:
    path = (root / name).resolve()
    if not path.is_relative_to(root.resolve()):
        raise ValueError(f"resource outside material directory: {name}")
    return path


def _verify_original_block(path: Path, block: dict[str, Any]) -> None:
    if path.suffix == ".pdf":
        import pymupdf

        with pymupdf.open(path) as pdf:  # type: ignore[no-untyped-call]
            index = int(block["id"].rsplit("-B", 1)[1])
            original = pdf[block["page"] - 1].get_text("blocks")[index]
        if original[4] != block["text"] or list(original[:4]) != block["bbox"]:
            raise ValueError("PDF block differs from original page")
    elif path.suffix == ".md":
        line = path.read_text(encoding="utf-8-sig").splitlines()[block["line"] - 1]
        if line != block["text"]:
            raise ValueError("Markdown line differs from original")
    elif path.suffix == ".html":
        tree = BeautifulSoup(path.read_bytes(), "html.parser")
        article = tree.select_one(".wp_articlecontent") or tree
        paragraph = article.find_all("p")[block["paragraph"] - 1]
        if paragraph.get_text().strip() != block["text"]:
            raise ValueError("HTML paragraph differs from original")
    elif block["text"] not in path.read_text(encoding="utf-8"):
        raise ValueError("text block not found in original")


def export_reviewed_annotations(workbook: Path, package: Path, output: Path) -> dict[str, Any]:
    """Validate the originals first; never overwrite the workbook or source answers."""
    try:
        from openpyxl import load_workbook
    except ImportError as exc:
        raise ValueError("Excel export requires `uv sync --extra evaluation`") from exc
    if output.resolve() == package.resolve() or output.resolve() in workbook.resolve().parents:
        raise ValueError("output must be a separate directory, not an original input directory")
    answers = _read(package / "annotations/answer_key.json")
    initial = _read(package / "annotations/initial_kb.json")
    sources = _read(package / "sources.json")
    source_paths = {
        source["document_id"]: _local(package, source["original_file"]) for source in sources
    }
    catalog = {item["id"]: item for item in answers["entities"]}
    original_mentions = {item["mention_id"]: item for item in answers["mentions"]}
    if len(original_mentions) != len(answers["mentions"]):
        raise ValueError("duplicate mention IDs in original JSON")
    entities = [CanonicalEntity.model_validate(item) for item in initial["entities"]]
    if len({entity.id for entity in entities}) != len(entities):
        raise ValueError("duplicate initial entity IDs")
    for source in sources:
        path = _local(package, source["original_file"])
        if _digest(path) != source["sha256"]:
            raise ValueError(f"original hash mismatch: {source['document_id']}")
        for asset in source["assets"]:
            path = _local(package, f"materials/{source['document_id']}/{asset['file']}")
            if _digest(path) != asset["sha256"]:
                raise ValueError(f"asset hash mismatch: {source['document_id']}/{asset['file']}")
    block_cache: dict[str, dict[str, Any]] = {}
    errors: list[str] = []
    confirmed: list[dict[str, Any]] = []
    excluded: list[str] = []
    seen: set[str] = set()
    input_digest = _digest(workbook)
    book = load_workbook(workbook, read_only=True, data_only=False)
    try:
        sheet = book["实体提及"]
        headers = [cell.value for cell in next(sheet.iter_rows())]
        required = [
            "提及ID",
            "文档ID",
            "原始名称",
            "实体类型",
            "初版实体ID",
            "复核状态",
            "人工实体ID",
            "人工动作",
        ]
        if any(name not in headers for name in required):
            raise ValueError("workbook is missing required columns")
        for row_number, cells in enumerate(sheet.iter_rows(min_row=2, values_only=True), 2):
            if not any(value is not None for value in cells):
                continue
            row = dict(zip(headers, cells, strict=True))
            mention_id = str(row["提及ID"])
            try:
                if mention_id in seen or mention_id not in original_mentions:
                    raise ValueError(f"duplicate or unknown mention ID: {mention_id}")
                seen.add(mention_id)
                original = original_mentions[mention_id]
                if row["复核状态"] == "排除" or row["人工动作"] == "排除":
                    excluded.append(mention_id)
                    continue
                if row["复核状态"] not in {"已确认", "已修正"}:
                    raise ValueError("record has not been confirmed")
                # Line wrapping is display-only and must not change the original name.
                surface = re.sub(r"\s+", " ", str(row["原始名称"])).strip()
                if surface != re.sub(r"\s+", " ", original["surface"]).strip():
                    raise ValueError("surface name differs from original JSON")
                if row["文档ID"] != original["document_id"]:
                    raise ValueError("document ID differs from original JSON")
                if row["初版实体ID"] != original["gold_entity_id"]:
                    raise ValueError("draft ID was changed; use the human answer column instead")
                gold = row["人工实体ID"] or original["gold_entity_id"]
                if gold not in catalog:
                    raise ValueError(f"unknown gold entity ID: {gold}")
                kind = catalog[gold]["entity_type"]
                if row["实体类型"] != original["entity_type"] or kind != original["entity_type"]:
                    raise ValueError("entity type mismatch")
                action = "链接已有" if gold in {e.id for e in entities} else "创建新实体"
                if row["人工动作"] not in (None, "", action):
                    raise ValueError("human action is incompatible with the fixed initial KB")
                evidence = original["evidence"]
                if original["modality"] == "text":
                    doc = original["document_id"]
                    if doc not in block_cache:
                        block_cache[doc] = {
                            item["id"]: item
                            for item in _read(package / f"materials/{doc}/blocks.json")
                        }
                    block = block_cache[doc][evidence["id"]]
                    _verify_original_block(source_paths[doc], block)
                    start, end = evidence["char_start"], evidence["char_end"]
                    if not 0 <= start < end <= len(block["text"]):
                        raise ValueError("invalid text span")
                    if block["text"][start:end] != original["surface"]:
                        raise ValueError("text evidence no longer supports the mention")
                    if "bbox" in evidence and evidence["bbox"] != block["bbox"]:
                        raise ValueError("PDF evidence bbox differs from extracted block")
                else:
                    path = _local(package, evidence["asset_file"])
                    if _digest(path) != evidence["blob_hash"]:
                        raise ValueError("visual evidence hash mismatch")
                    with Image.open(path) as image:
                        width, height = image.size
                    if (width, height) != (evidence["canvas_width"], evidence["canvas_height"]):
                        raise ValueError("visual canvas dimensions differ")
                    x0, y0, x1, y1 = evidence["bbox"]
                    if not 0 <= x0 < x1 <= width or not 0 <= y0 < y1 <= height:
                        raise ValueError("visual bbox out of bounds")
                evidence_id = f"evidence:real-eval:{mention_id}"
                confirmed.append(
                    {
                        "id": mention_id,
                        "name": original["surface"],
                        "entity_type": original["entity_type"],
                        "context": original["context"],
                        "modality": original["modality"],
                        "document_id": original["document_id"],
                        "evidence_ids": [evidence_id],
                        "evidence": evidence,
                        "expected_entity_id": gold if action == "链接已有" else None,
                        "cluster_id": gold,
                        "category": original["modality"],
                        "review_status": row["复核状态"],
                        "reviewer": row.get("复核人"),
                        "review_note": row.get("复核意见"),
                    }
                )
            except (ValueError, KeyError, TypeError) as exc:
                errors.append(f"Excel row {row_number} ({mention_id}): {exc}")
        missing = original_mentions.keys() - seen
        if missing:
            errors.append(f"missing workbook IDs: {sorted(missing)}")
        pending_rows = list(book["待复核"].iter_rows(values_only=True))
        pending_headers = pending_rows[0]
        pending = [dict(zip(pending_headers, row, strict=True)) for row in pending_rows[1:]]
    finally:
        book.close()
    if _digest(workbook) != input_digest:
        errors.append("workbook changed while exporting")
    if errors:
        raise ValueError("\n".join(errors))
    if not confirmed:
        raise ValueError("no confirmed records")
    manifest = {
        "version": "real-entity-baseline-1",
        "protocol": "fixed",
        "entities": initial["entities"],
        "mentions": confirmed,
        "governance": [],
        "provenance": {
            "workbook_sha256": input_digest,
            "draft_answers_sha256": _digest(package / "annotations/answer_key.json"),
            "initial_kb_sha256": _digest(package / "annotations/initial_kb.json"),
            "sources_sha256": _digest(package / "sources.json"),
            "human_confirmed": True,
            "independent_double_annotation": False,
        },
    }
    output.mkdir(parents=True, exist_ok=True)
    products = {
        "manifest.json": manifest,
        "confirmed_answers.json": {"mentions": confirmed, "pending": pending, "excluded": excluded},
        "initial_kb.json": initial,
        "evidence_index.json": {
            item["evidence_ids"][0]: {"document_id": item["document_id"], **item["evidence"]}
            for item in confirmed
        },
    }
    for name in [*products, "export_summary.json"]:
        path = output / name
        if path.exists():
            raise ValueError(f"output already exists; choose a fresh directory: {name}")
    for name, value in products.items():
        (output / name).write_text(
            json.dumps(value, ensure_ascii=False, indent=2),
            encoding="utf-8",
            newline="\n",
        )
    summary = {
        "confirmed": len(confirmed),
        "excluded": len(excluded),
        "seed_entities": len(entities),
        "pending_unscored": len(pending),
        "workbook_sha256": input_digest,
        "files": {name: _digest(output / name) for name in products},
    }
    (output / "export_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2),
        encoding="utf-8",
        newline="\n",
    )
    return summary
