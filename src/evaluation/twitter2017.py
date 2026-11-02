"""Isolated Twitter-2017 case-library and schema-guided NER evaluation."""

from __future__ import annotations

import asyncio
import base64
import json
import math
import os
import random
import struct
import subprocess
from collections import defaultdict
from functools import lru_cache
from hashlib import sha256
from io import BytesIO
from pathlib import Path
from typing import Any, Literal

import orjson
import yaml
from PIL import Image
from pydantic import BaseModel, Field

from src.core.errors import ProviderRequestError
from src.core.ids import canonical_hash, file_sha256
from src.core.settings import Settings
from src.domain import ProviderCallRecord
from src.providers.common import parse_json_object
from src.providers.embedding import BGEM3EmbeddingProvider
from src.providers.http_client import post_chat_completion

DATASET_VERSION = "twitter2017-eval-v1"
CAPTION_PROMPT_VERSION = "twitter2017-caption-v1"
NER_PROMPT_VERSIONS = ("twitter2017-ner-v1", "twitter2017-ner-v2", "twitter2017-ner-v3")
SCORING_VERSION = "exact-surface-align-v2"
IMAGE_UNAVAILABLE = "IMAGE_UNAVAILABLE:v1"
IMAGE_UNAVAILABLE_PROVIDER_FILTER = "IMAGE_UNAVAILABLE:provider_content_filter:v1"
IMAGE_UNAVAILABLE_PROVIDER_RESPONSE = "IMAGE_UNAVAILABLE:provider_response_invalid:v1"
CANONICAL_TYPES = {
    "PER": "Person",
    "ORG": "Organization",
    "LOC": "Location",
    "MISC": "Miscellaneous",
}
DATASET_LABELS = {value: key for key, value in CANONICAL_TYPES.items()}


class GoldEntity(BaseModel):
    text: str
    start: int = Field(ge=0)
    end: int = Field(ge=0)
    type: str
    dataset_label: str


class TwitterCase(BaseModel):
    id: str
    split: Literal["train", "validation", "test"]
    tokens: list[str]
    text: str
    text_sha256: str
    image_path: str
    image_sha256: str | None
    image_valid: bool
    invalid_image_reason: str | None = None
    entities: list[GoldEntity]


class PredictedEntity(BaseModel):
    text: str
    start: int = Field(ge=0)
    end: int = Field(ge=0)
    type: str


class BudgetStop(RuntimeError):
    """Raised before a request that could exceed the authorized CNY budget."""


def _json_bytes(value: Any) -> bytes:
    return orjson.dumps(value, option=orjson.OPT_INDENT_2 | orjson.OPT_SORT_KEYS)


def atomic_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    try:
        temporary.write_bytes(_json_bytes(value))
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def load_json(path: Path) -> Any:
    return orjson.loads(path.read_bytes())


def load_schema(path: Path) -> dict[str, Any]:
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("Twitter-2017 evaluation schema must be an object")
    types = payload.get("entity_types")
    if not isinstance(types, list):
        raise ValueError("Twitter-2017 evaluation schema requires entity_types")
    observed = {
        str(item.get("evaluation_label")): str(item.get("id"))
        for item in types
        if isinstance(item, dict)
    }
    if observed != CANONICAL_TYPES:
        raise ValueError(f"unexpected Twitter-2017 type mapping: {observed}")
    return payload


def _parse_entities(tokens: list[str], labels: list[str]) -> list[GoldEntity]:
    starts: list[int] = []
    cursor = 0
    for token in tokens:
        starts.append(cursor)
        cursor += len(token) + 1
    output: list[GoldEntity] = []
    active_start: int | None = None
    active_end = 0
    active_label: str | None = None

    def flush() -> None:
        nonlocal active_start, active_end, active_label
        if active_start is None or active_label is None:
            return
        text = " ".join(tokens)[active_start:active_end]
        output.append(
            GoldEntity(
                text=text,
                start=active_start,
                end=active_end,
                type=CANONICAL_TYPES[active_label],
                dataset_label=active_label,
            )
        )
        active_start = None
        active_label = None

    for index, raw_label in enumerate(labels):
        if raw_label == "O":
            flush()
            continue
        prefix, separator, label = raw_label.partition("-")
        if not separator or label not in CANONICAL_TYPES:
            raise ValueError(f"invalid BIO label: {raw_label}")
        continues = prefix == "I" and active_label == label and active_start is not None
        if not continues:
            flush()
            active_start = starts[index]
            active_label = label
        active_end = starts[index] + len(tokens[index])
    flush()
    return output


def _invalid_images(path: Path) -> dict[str, str]:
    payload = load_json(path)
    return {
        str(item["filename"]): str(item["reason"])
        for item in payload["images"]
        if isinstance(item, dict)
    }


