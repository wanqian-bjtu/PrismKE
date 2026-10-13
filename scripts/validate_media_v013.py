"""Run the bounded, isolated live VLM acceptance for the v0.13 media layer."""

from __future__ import annotations

import argparse
import asyncio
import json
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw

from src.core.ids import file_sha256, stable_id
from src.core.settings import Settings
from src.domain import (
    AttributeDef,
    CandidateAttribute,
    CanonicalEntity,
    EntityMention,
    EntityTypeDef,
    Modality,
    OutputSchema,
    RelationDef,
    SourceDocument,
    TaskMode,
    VisualExtractionRequest,
    WorkflowState,
)
from src.evaluation.request_budget import (
    BudgetedTransport,
    EvaluationBudgetStop,
    RequestBudget,
)
from src.governance.media import MediaKnowledgeProjector
from src.parsing import ParserRegistry
from src.persistence import FileEvidenceStore
from src.providers.vlm import OpenAICompatibleVLMProvider


def _draw_product(path: Path) -> None:
    image = Image.new("RGB", (1200, 760), "white")
    draw = ImageDraw.Draw(image)
    draw.rectangle((90, 90, 1110, 670), outline="#155eef", width=8)
    draw.rectangle((165, 205, 470, 535), fill="#e8f0ff", outline="#0b4ecb", width=5)
    draw.ellipse((265, 305, 370, 410), fill="#f4b740", outline="#202939", width=4)
    draw.text((540, 190), "NOVA SENSOR", fill="#111827", font_size=54)
    draw.text((540, 285), "model: NS-24", fill="#344054", font_size=36)
    draw.text((540, 355), "manufacturer: PRISM LABS", fill="#344054", font_size=34)
    draw.text((540, 425), "status: ACTIVE", fill="#067647", font_size=38)
    image.save(path)


def _draw_metrics(path: Path) -> None:
    image = Image.new("RGB", (1200, 800), "white")
    draw = ImageDraw.Draw(image)
    draw.text((80, 55), "NOVA SENSOR - QUARTERLY METRICS", fill="#101828", font_size=46)
    rows = [("Q1", 40), ("Q2", 60), ("Q3", 85)]
    y = 170
    for quarter, value in rows:
        draw.text((100, y + 22), quarter, fill="#344054", font_size=32)
        draw.rectangle((250, y, 250 + value * 8, y + 70), fill="#155eef")
        draw.text((970, y + 22), str(value), fill="#101828", font_size=32)
        y += 130
    draw.rectangle((80, 600, 1120, 730), outline="#98a2b3", width=3)
    draw.text((115, 635), "units_sold: 85", fill="#101828", font_size=36)
    draw.text((600, 635), "defect_count: 2", fill="#b42318", font_size=36)
    image.save(path)


def _draw_conflict(path: Path) -> None:
    image = Image.new("RGB", (1200, 700), "white")
    draw = ImageDraw.Draw(image)
    draw.rectangle((90, 100, 1110, 600), outline="#b42318", width=9)
    draw.text((175, 190), "ORION CONTROLLER", fill="#101828", font_size=58)
    draw.text((275, 350), "STATUS: INACTIVE", fill="#b42318", font_size=62)
    image.save(path)


def _write_samples(directory: Path) -> list[tuple[str, Path, str | None]]:
    directory.mkdir(parents=True, exist_ok=False)
    product = directory / "product.png"
    metrics = directory / "metrics.png"
    conflict_image = directory / "conflict.png"
    _draw_product(product)
    _draw_metrics(metrics)
    _draw_conflict(conflict_image)
    conflict = directory / "conflict.md"
    conflict.write_text(
        "# Orion controller record\n\n"
        "The Orion Controller status is ACTIVE.\n\n"
        "![Current status panel](conflict.png)\n",
        encoding="utf-8",
    )
    return [
        ("product-photo", product, None),
        ("table-chart", metrics, None),
        ("text-image-conflict", conflict, "ACTIVE"),
    ]


