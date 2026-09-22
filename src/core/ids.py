"""Stable content-derived identifiers and fingerprints."""

from __future__ import annotations

from hashlib import sha256
from pathlib import Path
from typing import Any

import orjson


def stable_id(prefix: str, *parts: object) -> str:
    normalized = "\x1f".join(str(part).strip() for part in parts)
    return f"{prefix}:{sha256(normalized.encode('utf-8')).hexdigest()[:24]}"


def canonical_hash(value: Any) -> str:
    payload = orjson.dumps(value, option=orjson.OPT_SORT_KEYS)
    return sha256(payload).hexdigest()


def file_sha256(path: Path) -> str:
    digest = sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()