def parse_annotation_split(
    annotation_path: Path,
    images_dir: Path,
    split: Literal["train", "validation", "test"],
    invalid_images: dict[str, str],
) -> list[TwitterCase]:
    blocks = [
        block
        for block in annotation_path.read_text(encoding="utf-8").split("\n\n")
        if block.strip()
    ]
    cases: list[TwitterCase] = []
    for block in blocks:
        lines = [line.rstrip("\r") for line in block.splitlines() if line.strip()]
        if not lines or not lines[0].startswith("IMGID:"):
            raise ValueError(f"invalid annotation block in {annotation_path}")
        sample_id = lines[0].split(":", 1)[1].strip()
        tokens: list[str] = []
        labels: list[str] = []
        for line in lines[1:]:
            token, separator, label = line.rpartition("\t")
            if not separator:
                raise ValueError(f"invalid annotation row for {sample_id}: {line}")
            tokens.append(token)
            labels.append(label)
        text = " ".join(tokens)
        filename = f"{sample_id}.jpg"
        image_path = images_dir / filename
        if not image_path.is_file():
            raise ValueError(f"missing image for {sample_id}: {image_path}")
        reason = invalid_images.get(filename)
        cases.append(
            TwitterCase(
                id=sample_id,
                split=split,
                tokens=tokens,
                text=text,
                text_sha256=sha256(text.encode("utf-8")).hexdigest(),
                image_path=image_path.as_posix(),
                image_sha256=None if reason else file_sha256(image_path),
                image_valid=reason is None,
                invalid_image_reason=reason,
                entities=_parse_entities(tokens, labels),
            )
        )
    return cases


def _leakage_reasons(
    case: TwitterCase,
    ids: set[str],
    text_hashes: set[str],
    image_hashes: set[str],
) -> list[str]:
    reasons = []
    if case.id in ids:
        reasons.append("sample_id")
    if case.text_sha256 in text_hashes:
        reasons.append("text_sha256")
    if case.image_sha256 is not None and case.image_sha256 in image_hashes:
        reasons.append("valid_image_sha256")
    return reasons


def _stratum(case: TwitterCase) -> str:
    labels = sorted({entity.dataset_label for entity in case.entities})
    return f"{'|'.join(labels) or 'NONE'}::{'valid' if case.image_valid else 'invalid'}"


def stratified_validation_split(
    cases: list[TwitterCase], *, seed: int = 2027, dev_size: int = 100
) -> dict[str, Any]:
    if dev_size <= 0 or dev_size >= len(cases):
        raise ValueError("dev_size must be between zero and the validation size")
    groups: dict[str, list[TwitterCase]] = defaultdict(list)
    for case in cases:
        groups[_stratum(case)].append(case)
    shuffled: dict[str, list[TwitterCase]] = {}
    rng = random.Random(seed)
    for key in sorted(groups):
        shuffled[key] = sorted(groups[key], key=lambda item: item.id)
        rng.shuffle(shuffled[key])
    exact = {key: len(group) * dev_size / len(cases) for key, group in shuffled.items()}
    quotas = {key: math.floor(value) for key, value in exact.items()}
    remaining = dev_size - sum(quotas.values())
    order = sorted(shuffled, key=lambda key: (-(exact[key] - quotas[key]), key))
    for key in order[:remaining]:
        quotas[key] += 1
    dev = sorted(
        [case.id for key, group in shuffled.items() for case in group[: quotas[key]]]
    )
    holdout = sorted(
        [case.id for key, group in shuffled.items() for case in group[quotas[key] :]]
    )
    if len(dev) != dev_size or set(dev) & set(holdout):
        raise AssertionError("validation split invariant failed")
    return {
        "seed": seed,
        "method": "stratified-by-label-combination-and-image-validity-v1",
        "prompt_dev": dev,
        "prompt_holdout": holdout,
        "strata": {
            key: {"total": len(shuffled[key]), "prompt_dev": quotas[key]}
            for key in sorted(shuffled)
        },
    }