def _schema() -> OutputSchema:
    return OutputSchema(
        schema_id="prismke-v013-live-media",
        version="1",
        entity_types=[
            EntityTypeDef(id="Product", aliases=["device", "sensor", "controller"]),
            EntityTypeDef(id="Organization", aliases=["company", "manufacturer"]),
        ],
        relations=[
            RelationDef(
                id="manufactured_by",
                aliases=["manufacturer"],
                domain=["Product"],
                range=["Organization"],
            )
        ],
        attributes=[
            AttributeDef(id="status", subject_types=["Product"], value_type="string"),
            AttributeDef(id="model", subject_types=["Product"], value_type="string"),
            AttributeDef(id="units_sold", subject_types=["Product"], value_type="integer"),
            AttributeDef(id="defect_count", subject_types=["Product"], value_type="integer"),
        ],
    )


def _canonicalize(state: WorkflowState) -> None:
    entities: dict[tuple[str, str], CanonicalEntity] = {}
    for mention in state.extracted_entities:
        key = (mention.name.casefold(), mention.entity_type)
        entity = entities.setdefault(
            key,
            CanonicalEntity(
                id=stable_id("live-media-entity", mention.name, mention.entity_type),
                name=mention.name,
                entity_type=mention.entity_type,
            ),
        )
        state.mention_to_entity[mention.id] = entity.id
    state.entities = list(entities.values())


def _add_conflict_attribute(state: WorkflowState, expected: str) -> None:
    if state.document is None or not state.document.text_blocks:
        return
    visual_product = next(
        (
            item
            for item in state.extracted_entities
            if item.modality is Modality.IMAGE and item.entity_type == "Product"
        ),
        None,
    )
    if visual_product is None:
        return
    text_block = state.document.text_blocks[0]
    text_mention = EntityMention(
        id=stable_id("live-media-text-mention", state.run_id, visual_product.name),
        name=visual_product.name,
        entity_type=visual_product.entity_type,
        context=text_block.text,
        modality=Modality.TEXT,
        evidence_ids=[text_block.evidence_id],
        confidence=1.0,
    )
    state.extracted_entities.append(text_mention)
    state.mention_to_entity[text_mention.id] = state.mention_to_entity[visual_product.id]
    state.candidate_attributes.append(
        CandidateAttribute(
            id=stable_id("live-media-text-attribute", state.run_id, "status", expected),
            subject=text_mention,
            field="status",
            value=expected,
            confidence=1.0,
            evidence_ids=[text_block.evidence_id],
        )
    )


