from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import httpx

from data.tools.common import (
    PUBLIC_LOCK,
    PUBLIC_MANIFEST,
    PUBLIC_ROOT,
    load_yaml,
    sha256_file,
    write_json,
)

ALLOWED_HOSTS = {
    "aclanthology.org",
    "airc.nist.gov",
    "assets.publishing.service.gov.uk",
    "nvlpubs.nist.gov",
    "www.wikidata.org",
}
ALLOWED_TYPES = {"application/json", "application/pdf", "application/octet-stream"}


def _validate_url(url: str) -> None:
    parsed = urlparse(url)
    if parsed.scheme != "https":
        raise ValueError(f"Only HTTPS sources are permitted: {url}")
    if parsed.hostname not in ALLOWED_HOSTS:
        raise ValueError(f"Source host is not allowlisted: {parsed.hostname}")
    if parsed.username or parsed.password:
        raise ValueError("Credentials are not permitted in source URLs")


def _validate_payload(path: Path, expected_type: str) -> None:
    prefix = path.read_bytes()[:16]
    if expected_type == "application/pdf" and not prefix.startswith(b"%PDF-"):
        raise ValueError(f"Downloaded file is not a PDF: {path.name}")
    if expected_type == "application/json":
        try:
            json.loads(path.read_text(encoding="utf-8-sig"))
        except (UnicodeDecodeError, json.JSONDecodeError) as error:
            raise ValueError(f"Downloaded file is not valid JSON: {path.name}") from error


def _download(
    client: httpx.Client,
    source: dict[str, Any],
    target: Path,
) -> tuple[str, int]:
    url = str(source["download_url"])
    _validate_url(url)
    maximum = int(source["max_bytes"])
    partial = target.with_suffix(target.suffix + ".part")
    headers: dict[str, str] = {}
    existing = partial.stat().st_size if partial.exists() else 0
    if existing:
        headers["Range"] = f"bytes={existing}-"
    with client.stream("GET", url, headers=headers) as response:
        response.raise_for_status()
        _validate_url(str(response.url))
        content_type = response.headers.get("content-type", "").split(";", 1)[0].strip()
        if content_type and content_type not in ALLOWED_TYPES:
            raise ValueError(f"Unexpected content type {content_type!r} for {source['id']}")
        append = existing > 0 and response.status_code == 206
        if not append:
            existing = 0
        mode = "ab" if append else "wb"
        partial.parent.mkdir(parents=True, exist_ok=True)
        with partial.open(mode) as stream:
            total = existing
            for chunk in response.iter_bytes(1024 * 1024):
                total += len(chunk)
                if total > maximum:
                    raise ValueError(f"Source exceeds max_bytes: {source['id']}")
                stream.write(chunk)
            stream.flush()
            os.fsync(stream.fileno())
    _validate_payload(partial, str(source["media_type"]))
    os.replace(partial, target)
    return content_type or str(source["media_type"]), target.stat().st_size


def fetch_public(
    *,
    manifest_path: Path = PUBLIC_MANIFEST,
    lock_path: Path = PUBLIC_LOCK,
    output: Path = PUBLIC_ROOT / "originals",
    refresh_lock: bool = False,
) -> dict[str, Any]:
    manifest = load_yaml(manifest_path)
    sources = manifest.get("sources")
    if not isinstance(sources, list) or not sources:
        raise ValueError("Public source manifest contains no sources")
    old_lock: dict[str, Any] = {}
    if lock_path.exists():
        old_lock = json.loads(lock_path.read_text(encoding="utf-8"))
    old_records = {
        str(item["id"]): item for item in old_lock.get("sources", []) if isinstance(item, dict)
    }
    lock_records: list[dict[str, Any]] = []
    with httpx.Client(
        follow_redirects=True,
        max_redirects=5,
        timeout=httpx.Timeout(120.0, connect=30.0),
        headers={
            "User-Agent": (
                "PrismKEResearchDataset/1.0 "
                "(academic evaluation corpus; https://github.com/FUSHENG1221/PrismKE)"
            )
        },
    ) as client:
        for raw_source in sources:
            if not isinstance(raw_source, dict):
                raise ValueError("Each source entry must be an object")
            source = dict(raw_source)
            source_id = str(source["id"])
            target = output / str(source["filename"])
            target.parent.mkdir(parents=True, exist_ok=True)
            content_type = str(source["media_type"])
            if not target.exists():
                content_type, _ = _download(client, source, target)
            else:
                _validate_payload(target, content_type)
            actual_hash = sha256_file(target)
            actual_bytes = target.stat().st_size
            previous = old_records.get(source_id)
            if previous and not refresh_lock:
                expected_hash = str(previous["sha256"])
                expected_bytes = int(previous["bytes"])
                if actual_hash != expected_hash or actual_bytes != expected_bytes:
                    message = (
                        f"SOURCE_HASH_CHANGED:{source_id}: "
                        f"expected {expected_hash}, got {actual_hash}"
                    )
                    raise RuntimeError(message)
            lock_records.append(
                {
                    "id": source_id,
                    "filename": target.name,
                    "download_url": str(source["download_url"]),
                    "license_id": str(source["license_id"]),
                    "media_type": str(source["media_type"]),
                    "content_type": content_type,
                    "bytes": actual_bytes,
                    "sha256": actual_hash,
                }
            )
    lock = {"schema_version": 1, "sources": sorted(lock_records, key=lambda item: item["id"])}
    if old_lock and old_lock != lock and not refresh_lock:
        raise RuntimeError("SOURCE_LOCK_CHANGED: use --refresh-lock only after manual review")
    write_json(lock_path, lock)
    return lock


def main() -> None:
    parser = argparse.ArgumentParser(description="Fetch locked public PrismKE test sources")
    parser.add_argument("--accept-licenses", action="store_true")
    parser.add_argument("--refresh-lock", action="store_true")
    parser.add_argument("--manifest", type=Path, default=PUBLIC_MANIFEST)
    parser.add_argument("--lock", type=Path, default=PUBLIC_LOCK)
    parser.add_argument("--output", type=Path, default=PUBLIC_ROOT / "originals")
    arguments = parser.parse_args()
    if not arguments.accept_licenses:
        parser.error("--accept-licenses is required after reviewing data/public/licenses/README.md")
    lock = fetch_public(
        manifest_path=arguments.manifest,
        lock_path=arguments.lock,
        output=arguments.output,
        refresh_lock=arguments.refresh_lock,
    )
    print(f"Fetched and verified {len(lock['sources'])} public sources")


if __name__ == "__main__":
    main()