def prepare_dataset(
    dataset_root: Path,
    invalid_manifest: Path,
    schema_path: Path,
    output: Path,
) -> dict[str, Any]:
    invalid = _invalid_images(invalid_manifest)
    annotations = dataset_root / "annotations"
    images = dataset_root / "images"
    train = parse_annotation_split(annotations / "train.txt", images, "train", invalid)
    validation = parse_annotation_split(
        annotations / "valid.txt", images, "validation", invalid
    )
    test = parse_annotation_split(annotations / "test.txt", images, "test", invalid)
    protected_ids = {case.id for case in [*validation, *test]}
    protected_text = {case.text_sha256 for case in [*validation, *test]}
    protected_images = {
        case.image_sha256 for case in [*validation, *test] if case.image_sha256 is not None
    }
    kept: list[TwitterCase] = []
    exclusions: list[dict[str, Any]] = []
    for case in train:
        reasons = _leakage_reasons(case, protected_ids, protected_text, protected_images)
        if reasons:
            exclusions.append({"id": case.id, "reasons": reasons})
        else:
            kept.append(case)
    schema = load_schema(schema_path)
    split = stratified_validation_split(validation)
    output.mkdir(parents=True, exist_ok=True)
    atomic_json(output / "train_cases.json", [case.model_dump(mode="json") for case in kept])
    atomic_json(
        output / "validation_cases.json",
        [case.model_dump(mode="json") for case in validation],
    )
    atomic_json(output / "exclusions.json", exclusions)
    atomic_json(output / "validation_split.json", split)
    schema_hash = canonical_hash(schema)
    case_hash = canonical_hash(
        [
            {
                "id": case.id,
                "text_sha256": case.text_sha256,
                "image_sha256": case.image_sha256,
                "entities": [item.model_dump(mode="json") for item in case.entities],
            }
            for case in kept
        ]
    )
    manifest = {
        "dataset_version": DATASET_VERSION,
        "schema_hash": schema_hash,
        "case_library_hash": case_hash,
        "counts": {
            "train_original": len(train),
            "train_excluded": len(exclusions),
            "train_cases": len(kept),
            "train_valid_images": sum(case.image_valid for case in kept),
            "train_invalid_images": sum(not case.image_valid for case in kept),
            "validation_cases": len(validation),
            "validation_valid_images": sum(case.image_valid for case in validation),
            "validation_invalid_images": sum(not case.image_valid for case in validation),
            "test_cases_hash_audited_only": len(test),
        },
        "test_artifacts_generated": 0,
        "artifacts": {
            "train_cases": "train_cases.json",
            "validation_cases": "validation_cases.json",
            "exclusions": "exclusions.json",
            "validation_split": "validation_split.json",
        },
    }
    atomic_json(output / "manifest.json", manifest)
    return manifest


class CNYBudgetLedger:
    """Atomic list-price ledger with conservative pre-request reservations."""

    def __init__(self, path: Path, limit_cny: float = 80.0) -> None:
        self.path = path
        self.limit_cny = limit_cny
        if path.exists():
            self.payload: dict[str, Any] = dict(load_json(path))
            saved_limit = float(self.payload["limit_cny"])
            if saved_limit != limit_cny:
                raise BudgetStop(
                    "existing budget limit is "
                    f"{saved_limit}; refusing implicit change to {limit_cny}"
                )
            stale = sum(float(value) for value in self.payload.pop("reservations", {}).values())
            if stale:
                self.payload["estimated_cost_cny"] = round(self.cost + stale, 8)
                self.payload.setdefault("reservation_recoveries", []).append(
                    {
                        "conservative_cost_cny": stale,
                        "reason": "stale in-flight reservation charged on resume",
                    }
                )
            self.payload["reservations"] = {}
            self.persist()
        else:
            self.payload = {
                "version": 1,
                "limit_cny": limit_cny,
                "estimated_cost_cny": 0.0,
                "input_tokens": 0,
                "output_tokens": 0,
                "calls": [],
                "milestones": [],
                "reservations": {},
                "stopped_reason": None,
            }
            self.persist()

    @property
    def cost(self) -> float:
        return float(self.payload["estimated_cost_cny"])

    def persist(self) -> None:
        atomic_json(self.path, self.payload)

    def authorize(self, operation_id: str, reserve_cny: float = 0.01) -> None:
        if self.payload.get("stopped_reason"):
            raise BudgetStop(str(self.payload["stopped_reason"]))
        reservations = self.payload.setdefault("reservations", {})
        reserved = sum(float(value) for value in reservations.values())
        if self.cost + reserved + reserve_cny > self.limit_cny:
            reason = f"next request {operation_id} could exceed {self.limit_cny:.2f} CNY"
            self.payload["stopped_reason"] = reason
            self.persist()
            raise BudgetStop(reason)
        reservations[operation_id] = reserve_cny
        self.persist()

    def record(self, operation_id: str, record: ProviderCallRecord) -> list[float]:
        self.payload.setdefault("reservations", {}).pop(operation_id, None)
        if record.total_tokens is None or record.estimated_cost_cny is None:
            self.payload["stopped_reason"] = "provider usage or price accounting unavailable"
            self.persist()
            raise BudgetStop(str(self.payload["stopped_reason"]))
        before = self.cost
        self.payload["calls"].append(record.model_dump(mode="json"))
        self.payload["estimated_cost_cny"] = round(before + record.estimated_cost_cny, 8)
        self.payload["input_tokens"] += record.input_tokens or 0
        self.payload["output_tokens"] += record.output_tokens or 0
        crossed = []
        for milestone in (50.0, 70.0):
            if before < milestone <= self.cost and milestone not in self.payload["milestones"]:
                self.payload["milestones"].append(milestone)
                crossed.append(milestone)
        if self.cost >= self.limit_cny:
            self.payload["stopped_reason"] = f"{self.limit_cny:.2f} CNY hard limit reached"
        self.persist()
        return crossed

    def record_failed(
        self,
        operation_id: str,
        record: ProviderCallRecord,
        *,
        conservative_cost_cny: float = 0.01,
    ) -> None:
        self.payload.setdefault("reservations", {}).pop(operation_id, None)
        self.payload["calls"].append(record.model_dump(mode="json"))
        self.payload["estimated_cost_cny"] = round(
            self.cost + conservative_cost_cny, 8
        )
        self.payload.setdefault("conservative_failure_costs", []).append(
            {
                "operation_id": operation_id,
                "cost_cny": conservative_cost_cny,
                "error_code": record.error_code,
            }
        )
        if self.cost >= self.limit_cny:
            self.payload["stopped_reason"] = f"{self.limit_cny:.2f} CNY hard limit reached"
        self.persist()


