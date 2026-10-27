"""Safe, reproducible ZIP exports for one extraction run."""

from __future__ import annotations

import csv
import re
from io import StringIO
from pathlib import Path
from typing import Any
from uuid import uuid4
from zipfile import ZIP_DEFLATED, ZipFile

import orjson

from src import __version__
from src.core.errors import EvidenceIntegrityError
from src.core.ids import canonical_hash
from src.domain import EntityMention, WorkflowState
from src.workflow.result_projection import (
    aggregate_entity_mentions,
    candidate_graph,
    mention_occurrences,
    run_insight,
)


def _safe_name(value: str, fallback: str) -> str:
    name = Path(value).name.strip()
    name = re.sub(r"[^A-Za-z0-9._-]+", "-", name).strip(".-")
    return name[:120] or fallback


def _json_bytes(value: Any) -> bytes:
    return orjson.dumps(value, option=orjson.OPT_INDENT_2 | orjson.OPT_SORT_KEYS)


def _csv_cell(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, (dict, list, tuple, set)):
        text = orjson.dumps(value, option=orjson.OPT_SORT_KEYS).decode("utf-8")
    else:
        text = str(value)
    if text.startswith(("=", "+", "-", "@")):
        return f"'{text}"
    return text


def _csv_bytes(headers: list[str], rows: list[dict[str, Any]]) -> bytes:
    stream = StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=headers, extrasaction="ignore", lineterminator="\n")
    writer.writeheader()
    for row in rows:
        writer.writerow({header: _csv_cell(row.get(header)) for header in headers})
    return stream.getvalue().encode("utf-8-sig")


def _relation_rows(state: WorkflowState) -> list[dict[str, Any]]:
    result = state.extraction_result
    if result is None:
        return []
    rows: list[dict[str, Any]] = []
    for item in result.relations:
        object_name = item.object.name if isinstance(item.object, EntityMention) else item.object
        rows.append(
            {
                "id": item.id,
                "subject_mention_id": item.subject.id,
                "subject": item.subject.name,
                "relation": item.relation,
                "object": object_name,
                "confidence": item.confidence,
                "modalities": [value.value for value in item.modalities],
                "evidence_ids": item.evidence_ids,
                "cross_modal_support": item.cross_modal_support,
            }
        )
    return rows


def _attribute_rows(state: WorkflowState) -> list[dict[str, Any]]:
    result = state.extraction_result
    if result is None:
        return []
    return [
        {
            "id": item.id,
            "subject_mention_id": item.subject.id,
            "subject": item.subject.name,
            "field": item.field,
            "value": item.value,
            "confidence": item.confidence,
            "evidence_ids": item.evidence_ids,
        }
        for item in result.attributes
    ]


def _event_rows(state: WorkflowState) -> list[dict[str, Any]]:
    result = state.extraction_result
    if result is None:
        return []
    return [
        {
            "id": item.id,
            "event_type": item.event_type,
            "trigger": item.trigger,
            "arguments": [argument.model_dump(mode="json") for argument in item.arguments],
            "confidence": item.confidence,
            "evidence_ids": item.evidence_ids,
        }
        for item in result.events
    ]