async def _run(
    output: Path,
    env_file: Path,
    ledger_path: Path | None = None,
    *,
    resume_ledger: bool = False,
) -> dict[str, Any]:
    if output.exists():
        raise ValueError("choose a fresh, isolated output directory")
    if not env_file.is_file():
        raise ValueError("configuration file is missing")
    output.mkdir(parents=True)
    effective_ledger = ledger_path or output / "request-ledger.json"
    budget = RequestBudget(
        limit=30_000,
        stop_at=27_000,
        max_output_tokens=2_048,
        ledger_path=effective_ledger,
        resume_ledger=resume_ledger,
    )
    settings = Settings(_env_file=env_file)
    if not settings.vlm_api_key or not settings.vlm_model:
        raise ValueError("VLM configuration is incomplete")
    if settings.vlm_model != "qwen3.7-flash":
        raise ValueError("live acceptance requires qwen3.7-flash")
    samples = _write_samples(output / "samples")
    evidence_store = FileEvidenceStore(output / "runtime" / "evidence")
    parser = ParserRegistry(
        asset_dir=output / "runtime" / "assets",
        allow_remote_assets=False,
    )
    provider = OpenAICompatibleVLMProvider(
        settings.vlm_base_url,
        settings.vlm_api_key,
        settings.vlm_model,
        settings.vlm_timeout,
        settings.vlm_max_image_edge,
        transport=BudgetedTransport(budget),
    )
    schema = _schema()
    report: dict[str, Any] = {
        "code_version": "0.13.0.dev0",
        "graph_backend": "none",
        "production_graph_access": False,
        "token_limit": budget.limit,
        "stop_at": budget.stop_at,
        "tokens_before_run": budget.total_tokens,
        "samples": [],
        "stopped_reason": None,
    }
    try:
        for case_id, source, expected_text_status in samples:
            if budget.stopped_reason or budget.total_tokens >= budget.stop_at:
                break
            budget.case_id = case_id
            document = await parser.parse(SourceDocument(path=source))
            await evidence_store.put_document(document)
            asset = document.media_assets[0]
            result = await provider.extract(
                VisualExtractionRequest(
                    document=document,
                    output_schema=schema,
                    task_mode=TaskMode.SCHEMA_INFORMATION_EXTRACTION,
                    asset=asset,
                )
            )
            document.visual_observations = result.observations
            for evidence in result.evidence:
                if evidence.id not in {item.id for item in document.evidence}:
                    document.evidence.append(evidence)
                    await evidence_store.put_ref(evidence)
            state = WorkflowState(
                run_id=stable_id("live-media-run", case_id, document.source_hash),
                input_path=str(source),
                schema_path="embedded:v013-live-media",
                task_mode=TaskMode.SCHEMA_INFORMATION_EXTRACTION,
                document=document,
                output_schema=schema,
                visual_candidates=result.candidates,
                extracted_entities=result.entities,
                provider_calls=result.call_records,
                validation=result.validation,
                warnings=result.warnings,
            )
            _canonicalize(state)
            if expected_text_status:
                _add_conflict_attribute(state, expected_text_status)
            projected = MediaKnowledgeProjector().project(state)
            referenced_evidence = {
                asset.evidence_id,
                *(item.evidence_id for item in projected.media_occurrences),
                *(eid for item in result.entities for eid in item.evidence_ids),
                *(eid for item in result.candidates for eid in item.evidence_ids),
                *(eid for item in projected.candidate_media_relations for eid in item.evidence_ids),
                *(
                    eid
                    for item in projected.candidate_visual_assertions
                    for eid in item.evidence_ids
                ),
            }
            evidence_valid = all(
                [await evidence_store.verify(item) for item in referenced_evidence]
            )
            conflict_review_count = sum(
                "cross_modal_attribute_conflict" in item.reasons
                for item in projected.visual_review_tasks
            )
            sample_report = {
                "case_id": case_id,
                "source_sha256": file_sha256(source),
                "media_content_count": len(projected.media_contents),
                "media_occurrence_count": len(projected.media_occurrences),
                "entity_count": len(result.entities),
                "claim_candidate_count": len(result.candidates),
                "visual_observation_count": len(result.observations),
                "depicts_candidate_count": len(projected.candidate_media_relations),
                "visual_assertion_count": len(projected.candidate_visual_assertions),
                "visual_review_count": len(projected.visual_review_tasks),
                "conflict_review_count": conflict_review_count,
                "evidence_reference_count": len(referenced_evidence),
                "evidence_valid": evidence_valid,
                "blocking_issue_count": result.validation.blocking_count,
                "model_tokens": sum(item.total_tokens or 0 for item in result.call_records),
            }
            report["samples"].append(sample_report)
            if not evidence_valid or not projected.media_occurrences:
                report["stopped_reason"] = "media evidence validation failed"
                break
            if case_id == "product-photo" and not projected.candidate_media_relations:
                report["stopped_reason"] = "product sample produced no DEPICTS candidate"
                break
            if case_id == "table-chart" and not projected.candidate_visual_assertions:
                report["stopped_reason"] = "metrics sample produced no visual assertion"
                break
            if case_id == "text-image-conflict" and not conflict_review_count:
                report["stopped_reason"] = "cross-modal conflict did not enter review"
                break
    except EvaluationBudgetStop as exc:
        report["stopped_reason"] = str(exc)
    except Exception as exc:
        report["stopped_reason"] = f"live_media_error:{type(exc).__name__}"
    finally:
        await budget.settle()
        report["total_tokens"] = budget.total_tokens
        report["accounting_complete"] = budget.accounting_complete
        report["stopped_reason"] = report["stopped_reason"] or budget.stopped_reason
        (output / "report.json").write_text(
            json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
        )
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--env-file", type=Path, required=True)
    parser.add_argument("--ledger", type=Path)
    parser.add_argument("--resume-ledger", action="store_true")
    args = parser.parse_args()
    report = asyncio.run(
        _run(
            args.output.resolve(),
            args.env_file.resolve(),
            args.ledger.resolve() if args.ledger else None,
            resume_ledger=args.resume_ledger,
        )
    )
    print(
        json.dumps(
            {
                "samples": len(report["samples"]),
                "tokens": report["total_tokens"],
                "accounting_complete": report["accounting_complete"],
                "stopped_reason": report["stopped_reason"],
                "report": str(args.output.resolve() / "report.json"),
            },
            ensure_ascii=False,
        )
    )
    if (
        report["stopped_reason"]
        or not report["accounting_complete"]
        or len(report["samples"]) != 3
    ):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