def _image_data_url(path: Path, max_edge: int = 2048) -> str:
    with Image.open(path) as source:
        image = source.copy()
        image.load()
    if image.mode not in {"RGB", "RGBA", "L", "LA", "P", "1"}:
        image = image.convert("RGB")
    if max(image.size) > max_edge:
        image.thumbnail((max_edge, max_edge))
    output = BytesIO()
    image.save(output, format="PNG")
    return f"data:image/png;base64,{base64.b64encode(output.getvalue()).decode('ascii')}"


def _caption_prompt() -> str:
    return (
        "Describe only what is directly visible in this image for multimodal retrieval. "
        "Mention visible people, organizations, locations, objects, scenes, logos, and short "
        "readable text. Do not infer a person's or organization's identity from hidden labels, "
        "metadata, or external knowledge. Use one concise English sentence of at most 60 words. "
        "Return JSON only: {\"description\":\"...\"}."
    )


async def _chat(
    settings: Settings,
    ledger: CNYBudgetLedger,
    body: dict[str, Any],
    operation_id: str,
    prompt_version: str,
    provider: Literal["llm", "vlm"],
) -> tuple[dict[str, Any], list[float]]:
    ledger.authorize(operation_id)
    base_url = settings.vlm_base_url if provider == "vlm" else settings.llm_base_url
    api_key = settings.vlm_api_key if provider == "vlm" else settings.llm_api_key
    if not api_key:
        raise ValueError(f"{provider.upper()} API key is not configured")
    try:
        response, record = await post_chat_completion(
            base_url=base_url,
            api_key=api_key,
            body=body,
            timeout=settings.vlm_timeout if provider == "vlm" else settings.request_timeout,
            provider=provider,
            operation_id=operation_id,
            prompt_version=prompt_version,
        )
    except ProviderRequestError as exc:
        if isinstance(exc.call_record, ProviderCallRecord):
            atomic_json(
                ledger.path.with_name("last-failed-call.json"),
                exc.call_record.model_dump(mode="json"),
            )
            ledger.record_failed(operation_id, exc.call_record)
        raise
    return response, ledger.record(operation_id, record)


def _caption_path(root: Path, case: TwitterCase) -> Path:
    return root / "captions" / case.split / f"{case.id}.json"


def caption_for_case(root: Path, case: TwitterCase) -> str:
    payload = load_json(_caption_path(root, case))
    return str(payload["description"])


