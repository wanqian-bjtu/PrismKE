"""Four-level component ablation for Twitter-2017 and MNRE-V2."""

from __future__ import annotations

import asyncio
import json
import math
import os
import random
import struct
import subprocess
from collections import Counter, defaultdict
from functools import lru_cache
from pathlib import Path
from statistics import mean, pstdev
from typing import Any, Literal

import orjson

from src.core.errors import ProviderRequestError
from src.core.ids import canonical_hash
from src.core.settings import Settings
from src.domain import ProviderCallRecord
from src.evaluation import mnre_v2 as mnre
from src.evaluation import twitter2017 as twitter
from src.providers.common import parse_json_object
from src.providers.embedding import BGEM3EmbeddingProvider

DatasetName = Literal["twitter2017", "mnre-v2"]
VariantName = Literal["vanilla", "schema", "multimodal", "full"]
StageName = Literal["smoke", "main", "stability"]

EXPERIMENT_VERSION = "component-ablation-v1"
SCORING_VERSION = "component-ablation-scoring-v1"
VARIANTS: tuple[VariantName, ...] = ("vanilla", "schema", "multimodal", "full")
DATASETS: tuple[DatasetName, ...] = ("twitter2017", "mnre-v2")
VARIANT_LABELS: dict[VariantName, str] = {
    "vanilla": "Vanilla",
    "schema": "+ Schema Guidance",
    "multimodal": "+ Multimodal Extraction",
    "full": "Full PrismKE",
}
SEED = 2027
BOOTSTRAP_SAMPLES = 10_000
TWITTER_TOP_K = 3
MNRE_TOP_K = 5


class AblationBudgetLedger(twitter.CNYBudgetLedger):
    """The shared ledger with experiment-specific 20/27 CNY milestones."""

    def record(self, operation_id: str, record: ProviderCallRecord) -> list[float]:
        before = self.cost
        crossed = super().record(operation_id, record)
        for milestone in (20.0, 27.0):
            if before < milestone <= self.cost and milestone not in self.payload["milestones"]:
                self.payload["milestones"].append(milestone)
                crossed.append(milestone)
        self.persist()
        return sorted(crossed)


def _git_commit() -> str:
    try:
        return subprocess.run(
            ["git", "rev-parse", "HEAD"], check=True, capture_output=True, text=True
        ).stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        return "unknown"


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


def _artifact_name(case_id: str) -> str:
    return case_id.replace(":", "-") + ".json"


def _settings_fingerprint(settings: Settings) -> dict[str, Any]:
    return {
        "llm_model": settings.llm_model,
        "vlm_model": settings.vlm_model,
        "temperature": 0,
        "max_output_tokens": 1024,
        "embedding_model": settings.embedding_model,
        "embedding_revision": settings.embedding_model_revision,
    }


def _twitter_cases(path: Path) -> list[twitter.TwitterCase]:
    return [twitter.TwitterCase.model_validate(item) for item in load_json(path)]


def _mnre_cases(path: Path) -> list[mnre.MNRECase]:
    return [mnre.MNRECase.model_validate(item) for item in load_json(path)]


@lru_cache(maxsize=8)
def _twitter_train_by_id(path_value: str) -> dict[str, twitter.TwitterCase]:
    return {case.id: case for case in _twitter_cases(Path(path_value) / "train_cases.json")}


@lru_cache(maxsize=8)
def _mnre_index_by_id(path_value: str, index_name: str) -> dict[str, mnre.MNRECase]:
    return {
        case.id: case
        for case in _mnre_cases(Path(path_value) / f"{index_name}_cases.json")
    }


def prepare_experiment(
    output: Path,
    twitter_source: Path,
    mnre_source: Path,
    twitter_dataset: Path,
    twitter_schema_path: Path,
    mnre_schema_path: Path,
    invalid_images_path: Path,
    settings: Settings,
) -> dict[str, Any]:
    twitter_schema = twitter.load_schema(twitter_schema_path)
    mnre_schema = mnre.load_schema(mnre_schema_path)
    twitter_manifest = load_json(twitter_source / "manifest.json")
    twitter_frozen = load_json(twitter_source / "frozen-config.json")
    mnre_manifest = load_json(mnre_source / "manifest.json")
    mnre_frozen = load_json(mnre_source / "frozen-config.json")
    if twitter_frozen["top_k"] != TWITTER_TOP_K or mnre_frozen["top_k"] != MNRE_TOP_K:
        raise RuntimeError("source experiments do not match the locked retrieval top-k values")

    invalid = twitter._invalid_images(invalid_images_path)
    test_cases = twitter.parse_annotation_split(
        twitter_dataset / "annotations" / "test.txt",
        twitter_dataset / "images",
        "test",
        invalid,
    )
    if (
        len(test_cases) != 723
        or sum(case.image_valid for case in test_cases) != 673
        or sum(not case.image_valid for case in test_cases) != 50
    ):
        raise RuntimeError("Twitter-2017 test split does not match the accepted baseline")
    output.mkdir(parents=True, exist_ok=True)
    atomic_json(
        output / "twitter2017" / "test_cases.json",
        [case.model_dump(mode="json") for case in test_cases],
    )

    twitter_validation = _twitter_cases(twitter_source / "validation_cases.json")
    mnre_validation = _mnre_cases(mnre_source / "validation_cases.json")
    smoke = {
        "twitter2017": _stratified_ids_twitter(twitter_validation, 20),
        "mnre-v2": _stratified_ids_mnre(mnre_validation, 20),
    }
    atomic_json(output / "smoke-split.json", {"seed": SEED, "ids": smoke})
    mnre_test = _mnre_cases(mnre_source / "test_cases.json")
    stability = {
        "twitter2017": _stratified_ids_twitter(test_cases, round(len(test_cases) * 0.2)),
        "mnre-v2": _stratified_ids_mnre(mnre_test, round(len(mnre_test) * 0.2)),
    }
    atomic_json(output / "stability-split.json", {"seed": SEED, "ids": stability})
    manifest = {
        "experiment_version": EXPERIMENT_VERSION,
        "code_commit": _git_commit(),
        "settings": _settings_fingerprint(settings),
        "settings_hash": canonical_hash(_settings_fingerprint(settings)),
        "twitter_source": twitter_source.resolve().as_posix(),
        "mnre_source": mnre_source.resolve().as_posix(),
        "schemas": {
            "twitter2017": {
                "path": twitter_schema_path.as_posix(),
                "hash": canonical_hash(twitter_schema),
            },
            "mnre-v2": {
                "path": mnre_schema_path.as_posix(),
                "hash": canonical_hash(mnre_schema),
            },
        },
        "source_hashes": {
            "twitter_case_library": twitter_manifest["case_library_hash"],
            "twitter_frozen_config": canonical_hash(twitter_frozen),
            "mnre_final_case_library": mnre_manifest["final_case_library_hash"],
            "mnre_frozen_config": canonical_hash(mnre_frozen),
        },
        "counts": {
            "twitter2017_test": 723,
            "twitter2017_valid_images": 673,
            "twitter2017_invalid_images": 50,
            "mnre_v2_test": 1614,
        },
        "variants": list(VARIANTS),
        "bootstrap_samples": BOOTSTRAP_SAMPLES,
        "seed": SEED,
        "test_results_used_for_configuration": False,
    }
    atomic_json(output / "manifest.json", manifest)
    return manifest


