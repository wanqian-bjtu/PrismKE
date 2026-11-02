"""Isolated MNRE-V2 case-library and schema-guided relation evaluation."""

from __future__ import annotations

import ast
import asyncio
import json
import math
import os
import random
import struct
import subprocess
from collections import Counter, defaultdict
from functools import lru_cache
from hashlib import sha256
from pathlib import Path
from typing import Any, Literal

import yaml
from pydantic import BaseModel, Field

from src.core.errors import ProviderRequestError
from src.core.ids import canonical_hash, file_sha256
from src.core.settings import Settings
from src.domain import ProviderCallRecord
from src.evaluation.twitter2017 import (
    IMAGE_UNAVAILABLE_PROVIDER_FILTER,
    IMAGE_UNAVAILABLE_PROVIDER_RESPONSE,
    CNYBudgetLedger,
    _chat,
    _image_data_url,
    _resolve_local_bge,
    atomic_json,
    load_json,
)
from src.providers.common import parse_json_object
from src.providers.embedding import BGEM3EmbeddingProvider

DATASET_VERSION = "mnre-v2-eval-v1"
CAPTION_PROMPT_VERSION = "mnre-v2-caption-v1"
RE_PROMPT_VERSIONS = ("mnre-v2-re-v1", "mnre-v2-re-v2", "mnre-v2-re-v3")
SCORING_VERSION = "mnre-v2-positive-micro-v1"
NO_RELATION = "NoRelation"

DATASET_TO_CANONICAL = {
    "None": NO_RELATION,
    "/loc/loc/contain": "Contains",
    "/misc/loc/held_on": "HeldAt",
    "/misc/misc/part_of": "PartOf",
    "/org/loc/locate_at": "LocatedAt",
    "/org/org/alternate_names": "OrganizationAlternateName",
    "/org/org/subsidiary": "SubsidiaryOf",
    "/per/loc/place_of_birth": "PlaceOfBirth",
    "/per/loc/place_of_residence": "PlaceOfResidence",
    "/per/misc/awarded": "ReceivedAward",
    "/per/misc/nationality": "HasNationality",
    "/per/misc/present_in": "PresentIn",
    "/per/misc/race": "HasRace",
    "/per/misc/religion": "HasReligion",
    "/per/org/member_of": "MemberOf",
    "/per/per/alternate_names": "PersonAlternateName",
    "/per/per/alumi": "FellowAlumni",
    "/per/per/charges": "ChargeRelation",
    "/per/per/couple": "CoupleWith",
    "/per/per/neighbor": "NeighborOf",
    "/per/per/parent": "ParentOf",
    "/per/per/peer": "PeerWith",
    "/per/per/siblings": "SiblingOf",
}
CANONICAL_TO_DATASET = {value: key for key, value in DATASET_TO_CANONICAL.items()}
ENTITY_TYPE_ALIASES = {
    "per": "Person",
    "org": "Organization",
    "loc": "Location",
    "misc": "Miscellaneous",
}


class EntityMention(BaseModel):
    text: str
    start: int = Field(ge=0)
    end: int = Field(ge=0)


class MNRECase(BaseModel):
    id: str
    split: Literal["train", "validation", "test"]
    line_number: int = Field(ge=1)
    tokens: list[str]
    text: str
    text_sha256: str
    source_sha256: str
    head: EntityMention
    tail: EntityMention
    image_path: str
    image_sha256: str
    relation: str
    dataset_label: str
    head_type: str | None = None
    tail_type: str | None = None


def load_schema(path: Path) -> dict[str, Any]:
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("MNRE-V2 evaluation schema must be an object")
    relations = payload.get("relations")
    if not isinstance(relations, list):
        raise ValueError("MNRE-V2 evaluation schema requires relations")
    observed = {
        str(item.get("evaluation_label")): str(item.get("id"))
        for item in relations
        if isinstance(item, dict)
    }
    if observed != DATASET_TO_CANONICAL:
        raise ValueError(f"unexpected MNRE-V2 relation mapping: {observed}")
    entities = payload.get("entity_types")
    if not isinstance(entities, list) or {str(item.get("id")) for item in entities} != set(
        ENTITY_TYPE_ALIASES.values()
    ):
        raise ValueError("unexpected MNRE-V2 entity type mapping")
    return payload


def _relation_types(label: str) -> tuple[str | None, str | None]:
    if label == "None":
        return None, None
    parts = label.strip("/").split("/")
    if (
        len(parts) != 3
        or parts[0] not in ENTITY_TYPE_ALIASES
        or parts[1] not in ENTITY_TYPE_ALIASES
    ):
        raise ValueError(f"invalid MNRE-V2 relation label: {label}")
    return ENTITY_TYPE_ALIASES[parts[0]], ENTITY_TYPE_ALIASES[parts[1]]


def _parse_mention(
    raw: dict[str, Any],
    key: str,
    tokens: list[str],
    annotation_path: Path,
    line_number: int,
) -> EntityMention:
    value = raw[key]
    if not isinstance(value, dict) or not isinstance(value.get("name"), str):
        raise ValueError(f"invalid {key} mention at {annotation_path}:{line_number}")
    position = value.get("pos")
    if (
        not isinstance(position, list)
        or len(position) != 2
        or not all(isinstance(item, int) for item in position)
    ):
        raise ValueError(f"invalid {key} position at {annotation_path}:{line_number}")
    start, end = position
    if start < 0 or end <= start or end > len(tokens):
        raise ValueError(f"out-of-range {key} position at {annotation_path}:{line_number}")
    surface = " ".join(tokens[start:end])
    if surface != value["name"]:
        raise ValueError(
            f"{key} surface mismatch at {annotation_path}:{line_number}: "
            f"{value['name']!r} != {surface!r}"
        )
    return EntityMention(text=surface, start=start, end=end)


