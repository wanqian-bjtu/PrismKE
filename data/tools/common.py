from __future__ import annotations

import hashlib
import json
import os
import re
import tempfile
import zipfile
from collections.abc import Iterable, Mapping
from pathlib import Path
from typing import Any

import yaml

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_ROOT = PROJECT_ROOT / "data"
PUBLIC_ROOT = DATA_ROOT / "public"
SYNTHETIC_ROOT = DATA_ROOT / "synthetic"
PUBLIC_MANIFEST = DATA_ROOT / "manifests" / "public_sources.yaml"
PUBLIC_LOCK = PUBLIC_ROOT / "manifest.lock.json"

EMAIL_RE = re.compile(r"(?i)\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b")
PHONE_RE = re.compile(
    r"(?<![\w.])(?:\+?\d{1,3}[ \t().-]+)?(?:\(?\d{2,4}\)?[ \t.-]+)"
    r"\d{3,4}[ \t.-]+\d{3,4}(?![\w.])"
)
ADDRESS_HINT_RE = re.compile(
    r"(?i)\b(?:street|road|avenue|lane|drive|boulevard|postcode|zip code|"
    r"floor\s+\d+|PO Box)\b"
)


def load_yaml(path: Path) -> dict[str, Any]:
    value = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"Expected an object in {path}")
    return value


def stable_json(value: Any) -> bytes:
    return (json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode()


def atomic_write(path: Path, payload: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temp_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(payload)
        os.replace(temp_name, path)
    except BaseException:
        Path(temp_name).unlink(missing_ok=True)
        raise


def write_json(path: Path, value: Any) -> None:
    atomic_write(path, stable_json(value))


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def file_record(path: Path, root: Path) -> dict[str, Any]:
    return {
        "path": path.relative_to(root).as_posix(),
        "bytes": path.stat().st_size,
        "sha256": sha256_file(path),
    }


def records(paths: Iterable[Path], root: Path) -> list[dict[str, Any]]:
    ordered = sorted(
        paths,
        key=lambda path: path.relative_to(root).as_posix().casefold(),
    )
    return [file_record(path, root) for path in ordered]


def canonicalize_zip(path: Path) -> None:
    entries: list[tuple[zipfile.ZipInfo, bytes]] = []
    with zipfile.ZipFile(path) as source:
        for info in sorted(source.infolist(), key=lambda item: item.filename):
            entries.append((info, source.read(info.filename)))
    descriptor, temp_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    os.close(descriptor)
    try:
        with zipfile.ZipFile(temp_name, "w", compression=zipfile.ZIP_DEFLATED) as target:
            for original, payload in entries:
                info = zipfile.ZipInfo(original.filename, date_time=(1980, 1, 1, 0, 0, 0))
                info.compress_type = zipfile.ZIP_DEFLATED
                info.external_attr = original.external_attr
                info.create_system = 0
                target.writestr(info, payload)
        os.replace(temp_name, path)
    except BaseException:
        Path(temp_name).unlink(missing_ok=True)
        raise


def redact_text(value: str) -> tuple[str, dict[str, int]]:
    counts = {"email": 0, "phone": 0, "address_line": 0}

    def email(_: re.Match[str]) -> str:
        counts["email"] += 1
        return "[REDACTED EMAIL]"

    def phone(_: re.Match[str]) -> str:
        counts["phone"] += 1
        return "[REDACTED PHONE]"

    redacted = EMAIL_RE.sub(email, value)
    redacted = PHONE_RE.sub(phone, redacted)
    lines: list[str] = []
    for line in redacted.splitlines(keepends=True):
        if ADDRESS_HINT_RE.search(line) and any(character.isdigit() for character in line):
            suffix = "\n" if line.endswith("\n") else ""
            lines.append(f"[REDACTED ADDRESS]{suffix}")
            counts["address_line"] += 1
        else:
            lines.append(line)
    return "".join(lines), counts


def sanitize_json(value: Any, counts: dict[str, int]) -> Any:
    removed_keys = {
        "contributor",
        "contributors",
        "downloaded_at",
        "lastrevid",
        "modified",
        "revision_user",
        "timestamp",
        "user",
        "username",
    }
    if isinstance(value, Mapping):
        result: dict[str, Any] = {}
        for key, item in value.items():
            if str(key).casefold() in removed_keys:
                counts["dynamic_keys_removed"] = counts.get("dynamic_keys_removed", 0) + 1
                continue
            result[str(key)] = sanitize_json(item, counts)
        return result
    if isinstance(value, list):
        return [sanitize_json(item, counts) for item in value]
    if isinstance(value, str):
        redacted, replacements = redact_text(value)
        for key, amount in replacements.items():
            counts[key] = counts.get(key, 0) + amount
        return redacted
    return value


def ensure_relative_records(report: dict[str, Any]) -> None:
    serialized = json.dumps(report, ensure_ascii=False)
    forbidden = (str(PROJECT_ROOT), "/root/", "C:\\Users\\")
    if any(item in serialized for item in forbidden):
        raise ValueError("Dataset report contains an absolute local path")