def _allocate_stratified(
    groups: dict[str, list[str]], size: int, *, seed: int = SEED
) -> list[str]:
    total = sum(len(items) for items in groups.values())
    rng = random.Random(seed)
    shuffled: dict[str, list[str]] = {}
    for key in sorted(groups):
        shuffled[key] = sorted(groups[key])
        rng.shuffle(shuffled[key])
    exact = {key: len(items) * size / total for key, items in shuffled.items()}
    quota = {key: math.floor(value) for key, value in exact.items()}
    remaining = size - sum(quota.values())
    order = sorted(shuffled, key=lambda key: (-(exact[key] - quota[key]), key))
    for key in order[:remaining]:
        quota[key] += 1
    return sorted(
        item for key, items in shuffled.items() for item in items[: quota[key]]
    )


def _stratified_ids_twitter(cases: list[twitter.TwitterCase], size: int) -> list[str]:
    groups: dict[str, list[str]] = defaultdict(list)
    for case in cases:
        labels = "|".join(sorted({entity.dataset_label for entity in case.entities})) or "NONE"
        groups[f"{labels}::{case.image_valid}"].append(case.id)
    return _allocate_stratified(groups, size)


def _stratified_ids_mnre(cases: list[mnre.MNRECase], size: int) -> list[str]:
    groups: dict[str, list[str]] = defaultdict(list)
    for case in cases:
        groups[case.dataset_label].append(case.id)
    return _allocate_stratified(groups, size)


def twitter_prompt(
    variant: VariantName,
    schema: dict[str, Any],
    case: twitter.TwitterCase,
    *,
    description: str | None = None,
    examples: list[dict[str, Any]] | None = None,
) -> str:
    instruction = (
        "Perform named entity recognition. Return JSON only as "
        '{"entities":[{"text":"...","start":0,"end":1,"type":"Person"}]}. '
        "Offsets are Unicode character offsets in the source and use [start,end). Every text "
        "must exactly equal source[start:end]. Use only the allowed canonical type IDs. Do not "
        "translate, rewrite, or normalize source text."
    )
    blocks = [instruction]
    if variant == "vanilla":
        blocks.append(
            "LABEL_INVENTORY: "
            + json.dumps(["Person", "Organization", "Location", "Miscellaneous"])
        )
    else:
        blocks.append("SCHEMA: " + json.dumps(schema, ensure_ascii=False))
    if variant in {"multimodal", "full"}:
        blocks.append("VISUAL: " + json.dumps(description or twitter.IMAGE_UNAVAILABLE))
    if variant == "full":
        blocks.append("EXAMPLES: " + json.dumps(examples or [], ensure_ascii=False))
    blocks.append("SOURCE: " + json.dumps(case.text, ensure_ascii=False))
    return "\n".join(blocks)


def mnre_prompt(
    variant: VariantName,
    schema: dict[str, Any],
    case: mnre.MNRECase,
    *,
    description: str | None = None,
    examples: list[dict[str, Any]] | None = None,
) -> str:
    instruction = (
        "Classify the relation for the supplied ordered head-tail pair. Select exactly one "
        "allowed canonical relation ID. Never exchange head and tail. Return JSON only as "
        '{"relation":"MemberOf"}. Use NoRelation when no positive allowed relation is supported.'
    )
    blocks = [instruction]
    if variant == "vanilla":
        blocks.append("LABEL_INVENTORY: " + json.dumps(sorted(mnre.CANONICAL_TO_DATASET)))
    else:
        blocks.append("SCHEMA: " + json.dumps(schema, ensure_ascii=False))
    if variant in {"multimodal", "full"}:
        blocks.append("VISUAL: " + json.dumps(description or twitter.IMAGE_UNAVAILABLE))
    if variant == "full":
        blocks.append("EXAMPLES: " + json.dumps(examples or [], ensure_ascii=False))
    blocks.extend(
        [
            "SOURCE: " + json.dumps(mnre.marked_text(case), ensure_ascii=False),
            "HEAD: " + json.dumps(case.head.model_dump(mode="json"), ensure_ascii=False),
            "TAIL: " + json.dumps(case.tail.model_dump(mode="json"), ensure_ascii=False),
        ]
    )
    return "\n".join(blocks)


def reflection_prompt(
    dataset: DatasetName,
    initial_response: str,
    validation_errors: list[str],
    original_prompt: str,
) -> str:
    output_shape = (
        '{"entities":[{"text":"...","start":0,"end":1,"type":"Person"}]}'
        if dataset == "twitter2017"
        else '{"relation":"MemberOf"}'
    )
    return (
        "REFLECTION_PASS: Review the first prediction once using the same task, evidence, Schema, "
        "and examples. Correct omissions, unsupported predictions, boundary/type errors, and "
        "relation direction errors. Return only the final JSON in shape "
        f"{output_shape}.\nORIGINAL_TASK:\n{original_prompt}\n"
        f"FIRST_RESPONSE: {initial_response}\n"
        f"DETERMINISTIC_VALIDATION: {json.dumps(validation_errors)}"
    )


def _twitter_caption_path(output: Path, case: twitter.TwitterCase) -> Path:
    return output / "twitter2017" / "captions" / "test" / f"{case.id}.json"


def _twitter_description(
    output: Path,
    source: Path,
    case: twitter.TwitterCase,
    stage: StageName,
) -> str:
    if stage == "smoke":
        return twitter.caption_for_case(source, case)
    return str(load_json(_twitter_caption_path(output, case))["description"])