def _literal_row(line: str, annotation_path: Path, line_number: int) -> dict[str, Any]:
    try:
        value = ast.literal_eval(line)
    except (SyntaxError, ValueError) as exc:
        raise ValueError(f"invalid annotation at {annotation_path}:{line_number}") from exc
    if not isinstance(value, dict):
        raise ValueError(f"annotation row is not an object at {annotation_path}:{line_number}")
    return value


def parse_annotation_split(
    annotation_path: Path,
    images_dir: Path,
    split: Literal["train", "validation", "test"],
    *,
    image_hash_cache: dict[Path, str] | None = None,
) -> list[MNRECase]:
    cache = image_hash_cache if image_hash_cache is not None else {}
    cases: list[MNRECase] = []
    for line_number, line in enumerate(
        annotation_path.read_text(encoding="utf-8").splitlines(), 1
    ):
        raw = _literal_row(line, annotation_path, line_number)
        if set(raw) != {"token", "h", "t", "img_id", "relation"}:
            raise ValueError(f"unexpected annotation keys at {annotation_path}:{line_number}")
        tokens = raw["token"]
        if not isinstance(tokens, list) or not all(isinstance(token, str) for token in tokens):
            raise ValueError(f"invalid tokens at {annotation_path}:{line_number}")
        text = " ".join(tokens)

        dataset_label = str(raw["relation"])
        if dataset_label not in DATASET_TO_CANONICAL:
            raise ValueError(
                f"unknown relation at {annotation_path}:{line_number}: {dataset_label}"
            )
        image_path = images_dir / str(raw["img_id"])
        if not image_path.is_file():
            raise ValueError(f"missing image at {annotation_path}:{line_number}: {image_path}")
        image_hash = cache.get(image_path)
        if image_hash is None:
            image_hash = file_sha256(image_path)
            cache[image_path] = image_hash
        head_type, tail_type = _relation_types(dataset_label)
        source_payload = {
            "tokens": tokens,
            "head": raw["h"],
            "tail": raw["t"],
            "image": str(raw["img_id"]),
            "relation": dataset_label,
        }
        cases.append(
            MNRECase(
                id=f"{split}:{line_number:05d}",
                split=split,
                line_number=line_number,
                tokens=tokens,
                text=text,
                text_sha256=sha256(text.encode("utf-8")).hexdigest(),
                source_sha256=canonical_hash(source_payload),
                head=_parse_mention(raw, "h", tokens, annotation_path, line_number),
                tail=_parse_mention(raw, "t", tokens, annotation_path, line_number),
                image_path=image_path.as_posix(),
                image_sha256=image_hash,
                relation=DATASET_TO_CANONICAL[dataset_label],
                dataset_label=dataset_label,
                head_type=head_type,
                tail_type=tail_type,
            )
        )
    return cases


def stratified_validation_split(
    cases: list[MNRECase], *, seed: int = 2027, dev_size: int = 200
) -> dict[str, Any]:
    if dev_size <= 0 or dev_size >= len(cases):
        raise ValueError("dev_size must be between zero and the validation size")
    groups: dict[str, list[MNRECase]] = defaultdict(list)
    for case in cases:
        groups[case.dataset_label].append(case)
    rng = random.Random(seed)
    shuffled: dict[str, list[MNRECase]] = {}
    for label in sorted(groups):
        shuffled[label] = sorted(groups[label], key=lambda item: item.id)
        rng.shuffle(shuffled[label])
    exact = {label: len(group) * dev_size / len(cases) for label, group in shuffled.items()}
    quotas = {label: math.floor(value) for label, value in exact.items()}
    remaining = dev_size - sum(quotas.values())
    order = sorted(shuffled, key=lambda label: (-(exact[label] - quotas[label]), label))
    for label in order[:remaining]:
        quotas[label] += 1
    dev = sorted(
        case.id for label, group in shuffled.items() for case in group[: quotas[label]]
    )
    holdout = sorted(
        case.id for label, group in shuffled.items() for case in group[quotas[label] :]
    )
    if len(dev) != dev_size or len(holdout) != len(cases) - dev_size or set(dev) & set(holdout):
        raise AssertionError("validation split invariant failed")
    return {
        "seed": seed,
        "method": "stratified-by-relation-label-v1",
        "prompt_dev": dev,
        "prompt_holdout": holdout,
        "strata": {
            label: {"total": len(shuffled[label]), "prompt_dev": quotas[label]}
            for label in sorted(shuffled)
        },
    }


def _case_fingerprint(case: MNRECase) -> dict[str, Any]:
    return {
        "id": case.id,
        "source_sha256": case.source_sha256,
        "image_sha256": case.image_sha256,
        "head": case.head.model_dump(mode="json"),
        "tail": case.tail.model_dump(mode="json"),
        "relation": case.relation,
    }


