from __future__ import annotations

import argparse
import ast
import hashlib
import json
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path

from PIL import Image

IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png", ".webp"}


@dataclass(frozen=True)
class DatasetReport:
    dataset: str
    file_count: int
    image_count: int
    annotation_count: int
    unique_image_references: int
    missing_image_references: int
    corrupt_image_count: int
    checksum_manifest_sha256: str


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _dataset_files(root: Path) -> list[Path]:
    files: list[Path] = []
    for directory_name in ("annotations", "images"):
        directory = root / directory_name
        if not directory.is_dir():
            raise ValueError(f"Missing required directory: {directory}")
        files.extend(path for path in directory.rglob("*") if path.is_file())
    return sorted(files, key=lambda path: path.relative_to(root).as_posix())


def _image_files(root: Path) -> list[Path]:
    return sorted(
        (
            path
            for path in (root / "images").rglob("*")
            if path.is_file() and path.suffix.lower() in IMAGE_SUFFIXES
        ),
        key=lambda path: path.relative_to(root).as_posix(),
    )


def _classify_image_failure(path: Path) -> str | None:
    if path.stat().st_size == 0:
        return "empty"
    with path.open("rb") as handle:
        prefix = handle.read(256).lstrip().lower()
    if prefix.startswith(b"<!doctype html") or prefix.startswith(b"<html"):
        return "html"
    try:
        with Image.open(path) as image:
            image.verify()
    except Exception:
        return "decode_error"
    return None


def _ensure_unique_image_names(images: Iterable[Path]) -> dict[str, Path]:
    by_name: dict[str, Path] = {}
    duplicates: list[str] = []
    for image in images:
        if image.name in by_name:
            duplicates.append(image.name)
        by_name[image.name] = image
    if duplicates:
        raise ValueError(f"Duplicate image names: {sorted(set(duplicates))[:10]}")
    return by_name


def _twitter_references(root: Path) -> tuple[list[str], dict[str, int]]:
    expected_splits = {"train.txt": 3373, "valid.txt": 723, "test.txt": 723}
    references: list[str] = []
    split_counts: dict[str, int] = {}
    for filename, expected in expected_splits.items():
        path = root / "annotations" / filename
        if not path.is_file():
            raise ValueError(f"Missing annotation file: {path}")
        values = [
            line.split(":", 1)[1].strip()
            for line in path.read_text(encoding="utf-8", errors="replace").splitlines()
            if line.startswith("IMGID:")
        ]
        split_counts[filename] = len(values)
        if len(values) != expected:
            raise ValueError(
                f"Unexpected Twitter2017 {filename} count: {len(values)} != {expected}"
            )
        references.extend(values)
    return references, split_counts


def _mnre_references(root: Path) -> tuple[list[str], dict[str, int]]:
    expected_splits = {
        "mnre_train.txt": 12247,
        "mnre_val.txt": 1624,
        "mnre_test.txt": 1614,
    }
    references: list[str] = []
    split_counts: dict[str, int] = {}
    for filename, expected in expected_splits.items():
        path = root / "annotations" / filename
        if not path.is_file():
            raise ValueError(f"Missing annotation file: {path}")
        values: list[str] = []
        for line_number, line in enumerate(
            path.read_text(encoding="utf-8", errors="strict").splitlines(), start=1
        ):
            if not line.strip():
                continue
            record = ast.literal_eval(line)
            image_id = record.get("img_id")
            if not isinstance(image_id, str) or not image_id:
                raise ValueError(f"Invalid img_id in {path}:{line_number}")
            values.append(image_id)
        split_counts[filename] = len(values)
        if len(values) != expected:
            raise ValueError(
                f"Unexpected MNRE-V2 {filename} count: {len(values)} != {expected}"
            )
        references.extend(values)
    return references, split_counts