async def prepare_twitter_test_captions(
    output: Path,
    settings: Settings,
    *,
    budget_limit_cny: float = 30.0,
    concurrency: int = 2,
) -> dict[str, Any]:
    if concurrency not in {1, 2}:
        raise ValueError("caption concurrency must be 1 or 2")
    cases = _twitter_cases(output / "twitter2017" / "test_cases.json")
    ledger = AblationBudgetLedger(output / "budget.json", budget_limit_cny)
    next_index = 0
    completed = resumed = failed = 0
    first_error: BaseException | None = None

    async def process(case: twitter.TwitterCase) -> str:
        target = _twitter_caption_path(output, case)
        if target.exists():
            return "resumed"
        if not case.image_valid:
            atomic_json(
                target,
                {
                    "id": case.id,
                    "description": twitter.IMAGE_UNAVAILABLE,
                    "source": "deterministic-fallback",
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
                        {"type": "text", "text": twitter._caption_prompt()},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": twitter._image_data_url(Path(case.image_path))
                            },
                        },
                    ],
                }
            ],
            "temperature": 0,
            "max_tokens": 160,
            "enable_thinking": False,
            "response_format": {"type": "json_object"},
        }
        for attempt in range(2):
            operation_id = f"ablation:twitter-caption:{case.id}:attempt-{attempt + 1}"
            try:
                response, _ = await twitter._chat(
                    settings,
                    ledger,
                    body,
                    operation_id,
                    twitter.CAPTION_PROMPT_VERSION,
                    "vlm",
                )
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
                            "description": twitter.IMAGE_UNAVAILABLE_PROVIDER_FILTER,
                            "source": settings.vlm_model,
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
                await asyncio.sleep(2)
                continue
            try:
                raw = str(response["choices"][0]["message"]["content"])
                description = str(parse_json_object(raw).get("description", "")).strip()
            except (KeyError, IndexError, TypeError, json.JSONDecodeError):
                description = ""
            if description and len(description.split()) <= 80:
                atomic_json(
                    target,
                    {
                        "id": case.id,
                        "description": description,
                        "source": settings.vlm_model,
                        "image_sha256": case.image_sha256,
                    },
                )
                return "completed"
            if attempt == 1:
                atomic_json(
                    target,
                    {
                        "id": case.id,
                        "description": twitter.IMAGE_UNAVAILABLE_PROVIDER_RESPONSE,
                        "source": settings.vlm_model,
                        "reason": "provider_response_invalid_after_retry",
                    },
                )
                return "completed"
        raise AssertionError("caption retry loop exhausted")

    async def worker() -> None:
        nonlocal next_index, completed, resumed, failed, first_error
        while first_error is None:
            if next_index >= len(cases):
                return
            case = cases[next_index]
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
        "cases": len(cases),
        "completed": completed,
        "resumed": resumed,
        "failed": failed,
        "estimated_cost_cny": ledger.cost,
    }


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


async def prepare_twitter_test_vectors(
    output: Path, settings: Settings
) -> dict[str, Any]:
    cases = _twitter_cases(output / "twitter2017" / "test_cases.json")
    texts = [
        twitter.retrieval_text(case, _twitter_description(output, Path(), case, "main"))
        for case in cases
    ]
    os.environ.setdefault("HF_HUB_OFFLINE", "1")
    os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")
    model_path = twitter._resolve_local_bge(settings)
    provider = BGEM3EmbeddingProvider(
        model_name=str(model_path),
        model_revision=settings.embedding_model_revision,
        device=settings.embedding_device,
        use_fp16=settings.embedding_use_fp16,
        batch_size=min(settings.embedding_batch_size, 32),
        max_tokens=settings.embedding_max_tokens,
        cache_dir=output / "embedding-cache",
        model_cache_dir=settings.embedding_model_cache_dir,
        allow_download=False,
    )
    vectors = await provider.encode(texts)
    vector_path = output / "twitter2017" / "vectors" / "test.f32"
    _write_vectors(vector_path, vectors)
    metadata = {
        "ids": [case.id for case in cases],
        "count": len(cases),
        "dimension": provider.dimension,
        "dtype": "float32-le",
        "provider_fingerprint": provider.fingerprint(),
        "input_hash": canonical_hash(texts),
    }
    atomic_json(vector_path.with_suffix(".json"), metadata)
    return metadata


def _load_matrix(metadata_path: Path) -> tuple[list[str], Any]:
    try:
        import numpy as np
    except ImportError as exc:
        raise RuntimeError("component ablation retrieval requires NumPy") from exc
    metadata = load_json(metadata_path)
    shape = (int(metadata["count"]), int(metadata["dimension"]))
    matrix = np.memmap(
        metadata_path.with_suffix(".f32"), dtype="<f4", mode="r", shape=shape
    )
    return [str(item) for item in metadata["ids"]], matrix


def _twitter_test_retrieve(
    output: Path, twitter_source: Path, query_id: str, top_k: int = TWITTER_TOP_K
) -> list[str]:
    import numpy as np

    train_ids, train = twitter._load_matrix(twitter_source, "train")
    query_ids, queries = _load_matrix(output / "twitter2017" / "vectors" / "test.json")
    query = np.asarray(queries[query_ids.index(query_id)], dtype=np.float32)
    train_array = np.asarray(train, dtype=np.float32)
    denominator = np.linalg.norm(train_array, axis=1) * max(float(np.linalg.norm(query)), 1e-12)
    scores = train_array @ query / np.maximum(denominator, 1e-12)
    indexes = np.argsort(-scores, kind="stable")[:top_k]
    return [train_ids[int(index)] for index in indexes]


async def _provider_json(
    settings: Settings,
    ledger: AblationBudgetLedger,
    prompt: str,
    operation_id: str,
    prompt_version: str,
) -> tuple[str, list[str]]:
    body = {
        "model": settings.llm_model,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0,
        "max_tokens": 1024,
        "enable_thinking": False,
        "response_format": {"type": "json_object"},
    }
    for attempt in range(2):
        try:
            response, _ = await twitter._chat(
                settings, ledger, body, operation_id, prompt_version, "llm"
            )
            return str(response["choices"][0]["message"]["content"]), []
        except ProviderRequestError as exc:
            record = exc.call_record
            if isinstance(record, ProviderCallRecord) and record.error_code == "content_filtered":
                return "", ["provider_content_filtered"]
            retryable = (
                isinstance(record, ProviderCallRecord) and record.error_code == "request_failed"
            )
            if not retryable or attempt == 1:
                raise
            await asyncio.sleep(2)
    raise AssertionError("provider retry loop exhausted")