async def generate_captions(
    prepared: Path,
    settings: Settings,
    *,
    split: Literal["train", "validation", "all"] = "all",
    limit: int | None = None,
    smoke: bool = False,
    concurrency: int = 1,
    budget_limit_cny: float = 80.0,
) -> dict[str, Any]:
    selected: list[TwitterCase] = []
    names = ["train", "validation"] if split == "all" else [split]
    for name in names:
        filename = "train_cases.json" if name == "train" else "validation_cases.json"
        selected.extend(TwitterCase.model_validate(item) for item in load_json(prepared / filename))
    if smoke:
        valid = [case for case in selected if case.image_valid]
        valid.sort(key=lambda case: (-len({item.type for item in case.entities}), case.id))
        selected = valid
    if limit is not None:
        selected = selected[:limit]
    ledger = CNYBudgetLedger(prepared / "budget.json", budget_limit_cny)
    if concurrency not in {1, 2}:
        raise ValueError("caption concurrency must be 1 or 2")
    completed = skipped = failed = 0
    milestones: list[float] = []
    next_index = 0
    first_error: BaseException | None = None

    async def process(case: TwitterCase) -> Literal["completed", "resumed"]:
        target = _caption_path(prepared, case)
        if target.exists():
            return "resumed"
        if not case.image_valid:
            atomic_json(
                target,
                {
                    "id": case.id,
                    "description": IMAGE_UNAVAILABLE,
                    "source": "invalid-image-manifest",
                    "reason": case.invalid_image_reason,
                },
            )
            return "completed"
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
        operation_base = f"twitter2017:caption:{case.split}:{case.id}"
        for format_attempt in range(2):
            operation_id = (
                operation_base
                if format_attempt == 0
                else f"{operation_base}:format-retry"
            )
            response: dict[str, Any] | None = None
            for attempt in range(2):
                try:
                    response, crossed = await _chat(
                        settings,
                        ledger,
                        body,
                        operation_id,
                        CAPTION_PROMPT_VERSION,
                        "vlm",
                    )
                    milestones.extend(crossed)
                    break
                except ProviderRequestError as exc:
                    record = exc.call_record
                    if (
                        isinstance(record, ProviderCallRecord)
                        and record.error_code == "content_filtered"
                    ):
                        atomic_json(
                            target,
                            {
                                "id": case.id,
                                "description": IMAGE_UNAVAILABLE_PROVIDER_FILTER,
                                "source": settings.vlm_model,
                                "prompt_version": CAPTION_PROMPT_VERSION,
                                "image_sha256": case.image_sha256,
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
            assert response is not None
            try:
                content = response["choices"][0]["message"]["content"]
                payload = parse_json_object(content)
                description = str(payload.get("description", "")).strip()
                if not description or len(description.split()) > 80:
                    raise ValueError("caption is empty or unexpectedly long")
            except (KeyError, IndexError, TypeError, json.JSONDecodeError, ValueError):
                if format_attempt == 0:
                    await asyncio.sleep(0.5)
                    continue
                atomic_json(
                    target,
                    {
                        "id": case.id,
                        "description": IMAGE_UNAVAILABLE_PROVIDER_RESPONSE,
                        "source": settings.vlm_model,
                        "prompt_version": CAPTION_PROMPT_VERSION,
                        "image_sha256": case.image_sha256,
                        "reason": "provider_response_invalid_after_retry",
                    },
                )
                return "completed"
            else:
                atomic_json(
                    target,
                    {
                        "id": case.id,
                        "description": description,
                        "source": settings.vlm_model,
                        "prompt_version": CAPTION_PROMPT_VERSION,
                        "image_sha256": case.image_sha256,
                    },
                )
                return "completed"
        raise AssertionError("caption format retry loop exhausted unexpectedly")

    async def worker() -> None:
        nonlocal next_index, completed, skipped, failed, first_error
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
                    skipped += 1
            except BaseException as exc:
                failed += 1
                first_error = exc
                return

    await asyncio.gather(*(worker() for _ in range(concurrency)))
    if first_error is not None:
        raise first_error
    return {
        "selected": len(selected),
        "completed": completed,
        "resumed": skipped,
        "failed": failed,
        "concurrency": concurrency,
        "estimated_cost_cny": ledger.cost,
        "crossed_milestones": milestones,
    }


def _resolve_local_bge(settings: Settings) -> Path:
    root = settings.embedding_model_cache_dir / "hub" / "models--BAAI--bge-m3" / "snapshots"
    candidate = root / settings.embedding_model_revision
    if not (candidate / "config.json").is_file():
        raise RuntimeError(f"BGE-M3 snapshot is unavailable: {candidate}")
    return candidate.resolve()


def retrieval_text(case: TwitterCase, description: str) -> str:
    return f"TEXT: {case.text}\nVISUAL: {description}"


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


async def build_vectors(prepared: Path, settings: Settings) -> dict[str, Any]:
    model_path = _resolve_local_bge(settings)
    provider = BGEM3EmbeddingProvider(
        model_name=str(model_path),
        model_revision=settings.embedding_model_revision,
        device=settings.embedding_device,
        use_fp16=settings.embedding_use_fp16,
        batch_size=min(settings.embedding_batch_size, 16),
        max_tokens=settings.embedding_max_tokens,
        cache_dir=prepared / "embedding-cache",
        model_cache_dir=settings.embedding_model_cache_dir,
        allow_download=False,
    )
    summary: dict[str, Any] = {}
    for split, filename in (
        ("train", "train_cases.json"),
        ("validation", "validation_cases.json"),
    ):
        cases = [TwitterCase.model_validate(item) for item in load_json(prepared / filename)]
        texts = [retrieval_text(case, caption_for_case(prepared, case)) for case in cases]
        vectors = await provider.encode(texts)
        if len(vectors) != len(cases):
            raise RuntimeError(f"embedding count mismatch for {split}")
        _write_vectors(prepared / "vectors" / f"{split}.f32", vectors)
        metadata = {
            "split": split,
            "ids": [case.id for case in cases],
            "count": len(cases),
            "dimension": provider.dimension,
            "dtype": "float32-le",
            "provider_fingerprint": provider.fingerprint(),
            "input_hash": canonical_hash(texts),
        }
        atomic_json(prepared / "vectors" / f"{split}.json", metadata)
        summary[split] = metadata
    return summary


def _load_matrix(prepared: Path, split: str) -> tuple[list[str], Any]:
    try:
        import numpy as np
    except ImportError as exc:
        raise RuntimeError("Twitter-2017 retrieval requires NumPy") from exc
    metadata = load_json(prepared / "vectors" / f"{split}.json")
    shape = (int(metadata["count"]), int(metadata["dimension"]))
    matrix = np.memmap(prepared / "vectors" / f"{split}.f32", dtype="<f4", mode="r", shape=shape)
    return [str(item) for item in metadata["ids"]], matrix


@lru_cache(maxsize=2048)
def _retrieve_top_five(prepared_value: str, validation_id: str) -> tuple[str, ...]:
    try:
        import numpy as np
    except ImportError as exc:
        raise RuntimeError("Twitter-2017 retrieval requires NumPy") from exc
    prepared = Path(prepared_value)
    train_ids, train = _load_matrix(prepared, "train")
    validation_ids, validation = _load_matrix(prepared, "validation")
    query_index = validation_ids.index(validation_id)
    query = np.asarray(validation[query_index], dtype=np.float32)
    train_array = np.asarray(train, dtype=np.float32)
    denominator = np.linalg.norm(train_array, axis=1) * max(float(np.linalg.norm(query)), 1e-12)
    scores = train_array @ query / np.maximum(denominator, 1e-12)
    indexes = np.argsort(-scores, kind="stable")[:5]
    return tuple(train_ids[int(index)] for index in indexes)


def retrieve_case_ids(prepared: Path, validation_id: str, top_k: int) -> list[str]:
    if top_k not in {1, 3, 5}:
        raise ValueError("top_k must be 1, 3, or 5")
    return list(_retrieve_top_five(str(prepared.resolve()), validation_id)[:top_k])


def _prompt_instruction(version: str) -> str:
    base = (
        "Perform schema-guided named entity recognition. Extract only entities allowed by the "
        "supplied Schema. Return JSON only as {\"entities\":[{\"text\":\"...\","
        "\"start\":0,\"end\":1,\"type\":\"Person\"}]}. Offsets are Unicode character "
        "offsets in the supplied source and use the half-open interval [start,end). Every text "
        "must exactly equal source[start:end]. Use only canonical Schema type IDs. Do not "
        "translate, rewrite, normalize, or infer text that is absent from the source."
    )
    if version == NER_PROMPT_VERSIONS[0]:
        return base
    if version == NER_PROMPT_VERSIONS[1]:
        return (
            base
            + " Preserve the complete source-written boundary of every multi-token proper name. "
            "Do not shorten a full name to a surname or split one proper name into fragments."
        )
    if version == NER_PROMPT_VERSIONS[2]:
        return (
            base
            + " Before answering, silently verify each entity character by character against "
            "the source, expand truncated multi-token proper names, remove surrounding "
            "punctuation, "
            "and discard any entity whose exact boundary cannot be verified."
        )
    raise ValueError(f"unknown prompt version: {version}")


def _example_payload(case: TwitterCase, description: str) -> dict[str, Any]:
    return {
        "source": case.text,
        "visual_description": description,
        "answer": {
            "entities": [
                {"text": item.text, "start": item.start, "end": item.end, "type": item.type}
                for item in case.entities
            ]
        },
    }


def _ner_prompt(
    schema: dict[str, Any],
    version: str,
    examples: list[dict[str, Any]],
    target: TwitterCase,
    target_description: str,
) -> str:
    return (
        f"{_prompt_instruction(version)}\n"
        f"Schema: {json.dumps(schema, ensure_ascii=False)}\n"
        f"Gold training examples: {json.dumps(examples, ensure_ascii=False)}\n"
        f"Target source: {json.dumps(target.text, ensure_ascii=False)}\n"
        f"Target visual description: {json.dumps(target_description, ensure_ascii=False)}"
    )


def validate_prediction(case: TwitterCase, payload: Any) -> tuple[list[PredictedEntity], list[str]]:
    errors: list[str] = []
    if not isinstance(payload, dict) or not isinstance(payload.get("entities"), list):
        return [], ["invalid_json_shape"]
    output: list[PredictedEntity] = []
    used_spans: set[tuple[int, int]] = set()
    for index, raw in enumerate(payload["entities"]):
        if not isinstance(raw, dict):
            errors.append(f"invalid_entity_structure:{index}")
            continue
        text = raw.get("text")
        entity_type = raw.get("type")
        if not isinstance(text, str) or not text or not isinstance(entity_type, str):
            errors.append(f"invalid_entity_structure:{index}")
            continue
        if entity_type not in DATASET_LABELS:
            errors.append(f"type_not_in_schema:{index}")
            continue
        candidates: list[tuple[int, int]] = []
        cursor = 0
        while True:
            start = case.text.find(text, cursor)
            if start < 0:
                break
            span = (start, start + len(text))
            if span not in used_spans:
                candidates.append(span)
            cursor = start + 1
        if not candidates:
            errors.append(f"surface_not_in_source:{index}")
            continue
        raw_start = raw.get("start")
        raw_end = raw.get("end")
        exact = (
            (raw_start, raw_end)
            if type(raw_start) is int and type(raw_end) is int
            else None
        )
        if exact in candidates:
            chosen = exact
        else:
            chosen = min(
                candidates,
                key=lambda span: abs(span[0] - raw_start)
                if type(raw_start) is int
                else span[0],
            )
            errors.append(f"offset_repaired:{index}")
        assert chosen is not None
        used_spans.add(chosen)
        output.append(
            PredictedEntity(
                text=text,
                start=chosen[0],
                end=chosen[1],
                type=entity_type,
            )
        )
    return output, errors


def _entity_key(entity: GoldEntity | PredictedEntity) -> tuple[int, int, str]:
    return entity.start, entity.end, entity.type


def _result_metrics(case: TwitterCase, predicted: list[PredictedEntity]) -> dict[str, int]:
    gold = {_entity_key(item) for item in case.entities}
    guess = {_entity_key(item) for item in predicted}
    return {"tp": len(gold & guess), "fp": len(guess - gold), "fn": len(gold - guess)}


def _aggregate(results: list[dict[str, Any]]) -> dict[str, Any]:
    tp = sum(int(item["metrics"]["tp"]) for item in results)
    fp = sum(int(item["metrics"]["fp"]) for item in results)
    fn = sum(int(item["metrics"]["fn"]) for item in results)
    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    error_counts: dict[str, int] = defaultdict(int)
    for result in results:
        for error in result["errors"]:
            error_counts[str(error).split(":", 1)[0]] += 1
    return {
        "cases": len(results),
        "true_positive": tp,
        "false_positive": fp,
        "false_negative": fn,
        "precision": round(precision, 6),
        "recall": round(recall, 6),
        "micro_f1": round(f1, 6),
        "errors": dict(sorted(error_counts.items())),
    }


def _git_commit() -> str:
    try:
        return subprocess.run(
            ["git", "rev-parse", "HEAD"],
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        return "unknown"


async def _run_one_prediction(
    prepared: Path,
    settings: Settings,
    ledger: CNYBudgetLedger,
    schema: dict[str, Any],
    train_by_id: dict[str, TwitterCase],
    case: TwitterCase,
    prompt_version: str,
    top_k: int,
    output: Path,
) -> dict[str, Any]:
    if output.exists():
        saved = dict(load_json(output))
        if saved.get("scoring_version") == SCORING_VERSION:
            return saved
        saved_errors: list[str] = []
        try:
            payload = parse_json_object(str(saved.get("raw_response", "")))
            saved_predicted, saved_errors = validate_prediction(case, payload)
        except (TypeError, json.JSONDecodeError):
            saved_predicted = []
            saved_errors = ["invalid_json_shape"]
        saved.update(
            {
                "predicted": [
                    item.model_dump(mode="json") for item in saved_predicted
                ],
                "errors": saved_errors,
                "metrics": _result_metrics(case, saved_predicted),
                "scoring_version": SCORING_VERSION,
            }
        )
        atomic_json(output, saved)
        return saved
    retrieved_ids = retrieve_case_ids(prepared, case.id, top_k)
    examples = [
        _example_payload(train_by_id[item], caption_for_case(prepared, train_by_id[item]))
        for item in retrieved_ids
    ]
    prompt = _ner_prompt(
        schema,
        prompt_version,
        examples,
        case,
        caption_for_case(prepared, case),
    )
    body = {
        "model": settings.llm_model,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0,
        "max_tokens": 1024,
        "enable_thinking": False,
        "response_format": {"type": "json_object"},
    }
    operation_id = f"twitter2017:ner:{prompt_version}:k{top_k}:{case.id}"
    response: dict[str, Any] | None = None
    for attempt in range(2):
        try:
            response, _ = await _chat(
                settings,
                ledger,
                body,
                operation_id,
                prompt_version,
                "llm",
            )
            break
        except ProviderRequestError as exc:
            record = exc.call_record
            if (
                isinstance(record, ProviderCallRecord)
                and record.error_code == "content_filtered"
            ):
                result = {
                    "id": case.id,
                    "prompt_version": prompt_version,
                    "top_k": top_k,
                    "retrieved_case_ids": retrieved_ids,
                    "predicted": [],
                    "gold": [item.model_dump(mode="json") for item in case.entities],
                    "errors": ["provider_content_filtered"],
                    "metrics": _result_metrics(case, []),
                    "raw_response": "",
                    "scoring_version": SCORING_VERSION,
                }
                atomic_json(output, result)
                return result
            retryable = (
                isinstance(record, ProviderCallRecord)
                and record.error_code == "request_failed"
            )
            if not retryable or attempt == 1:
                raise
            await asyncio.sleep(2.0)
    assert response is not None
    errors: list[str] = []
    raw_content = ""
    try:
        raw_content = str(response["choices"][0]["message"]["content"])
        payload = parse_json_object(raw_content)
        predicted, errors = validate_prediction(case, payload)
    except (KeyError, IndexError, TypeError, json.JSONDecodeError):
        predicted = []
        errors = ["invalid_json_shape"]
    result = {
        "id": case.id,
        "prompt_version": prompt_version,
        "top_k": top_k,
        "retrieved_case_ids": retrieved_ids,
        "predicted": [item.model_dump(mode="json") for item in predicted],
        "gold": [item.model_dump(mode="json") for item in case.entities],
        "errors": errors,
        "metrics": _result_metrics(case, predicted),
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
    train = [TwitterCase.model_validate(item) for item in load_json(prepared / "train_cases.json")]
    validation = [
        TwitterCase.model_validate(item) for item in load_json(prepared / "validation_cases.json")
    ]
    train_by_id = {case.id: case for case in train}
    validation_by_id = {case.id: case for case in validation}
    split = load_json(prepared / "validation_split.json")
    dev_ids = [str(item) for item in split["prompt_dev"]]
    ledger = CNYBudgetLedger(prepared / "budget.json", budget_limit_cny)
    summaries: list[dict[str, Any]] = []
    for version_index, version in enumerate(NER_PROMPT_VERSIONS):
        for top_k in (1, 3, 5):
            results = []
            directory = prepared / "prompt-dev" / f"{version}-k{top_k}"
            for case_id in dev_ids:
                results.append(
                    await _run_one_prediction(
                        prepared,
                        settings,
                        ledger,
                        schema,
                        train_by_id,
                        validation_by_id[case_id],
                        version,
                        top_k,
                        directory / f"{case_id}.json",
                    )
                )
            summary = _aggregate(results)
            summary.update(
                {"prompt_version": version, "prompt_order": version_index, "top_k": top_k}
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
        "case_library_hash": manifest["case_library_hash"],
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
        raise RuntimeError("schema changed after prompt configuration was frozen")
    if frozen["case_library_hash"] != manifest["case_library_hash"]:
        raise RuntimeError("case library changed after prompt configuration was frozen")
    if frozen["validation_split_hash"] != canonical_hash(split):
        raise RuntimeError("validation split changed after prompt configuration was frozen")
    train = [TwitterCase.model_validate(item) for item in load_json(prepared / "train_cases.json")]
    validation = [
        TwitterCase.model_validate(item) for item in load_json(prepared / "validation_cases.json")
    ]
    train_by_id = {case.id: case for case in train}
    validation_by_id = {case.id: case for case in validation}
    ledger = CNYBudgetLedger(prepared / "budget.json", budget_limit_cny)
    results = []
    directory = prepared / "prompt-holdout" / "predictions"
    for case_id in split["prompt_holdout"]:
        results.append(
            await _run_one_prediction(
                prepared,
                settings,
                ledger,
                schema,
                train_by_id,
                validation_by_id[str(case_id)],
                str(frozen["prompt_version"]),
                int(frozen["top_k"]),
                directory / f"{case_id}.json",
            )
        )
    report = {
        "configuration": frozen,
        "execution_commit": _git_commit(),
        "protocol_amendment": {
            "applied_after_freeze": True,
            "reason": "retain provider-content-filtered cases as empty predictions",
            "configuration_changed": False,
            "existing_predictions_rerun": False,
        },
        "metrics": _aggregate(results),
        "estimated_cost_cny": ledger.cost,
        "test_artifacts_generated": 0,
    }
    atomic_json(prepared / "prompt-holdout" / "report.json", report)
    return report


def evaluation_status(prepared: Path) -> dict[str, Any]:
    manifest_path = prepared / "manifest.json"
    split_path = prepared / "validation_split.json"
    manifest = load_json(manifest_path) if manifest_path.exists() else None
    split = load_json(split_path) if split_path.exists() else None

    def count(pattern: str) -> int:
        return sum(1 for _ in prepared.glob(pattern))

    def unavailable_by_provider() -> dict[str, int]:
        counts = {"content_filtered": 0, "response_invalid": 0}
        for path in prepared.glob("captions/*/*.json"):
            payload = load_json(path)
            if payload.get("description") == IMAGE_UNAVAILABLE_PROVIDER_FILTER:
                counts["content_filtered"] += 1
            elif payload.get("description") == IMAGE_UNAVAILABLE_PROVIDER_RESPONSE:
                counts["response_invalid"] += 1
        return counts

    ledger = load_json(prepared / "budget.json") if (prepared / "budget.json").exists() else None
    vector_status = {}
    for name in ("train", "validation"):
        metadata = prepared / "vectors" / f"{name}.json"
        vector_status[name] = load_json(metadata) if metadata.exists() else None
    return {
        "manifest": manifest,
        "validation_split": {
            "prompt_dev": len(split["prompt_dev"]),
            "prompt_holdout": len(split["prompt_holdout"]),
        }
        if split
        else None,
        "captions": {
            "train": count("captions/train/*.json"),
            "validation": count("captions/validation/*.json"),
            "test": count("captions/test/*.json"),
            "provider_unavailable": unavailable_by_provider(),
        },
        "vectors": vector_status,
        "predictions": {
            "prompt_dev": count("prompt-dev/*-k*/*.json"),
            "prompt_holdout": count("prompt-holdout/predictions/*.json"),
            "test": count("**/test/predictions/*.json"),
        },
        "budget": ledger,
        "frozen": load_json(prepared / "frozen-config.json")
        if (prepared / "frozen-config.json").exists()
        else None,
    }