def prepare_dataset(dataset_root: Path, schema_path: Path, output: Path) -> dict[str, Any]:
    schema = load_schema(schema_path)
    annotations = dataset_root / "annotations"
    images = dataset_root / "images" / "img_org"
    cache: dict[Path, str] = {}
    train = parse_annotation_split(
        annotations / "mnre_train.txt", images / "train", "train", image_hash_cache=cache
    )
    validation = parse_annotation_split(
        annotations / "mnre_val.txt", images / "val", "validation", image_hash_cache=cache
    )
    test = parse_annotation_split(
        annotations / "mnre_test.txt", images / "test", "test", image_hash_cache=cache
    )
    if (len(train), len(validation), len(test)) != (12247, 1624, 1614):
        raise ValueError("MNRE-V2 split counts do not match the accepted benchmark baseline")

    test_text = {case.text_sha256 for case in test}
    conflict_groups: dict[tuple[str, int, int, int, int], list[MNRECase]] = defaultdict(list)
    for case in [*train, *validation]:
        conflict_groups[
            (
                case.text_sha256,
                case.head.start,
                case.head.end,
                case.tail.start,
                case.tail.end,
            )
        ].append(case)
    conflicts = {
        case.id
        for group in conflict_groups.values()
        if {item.split for item in group} == {"train", "validation"}
        and len({item.dataset_label for item in group}) > 1
        for case in group
    }
    test_overlap = {
        case.id for case in [*train, *validation] if case.text_sha256 in test_text
    }
    exclusions: list[dict[str, Any]] = []
    for case in [*train, *validation]:
        reasons = []
        if case.id in test_overlap:
            reasons.append("test_text_overlap")
        if case.id in conflicts:
            reasons.append("cross_split_pair_label_conflict")
        if reasons:
            exclusions.append(
                {
                    "id": case.id,
                    "split": case.split,
                    "line_number": case.line_number,
                    "dataset_label": case.dataset_label,
                    "reasons": reasons,
                }
            )

    train_cases = [case for case in train if case.id not in test_overlap | conflicts]
    validation_cases = [case for case in validation if case.id not in test_overlap]
    validation_library = [
        case for case in validation if case.id not in test_overlap | conflicts
    ]
    final_cases = [*train_cases, *validation_library]
    split = stratified_validation_split(validation_cases)
    if (
        len(train_cases) != 12239
        or len(validation_cases) != 1623
        or len(final_cases) != 13856
        or len(exclusions) != 15
    ):
        raise AssertionError("MNRE-V2 cleaning invariants failed")

    output.mkdir(parents=True, exist_ok=True)
    atomic_json(output / "train_cases.json", [case.model_dump(mode="json") for case in train_cases])
    atomic_json(
        output / "validation_cases.json",
        [case.model_dump(mode="json") for case in validation_cases],
    )
    atomic_json(
        output / "validation_library_cases.json",
        [case.model_dump(mode="json") for case in validation_library],
    )
    atomic_json(output / "exclusions.json", exclusions)
    atomic_json(output / "validation_split.json", split)
    manifest = {
        "dataset_version": DATASET_VERSION,
        "dataset_root": dataset_root.as_posix(),
        "schema_hash": canonical_hash(schema),
        "tuning_case_library_hash": canonical_hash(
            [_case_fingerprint(case) for case in train_cases]
        ),
        "final_case_library_hash": canonical_hash(
            [_case_fingerprint(case) for case in final_cases]
        ),
        "counts": {
            "train_original": len(train),
            "validation_original": len(validation),
            "test_hash_audited_only": len(test),
            "train_tuning_cases": len(train_cases),
            "validation_evaluation_cases": len(validation_cases),
            "validation_library_cases": len(validation_library),
            "final_library_cases": len(final_cases),
            "test_text_overlap_exclusions": len(test_overlap),
            "conflict_exclusions": len(conflicts),
            "unique_train_validation_images_original": len(
                {case.image_sha256 for case in [*train, *validation]}
            ),
            "unique_train_validation_image_ids_original": len(
                {Path(case.image_path).name for case in [*train, *validation]}
            ),
        },
        "label_counts": {
            "train_tuning": dict(
                sorted(Counter(case.dataset_label for case in train_cases).items())
            ),
            "validation_evaluation": dict(
                sorted(Counter(case.dataset_label for case in validation_cases).items())
            ),
            "final_library": dict(
                sorted(Counter(case.dataset_label for case in final_cases).items())
            ),
        },
        "test_artifacts_generated": 0,
        "artifacts": {
            "train_cases": "train_cases.json",
            "validation_cases": "validation_cases.json",
            "validation_library_cases": "validation_library_cases.json",
            "exclusions": "exclusions.json",
            "validation_split": "validation_split.json",
        },
    }
    atomic_json(output / "manifest.json", manifest)
    return manifest


def _caption_prompt() -> str:
    return (
        "Describe only what is directly visible in this image for multimodal relation "
        "retrieval. Mention visible people, organizations, locations, objects, scenes, logos, "
        "and short readable text. Do not infer identities or relationships from hidden labels, "
        "metadata, filenames, or external knowledge. Use one concise English sentence of at "
        "most 60 words. Return JSON only: {\"description\":\"...\"}."
    )


def _caption_path(prepared: Path, image_sha256: str) -> Path:
    return prepared / "captions" / "by-sha256" / f"{image_sha256}.json"


def caption_for_case(prepared: Path, case: MNRECase) -> str:
    return str(load_json(_caption_path(prepared, case.image_sha256))["description"])


def _load_cases(prepared: Path, name: str) -> list[MNRECase]:
    return [MNRECase.model_validate(item) for item in load_json(prepared / f"{name}_cases.json")]


