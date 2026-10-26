from __future__ import annotations

import argparse
import json
import subprocess
import zipfile
from pathlib import Path
from typing import Any

import pymupdf

from data.tools.common import (
    DATA_ROOT,
    EMAIL_RE,
    PHONE_RE,
    PROJECT_ROOT,
    ensure_relative_records,
    load_yaml,
    sha256_file,
    write_json,
)

PUBLIC_BINARY_DIRS = {"originals", "sanitized", "smoke"}


def _verify_synthetic(root: Path) -> dict[str, Any]:
    manifest_path = root / "manifest.json"
    if not manifest_path.exists():
        raise FileNotFoundError("Synthetic manifest is missing; run generate_synthetic.py")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    for item in manifest["files"]:
        path = root / item["path"]
        if not path.is_file():
            raise FileNotFoundError(f"Synthetic fixture is missing: {item['path']}")
        if path.stat().st_size != item["bytes"] or sha256_file(path) != item["sha256"]:
            raise RuntimeError(f"SYNTHETIC_HASH_MISMATCH:{item['path']}")
    native_pdf = pymupdf.open(root / "native" / "research-brief.pdf")
    if "Nebula Technology" not in "".join(page.get_text() for page in native_pdf):
        raise RuntimeError("Native PDF lost its searchable text")
    native_pdf.close()
    scan = pymupdf.open(root / "scanned" / "bilingual-scan.pdf")
    if any(page.get_text().strip() for page in scan):
        raise RuntimeError("Scanned PDF unexpectedly contains a native text layer")
    scan.close()
    docx = root / "native" / "research-brief.docx"
    if not zipfile.is_zipfile(docx):
        raise RuntimeError("Synthetic DOCX is not a valid OOXML archive")
    return {
        "manifest_sha256": sha256_file(manifest_path),
        "file_count": len(manifest["files"]),
    }


def _assert_pdf_sanitized(path: Path) -> None:
    document = pymupdf.open(path)
    sensitive_metadata = {
        key: document.metadata.get(key)
        for key in (
            "title",
            "author",
            "subject",
            "keywords",
            "creator",
            "producer",
            "creationDate",
            "modDate",
            "trapped",
        )
    }
    if any(value for value in sensitive_metadata.values()):
        raise RuntimeError(f"PDF metadata was not fully removed: {path.name}")
    if document.embfile_count() > 0:
        raise RuntimeError(f"PDF still contains embedded files: {path.name}")
    if document.is_form_pdf:
        raise RuntimeError(f"PDF still contains an interactive form: {path.name}")
    text = "\n".join(page.get_text("text") for page in document)
    if EMAIL_RE.search(text) or PHONE_RE.search(text):
        raise RuntimeError(f"PDF still contains detected contact information: {path.name}")
    unsafe_tokens = ("/JavaScript", "/S /Launch", "/S /SubmitForm", "/S /ImportData")
    for xref in range(1, document.xref_length()):
        try:
            object_text = document.xref_object(xref, compressed=False)
        except RuntimeError:
            continue
        if any(token in object_text for token in unsafe_tokens):
            raise RuntimeError(f"PDF still contains active content: {path.name}")
    document.close()


def _verify_public(root: Path, lock_path: Path, manifest_path: Path) -> dict[str, Any]:
    if not lock_path.exists():
        raise FileNotFoundError("Public source lock is missing; run fetch_public.py")
    lock = json.loads(lock_path.read_text(encoding="utf-8"))
    manifest = load_yaml(manifest_path)
    sources = {str(item["id"]): item for item in manifest["sources"]}
    stable_sources: list[dict[str, Any]] = []
    for item in lock["sources"]:
        source_id = str(item["id"])
        source = sources[source_id]
        original = root / "originals" / str(item["filename"])
        sanitized = root / "sanitized" / str(item["filename"])
        smoke = root / "smoke" / str(item["filename"])
        if not original.exists() or sha256_file(original) != item["sha256"]:
            raise RuntimeError(f"PUBLIC_SOURCE_MISSING_OR_CHANGED:{source_id}")
        if not sanitized.exists() or not smoke.exists():
            raise FileNotFoundError(f"Sanitized outputs are missing for {source_id}")
        if source["media_type"] == "application/pdf":
            _assert_pdf_sanitized(sanitized)
            _assert_pdf_sanitized(smoke)
        else:
            for candidate in (sanitized, smoke):
                payload = candidate.read_text(encoding="utf-8")
                json.loads(payload)
                if EMAIL_RE.search(payload) or PHONE_RE.search(payload):
                    message = f"JSON still contains detected contact data: {candidate.name}"
                    raise RuntimeError(message)
        local_report = root / "provenance" / "local" / f"{source_id}.json"
        if not local_report.exists():
            raise FileNotFoundError(f"Transformation report is missing for {source_id}")
        report = json.loads(local_report.read_text(encoding="utf-8"))
        if report["source_sha256"] != item["sha256"]:
            raise RuntimeError(f"Provenance source hash mismatch: {source_id}")
        stable_sources.append(
            {
                "id": source_id,
                "license_id": source["license_id"],
                "source_sha256": item["sha256"],
                "sanitized_sha256": sha256_file(sanitized),
                "smoke_sha256": sha256_file(smoke),
                "smoke_source_pages": report.get("smoke_source_pages", []),
            }
        )
    return {
        "lock_sha256": sha256_file(lock_path),
        "source_count": len(stable_sources),
        "sources": stable_sources,
    }


def _verify_git_boundary(project_root: Path) -> None:
    process = subprocess.run(
        ["git", "ls-files", "data/public"],
        cwd=project_root,
        check=True,
        capture_output=True,
        text=True,
    )
    for line in process.stdout.splitlines():
        parts = Path(line).parts
        if len(parts) >= 3 and parts[2] in PUBLIC_BINARY_DIRS:
            raise RuntimeError(f"Public binary output is tracked by Git: {line}")


def verify_dataset(
    *,
    strict: bool,
    data_root: Path = DATA_ROOT,
) -> dict[str, Any]:
    synthetic = _verify_synthetic(data_root / "synthetic")
    report: dict[str, Any] = {"schema_version": 1, "synthetic": synthetic}
    if strict:
        report["public"] = _verify_public(
            data_root / "public",
            data_root / "public" / "manifest.lock.json",
            data_root / "manifests" / "public_sources.yaml",
        )
    _verify_git_boundary(PROJECT_ROOT)
    ensure_relative_records(report)
    write_json(data_root / "dataset-report.json", report)
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description="Verify the PrismKE evaluation dataset")
    parser.add_argument("--strict", action="store_true")
    parser.add_argument("--data-root", type=Path, default=DATA_ROOT)
    arguments = parser.parse_args()
    report = verify_dataset(strict=arguments.strict, data_root=arguments.data_root)
    public_count = report.get("public", {}).get("source_count", 0)
    print(
        f"Verified {report['synthetic']['file_count']} synthetic files "
        f"and {public_count} public sources"
    )


if __name__ == "__main__":
    main()