def _parse_twitter_prediction(
    case: twitter.TwitterCase, raw: str, provider_errors: list[str]
) -> tuple[list[twitter.PredictedEntity], list[str]]:
    if provider_errors:
        return [], [*provider_errors, "invalid_json_shape"]
    try:
        payload = parse_json_object(raw)
        predicted, errors = twitter.validate_prediction(case, payload)
        return predicted, errors
    except (TypeError, json.JSONDecodeError):
        return [], ["invalid_json_shape"]


def _parse_mnre_prediction(raw: str, provider_errors: list[str]) -> tuple[str, list[str]]:
    if provider_errors:
        return mnre.NO_RELATION, [*provider_errors, "invalid_json_shape"]
    try:
        return mnre.validate_prediction(parse_json_object(raw))
    except (TypeError, json.JSONDecodeError):
        return mnre.NO_RELATION, ["invalid_json_shape"]


def _twitter_examples(
    output: Path,
    source: Path,
    case: twitter.TwitterCase,
    stage: StageName,
) -> tuple[list[str], list[dict[str, Any]]]:
    train_by_id = _twitter_train_by_id(str(source.resolve()))
    if stage == "smoke":
        ids = twitter.retrieve_case_ids(source, case.id, TWITTER_TOP_K)
    else:
        ids = _twitter_test_retrieve(output, source, case.id)
    examples = [
        twitter._example_payload(item, twitter.caption_for_case(source, item))
        for item in (train_by_id[item_id] for item_id in ids)
    ]
    return ids, examples


def _mnre_examples(
    source: Path, case: mnre.MNRECase, stage: StageName
) -> tuple[list[str], list[dict[str, Any]]]:
    if stage == "smoke":
        index_name: Literal["train", "final"] = "train"
        query_name: Literal["validation", "test"] = "validation"
    else:
        index_name = "final"
        query_name = "test"
    by_id = _mnre_index_by_id(str(source.resolve()), index_name)
    ids = mnre.retrieve_case_ids(
        source,
        case.id,
        MNRE_TOP_K,
        index_name=index_name,
        query_name=query_name,
    )
    examples = [
        mnre._example_payload(item, mnre.caption_for_case(source, item))
        for item in (by_id[item_id] for item_id in ids)
    ]
    return ids, examples


def _twitter_gold_payload(case: twitter.TwitterCase) -> list[dict[str, Any]]:
    return [entity.model_dump(mode="json") for entity in case.entities]


async def _run_twitter_one(
    output: Path,
    source: Path,
    schema: dict[str, Any],
    case: twitter.TwitterCase,
    variant: VariantName,
    stage: StageName,
    repetition: int,
    settings: Settings,
    ledger: AblationBudgetLedger,
    target: Path,
) -> dict[str, Any]:
    if target.exists():
        return dict(load_json(target))
    description = None
    if variant in {"multimodal", "full"}:
        description = _twitter_description(output, source, case, stage)
    retrieved_ids: list[str] = []
    examples: list[dict[str, Any]] = []
    if variant == "full":
        retrieved_ids, examples = _twitter_examples(output, source, case, stage)
    prompt = twitter_prompt(
        variant, schema, case, description=description, examples=examples
    )
    operation = f"ablation:twitter:{stage}:r{repetition}:{variant}:{case.id}:initial"
    raw_initial, provider_errors = await _provider_json(
        settings, ledger, prompt, operation, f"ablation-twitter-{variant}-v1"
    )
    initial, initial_errors = _parse_twitter_prediction(case, raw_initial, provider_errors)
    final = initial
    final_errors = initial_errors
    raw_reflection = ""
    reflection_accepted = False
    if variant == "full":
        reflect = reflection_prompt("twitter2017", raw_initial, initial_errors, prompt)
        raw_reflection, reflection_provider_errors = await _provider_json(
            settings,
            ledger,
            reflect,
            f"ablation:twitter:{stage}:r{repetition}:{variant}:{case.id}:reflection",
            "ablation-twitter-reflection-v1",
        )
        reflected, reflected_errors = _parse_twitter_prediction(
            case, raw_reflection, reflection_provider_errors
        )
        if "invalid_json_shape" not in reflected_errors:
            final = reflected
            final_errors = reflected_errors
            reflection_accepted = True
        else:
            final_errors = [*initial_errors, "reflection_rejected"]
    result = {
        "id": case.id,
        "dataset": "twitter2017",
        "variant": variant,
        "stage": stage,
        "repetition": repetition,
        "retrieved_case_ids": retrieved_ids,
        "gold": _twitter_gold_payload(case),
        "initial_predicted": [item.model_dump(mode="json") for item in initial],
        "predicted": [item.model_dump(mode="json") for item in final],
        "initial_metrics": twitter._result_metrics(case, initial),
        "metrics": twitter._result_metrics(case, final),
        "initial_errors": initial_errors,
        "errors": final_errors,
        "reflection_accepted": reflection_accepted,
        "image_valid": case.image_valid,
        "prompt_hash": canonical_hash(prompt),
        "raw_initial": raw_initial,
        "raw_reflection": raw_reflection,
        "scoring_version": SCORING_VERSION,
    }
    atomic_json(target, result)
    return result