async def generate_captions(
    prepared: Path,
    settings: Settings,
    *,
    split: Literal["train", "validation", "all", "final", "test"] = "all",
    limit: int | None = None,
    smoke: bool = False,
    concurrency: int = 1,
    budget_limit_cny: float = 80.0,
) -> dict[str, Any]:
    if concurrency not in {1, 2}:
        raise ValueError("caption concurrency must be 1 or 2")
    names = ["train", "validation"] if split == "all" else [split]
    selected_cases: list[MNRECase] = []
    for name in names:
        path = prepared / f"{name}_cases.json"
        if not path.exists():
            raise FileNotFoundError(f"case file is unavailable: {path}")
        selected_cases.extend(_load_cases(prepared, name))
    unique: dict[str, MNRECase] = {}
    for case in selected_cases:
        unique.setdefault(case.image_sha256, case)
    selected = list(unique.values())
    if smoke:
        selected = selected[:10]
    if limit is not None:
        selected = selected[:limit]
    ledger = CNYBudgetLedger(prepared / "budget.json", budget_limit_cny)
    next_index = 0
    completed = 0
    resumed = 0
    failed = 0
    first_error: BaseException | None = None
    crossed: list[float] = []

    async def process(case: MNRECase) -> str:
        target = _caption_path(prepared, case.image_sha256)
        if target.exists():
            return "resumed"
        body = {
            "model": settings.vlm_model,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": _caption_prompt()},
                        {
                            "type": "image_url",
                            "image_url": {"url": _image_data_url(Path(case.image_path))},
                        },
                    ],
                }
            ],
            "temperature": 0,
            "max_tokens": 160,
            "enable_thinking": False,
            "response_format": {"type": "json_object"},
        }
        operation_base = f"mnre-v2:caption:{case.image_sha256}"
        for attempt in range(2):
            operation_id = f"{operation_base}:attempt-{attempt + 1}"
            try:
                response, milestones = await _chat(
                    settings,
                    ledger,
                    body,
                    operation_id,
                    CAPTION_PROMPT_VERSION,
                    "vlm",
                )
                crossed.extend(milestones)
            except ProviderRequestError as exc:
                record = exc.call_record
                if (
                    isinstance(record, ProviderCallRecord)
                    and record.error_code == "content_filtered"
                ):
                    atomic_json(
                        target,
                        {
                            "image_sha256": case.image_sha256,
                            "description": IMAGE_UNAVAILABLE_PROVIDER_FILTER,
                            "source": settings.vlm_model,
                            "prompt_version": CAPTION_PROMPT_VERSION,
                            "reason": "provider_content_filter",
                        },
                    )
                    return "completed"
                retryable = (
                    isinstance(record, ProviderCallRecord)
                    and record.error_code == "request_failed"
                )
                if not retryable or attempt == 1:
                    raise
                await asyncio.sleep(2.0)
                continue
            raw = ""
            try:
                raw = str(response["choices"][0]["message"]["content"])
                payload = parse_json_object(raw)
                description = str(payload.get("description", "")).strip()
            except (KeyError, IndexError, TypeError, json.JSONDecodeError):
                description = ""
            if description and len(description.split()) <= 80:
                atomic_json(
                    target,
                    {
                        "image_sha256": case.image_sha256,
                        "description": description,
                        "source": settings.vlm_model,
                        "prompt_version": CAPTION_PROMPT_VERSION,
                    },
                )
                return "completed"
            if attempt == 1:
                atomic_json(
                    target,
                    {
                        "image_sha256": case.image_sha256,
                        "description": IMAGE_UNAVAILABLE_PROVIDER_RESPONSE,
                        "source": settings.vlm_model,
                        "prompt_version": CAPTION_PROMPT_VERSION,
                        "reason": "provider_response_invalid_after_retry",
                    },
                )
                return "completed"
        raise AssertionError("caption retry loop exhausted unexpectedly")

    async def worker() -> None:
        nonlocal next_index, completed, resumed, failed, first_error
        while first_error is None:
            if next_index >= len(selected):
                return
            case = selected[next_index]
            next_index += 1
            try:
                outcome = await process(case)
                if outcome == "completed":
                    completed += 1
                else:
                    resumed += 1
            except BaseException as exc:
                failed += 1
                first_error = exc
                return

    await asyncio.gather(*(worker() for _ in range(concurrency)))
    if first_error is not None:
        raise first_error
    return {
        "selected_unique_images": len(selected),
        "completed": completed,
        "resumed": resumed,
        "failed": failed,
        "estimated_cost_cny": ledger.cost,
        "crossed_milestones": sorted(set(crossed)),
    }


def marked_text(case: MNRECase) -> str:
    markers: dict[int, list[str]] = defaultdict(list)
    markers[case.head.start].append("[HEAD]")
    markers[case.head.end].append("[/HEAD]")
    markers[case.tail.start].append("[TAIL]")
    markers[case.tail.end].append("[/TAIL]")
    output: list[str] = []
    for index, token in enumerate(case.tokens):
        output.extend(markers.get(index, []))
        output.append(token)
    output.extend(markers.get(len(case.tokens), []))
    return " ".join(output)


def retrieval_text(case: MNRECase, description: str) -> str:
    return (
        f"TEXT: {marked_text(case)}\n"
        f"PAIR: head={case.head.text}; tail={case.tail.text}\n"
        f"VISUAL: {description}"
    )


