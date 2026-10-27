"""Validation and reproducible materialization for Web-entered schemas."""

from __future__ import annotations

import os
from html import escape
from pathlib import Path
from uuid import uuid4

import orjson
import yaml

from src.core.ids import canonical_hash
from src.domain import OutputSchema, load_schema


def resolve_schema(
    source: str,
    uploaded_path: str | None,
    schema_text: str | None,
    directory: Path,
) -> tuple[Path, OutputSchema]:
    if source == "upload":
        if not uploaded_path:
            raise ValueError("请上传 Schema 文件")
        path = Path(uploaded_path).resolve()
        return path, load_schema(path)
    if source != "text":
        raise ValueError("未知的 Schema 来源")
    raw = (schema_text or "").strip()
    if not raw:
        raise ValueError("请输入 JSON 或 YAML Schema")
    try:
        payload = yaml.safe_load(raw)
        schema = OutputSchema.model_validate(payload)
    except Exception as exc:
        raise ValueError(f"Schema 文本无效：{exc}") from exc
    canonical = schema.model_dump(mode="json")
    schema_id = canonical_hash(canonical)
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / f"{schema_id}.json"
    if not path.exists():
        temporary = directory / f".{schema_id}.{uuid4().hex}.tmp"
        try:
            with temporary.open("wb") as stream:
                stream.write(orjson.dumps(canonical, option=orjson.OPT_INDENT_2))
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(temporary, path)
        finally:
            temporary.unlink(missing_ok=True)
    return path, schema


def schema_summary(schema: OutputSchema) -> str:
    fingerprint = canonical_hash(schema.model_dump(mode="json"))
    summary = (
        f"✓ Valid · Schema {schema.schema_id} · Version {schema.version} · "
        f"Entity types {len(schema.entity_types)} · Relations {len(schema.relations)} · "
        f"Hash {fingerprint}"
    )
    return f'<span class="schema-validation-valid">{escape(summary)}</span>'