async def _run_mnre_one(
    source: Path,
    schema: dict[str, Any],
    case: mnre.MNRECase,
    variant: VariantName,
    stage: StageName,
    repetition: int,
    settings: Settings,
    ledger: AblationBudgetLedger,
    target: Path,
) -> dict[str, Any]:
    if target.exists():
        return dict(load_json(target))
    description = None
    if variant in {"multimodal", "full"}:
        description = mnre.caption_for_case(source, case)
    retrieved_ids: list[str] = []
    examples: list[dict[str, Any]] = []
    if variant == "full":
        retrieved_ids, examples = _mnre_examples(source, case, stage)
    prompt = mnre_prompt(variant, schema, case, description=description, examples=examples)
    raw_initial, provider_errors = await _provider_json(
        settings,
        ledger,
        prompt,
        f"ablation:mnre:{stage}:r{repetition}:{variant}:{case.id}:initial",
        f"ablation-mnre-{variant}-v1",
    )
    initial, initial_errors = _parse_mnre_prediction(raw_initial, provider_errors)
    final = initial
    final_errors = initial_errors
    raw_reflection = ""
    reflection_accepted = False
    if variant == "full":
        reflect = reflection_prompt("mnre-v2", raw_initial, initial_errors, prompt)
        raw_reflection, reflection_provider_errors = await _provider_json(
            settings,
            ledger,
            reflect,
            f"ablation:mnre:{stage}:r{repetition}:{variant}:{case.id}:reflection",
            "ablation-mnre-reflection-v1",
        )
        reflected, reflected_errors = _parse_mnre_prediction(
            raw_reflection, reflection_provider_errors
        )
        if not {"invalid_json_shape", "relation_not_in_schema"} & set(reflected_errors):
            final = reflected
            final_errors = reflected_errors
            reflection_accepted = True
        else:
            final_errors = [*initial_errors, "reflection_rejected"]
    result = {
        "id": case.id,
        "dataset": "mnre-v2",
        "variant": variant,
        "stage": stage,
        "repetition": repetition,
        "retrieved_case_ids": retrieved_ids,
        "gold": case.relation,
        "gold_dataset_label": case.dataset_label,
        "initial_predicted": initial,
        "predicted": final,
        "initial_metrics": mnre._result_metrics(case, initial),
        "metrics": mnre._result_metrics(case, final),
        "initial_errors": initial_errors,
        "errors": final_errors,
        "reflection_accepted": reflection_accepted,
        "prompt_hash": canonical_hash(prompt),
        "raw_initial": raw_initial,
        "raw_reflection": raw_reflection,
        "scoring_version": SCORING_VERSION,
    }
    atomic_json(target, result)
    return result


def _cases_for_run(
    output: Path,
    source: Path,
    dataset: DatasetName,
    stage: StageName,
) -> list[twitter.TwitterCase] | list[mnre.MNRECase]:
    if dataset == "twitter2017":
        twitter_cases = (
            _twitter_cases(source / "validation_cases.json")
            if stage == "smoke"
            else _twitter_cases(output / "twitter2017" / "test_cases.json")
        )
        if stage == "smoke":
            ids = set(load_json(output / "smoke-split.json")["ids"][dataset])
            return [case for case in twitter_cases if case.id in ids]
        if stage == "stability":
            ids = set(load_json(output / "stability-split.json")["ids"][dataset])
            return [case for case in twitter_cases if case.id in ids]
        return twitter_cases
    mnre_cases = _mnre_cases(
        source / ("validation_cases.json" if stage == "smoke" else "test_cases.json")
    )
    if stage == "smoke":
        ids = set(load_json(output / "smoke-split.json")["ids"][dataset])
        return [case for case in mnre_cases if case.id in ids]
    if stage == "stability":
        ids = set(load_json(output / "stability-split.json")["ids"][dataset])
        return [case for case in mnre_cases if case.id in ids]
    return mnre_cases


def _f1(tp: float, fp: float, fn: float) -> float:
    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    return 2 * precision * recall / (precision + recall) if precision + recall else 0.0


def _bootstrap_f1(records: list[dict[str, Any]]) -> dict[str, float]:
    import numpy as np

    values = np.asarray(
        [
            [
                float(record["metrics"].get("tp", record["metrics"].get("true_positive", 0))),
                float(record["metrics"].get("fp", record["metrics"].get("false_positive", 0))),
                float(record["metrics"].get("fn", record["metrics"].get("false_negative", 0))),
            ]
            for record in records
        ],
        dtype=np.float64,
    )
    rng = np.random.default_rng(SEED)
    scores: list[float] = []
    for _ in range(0, BOOTSTRAP_SAMPLES, 500):
        count = min(500, BOOTSTRAP_SAMPLES - len(scores))
        indexes = rng.integers(0, len(values), size=(count, len(values)))
        totals = values[indexes].sum(axis=1)
        precision = np.divide(
            totals[:, 0],
            totals[:, 0] + totals[:, 1],
            out=np.zeros(count),
            where=(totals[:, 0] + totals[:, 1]) != 0,
        )
        recall = np.divide(
            totals[:, 0],
            totals[:, 0] + totals[:, 2],
            out=np.zeros(count),
            where=(totals[:, 0] + totals[:, 2]) != 0,
        )
        f1 = np.divide(
            2 * precision * recall,
            precision + recall,
            out=np.zeros(count),
            where=(precision + recall) != 0,
        )
        scores.extend(float(item) for item in f1)
    lower, upper = np.percentile(np.asarray(scores), [2.5, 97.5])
    return {"lower": round(float(lower), 6), "upper": round(float(upper), 6)}


def _usage_for(
    ledger: AblationBudgetLedger,
    dataset: DatasetName,
    stage: StageName,
    variant: VariantName,
    repetition: int,
) -> dict[str, Any]:
    prefix = (
        f"ablation:twitter:{stage}:r{repetition}:{variant}:"
        if dataset == "twitter2017"
        else f"ablation:mnre:{stage}:r{repetition}:{variant}:"
    )
    calls = [
        item
        for item in ledger.payload.get("calls", [])
        if str(item.get("operation_id", "")).startswith(prefix)
    ]
    latencies = [float(item["latency_ms"]) for item in calls if item.get("latency_ms")]
    return {
        "calls": len(calls),
        "input_tokens": sum(int(item.get("input_tokens") or 0) for item in calls),
        "output_tokens": sum(int(item.get("output_tokens") or 0) for item in calls),
        "estimated_cost_cny": round(
            sum(float(item.get("estimated_cost_cny") or 0) for item in calls), 8
        ),
        "average_latency_ms": round(mean(latencies), 3) if latencies else None,
    }


