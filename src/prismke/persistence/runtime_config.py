"""Private runtime configuration overrides with redacted public views."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any
from uuid import uuid4

import orjson
from filelock import FileLock

from prismke.core.settings import Settings

SECRET_FIELDS = {"llm_api_key", "vlm_api_key", "neo4j_password"}
EDITABLE_FIELDS = {
    "llm_base_url",
    "llm_model",
    "vlm_base_url",
    "vlm_model",
    "vlm_timeout",
    "ocr_device",
    "ocr_lang",
    "ocr_model",
    "allow_remote_assets",
    "request_timeout",
    "graph_store",
    "neo4j_uri",
    "neo4j_user",
    "neo4j_database",
    "embedding_provider",
    "embedding_model",
    "embedding_device",
    "embedding_use_fp16",
    "embedding_batch_size",
    "embedding_max_tokens",
    *SECRET_FIELDS,
}
RESTART_FIELDS = {
    "graph_store",
    "neo4j_uri",
    "neo4j_user",
    "neo4j_password",
    "neo4j_database",
}


class RuntimeConfigRepository:
    def __init__(self, path: Path) -> None:
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.lock = FileLock(str(path.with_suffix(".lock")))

    def load(self) -> dict[str, Any]:
        if not self.path.is_file():
            return {}
        payload = dict(orjson.loads(self.path.read_bytes()))
        return {key: value for key, value in payload.items() if key in EDITABLE_FIELDS}

    def apply(self, settings: Settings) -> None:
        for key, value in self.load().items():
            setattr(settings, key, value)

    def update(self, values: dict[str, Any]) -> None:
        invalid = set(values) - EDITABLE_FIELDS
        if invalid:
            raise ValueError(f"unsupported runtime settings: {', '.join(sorted(invalid))}")
        with self.lock:
            payload = self.load()
            payload.update(values)
            temporary = self.path.with_name(f".{self.path.name}.{uuid4().hex}.tmp")
            try:
                with temporary.open("wb") as stream:
                    stream.write(orjson.dumps(payload, option=orjson.OPT_INDENT_2))
                    stream.flush()
                    os.fsync(stream.fileno())
                os.chmod(temporary, 0o600)
                os.replace(temporary, self.path)
            finally:
                temporary.unlink(missing_ok=True)

    @staticmethod
    def public_view(settings: Settings) -> dict[str, Any]:
        return {
            key: (bool(getattr(settings, key)) if key in SECRET_FIELDS else getattr(settings, key))
            for key in sorted(EDITABLE_FIELDS)
        }
