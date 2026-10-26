from __future__ import annotations

import argparse
import io
import json
import re
from pathlib import Path
from typing import Any

import pymupdf
from PIL import Image

from data.tools.common import (
    ADDRESS_HINT_RE,
    EMAIL_RE,
    PHONE_RE,
    PUBLIC_LOCK,
    PUBLIC_MANIFEST,
    PUBLIC_ROOT,
    atomic_write,
    load_yaml,
    sanitize_json,
    sha256_file,
    write_json,
)

RIGHTS_RE = re.compile(r"(?i)(?:photo|image|figure)\s*(?:credit|copyright)|©")
SAFE_RIGHTS_RE = re.compile(r"(?i)crown copyright|NIST|association for computational linguistics")
SIGNATURE_RE = re.compile(r"(?i)\b(?:signed|signature)\b|签名")
LICENSE_RE = re.compile(r"(?i)licen[cs]e|copyright|creative commons|open government")


def _likely_qr(payload: bytes) -> bool:
    try:
        with Image.open(io.BytesIO(payload)) as image:
            width, height = image.size
            if min(width, height) < 80 or abs(width - height) > max(width, height) * 0.12:
                return False
            gray = image.convert("L").resize((64, 64))
            pixels = list(gray.get_flattened_data())
            black = sum(value < 55 for value in pixels) / len(pixels)
            white = sum(value > 200 for value in pixels) / len(pixels)
            transitions = 0
            for y in range(0, 64, 4):
                row = [pixels[y * 64 + x] < 128 for x in range(64)]
                transitions += sum(left != right for left, right in zip(row, row[1:], strict=False))
            return 0.12 <= black <= 0.65 and white >= 0.25 and transitions >= 90
    except Exception:
        return False


def _redact_matches(page: pymupdf.Page, pattern: re.Pattern[str], label: str) -> int:
    text = page.get_text("text")
    count = 0
    for match in pattern.finditer(text):
        matched = match.group(0).strip()
        if not matched:
            continue
        for rect in page.search_for(matched):
            page.add_redact_annot(rect, fill=(1, 1, 1), text=f"[{label}]", fontsize=6)
            count += 1
    return count


def _redact_address_lines(page: pymupdf.Page) -> int:
    count = 0
    for block in page.get_text("blocks"):
        text = str(block[4])
        if ADDRESS_HINT_RE.search(text) and any(character.isdigit() for character in text):
            rect = pymupdf.Rect(block[:4])
            page.add_redact_annot(rect, fill=(1, 1, 1), text="[REDACTED ADDRESS]", fontsize=6)
            count += 1
    return count


def _image_rectangles(document: pymupdf.Document, page: pymupdf.Page) -> list[pymupdf.Rect]:
    rectangles: list[pymupdf.Rect] = []
    seen: set[tuple[float, float, float, float]] = set()
    for image in page.get_images(full=True):
        xref = int(image[0])
        try:
            extracted = document.extract_image(xref)
        except RuntimeError:
            continue
        if not _likely_qr(extracted.get("image", b"")):
            continue
        for rect in page.get_image_rects(xref):
            key = tuple(round(value, 3) for value in rect)
            if key not in seen:
                seen.add(key)
                rectangles.append(rect)
    return rectangles


def _sanitize_pdf(
    source: Path,
    target: Path,
    smoke_target: Path,
    *,
    third_party_caveat: bool,
) -> dict[str, Any]:
    document = pymupdf.open(source)
    counts = {
        "email": 0,
        "phone": 0,
        "address_line": 0,
        "signature_image": 0,
        "qr_image": 0,
        "third_party_image": 0,
    }
    page_features: list[dict[str, Any]] = []
    for page_index, page in enumerate(document):
        page_text = page.get_text("text")
        counts["email"] += _redact_matches(page, EMAIL_RE, "REDACTED EMAIL")
        counts["phone"] += _redact_matches(page, PHONE_RE, "REDACTED PHONE")
        counts["address_line"] += _redact_address_lines(page)
        image_rects = [
            rect
            for image in page.get_images(full=True)
            for rect in page.get_image_rects(image[0])
        ]
        for rect in _image_rectangles(document, page):
            page.add_redact_annot(rect, fill=(1, 1, 1), text="[REDACTED QR]", fontsize=6)
            counts["qr_image"] += 1
        if SIGNATURE_RE.search(page_text):
            for rect in image_rects:
                if rect.y0 >= page.rect.height * 0.55:
                    page.add_redact_annot(
                        rect,
                        fill=(1, 1, 1),
                        text="[REDACTED SIGNATURE]",
                        fontsize=6,
                    )
                    counts["signature_image"] += 1
        third_party = (
            third_party_caveat
            and bool(RIGHTS_RE.search(page_text))
            and not bool(SAFE_RIGHTS_RE.search(page_text))
        )
        if third_party:
            for rect in image_rects:
                page.add_redact_annot(
                    rect,
                    fill=(1, 1, 1),
                    text="[THIRD-PARTY IMAGE REMOVED]",
                    fontsize=6,
                )
                counts["third_party_image"] += 1
        page.apply_redactions(images=2, graphics=1)
        drawing_count = len(page.get_drawings())
        try:
            table_count = len(page.find_tables().tables)
        except Exception:
            table_count = 0
        page_features.append(
            {
                "page": page_index + 1,
                "text_characters": len(page_text.strip()),
                "images": len(image_rects),
                "drawings": drawing_count,
                "tables": table_count,
                "license_text": bool(LICENSE_RE.search(page_text)),
                "third_party_images_removed": third_party,
            }
        )
    document.scrub(
        attached_files=True,
        clean_pages=True,
        embedded_files=True,
        hidden_text=False,
        javascript=True,
        metadata=True,
        redactions=True,
        redact_images=0,
        remove_links=True,
        reset_fields=True,
        reset_responses=True,
        thumbnails=True,
        xml_metadata=True,
    )
    document.set_metadata({})
    target.parent.mkdir(parents=True, exist_ok=True)
    document.save(
        target,
        garbage=4,
        clean=True,
        deflate=True,
        deflate_images=True,
        deflate_fonts=True,
        no_new_id=True,
        preserve_metadata=False,
        reproducible=True,
    )
    document.close()

    selected = _select_smoke_pages(page_features)
    sanitized = pymupdf.open(target)
    smoke = pymupdf.open()
    for page_number in selected:
        smoke.insert_pdf(sanitized, from_page=page_number - 1, to_page=page_number - 1)
    smoke.set_metadata({})
    smoke_target.parent.mkdir(parents=True, exist_ok=True)
    smoke.save(
        smoke_target,
        garbage=4,
        clean=True,
        deflate=True,
        no_new_id=True,
        preserve_metadata=False,
        reproducible=True,
    )
    smoke.close()
    sanitized.close()
    return {"redactions": counts, "pages": page_features, "smoke_source_pages": selected}