def aggregate_twitter(records: list[dict[str, Any]]) -> dict[str, Any]:
    tp = sum(int(item["metrics"]["tp"]) for item in records)
    fp = sum(int(item["metrics"]["fp"]) for item in records)
    fn = sum(int(item["metrics"]["fn"]) for item in records)
    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    types = sorted(twitter.DATASET_LABELS)
    per_type: dict[str, dict[str, Any]] = {}
    macro_values = []
    for entity_type in types:
        type_tp = type_fp = type_fn = 0
        for item in records:
            gold = {
                (entity["start"], entity["end"], entity["type"])
                for entity in item["gold"]
                if entity["type"] == entity_type
            }
            predicted = {
                (entity["start"], entity["end"], entity["type"])
                for entity in item["predicted"]
                if entity["type"] == entity_type
            }
            type_tp += len(gold & predicted)
            type_fp += len(predicted - gold)
            type_fn += len(gold - predicted)
        type_precision = type_tp / (type_tp + type_fp) if type_tp + type_fp else 0.0
        type_recall = type_tp / (type_tp + type_fn) if type_tp + type_fn else 0.0
        type_f1 = _f1(type_tp, type_fp, type_fn)
        macro_values.append(type_f1)
        per_type[entity_type] = {
            "precision": round(type_precision, 6),
            "recall": round(type_recall, 6),
            "f1": round(type_f1, 6),
            "support": type_tp + type_fn,
        }
    errors = Counter(
        str(error).split(":", 1)[0] for item in records for error in item["errors"]
    )
    result = {
        "cases": len(records),
        "true_positive": tp,
        "false_positive": fp,
        "false_negative": fn,
        "precision": round(precision, 6),
        "recall": round(recall, 6),
        "micro_f1": round(_f1(tp, fp, fn), 6),
        "macro_f1": round(sum(macro_values) / len(macro_values), 6),
        "f1_95_ci": _bootstrap_f1(records),
        "errors": dict(sorted(errors.items())),
        "per_type": per_type,
    }
    valid = [item for item in records if item.get("image_valid")]
    if valid and len(valid) != len(records):
        valid_tp = sum(int(item["metrics"]["tp"]) for item in valid)
        valid_fp = sum(int(item["metrics"]["fp"]) for item in valid)
        valid_fn = sum(int(item["metrics"]["fn"]) for item in valid)
        result["valid_image_subset"] = {
            "cases": len(valid),
            "precision": round(
                valid_tp / (valid_tp + valid_fp) if valid_tp + valid_fp else 0.0, 6
            ),
            "recall": round(
                valid_tp / (valid_tp + valid_fn) if valid_tp + valid_fn else 0.0, 6
            ),
            "micro_f1": round(_f1(valid_tp, valid_fp, valid_fn), 6),
        }
    return result


def aggregate_mnre(records: list[dict[str, Any]]) -> dict[str, Any]:
    tp = sum(int(item["metrics"]["true_positive"]) for item in records)
    fp = sum(int(item["metrics"]["false_positive"]) for item in records)
    fn = sum(int(item["metrics"]["false_negative"]) for item in records)
    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    all_f1 = []
    present_f1 = []
    per_relation: dict[str, dict[str, Any]] = {}
    for relation in sorted(set(mnre.CANONICAL_TO_DATASET) - {mnre.NO_RELATION}):
        relation_tp = sum(
            item["gold"] == relation and item["predicted"] == relation for item in records
        )
        relation_fp = sum(
            item["gold"] != relation and item["predicted"] == relation for item in records
        )
        relation_fn = sum(
            item["gold"] == relation and item["predicted"] != relation for item in records
        )
        support = relation_tp + relation_fn
        relation_f1 = _f1(relation_tp, relation_fp, relation_fn)
        all_f1.append(relation_f1)
        if support:
            present_f1.append(relation_f1)
        per_relation[relation] = {
            "support": support,
            "f1": round(relation_f1, 6),
        }
    errors = Counter(
        str(error).split(":", 1)[0] for item in records for error in item["errors"]
    )
    return {
        "cases": len(records),
        "true_positive": tp,
        "false_positive": fp,
        "false_negative": fn,
        "precision": round(precision, 6),
        "recall": round(recall, 6),
        "micro_f1": round(_f1(tp, fp, fn), 6),
        "macro_f1": round(sum(present_f1) / len(present_f1), 6),
        "macro_f1_all_schema_relations": round(sum(all_f1) / len(all_f1), 6),
        "f1_95_ci": _bootstrap_f1(records),
        "errors": dict(sorted(errors.items())),
        "per_relation": per_relation,
    }


def _report_directory(
    output: Path,
    stage: StageName,
    dataset: DatasetName,
    variant: VariantName,
    repetition: int,
) -> Path:
    base = output / stage / dataset / variant
    return base / f"repetition-{repetition}" if stage == "stability" else base


async def run_variant(
    output: Path,
    dataset: DatasetName,
    variant: VariantName,
    stage: StageName,
    settings: Settings,
    *,
    repetition: int = 0,
    concurrency: int = 2,
    budget_limit_cny: float = 30.0,
) -> dict[str, Any]:
    if concurrency not in {1, 2}:
        raise ValueError("prediction concurrency must be 1 or 2")
    if stage == "stability" and repetition not in {1, 2, 3}:
        raise ValueError("stability repetition must be 1, 2, or 3")
    manifest = load_json(output / "manifest.json")
    source = Path(
        manifest["twitter_source"]
        if dataset == "twitter2017"
        else manifest["mnre_source"]
    )
    schema = (
        twitter.load_schema(Path(manifest["schemas"][dataset]["path"]))
        if dataset == "twitter2017"
        else mnre.load_schema(Path(manifest["schemas"][dataset]["path"]))
    )
    cases = _cases_for_run(output, source, dataset, stage)
    expected = {
        ("twitter2017", "smoke"): 20,
        ("mnre-v2", "smoke"): 20,
        ("twitter2017", "main"): 723,
        ("mnre-v2", "main"): 1614,
        ("twitter2017", "stability"): 145,
        ("mnre-v2", "stability"): 323,
    }[(dataset, stage)]
    if len(cases) != expected:
        raise RuntimeError(f"unexpected {dataset} {stage} case count: {len(cases)}")
    ledger = AblationBudgetLedger(output / "budget.json", budget_limit_cny)
    directory = _report_directory(output, stage, dataset, variant, repetition)
    results: list[dict[str, Any]] = []
    next_index = 0
    first_error: BaseException | None = None

    async def worker() -> None:
        nonlocal next_index, first_error
        while first_error is None:
            if next_index >= len(cases):
                return
            case = cases[next_index]
            next_index += 1
            target = directory / "predictions" / _artifact_name(case.id)
            try:
                if dataset == "twitter2017":
                    assert isinstance(case, twitter.TwitterCase)
                    result = await _run_twitter_one(
                        output,
                        source,
                        schema,
                        case,
                        variant,
                        stage,
                        repetition,
                        settings,
                        ledger,
                        target,
                    )
                else:
                    assert isinstance(case, mnre.MNRECase)
                    result = await _run_mnre_one(
                        source,
                        schema,
                        case,
                        variant,
                        stage,
                        repetition,
                        settings,
                        ledger,
                        target,
                    )
                results.append(result)
            except BaseException as exc:
                first_error = exc
                return

    await asyncio.gather(*(worker() for _ in range(concurrency)))
    if first_error is not None:
        raise first_error
    results.sort(key=lambda item: str(item["id"]))
    metrics = aggregate_twitter(results) if dataset == "twitter2017" else aggregate_mnre(results)
    report: dict[str, Any] = {
        "dataset": dataset,
        "variant": variant,
        "variant_label": VARIANT_LABELS[variant],
        "stage": stage,
        "repetition": repetition,
        "configuration": {
            "model": settings.llm_model,
            "temperature": 0,
            "schema_hash": manifest["schemas"][dataset]["hash"],
            "settings_hash": manifest["settings_hash"],
            "code_commit": manifest["code_commit"],
        },
        "metrics": metrics,
        "usage": _usage_for(ledger, dataset, stage, variant, repetition),
    }
    if variant == "full":
        initial_records = [
            {
                **item,
                "predicted": item["initial_predicted"],
                "metrics": item["initial_metrics"],
                "errors": item["initial_errors"],
            }
            for item in results
        ]
        report["pre_reflection_metrics"] = (
            aggregate_twitter(initial_records)
            if dataset == "twitter2017"
            else aggregate_mnre(initial_records)
        )
        report["reflection"] = {
            "calls": len(results),
            "accepted": sum(bool(item["reflection_accepted"]) for item in results),
            "rejected": sum(not bool(item["reflection_accepted"]) for item in results),
        }
    atomic_json(directory / "report.json", report)
    return report