def _write_vectors(path: Path, vectors: list[list[float]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    try:
        with temporary.open("wb") as stream:
            for vector in vectors:
                stream.write(struct.pack(f"<{len(vector)}f", *vector))
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


async def build_vectors(
    prepared: Path,
    settings: Settings,
    *,
    mode: Literal["tuning", "final", "test"] = "tuning",
) -> dict[str, Any]:
    names = ("train", "validation") if mode == "tuning" else (mode,)
    os.environ.setdefault("HF_HUB_OFFLINE", "1")
    os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")
    model_path = _resolve_local_bge(settings)
    provider = BGEM3EmbeddingProvider(
        model_name=str(model_path),
        model_revision=settings.embedding_model_revision,
        device=settings.embedding_device,
        use_fp16=settings.embedding_use_fp16,
        batch_size=min(settings.embedding_batch_size, 32),
        max_tokens=settings.embedding_max_tokens,
        cache_dir=prepared / "embedding-cache",
        model_cache_dir=settings.embedding_model_cache_dir,
        allow_download=False,
    )
    summary: dict[str, Any] = {}
    for name in names:
        cases = _load_cases(prepared, name)
        texts = [retrieval_text(case, caption_for_case(prepared, case)) for case in cases]
        vectors = await provider.encode(texts)
        if len(vectors) != len(cases):
            raise RuntimeError(f"embedding count mismatch for {name}")
        _write_vectors(prepared / "vectors" / f"{name}.f32", vectors)
        metadata = {
            "split": name,
            "ids": [case.id for case in cases],
            "count": len(cases),
            "dimension": provider.dimension,
            "dtype": "float32-le",
            "provider_fingerprint": provider.fingerprint(),
            "input_hash": canonical_hash(texts),
        }
        atomic_json(prepared / "vectors" / f"{name}.json", metadata)
        summary[name] = metadata
    return summary


def _load_matrix(prepared: Path, name: str) -> tuple[list[str], Any]:
    try:
        import numpy as np
    except ImportError as exc:
        raise RuntimeError("MNRE-V2 retrieval requires NumPy") from exc
    metadata = load_json(prepared / "vectors" / f"{name}.json")
    shape = (int(metadata["count"]), int(metadata["dimension"]))
    matrix = np.memmap(
        prepared / "vectors" / f"{name}.f32", dtype="<f4", mode="r", shape=shape
    )
    return [str(item) for item in metadata["ids"]], matrix


@lru_cache(maxsize=4096)
def _semantic_candidates(
    prepared_value: str, index_name: str, query_name: str, query_id: str
) -> tuple[str, ...]:
    try:
        import numpy as np
    except ImportError as exc:
        raise RuntimeError("MNRE-V2 retrieval requires NumPy") from exc
    prepared = Path(prepared_value)
    index_ids, index = _load_matrix(prepared, index_name)
    query_ids, queries = _load_matrix(prepared, query_name)
    query_index = query_ids.index(query_id)
    query = np.asarray(queries[query_index], dtype=np.float32)
    index_array = np.asarray(index, dtype=np.float32)
    denominator = np.linalg.norm(index_array, axis=1) * max(float(np.linalg.norm(query)), 1e-12)
    scores = index_array @ query / np.maximum(denominator, 1e-12)
    indexes = np.argsort(-scores, kind="stable")[:50]
    return tuple(index_ids[int(index_value)] for index_value in indexes)


def retrieve_case_ids(
    prepared: Path,
    query_id: str,
    top_k: int,
    *,
    index_name: Literal["train", "final"] = "train",
    query_name: Literal["validation", "test"] = "validation",
) -> list[str]:
    if top_k not in {1, 3, 5}:
        raise ValueError("top_k must be 1, 3, or 5")
    candidates = _semantic_candidates(str(prepared.resolve()), index_name, query_name, query_id)
    cases = {case.id: case for case in _load_cases(prepared, index_name)}
    selected: list[str] = []
    seen_relations: set[str] = set()
    for case_id in candidates:
        relation = cases[case_id].relation
        if relation in seen_relations:
            continue
        selected.append(case_id)
        seen_relations.add(relation)
        if len(selected) == top_k:
            break
    if len(selected) < top_k:
        for case_id in candidates:
            if case_id not in selected:
                selected.append(case_id)
            if len(selected) == top_k:
                break
    if len(selected) != top_k:
        raise RuntimeError("insufficient retrieval candidates")
    return selected


def _prompt_instruction(version: str) -> str:
    base = (
        "Perform schema-guided multimodal relation classification for the supplied ordered "
        "head-tail entity pair. Select exactly one canonical relation ID from the supplied "
        "Schema. Never invent a relation, re-extract entities, or exchange the head and tail. "
        "Use NoRelation when the text and visible evidence do not support a positive Schema "
        "relation. Return JSON only as {\"relation\":\"MemberOf\"}."
    )
    if version == RE_PROMPT_VERSIONS[0]:
        return base
    if version == RE_PROMPT_VERSIONS[1]:
        return (
            base
            + " Treat direction as part of every non-symmetric relation: the supplied head is "
            "the domain and the supplied tail is the range. A relation supported only in the "
            "reverse direction must not be selected."
        )
    if version == RE_PROMPT_VERSIONS[2]:
        return (
            base
            + " Before answering, silently verify the entity pair, relation direction, Schema "
            "domain/range, and whether the evidence is explicit enough. Prefer NoRelation over "
            "an unsupported guess."
        )
    raise ValueError(f"unknown prompt version: {version}")


def _example_payload(case: MNRECase, description: str) -> dict[str, Any]:
    return {
        "source": marked_text(case),
        "head": case.head.model_dump(mode="json"),
        "tail": case.tail.model_dump(mode="json"),
        "visual_description": description,
        "answer": {"relation": case.relation},
    }


def _relation_prompt(
    schema: dict[str, Any],
    version: str,
    examples: list[dict[str, Any]],
    target: MNRECase,
    target_description: str,
) -> str:
    return (
        f"{_prompt_instruction(version)}\n"
        f"Schema: {json.dumps(schema, ensure_ascii=False)}\n"
        f"Gold training examples: {json.dumps(examples, ensure_ascii=False)}\n"
        f"Target source: {json.dumps(marked_text(target), ensure_ascii=False)}\n"
        f"Target head: {json.dumps(target.head.model_dump(mode='json'), ensure_ascii=False)}\n"
        f"Target tail: {json.dumps(target.tail.model_dump(mode='json'), ensure_ascii=False)}\n"
        f"Target visual description: {json.dumps(target_description, ensure_ascii=False)}"
    )


def validate_prediction(payload: Any) -> tuple[str, list[str]]:
    if not isinstance(payload, dict):
        return NO_RELATION, ["invalid_json_shape"]
    relation = payload.get("relation")
    if not isinstance(relation, str):
        return NO_RELATION, ["invalid_json_shape"]
    if relation not in CANONICAL_TO_DATASET:
        return NO_RELATION, ["relation_not_in_schema"]
    return relation, []


def _result_metrics(case: MNRECase, predicted: str) -> dict[str, Any]:
    gold_positive = case.relation != NO_RELATION
    predicted_positive = predicted != NO_RELATION
    return {
        "gold": case.relation,
        "predicted": predicted,
        "true_positive": int(gold_positive and predicted == case.relation),
        "false_positive": int(predicted_positive and predicted != case.relation),
        "false_negative": int(gold_positive and predicted != case.relation),
        "correct": int(predicted == case.relation),
    }


def _aggregate(results: list[dict[str, Any]]) -> dict[str, Any]:
    tp = sum(int(item["metrics"]["true_positive"]) for item in results)
    fp = sum(int(item["metrics"]["false_positive"]) for item in results)
    fn = sum(int(item["metrics"]["false_negative"]) for item in results)
    correct = sum(int(item["metrics"]["correct"]) for item in results)
    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    micro_f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    per_relation: dict[str, dict[str, Any]] = {}
    f1_values: list[float] = []
    for relation in sorted(set(CANONICAL_TO_DATASET) - {NO_RELATION}):
        relation_tp = sum(
            item["metrics"]["gold"] == relation and item["metrics"]["predicted"] == relation
            for item in results
        )
        relation_fp = sum(
            item["metrics"]["gold"] != relation and item["metrics"]["predicted"] == relation
            for item in results
        )
        relation_fn = sum(
            item["metrics"]["gold"] == relation and item["metrics"]["predicted"] != relation
            for item in results
        )
        relation_precision = (
            relation_tp / (relation_tp + relation_fp) if relation_tp + relation_fp else 0.0
        )
        relation_recall = (
            relation_tp / (relation_tp + relation_fn) if relation_tp + relation_fn else 0.0
        )
        relation_f1 = (
            2 * relation_precision * relation_recall / (relation_precision + relation_recall)
            if relation_precision + relation_recall
            else 0.0
        )
        f1_values.append(relation_f1)
        per_relation[relation] = {
            "support": sum(item["metrics"]["gold"] == relation for item in results),
            "precision": round(relation_precision, 6),
            "recall": round(relation_recall, 6),
            "f1": round(relation_f1, 6),
        }
    confusion: dict[str, Counter[str]] = defaultdict(Counter)
    for item in results:
        confusion[str(item["metrics"]["gold"])][str(item["metrics"]["predicted"])] += 1
    errors = Counter(
        str(error).split(":", 1)[0]
        for item in results
        for error in item.get("errors", [])
    )
    schema = results[0].get("schema_relations", {}) if results else {}
    directional_gold = [
        item
        for item in results
        if item["metrics"]["gold"] != NO_RELATION
        and not bool(schema.get(item["metrics"]["gold"], {}).get("symmetric", False))
    ]
    directional_errors = sum(
        item["metrics"]["gold"] != item["metrics"]["predicted"] for item in directional_gold
    )
    return {
        "cases": len(results),
        "true_positive": tp,
        "false_positive": fp,
        "false_negative": fn,
        "precision": round(precision, 6),
        "recall": round(recall, 6),
        "micro_f1": round(micro_f1, 6),
        "macro_f1_positive_relations": round(sum(f1_values) / len(f1_values), 6),
        "accuracy_all_classes": round(correct / len(results), 6) if results else 0.0,
        "directional_relation_error_rate": (
            round(directional_errors / len(directional_gold), 6) if directional_gold else 0.0
        ),
        "errors": dict(sorted(errors.items())),
        "per_relation": per_relation,
        "confusion_matrix": {
            gold: dict(sorted(predictions.items()))
            for gold, predictions in sorted(confusion.items())
        },
    }


def _git_commit() -> str:
    try:
        return subprocess.run(
            ["git", "rev-parse", "HEAD"], check=True, capture_output=True, text=True
        ).stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        return "unknown"


def _artifact_name(case_id: str) -> str:
    """Return a portable filename for a stable split-qualified case ID."""
    return case_id.replace(":", "-") + ".json"


def _schema_relation_metadata(schema: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {
        str(item["id"]): {
            "symmetric": bool(item.get("symmetric", False)),
            "domain": item.get("domain"),
            "range": item.get("range"),
        }
        for item in schema["relations"]
    }


async def _run_one_prediction(
    prepared: Path,
    settings: Settings,
    ledger: CNYBudgetLedger,
    schema: dict[str, Any],
    index_by_id: dict[str, MNRECase],
    case: MNRECase,
    prompt_version: str,
    top_k: int,
    output: Path,
    *,
    index_name: Literal["train", "final"] = "train",
    query_name: Literal["validation", "test"] = "validation",
) -> dict[str, Any]:
    if output.exists():
        saved = dict(load_json(output))
        if saved.get("scoring_version") == SCORING_VERSION:
            return saved
    retrieved_ids = retrieve_case_ids(
        prepared,
        case.id,
        top_k,
        index_name=index_name,
        query_name=query_name,
    )
    examples = [
        _example_payload(index_by_id[item], caption_for_case(prepared, index_by_id[item]))
        for item in retrieved_ids
    ]
    prompt = _relation_prompt(
        schema, prompt_version, examples, case, caption_for_case(prepared, case)
    )
    body = {
        "model": settings.llm_model,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0,
        "max_tokens": 128,
        "enable_thinking": False,
        "response_format": {"type": "json_object"},
    }
    operation_id = f"mnre-v2:re:{prompt_version}:k{top_k}:{case.id}"
    response: dict[str, Any] | None = None
    for attempt in range(2):
        try:
            response, _ = await _chat(
                settings, ledger, body, operation_id, prompt_version, "llm"
            )
            break
        except ProviderRequestError as exc:
            record = exc.call_record
            if isinstance(record, ProviderCallRecord) and record.error_code == "content_filtered":
                predicted = NO_RELATION
                errors = ["provider_content_filtered"]
                response = None
                break
            retryable = (
                isinstance(record, ProviderCallRecord) and record.error_code == "request_failed"
            )
            if not retryable or attempt == 1:
                raise
            await asyncio.sleep(2.0)
    raw_content = ""
    if response is not None:
        try:
            raw_content = str(response["choices"][0]["message"]["content"])
            predicted, errors = validate_prediction(parse_json_object(raw_content))
        except (KeyError, IndexError, TypeError, json.JSONDecodeError):
            predicted, errors = NO_RELATION, ["invalid_json_shape"]
    relation_metadata = _schema_relation_metadata(schema)
    result = {
        "id": case.id,
        "prompt_version": prompt_version,
        "top_k": top_k,
        "retrieved_case_ids": retrieved_ids,
        "predicted": predicted,
        "predicted_dataset_label": CANONICAL_TO_DATASET[predicted],
        "gold": case.relation,
        "gold_dataset_label": case.dataset_label,
        "errors": errors,
        "metrics": _result_metrics(case, predicted),
        "schema_relations": relation_metadata,
        "raw_response": raw_content,
        "scoring_version": SCORING_VERSION,
    }
    atomic_json(output, result)
    return result


async def run_prompt_dev(
    prepared: Path,
    schema_path: Path,
    settings: Settings,
    *,
    budget_limit_cny: float = 80.0,
) -> dict[str, Any]:
    schema = load_schema(schema_path)
    train = _load_cases(prepared, "train")
    validation = _load_cases(prepared, "validation")
    train_by_id = {case.id: case for case in train}
    validation_by_id = {case.id: case for case in validation}
    split = load_json(prepared / "validation_split.json")
    ledger = CNYBudgetLedger(prepared / "budget.json", budget_limit_cny)
    summaries: list[dict[str, Any]] = []
    for prompt_order, version in enumerate(RE_PROMPT_VERSIONS):
        for top_k in (1, 3, 5):
            directory = prepared / "prompt-dev" / f"{version}-k{top_k}"
            results = [
                await _run_one_prediction(
                    prepared,
                    settings,
                    ledger,
                    schema,
                    train_by_id,
                    validation_by_id[str(case_id)],
                    version,
                    top_k,
                    directory / _artifact_name(str(case_id)),
                )
                for case_id in split["prompt_dev"]
            ]
            summary = _aggregate(results)
            summary.update(
                {"prompt_version": version, "prompt_order": prompt_order, "top_k": top_k}
            )
            summaries.append(summary)
    summaries.sort(
        key=lambda row: (
            -float(row["micro_f1"]),
            int(row["top_k"]),
            int(row["prompt_order"]),
        )
    )
    best = summaries[0]
    manifest = load_json(prepared / "manifest.json")
    frozen = {
        "prompt_version": best["prompt_version"],
        "prompt_hash": canonical_hash(_prompt_instruction(str(best["prompt_version"]))),
        "top_k": best["top_k"],
        "model": settings.llm_model,
        "scoring_version": SCORING_VERSION,
        "schema_hash": manifest["schema_hash"],
        "tuning_case_library_hash": manifest["tuning_case_library_hash"],
        "final_case_library_hash": manifest["final_case_library_hash"],
        "validation_split_hash": canonical_hash(split),
        "code_commit": _git_commit(),
        "dev_metrics": best,
    }
    report = {"cells": summaries, "selected": frozen, "estimated_cost_cny": ledger.cost}
    atomic_json(prepared / "prompt-dev" / "report.json", report)
    atomic_json(prepared / "frozen-config.json", frozen)
    return report


async def run_prompt_holdout(
    prepared: Path,
    schema_path: Path,
    settings: Settings,
    *,
    budget_limit_cny: float = 80.0,
) -> dict[str, Any]:
    schema = load_schema(schema_path)
    frozen = load_json(prepared / "frozen-config.json")
    manifest = load_json(prepared / "manifest.json")
    split = load_json(prepared / "validation_split.json")
    if frozen["schema_hash"] != manifest["schema_hash"]:
        raise RuntimeError("schema changed after configuration freeze")
    if frozen["tuning_case_library_hash"] != manifest["tuning_case_library_hash"]:
        raise RuntimeError("training case library changed after configuration freeze")
    if frozen["validation_split_hash"] != canonical_hash(split):
        raise RuntimeError("validation split changed after configuration freeze")
    train = _load_cases(prepared, "train")
    validation = _load_cases(prepared, "validation")
    train_by_id = {case.id: case for case in train}
    validation_by_id = {case.id: case for case in validation}
    ledger = CNYBudgetLedger(prepared / "budget.json", budget_limit_cny)
    directory = prepared / "prompt-holdout" / "predictions"
    results = [
        await _run_one_prediction(
            prepared,
            settings,
            ledger,
            schema,
            train_by_id,
            validation_by_id[str(case_id)],
            str(frozen["prompt_version"]),
            int(frozen["top_k"]),
            directory / _artifact_name(str(case_id)),
        )
        for case_id in split["prompt_holdout"]
    ]
    report = {
        "configuration": frozen,
        "execution_commit": _git_commit(),
        "metrics": _aggregate(results),
        "estimated_cost_cny": ledger.cost,
        "test_artifacts_generated": 0,
    }
    atomic_json(prepared / "prompt-holdout" / "report.json", report)
    return report


def finalize_case_library(prepared: Path) -> dict[str, Any]:
    if not (prepared / "prompt-holdout" / "report.json").is_file():
        raise RuntimeError("run the frozen validation holdout before finalizing the library")
    frozen = load_json(prepared / "frozen-config.json")
    manifest = load_json(prepared / "manifest.json")
    train = _load_cases(prepared, "train")
    validation_library = _load_cases(prepared, "validation_library")
    final_cases = [*train, *validation_library]
    final_hash = canonical_hash([_case_fingerprint(case) for case in final_cases])
    if len(final_cases) != 13856 or final_hash != manifest["final_case_library_hash"]:
        raise RuntimeError("final case library no longer matches the prepared manifest")
    if frozen["final_case_library_hash"] != final_hash:
        raise RuntimeError("final case library changed after configuration freeze")
    atomic_json(
        prepared / "final_cases.json", [case.model_dump(mode="json") for case in final_cases]
    )
    report = {
        "count": len(final_cases),
        "case_library_hash": final_hash,
        "train_cases": len(train),
        "validation_cases": len(validation_library),
        "configuration": frozen,
    }
    atomic_json(prepared / "final-library.json", report)
    return report


def _prepare_test_cases(prepared: Path) -> list[MNRECase]:
    frozen = load_json(prepared / "frozen-config.json")
    manifest = load_json(prepared / "manifest.json")
    final_report = load_json(prepared / "final-library.json")
    if frozen["final_case_library_hash"] != final_report["case_library_hash"]:
        raise RuntimeError("final library does not match the frozen configuration")
    dataset_root = Path(str(manifest["dataset_root"]))
    test = parse_annotation_split(
        dataset_root / "annotations" / "mnre_test.txt",
        dataset_root / "images" / "img_org" / "test",
        "test",
    )
    if len(test) != 1614:
        raise RuntimeError("unexpected MNRE-V2 test count")
    final_text = {case.text_sha256 for case in _load_cases(prepared, "final")}
    overlaps = [case.id for case in test if case.text_sha256 in final_text]
    if overlaps:
        raise RuntimeError(f"test text leaked into final case library: {overlaps[:5]}")
    atomic_json(prepared / "test_cases.json", [case.model_dump(mode="json") for case in test])
    manifest["test_artifacts_generated"] = len(test)
    atomic_json(prepared / "manifest.json", manifest)
    return test


async def run_test(
    prepared: Path,
    schema_path: Path,
    settings: Settings,
    *,
    budget_limit_cny: float = 80.0,
    caption_concurrency: int = 1,
) -> dict[str, Any]:
    schema = load_schema(schema_path)
    frozen = load_json(prepared / "frozen-config.json")
    if not (prepared / "final_cases.json").is_file():
        raise RuntimeError("finalize the train+validation case library first")
    test = _prepare_test_cases(prepared)
    await generate_captions(
        prepared,
        settings,
        split="test",
        concurrency=caption_concurrency,
        budget_limit_cny=budget_limit_cny,
    )
    await build_vectors(prepared, settings, mode="test")
    final = _load_cases(prepared, "final")
    final_by_id = {case.id: case for case in final}
    ledger = CNYBudgetLedger(prepared / "budget.json", budget_limit_cny)
    directory = prepared / "test" / "predictions"
    results = [
        await _run_one_prediction(
            prepared,
            settings,
            ledger,
            schema,
            final_by_id,
            case,
            str(frozen["prompt_version"]),
            int(frozen["top_k"]),
            directory / _artifact_name(case.id),
            index_name="final",
            query_name="test",
        )
        for case in test
    ]
    report = {
        "configuration": frozen,
        "execution_commit": _git_commit(),
        "metrics": _aggregate(results),
        "estimated_cost_cny": ledger.cost,
        "test_cases": len(test),
    }
    atomic_json(prepared / "test" / "report.json", report)
    return report


def evaluation_status(prepared: Path) -> dict[str, Any]:
    def optional(path: Path) -> Any:
        return load_json(path) if path.exists() else None

    def count(pattern: str) -> int:
        return sum(1 for _ in prepared.glob(pattern))

    split = optional(prepared / "validation_split.json")
    vectors = {
        name: optional(prepared / "vectors" / f"{name}.json")
        for name in ("train", "validation", "final", "test")
    }
    return {
        "manifest": optional(prepared / "manifest.json"),
        "validation_split": (
            {
                "prompt_dev": len(split["prompt_dev"]),
                "prompt_holdout": len(split["prompt_holdout"]),
            }
            if split
            else None
        ),
        "captions": {"unique_images": count("captions/by-sha256/*.json")},
        "vectors": vectors,
        "prompt_dev_predictions": count("prompt-dev/*/*.json"),
        "prompt_holdout_predictions": count("prompt-holdout/predictions/*.json"),
        "test_predictions": count("test/predictions/*.json"),
        "frozen_configuration": optional(prepared / "frozen-config.json"),
        "final_library": optional(prepared / "final-library.json"),
        "budget": optional(prepared / "budget.json"),
        "reports": {
            "prompt_dev": optional(prepared / "prompt-dev" / "report.json"),
            "prompt_holdout": optional(prepared / "prompt-holdout" / "report.json"),
            "test": optional(prepared / "test" / "report.json"),
        },
    }