def _select_smoke_pages(features: list[dict[str, Any]]) -> list[int]:
    if not features:
        return []
    selected: list[int] = [1]

    def add_best(key: str) -> None:
        best = max(features, key=lambda item: int(item[key]))
        if int(best[key]) > 0 and int(best["page"]) not in selected:
            selected.append(int(best["page"]))

    for feature in ("license_text", "images", "tables", "drawings", "text_characters"):
        add_best(feature)
    for item in sorted(features, key=lambda value: int(value["page"])):
        if len(selected) >= min(12, len(features)):
            break
        page_number = int(item["page"])
        if page_number not in selected:
            selected.append(page_number)
    return sorted(selected[:12])


def _sanitize_json_file(source: Path, target: Path, smoke_target: Path) -> dict[str, Any]:
    payload = json.loads(source.read_text(encoding="utf-8-sig"))
    counts: dict[str, int] = {}
    sanitized = sanitize_json(payload, counts)
    write_json(target, sanitized)
    atomic_write(smoke_target, target.read_bytes())
    return {"redactions": counts, "smoke_source_pages": []}


def sanitize_public(
    *,
    manifest_path: Path = PUBLIC_MANIFEST,
    lock_path: Path = PUBLIC_LOCK,
    public_root: Path = PUBLIC_ROOT,
) -> dict[str, Any]:
    manifest = load_yaml(manifest_path)
    if not lock_path.exists():
        raise FileNotFoundError("Run fetch_public.py before sanitization")
    lock = json.loads(lock_path.read_text(encoding="utf-8"))
    locked = {str(item["id"]): item for item in lock["sources"]}
    reports: list[dict[str, Any]] = []
    originals = public_root / "originals"
    sanitized_root = public_root / "sanitized"
    smoke_root = public_root / "smoke"
    provenance = public_root / "provenance" / "local"
    for source in manifest["sources"]:
        source_id = str(source["id"])
        source_path = originals / str(source["filename"])
        locked_record = locked[source_id]
        if sha256_file(source_path) != locked_record["sha256"]:
            raise RuntimeError(f"SOURCE_HASH_CHANGED:{source_id}")
        target = sanitized_root / source_path.name
        smoke_target = smoke_root / source_path.name
        if source["media_type"] == "application/pdf":
            details = _sanitize_pdf(
                source_path,
                target,
                smoke_target,
                third_party_caveat=bool(source.get("third_party_caveat", False)),
            )
        elif source["media_type"] == "application/json":
            target.parent.mkdir(parents=True, exist_ok=True)
            smoke_target.parent.mkdir(parents=True, exist_ok=True)
            details = _sanitize_json_file(source_path, target, smoke_target)
        else:
            raise ValueError(f"Unsupported public media type: {source['media_type']}")
        report = {
            "id": source_id,
            "license_id": source["license_id"],
            "source_sha256": sha256_file(source_path),
            "sanitized_sha256": sha256_file(target),
            "smoke_sha256": sha256_file(smoke_target),
            **details,
        }
        write_json(provenance / f"{source_id}.json", report)
        reports.append(report)
    summary = {"schema_version": 1, "level": "research-safe", "sources": reports}
    write_json(public_root / "dataset-report.json", summary)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Sanitize public PrismKE test sources")
    parser.add_argument("--level", choices=["research-safe"], default="research-safe")
    parser.add_argument("--manifest", type=Path, default=PUBLIC_MANIFEST)
    parser.add_argument("--lock", type=Path, default=PUBLIC_LOCK)
    parser.add_argument("--public-root", type=Path, default=PUBLIC_ROOT)
    arguments = parser.parse_args()
    result = sanitize_public(
        manifest_path=arguments.manifest,
        lock_path=arguments.lock,
        public_root=arguments.public_root,
    )
    print(f"Sanitized {len(result['sources'])} public sources")


if __name__ == "__main__":
    main()