async def run_smoke(
    output: Path,
    settings: Settings,
    *,
    concurrency: int = 2,
    budget_limit_cny: float = 30.0,
) -> dict[str, Any]:
    reports = []
    for dataset in DATASETS:
        for variant in VARIANTS:
            report = await run_variant(
                output,
                dataset,
                variant,
                "smoke",
                settings,
                concurrency=concurrency,
                budget_limit_cny=budget_limit_cny,
            )
            errors = report["metrics"]["errors"]
            if int(errors.get("relation_not_in_schema", 0)):
                raise RuntimeError(f"{dataset}/{variant} smoke produced out-of-schema output")
            if int(errors.get("invalid_json_shape", 0)) > 1:
                raise RuntimeError(f"{dataset}/{variant} smoke JSON failure rate is too high")
            reports.append(report)
    frozen = {
        "experiment_version": EXPERIMENT_VERSION,
        "manifest_hash": canonical_hash(load_json(output / "manifest.json")),
        "smoke_split_hash": canonical_hash(load_json(output / "smoke-split.json")),
        "prompt_policy_hash": canonical_hash(
            {
                "twitter": twitter_prompt.__doc__ or "twitter-prompt-v1",
                "mnre": mnre_prompt.__doc__ or "mnre-prompt-v1",
                "reflection": reflection_prompt.__doc__ or "reflection-v1",
                "variants": list(VARIANTS),
            }
        ),
        "smoke_reports": [
            {
                "dataset": report["dataset"],
                "variant": report["variant"],
                "metrics": report["metrics"],
            }
            for report in reports
        ],
    }
    atomic_json(output / "frozen-config.json", frozen)
    return frozen


def _require_frozen(output: Path) -> None:
    frozen = load_json(output / "frozen-config.json")
    if frozen["manifest_hash"] != canonical_hash(load_json(output / "manifest.json")):
        raise RuntimeError("experiment manifest changed after smoke freeze")
    if frozen["smoke_split_hash"] != canonical_hash(load_json(output / "smoke-split.json")):
        raise RuntimeError("smoke split changed after freeze")


async def run_all_main(
    output: Path,
    settings: Settings,
    *,
    concurrency: int = 2,
    budget_limit_cny: float = 30.0,
) -> dict[str, Any]:
    _require_frozen(output)
    twitter_caption = await prepare_twitter_test_captions(
        output,
        settings,
        concurrency=concurrency,
        budget_limit_cny=budget_limit_cny,
    )
    vector_path = output / "twitter2017" / "vectors" / "test.json"
    twitter_vectors = (
        load_json(vector_path)
        if vector_path.exists()
        else await prepare_twitter_test_vectors(output, settings)
    )
    reports = []
    for dataset in DATASETS:
        for variant in VARIANTS:
            reports.append(
                await run_variant(
                    output,
                    dataset,
                    variant,
                    "main",
                    settings,
                    concurrency=concurrency,
                    budget_limit_cny=budget_limit_cny,
                )
            )
    summary = {
        "twitter_test_captions": twitter_caption,
        "twitter_test_vectors": twitter_vectors,
        "reports": reports,
    }
    atomic_json(output / "main-summary.json", summary)
    return summary


async def run_all_stability(
    output: Path,
    settings: Settings,
    *,
    concurrency: int = 2,
    budget_limit_cny: float = 30.0,
) -> dict[str, Any]:
    if not (output / "main-summary.json").exists():
        raise RuntimeError("complete the main full-test ablation before stability runs")
    reports = []
    for repetition in (1, 2, 3):
        for dataset in DATASETS:
            for variant in VARIANTS:
                reports.append(
                    await run_variant(
                        output,
                        dataset,
                        variant,
                        "stability",
                        settings,
                        repetition=repetition,
                        concurrency=concurrency,
                        budget_limit_cny=budget_limit_cny,
                    )
                )
    cells = []
    for dataset in DATASETS:
        for variant in VARIANTS:
            values = [
                float(report["metrics"]["micro_f1"])
                for report in reports
                if report["dataset"] == dataset and report["variant"] == variant
            ]
            cells.append(
                {
                    "dataset": dataset,
                    "variant": variant,
                    "repetitions": len(values),
                    "micro_f1_mean": round(mean(values), 6),
                    "micro_f1_std": round(pstdev(values), 6),
                    "micro_f1_values": values,
                }
            )
    summary = {"cells": cells}
    atomic_json(output / "stability-summary.json", summary)
    return summary


def _prediction_records(
    output: Path, dataset: DatasetName, variant: VariantName
) -> list[dict[str, Any]]:
    directory = _report_directory(output, "main", dataset, variant, 0) / "predictions"
    return sorted(
        [dict(load_json(path)) for path in directory.glob("*.json")],
        key=lambda item: str(item["id"]),
    )