async def build_run_export(
    service: Any,
    run_id: str,
    *,
    include_source: bool = False,
    output_dir: Path | None = None,
) -> Path:
    """Build a sanitized export archive and return its temporary path."""

    state: WorkflowState = service.show_run(run_id)
    result = state.extraction_result
    if result is None:
        raise ValueError("RUN_RESULT_NOT_READY")
    if state.document is None or state.output_schema is None:
        raise ValueError("RUN_DOCUMENT_NOT_READY")
    evidence_by_id = {
        evidence.id: evidence
        for evidence in [*state.document.evidence, *result.evidence]
    }
    evidence_records: list[dict[str, Any]] = []
    for evidence in evidence_by_id.values():
        verified = await service.evidence_store.verify(evidence.id)
        if not verified:
            raise EvidenceIntegrityError(f"evidence verification failed: {evidence.id}")
        record = evidence.model_dump(mode="json")
        record["verified"] = True
        evidence_records.append(record)

    export_dir = output_dir or service.settings.runtime_dir / "exports"
    export_dir.mkdir(parents=True, exist_ok=True)
    source_name = _safe_name(
        state.document.source_filename or Path(state.input_path).name,
        "document",
    )
    archive_path = export_dir / f"{_safe_name(run_id, 'run')}-{uuid4().hex[:12]}.zip"
    groups = aggregate_entity_mentions(state)
    mentions = mention_occurrences(state)
    graph = candidate_graph(state)
    insight = run_insight(state)
    manifest = {
        "format": "prismke-run-export",
        "format_version": "1.0",
        "run_id": state.run_id,
        "batch_id": state.batch_id,
        "task_mode": state.task_mode.value,
        "entity_source_mode": state.entity_source_mode.value,
        "software_version": __version__,
        "workflow_protocol": state.pipeline_version,
        "source_filename": source_name,
        "source_hash": state.document.source_hash,
        "source_included": include_source,
        "schema_id": state.output_schema.schema_id,
        "schema_version": state.output_schema.version,
        "schema_hash": canonical_hash(state.output_schema.model_dump(mode="json")),
        "pdf_parse_decision": (
            state.pdf_parse_decision.model_dump(mode="json")
            if state.pdf_parse_decision is not None
            else None
        ),
        "provider_fingerprints": {
            "llm": state.provider_fingerprint,
            "ocr": state.ocr_provider_fingerprint,
            "vlm": state.vlm_provider_fingerprint,
            "embedding": state.embedding_provider_fingerprint,
        },
        "files": [
            "manifest.json",
            "results.json",
            "schema_snapshot.json",
            "entities.csv",
            "mentions.csv",
            "relations.csv",
            "attributes.csv",
            "events.csv",
            "media.csv",
            "evidence.csv",
            "validation_issues.csv",
            "candidate_graph.json",
            "evidence_manifest.json",
            "run_insight.json",
        ],
    }
    relation_rows = _relation_rows(state)
    attribute_rows = _attribute_rows(state)
    event_rows = _event_rows(state)
    media_rows = [
        item.model_dump(mode="json")
        for item in [
            *result.media_contents,
            *result.media_occurrences,
            *result.candidate_media_relations,
            *result.candidate_visual_assertions,
        ]
    ]
    issue_rows = [item.model_dump(mode="json") for item in result.validation_issues]
    with ZipFile(archive_path, "w", compression=ZIP_DEFLATED, compresslevel=6) as archive:
        archive.writestr("manifest.json", _json_bytes(manifest))
        archive.writestr("results.json", _json_bytes(result.model_dump(mode="json")))
        archive.writestr(
            "schema_snapshot.json", _json_bytes(state.output_schema.model_dump(mode="json"))
        )
        archive.writestr("run_insight.json", _json_bytes(insight))
        archive.writestr("candidate_graph.json", _json_bytes(graph))
        archive.writestr("evidence_manifest.json", _json_bytes(evidence_records))
        archive.writestr(
            "entities.csv",
            _csv_bytes(
                [
                    "group_id",
                    "canonical_entity_id",
                    "grouping",
                    "name",
                    "entity_type",
                    "occurrence_count",
                    "confidence_average",
                    "confidence_max",
                    "modalities",
                    "pages",
                    "review_status",
                    "mention_ids",
                    "evidence_ids",
                ],
                groups,
            ),
        )
        archive.writestr(
            "mentions.csv",
            _csv_bytes(
                [
                    "group_id",
                    "mention_id",
                    "name",
                    "entity_type",
                    "context",
                    "confidence",
                    "review_status",
                    "evidence_id",
                    "modality",
                    "page_number",
                    "char_start",
                    "char_end",
                    "bbox",
                    "coordinate_space",
                ],
                mentions,
            ),
        )
        archive.writestr(
            "relations.csv",
            _csv_bytes(list(relation_rows[0]) if relation_rows else ["id"], relation_rows),
        )
        archive.writestr(
            "attributes.csv",
            _csv_bytes(
                list(attribute_rows[0]) if attribute_rows else ["id"], attribute_rows
            ),
        )
        archive.writestr(
            "events.csv",
            _csv_bytes(list(event_rows[0]) if event_rows else ["id"], event_rows),
        )
        media_headers = sorted({key for row in media_rows for key in row}) or ["id"]
        evidence_headers = sorted({key for row in evidence_records for key in row}) or [
            "id"
        ]
        issue_headers = sorted({key for row in issue_rows for key in row}) or ["id"]
        archive.writestr("media.csv", _csv_bytes(media_headers, media_rows))
        archive.writestr(
            "evidence.csv", _csv_bytes(evidence_headers, evidence_records)
        )
        archive.writestr(
            "validation_issues.csv", _csv_bytes(issue_headers, issue_rows)
        )
        if include_source:
            source_path = service.evidence_store.verified_blob_path(state.document.source_hash)
            archive.write(source_path, f"source/{source_name}")
            included_assets: set[str] = set()
            for asset in state.document.media_assets:
                if not asset.blob_hash or asset.blob_hash in included_assets:
                    continue
                asset_path = service.evidence_store.verified_blob_path(asset.blob_hash)
                suffix = Path(asset.path).suffix.lower() or ".bin"
                archive.write(
                    asset_path,
                    f"derived/{_safe_name(asset.id, 'asset')}{suffix}",
                )
                included_assets.add(asset.blob_hash)
    return archive_path