def _write_checksum_manifest(root: Path, output_path: Path) -> tuple[int, str]:
    files = _dataset_files(root)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    temporary = output_path.with_suffix(output_path.suffix + ".tmp")
    with temporary.open("w", encoding="utf-8", newline="\n") as handle:
        for path in files:
            relative = path.relative_to(root).as_posix()
            handle.write(f"{_sha256(path)}  {relative}\n")
    temporary.replace(output_path)
    return len(files), _sha256(output_path)


def _validate_twitter(root: Path, manifest_dir: Path) -> DatasetReport:
    references, _ = _twitter_references(root)
    images = _image_files(root)
    _ensure_unique_image_names(images)
    available_stems = {path.stem for path in images}
    missing = sorted(set(references) - available_stems)
    if len(images) != 4819 or len(references) != 4819 or len(set(references)) != 4819:
        raise ValueError("Twitter2017 counts do not match the 4,819-sample benchmark")
    if missing:
        raise ValueError(f"Twitter2017 missing image references: {missing[:10]}")

    invalid: list[dict[str, object]] = []
    for image in images:
        reason = _classify_image_failure(image)
        if reason is not None:
            invalid.append(
                {
                    "path": image.relative_to(root).as_posix(),
                    "filename": image.name,
                    "size_bytes": image.stat().st_size,
                    "reason": reason,
                }
            )
    if len(invalid) != 358:
        raise ValueError(f"Unexpected Twitter2017 invalid image count: {len(invalid)} != 358")

    invalid_path = manifest_dir / "twitter2017.invalid-images.json"
    invalid_path.parent.mkdir(parents=True, exist_ok=True)
    invalid_path.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "dataset": "twitter2017",
                "policy": "preserve-original-and-fallback-to-placeholder-at-load-time",
                "invalid_image_count": len(invalid),
                "images": invalid,
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    file_count, manifest_sha = _write_checksum_manifest(
        root, manifest_dir / "twitter2017.sha256"
    )
    return DatasetReport(
        dataset="twitter2017",
        file_count=file_count,
        image_count=len(images),
        annotation_count=len(references),
        unique_image_references=len(set(references)),
        missing_image_references=0,
        corrupt_image_count=len(invalid),
        checksum_manifest_sha256=manifest_sha,
    )


def _validate_mnre(root: Path, manifest_dir: Path) -> DatasetReport:
    references, _ = _mnre_references(root)
    images = _image_files(root)
    by_name = _ensure_unique_image_names(images)
    missing = sorted(set(references) - set(by_name))
    if len(images) != 9201 or len(references) != 15485 or len(set(references)) != 9201:
        raise ValueError("MNRE-V2 counts do not match the expected benchmark")
    if missing:
        raise ValueError(f"MNRE-V2 missing image references: {missing[:10]}")
    invalid = [image for image in images if _classify_image_failure(image) is not None]
    if invalid:
        raise ValueError(f"MNRE-V2 contains invalid images: {invalid[:10]}")

    file_count, manifest_sha = _write_checksum_manifest(
        root, manifest_dir / "mnre-v2.sha256"
    )
    return DatasetReport(
        dataset="mnre-v2",
        file_count=file_count,
        image_count=len(images),
        annotation_count=len(references),
        unique_image_references=len(set(references)),
        missing_image_references=0,
        corrupt_image_count=0,
        checksum_manifest_sha256=manifest_sha,
    )


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Validate PrismKE evaluation benchmarks and write checksum manifests."
    )
    parser.add_argument("--twitter-root", type=Path, required=True)
    parser.add_argument("--mnre-root", type=Path, required=True)
    parser.add_argument("--manifest-dir", type=Path, required=True)
    args = parser.parse_args()

    twitter = _validate_twitter(args.twitter_root.resolve(), args.manifest_dir.resolve())
    mnre = _validate_mnre(args.mnre_root.resolve(), args.manifest_dir.resolve())
    print(
        json.dumps(
            {
                "schema_version": 1,
                "datasets": [twitter.__dict__, mnre.__dict__],
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