def _paired_bootstrap_delta(
    left: list[dict[str, Any]], right: list[dict[str, Any]]
) -> dict[str, float]:
    import numpy as np

    if [item["id"] for item in left] != [item["id"] for item in right]:
        raise ValueError("paired bootstrap requires identical ordered sample IDs")
    left_values = np.asarray(
        [
            [
                item["metrics"].get("tp", item["metrics"].get("true_positive", 0)),
                item["metrics"].get("fp", item["metrics"].get("false_positive", 0)),
                item["metrics"].get("fn", item["metrics"].get("false_negative", 0)),
            ]
            for item in left
        ],
        dtype=np.float64,
    )
    right_values = np.asarray(
        [
            [
                item["metrics"].get("tp", item["metrics"].get("true_positive", 0)),
                item["metrics"].get("fp", item["metrics"].get("false_positive", 0)),
                item["metrics"].get("fn", item["metrics"].get("false_negative", 0)),
            ]
            for item in right
        ],
        dtype=np.float64,
    )
    rng = np.random.default_rng(SEED)
    deltas: list[float] = []
    for _ in range(0, BOOTSTRAP_SAMPLES, 500):
        count = min(500, BOOTSTRAP_SAMPLES - len(deltas))
        indexes = rng.integers(0, len(left_values), size=(count, len(left_values)))
        left_total = left_values[indexes].sum(axis=1)
        right_total = right_values[indexes].sum(axis=1)

        def scores(total: Any) -> Any:
            rows = total.shape[0]
            precision = np.divide(
                total[:, 0],
                total[:, 0] + total[:, 1],
                out=np.zeros(rows),
                where=(total[:, 0] + total[:, 1]) != 0,
            )
            recall = np.divide(
                total[:, 0],
                total[:, 0] + total[:, 2],
                out=np.zeros(rows),
                where=(total[:, 0] + total[:, 2]) != 0,
            )
            return np.divide(
                2 * precision * recall,
                precision + recall,
                out=np.zeros(rows),
                where=(precision + recall) != 0,
            )

        deltas.extend(float(item) for item in scores(right_total) - scores(left_total))
    array = np.asarray(deltas)
    lower, upper = np.percentile(array, [2.5, 97.5])
    return {
        "mean_delta": round(float(array.mean()), 6),
        "lower": round(float(lower), 6),
        "upper": round(float(upper), 6),
        "two_sided_p": round(
            float(2 * min((array <= 0).mean(), (array >= 0).mean())), 6
        ),
    }


def _adjacent_variant_pairs() -> tuple[tuple[VariantName, VariantName], ...]:
    return tuple(zip(VARIANTS[:-1], VARIANTS[1:], strict=True))


def export_results(output: Path) -> dict[str, Any]:
    if not (output / "main-summary.json").exists():
        raise RuntimeError("main ablation results are unavailable")
    rows: list[dict[str, Any]] = []
    paired: list[dict[str, Any]] = []
    for dataset in DATASETS:
        records_by_variant = {
            variant: _prediction_records(output, dataset, variant) for variant in VARIANTS
        }
        for variant in VARIANTS:
            report = load_json(
                _report_directory(output, "main", dataset, variant, 0) / "report.json"
            )
            metrics = report["metrics"]
            row = {
                "dataset": "Twitter-2017" if dataset == "twitter2017" else "MNRE-V2",
                "dataset_id": dataset,
                "variant": variant,
                "variant_label": VARIANT_LABELS[variant],
                "precision": metrics["precision"],
                "recall": metrics["recall"],
                "f1": metrics["micro_f1"],
                "macro_f1": metrics["macro_f1"],
                "f1_ci_lower": metrics["f1_95_ci"]["lower"],
                "f1_ci_upper": metrics["f1_95_ci"]["upper"],
                "cost_cny": report["usage"]["estimated_cost_cny"],
                "average_latency_ms": report["usage"]["average_latency_ms"],
                "errors": metrics["errors"],
            }
            if variant == "full":
                row["pre_reflection_f1"] = report["pre_reflection_metrics"]["micro_f1"]
                row["reflection_accepted"] = report["reflection"]["accepted"]
            rows.append(row)
        for left, right in _adjacent_variant_pairs():
            paired.append(
                {
                    "dataset": dataset,
                    "left": left,
                    "right": right,
                    **_paired_bootstrap_delta(
                        records_by_variant[left], records_by_variant[right]
                    ),
                }
            )
    payload = {
        "experiment_version": EXPERIMENT_VERSION,
        "rows": rows,
        "paired_bootstrap": paired,
        "stability": (
            load_json(output / "stability-summary.json")
            if (output / "stability-summary.json").exists()
            else None
        ),
        "manifest": load_json(output / "manifest.json"),
    }
    atomic_json(output / "results.json", payload)
    headers = [
        "dataset",
        "variant",
        "precision",
        "recall",
        "f1",
        "macro_f1",
        "f1_ci_lower",
        "f1_ci_upper",
        "cost_cny",
        "average_latency_ms",
    ]
    lines = [",".join(headers)]
    for row in rows:
        lines.append(
            ",".join(str(row.get(header, "")) for header in headers)
        )
    csv_path = output / "results.csv"
    temporary = csv_path.with_name(f".{csv_path.name}.{os.getpid()}.tmp")
    temporary.write_text("\n".join(lines) + "\n", encoding="utf-8")
    os.replace(temporary, csv_path)
    return payload


def evaluation_status(output: Path) -> dict[str, Any]:
    def optional(path: Path) -> Any:
        return load_json(path) if path.exists() else None

    def count(pattern: str) -> int:
        return sum(1 for _ in output.glob(pattern))

    cells = []
    for stage in ("smoke", "main", "stability"):
        for dataset in DATASETS:
            for variant in VARIANTS:
                cells.append(
                    {
                        "stage": stage,
                        "dataset": dataset,
                        "variant": variant,
                        "predictions": count(
                            f"{stage}/{dataset}/{variant}/**/predictions/*.json"
                        ),
                    }
                )
    return {
        "manifest": optional(output / "manifest.json"),
        "frozen": optional(output / "frozen-config.json"),
        "twitter_test_captions": count("twitter2017/captions/test/*.json"),
        "twitter_test_vectors": optional(output / "twitter2017/vectors/test.json"),
        "cells": cells,
        "budget": optional(output / "budget.json"),
        "main_complete": (output / "main-summary.json").exists(),
        "stability_complete": (output / "stability-summary.json").exists(),
        "results": optional(output / "results.json"),
    }
