"""V4 text-first, visually gated component ablation for Twitter-2017 and MNRE-V2."""

from __future__ import annotations

import asyncio
import json
import math
import os
from collections import Counter
from pathlib import Path
from statistics import mean
from typing import Any, Literal

from src.core.errors import ProviderRequestError
from src.core.ids import canonical_hash
from src.core.settings import Settings
from src.domain import ProviderCallRecord
from src.evaluation import component_ablation as v1
from src.evaluation import mnre_v2 as mnre
from src.evaluation import twitter2017 as twitter
from src.providers.common import parse_json_object

DatasetName = Literal["twitter2017", "mnre-v2"]
VariantName = Literal["vanilla", "schema", "multimodal", "full"]
StageName = Literal["smoke", "dev", "holdout", "main"]

EXPERIMENT_VERSION = "component-ablation-v4"
SCORING_VERSION = "component-ablation-scoring-v1"
SEED = 2027
BOOTSTRAP_SAMPLES = 10_000
TWITTER_TOP_K = 3
MNRE_TOP_K = 5
VARIANTS: tuple[VariantName, ...] = ("vanilla", "schema", "multimodal", "full")
DATASETS: tuple[DatasetName, ...] = ("twitter2017", "mnre-v2")
VARIANT_LABELS: dict[VariantName, str] = {
    "vanilla": "Vanilla",
    "schema": "+ Schema Guidance",
    "multimodal": "+ Multimodal Extraction V4",
    "full": "Full PrismKE V4",
}

# These relations can sometimes be grounded in a single image. Identity, membership,
# biographical, family, alias, award, belief, race, and legal relations are deliberately
# excluded because co-occurrence is not sufficient evidence for them.
VISUALLY_ELIGIBLE_RELATIONS = frozenset(
    {"Contains", "HeldAt", "PartOf", "LocatedAt", "PresentIn"}
)


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
    return [twitter.TwitterCase.model_validate(item) for item in v1.load_json(path)]


def _mnre_cases(path: Path) -> list[mnre.MNRECase]:
    return [mnre.MNRECase.model_validate(item) for item in v1.load_json(path)]


def _assert_split(split: dict[str, Any], dev: int, holdout: int, name: str) -> None:
    dev_ids = [str(item) for item in split.get("prompt_dev", [])]
    holdout_ids = [str(item) for item in split.get("prompt_holdout", [])]
    if len(dev_ids) != dev or len(holdout_ids) != holdout:
        raise RuntimeError(f"unexpected {name} validation split size")
    if set(dev_ids) & set(holdout_ids):
        raise RuntimeError(f"{name} validation split overlaps")


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
    """Prepare an isolated V4 manifest without modifying V1-V3 artifacts."""
    twitter_schema = twitter.load_schema(twitter_schema_path)
    mnre_schema = mnre.load_schema(mnre_schema_path)
    twitter_manifest = v1.load_json(twitter_source / "manifest.json")
    mnre_manifest = v1.load_json(mnre_source / "manifest.json")
    twitter_frozen = v1.load_json(twitter_source / "frozen-config.json")
    mnre_frozen_path = mnre_source / "frozen-config.json"
    mnre_frozen = v1.load_json(mnre_frozen_path) if mnre_frozen_path.exists() else {}
    if int(twitter_frozen["top_k"]) != TWITTER_TOP_K:
        raise RuntimeError("Twitter source experiment does not use top-k=3")
    if mnre_frozen and int(mnre_frozen["top_k"]) != MNRE_TOP_K:
        raise RuntimeError("MNRE source experiment does not use top-k=5")

    twitter_split = dict(v1.load_json(twitter_source / "validation_split.json"))
    mnre_split = dict(v1.load_json(mnre_source / "validation_split.json"))
    _assert_split(twitter_split, 100, 623, "Twitter-2017")
    _assert_split(mnre_split, 200, 1423, "MNRE-V2")

    invalid = twitter._invalid_images(invalid_images_path)
    twitter_test = twitter.parse_annotation_split(
        twitter_dataset / "annotations" / "test.txt",
        twitter_dataset / "images",
        "test",
        invalid,
    )
    if (
        len(twitter_test) != 723
        or sum(case.image_valid for case in twitter_test) != 673
        or sum(not case.image_valid for case in twitter_test) != 50
    ):
        raise RuntimeError("Twitter-2017 test split does not match the accepted baseline")
    mnre_test = _mnre_cases(mnre_source / "test_cases.json")
    if len(mnre_test) != 1614:
        raise RuntimeError("MNRE-V2 test split does not match the accepted baseline")

    output.mkdir(parents=True, exist_ok=True)
    v1.atomic_json(
        output / "twitter2017" / "test_cases.json",
        [case.model_dump(mode="json") for case in twitter_test],
    )
    v1.atomic_json(
        output / "validation-splits.json",
        {
            "twitter2017": twitter_split,
            "mnre-v2": mnre_split,
            "hashes": {
                "twitter2017": canonical_hash(twitter_split),
                "mnre-v2": canonical_hash(mnre_split),
            },
        },
    )
    smoke_ids = {
        "twitter2017": [str(item) for item in twitter_split["prompt_dev"][:20]],
        "mnre-v2": [str(item) for item in mnre_split["prompt_dev"][:20]],
    }
    v1.atomic_json(output / "smoke-split.json", {"seed": SEED, "ids": smoke_ids})

    settings_payload = _settings_fingerprint(settings)
    manifest = {
        "experiment_version": EXPERIMENT_VERSION,
        "code_commit": v1._git_commit(),
        "settings": settings_payload,
        "settings_hash": canonical_hash(settings_payload),
        "twitter_source": twitter_source.resolve().as_posix(),
        "mnre_source": mnre_source.resolve().as_posix(),
        "schemas": {
            "twitter2017": {
                "path": twitter_schema_path.resolve().as_posix(),
                "hash": canonical_hash(twitter_schema),
            },
            "mnre-v2": {
                "path": mnre_schema_path.resolve().as_posix(),
                "hash": canonical_hash(mnre_schema),
            },
        },
        "source_hashes": {
            "twitter_case_library": twitter_manifest["case_library_hash"],
            "twitter_frozen_config": canonical_hash(twitter_frozen),
            "mnre_final_case_library": mnre_manifest["final_case_library_hash"],
            "mnre_frozen_config": canonical_hash(mnre_frozen) if mnre_frozen else None,
        },
        "counts": {
            "twitter2017_test": 723,
            "twitter2017_valid_images": 673,
            "twitter2017_invalid_images": 50,
            "twitter2017_dev": 100,
            "twitter2017_holdout": 623,
            "mnre_v2_test": 1614,
            "mnre_v2_dev": 200,
            "mnre_v2_holdout": 1423,
        },
        "variants": list(VARIANTS),
        "retrieval_top_k": {"twitter2017": TWITTER_TOP_K, "mnre-v2": MNRE_TOP_K},
        "bootstrap_samples": BOOTSTRAP_SAMPLES,
        "seed": SEED,
        "paid_stability_repetitions": 0,
        "v3_diagnostic_informed_protocol": True,
        "v4_test_predictions_used_for_configuration": False,
    }
    v1.atomic_json(output / "manifest.json", manifest)
    return manifest


def twitter_text_prompt(
    variant: VariantName,
    schema: dict[str, Any],
    case: twitter.TwitterCase,
    examples: list[dict[str, Any]] | None = None,
) -> str:
    """Build the text-only entity candidate prompt for V4."""
    instruction = (
        "Perform named entity recognition from SOURCE text only. Return JSON only as "
        '{"entities":[{"text":"...","start":0,"end":1,"type":"Person"}]}. '
        'If SOURCE contains no allowed entity, return exactly {"entities":[]}; never return '
        "a bare array or an empty object. "
        "Offsets are Unicode character offsets using [start,end). Every text must exactly equal "
        "SOURCE[start:end]. Preserve the complete source-written proper name. Do not translate, "
        "rewrite, normalize, strip, or add @, #, or punctuation. Use only allowed canonical type "
        "IDs."
    )
    blocks = [instruction]
    if variant == "vanilla":
        blocks.append(
            "LABEL_INVENTORY: "
            + json.dumps(["Person", "Organization", "Location", "Miscellaneous"])
        )
    else:
        blocks.append("SCHEMA: " + json.dumps(schema, ensure_ascii=False))
    if variant == "full":
        blocks.append("GOLD_TRAINING_EXAMPLES: " + json.dumps(examples or [], ensure_ascii=False))
    blocks.append("SOURCE: " + json.dumps(case.text, ensure_ascii=False))
    return "\n".join(blocks)


def twitter_visual_prompt(
    schema: dict[str, Any],
    case: twitter.TwitterCase,
    candidates: list[twitter.PredictedEntity],
) -> str:
    """Build an image-only type evidence prompt that cannot alter entity spans."""
    candidate_payload = [
        {
            "candidate_id": index,
            "text": item.text,
            "start": item.start,
            "end": item.end,
            "text_type": item.type,
        }
        for index, item in enumerate(candidates)
    ]
    return (
        "Assess whether the image provides reliable type evidence for the supplied text entity "
        "candidates. Visual context is not an entity source. Never add, delete, merge, split, "
        "rename, or change the boundary of a candidate. Return JSON only as "
        '{"candidates":[{"candidate_id":0,"visible":"yes|no|uncertain",'
        '"suggested_type":"Person|Organization|Location|Miscellaneous|null",'
        '"visual_support":"supports|contradicts|insufficient"}]}. '
        "Use supports only when the image clearly supports suggested_type for that exact named "
        "candidate. Otherwise use insufficient and null.\n"
        f"SCHEMA: {json.dumps(schema, ensure_ascii=False)}\n"
        f"SOURCE_CONTEXT: {json.dumps(case.text, ensure_ascii=False)}\n"
        f"FIXED_CANDIDATES: {json.dumps(candidate_payload, ensure_ascii=False)}"
    )


def twitter_reflection_prompt(
    schema: dict[str, Any],
    case: twitter.TwitterCase,
    candidates: list[twitter.PredictedEntity],
    errors: list[str],
) -> str:
    """Build one bounded MNER reflection that preserves all entity spans."""
    fixed_entities = [item.model_dump(mode="json") for item in candidates]
    return (
        "REFLECTION_PASS: Review entity types and JSON format once. The entity candidate set is "
        "immutable. Do not add, delete, merge, split, rename, or change text/start/end. Return "
        "JSON only in the original entity format. Any span change will be rejected.\n"
        f"SCHEMA: {json.dumps(schema, ensure_ascii=False)}\n"
        f"SOURCE: {json.dumps(case.text, ensure_ascii=False)}\n"
        f"FIXED_ENTITIES: {json.dumps(fixed_entities, ensure_ascii=False)}\n"
        f"DETERMINISTIC_VALIDATION: {json.dumps(errors)}"
    )


def _mnre_base_instruction() -> str:
    return (
        "Classify the relation for the supplied ordered head-tail pair. Select exactly one "
        "allowed canonical relation ID. Never exchange head and tail. Return JSON only as "
        '{"relation":"MemberOf"}. Use NoRelation when no positive allowed relation is supported.'
    )


def mnre_text_prompt(
    variant: VariantName,
    schema: dict[str, Any],
    case: mnre.MNRECase,
    examples: list[dict[str, Any]] | None = None,
) -> str:
    """Build the text-first ordered-pair relation prompt for V4."""
    blocks = [_mnre_base_instruction()]
    if variant == "vanilla":
        blocks.append("LABEL_INVENTORY: " + json.dumps(sorted(mnre.CANONICAL_TO_DATASET)))
    else:
        blocks.append("SCHEMA: " + json.dumps(schema, ensure_ascii=False))
    if variant == "full":
        blocks.append("GOLD_TRAINING_EXAMPLES: " + json.dumps(examples or [], ensure_ascii=False))
    blocks.extend(
        [
            "SOURCE: " + json.dumps(mnre.marked_text(case), ensure_ascii=False),
            "HEAD: " + json.dumps(case.head.model_dump(mode="json"), ensure_ascii=False),
            "TAIL: " + json.dumps(case.tail.model_dump(mode="json"), ensure_ascii=False),
        ]
    )
    return "\n".join(blocks)


def mnre_visual_prompt(
    schema: dict[str, Any], case: mnre.MNRECase, text_prediction: str
) -> str:
    """Build pair-directed visual evidence prompt without asking the VLM for a relation label."""
    return (
        "Inspect only the image for the supplied ordered entity pair and the text model's current "
        "prediction. Do not output a relation ID or a replacement prediction. Determine whether "
        "both named endpoints are reliably grounded and whether visible evidence supports or "
        "contradicts the current prediction. Mere co-occurrence is insufficient. Return JSON only "
        "as {\"head_visible\":\"yes|no|uncertain\",\"tail_visible\":\"yes|no|uncertain\","
        "\"observable_interaction\":\"brief objective description or insufficient\","
        "\"visual_support\":\"supports|contradicts|insufficient\","
        "\"confidence\":\"high|medium|low\"}.\n"
        f"SCHEMA: {json.dumps(schema, ensure_ascii=False)}\n"
        f"SOURCE_CONTEXT: {json.dumps(mnre.marked_text(case), ensure_ascii=False)}\n"
        f"HEAD: {json.dumps(case.head.model_dump(mode='json'), ensure_ascii=False)}\n"
        f"TAIL: {json.dumps(case.tail.model_dump(mode='json'), ensure_ascii=False)}\n"
        f"TEXT_PREDICTION: {json.dumps(text_prediction)}"
    )


def mnre_fusion_prompt(
    schema: dict[str, Any],
    case: mnre.MNRECase,
    text_prediction: str,
    evidence: dict[str, str],
) -> str:
    """Build a conservative reclassification prompt after high-confidence contradiction."""
    return (
        f"{_mnre_base_instruction()} Reconsider the text prediction once because a separately "
        "validated image-evidence step found a high-confidence contradiction while grounding both "
        "endpoints. Image evidence may reject unsupported co-occurrence but must not override "
        "clear "
        "text or invent identity facts.\n"
        f"SCHEMA: {json.dumps(schema, ensure_ascii=False)}\n"
        f"SOURCE: {json.dumps(mnre.marked_text(case), ensure_ascii=False)}\n"
        f"HEAD: {json.dumps(case.head.model_dump(mode='json'), ensure_ascii=False)}\n"
        f"TAIL: {json.dumps(case.tail.model_dump(mode='json'), ensure_ascii=False)}\n"
        f"TEXT_PREDICTION: {json.dumps(text_prediction)}\n"
        f"GATED_VISUAL_EVIDENCE: {json.dumps(evidence, ensure_ascii=False)}"
    )


def mnre_reflection_prompt(
    schema: dict[str, Any], case: mnre.MNRECase, prediction: str, errors: list[str]
) -> str:
    """Build an MRE reflection only for deterministic output failures."""
    return (
        f"{_mnre_base_instruction()} REFLECTION_PASS: Correct only the listed JSON, Schema, "
        "required "
        "field, or direction failure. Preserve the supplied ordered endpoints.\n"
        f"SCHEMA: {json.dumps(schema, ensure_ascii=False)}\n"
        f"SOURCE: {json.dumps(mnre.marked_text(case), ensure_ascii=False)}\n"
        f"HEAD: {json.dumps(case.head.model_dump(mode='json'), ensure_ascii=False)}\n"
        f"TAIL: {json.dumps(case.tail.model_dump(mode='json'), ensure_ascii=False)}\n"
        f"CURRENT_PREDICTION: {json.dumps(prediction)}\n"
        f"DETERMINISTIC_VALIDATION: {json.dumps(errors)}"
    )


async def _provider_vlm_json(
    settings: Settings,
    ledger: v1.AblationBudgetLedger,
    prompt: str,
    image_path: Path,
    operation_id: str,
    prompt_version: str,
) -> tuple[str, list[str]]:
    body = {
        "model": settings.vlm_model,
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {
                        "type": "image_url",
                        "image_url": {"url": twitter._image_data_url(image_path)},
                    },
                ],
            }
        ],
        "temperature": 0,
        "max_tokens": 512,
        "enable_thinking": False,
        "response_format": {"type": "json_object"},
    }
    for attempt in range(2):
        try:
            response, _ = await twitter._chat(
                settings, ledger, body, operation_id, prompt_version, "vlm"
            )
            return str(response["choices"][0]["message"]["content"]), []
        except ProviderRequestError as exc:
            record = exc.call_record
            if isinstance(record, ProviderCallRecord) and record.error_code == "content_filtered":
                return "", ["provider_content_filtered"]
            retryable = (
                isinstance(record, ProviderCallRecord)
                and record.error_code == "request_failed"
            )
            if not retryable or attempt == 1:
                raise
            await asyncio.sleep(2)
    raise AssertionError("provider retry loop exhausted")


def _twitter_examples(
    output: Path,
    source: Path,
    case: twitter.TwitterCase,
    stage: StageName,
) -> tuple[list[str], list[dict[str, Any]]]:
    ids, examples = v1._twitter_examples(
        output, source, case, "main" if stage == "main" else "smoke"
    )
    text_only_examples = [
        {"source": item["source"], "answer": item["answer"]} for item in examples
    ]
    return ids, text_only_examples


def _mnre_examples(
    source: Path, case: mnre.MNRECase, stage: StageName
) -> tuple[list[str], list[dict[str, Any]]]:
    ids, examples = v1._mnre_examples(
        source, case, "main" if stage == "main" else "smoke"
    )
    text_only_examples = [
        {
            "source": item["source"],
            "head": item["head"],
            "tail": item["tail"],
            "answer": item["answer"],
        }
        for item in examples
    ]
    return ids, text_only_examples


def _parse_twitter_visual(
    raw: str, provider_errors: list[str], candidate_count: int
) -> tuple[dict[int, dict[str, str | None]], list[str]]:
    if provider_errors:
        return {}, [*provider_errors, "invalid_visual_json"]
    try:
        payload = parse_json_object(raw)
    except (TypeError, json.JSONDecodeError):
        return {}, ["invalid_visual_json"]
    items = payload.get("candidates")
    if not isinstance(items, list):
        return {}, ["invalid_visual_shape"]
    output: dict[int, dict[str, str | None]] = {}
    errors: list[str] = []
    for item in items:
        if not isinstance(item, dict) or type(item.get("candidate_id")) is not int:
            errors.append("invalid_visual_candidate")
            continue
        candidate_id = int(item["candidate_id"])
        visible = item.get("visible")
        suggested_type = item.get("suggested_type")
        support = item.get("visual_support")
        if candidate_id < 0 or candidate_id >= candidate_count or candidate_id in output:
            errors.append("invalid_visual_candidate")
            continue
        if visible not in {"yes", "no", "uncertain"}:
            errors.append("invalid_visual_candidate")
            continue
        if suggested_type is not None and suggested_type not in twitter.DATASET_LABELS:
            errors.append("type_not_in_schema")
            continue
        if support not in {"supports", "contradicts", "insufficient"}:
            errors.append("invalid_visual_candidate")
            continue
        output[candidate_id] = {
            "visible": str(visible),
            "suggested_type": str(suggested_type) if suggested_type is not None else None,
            "visual_support": str(support),
        }
    return output, errors


def apply_twitter_visual_gate(
    candidates: list[twitter.PredictedEntity],
    evidence: dict[int, dict[str, str | None]],
) -> tuple[list[twitter.PredictedEntity], int, int]:
    """Apply only supported type changes while preserving every candidate span."""
    output: list[twitter.PredictedEntity] = []
    accepted = rejected = 0
    for index, candidate in enumerate(candidates):
        item = evidence.get(index)
        suggested = item.get("suggested_type") if item else None
        if (
            item
            and item.get("visible") == "yes"
            and item.get("visual_support") == "supports"
            and isinstance(suggested, str)
            and suggested in twitter.DATASET_LABELS
        ):
            output.append(candidate.model_copy(update={"type": suggested}))
            accepted += int(suggested != candidate.type)
        else:
            output.append(candidate)
            if item and suggested not in {None, candidate.type}:
                rejected += 1
    return output, accepted, rejected


def _parse_mnre_visual(
    raw: str, provider_errors: list[str]
) -> tuple[dict[str, str] | None, list[str]]:
    if provider_errors:
        return None, [*provider_errors, "invalid_visual_json"]
    try:
        payload = parse_json_object(raw)
    except (TypeError, json.JSONDecodeError):
        return None, ["invalid_visual_json"]
    if "relation" in payload:
        return None, ["forbidden_relation_field"]
    required = {
        "head_visible",
        "tail_visible",
        "observable_interaction",
        "visual_support",
        "confidence",
    }
    if set(payload) != required:
        return None, ["invalid_visual_shape"]
    if payload["head_visible"] not in {"yes", "no", "uncertain"}:
        return None, ["invalid_visual_value"]
    if payload["tail_visible"] not in {"yes", "no", "uncertain"}:
        return None, ["invalid_visual_value"]
    if payload["visual_support"] not in {"supports", "contradicts", "insufficient"}:
        return None, ["invalid_visual_value"]
    if payload["confidence"] not in {"high", "medium", "low"}:
        return None, ["invalid_visual_value"]
    if not isinstance(payload["observable_interaction"], str):
        return None, ["invalid_visual_value"]
    return {key: str(payload[key]) for key in required}, []


def _span_signature(items: list[twitter.PredictedEntity]) -> list[tuple[str, int, int]]:
    return sorted((item.text, item.start, item.end) for item in items)


def _parse_twitter_prediction_v4(
    case: twitter.TwitterCase, raw: str, provider_errors: list[str]
) -> tuple[list[twitter.PredictedEntity], list[str]]:
    """Normalize only unambiguous empty NER outputs and keep an explicit audit error."""
    normalized = raw
    repaired = False
    if not provider_errors:
        try:
            payload = json.loads(raw)
        except json.JSONDecodeError:
            payload = None
        if payload == {} or payload == []:
            normalized = '{"entities":[]}'
            repaired = True
    predicted, errors = v1._parse_twitter_prediction(case, normalized, provider_errors)
    if repaired:
        errors.append("empty_shape_repaired")
    return predicted, errors


async def _run_twitter_one(
    output: Path,
    source: Path,
    schema: dict[str, Any],
    case: twitter.TwitterCase,
    variant: VariantName,
    stage: StageName,
    settings: Settings,
    ledger: v1.AblationBudgetLedger,
    target: Path,
) -> dict[str, Any]:
    if target.exists():
        return dict(v1.load_json(target))
    retrieved_ids: list[str] = []
    examples: list[dict[str, Any]] = []
    if variant == "full":
        retrieved_ids, examples = _twitter_examples(output, source, case, stage)
    prompt = twitter_text_prompt(variant, schema, case, examples)
    prefix = f"ablation-v4:twitter2017:{stage}:{variant}:{case.id}"
    raw_text, provider_errors = await v1._provider_json(
        settings, ledger, prompt, f"{prefix}:text", f"ablation-v4-twitter-{variant}-text"
    )
    text_prediction, text_errors = _parse_twitter_prediction_v4(
        case, raw_text, provider_errors
    )
    pre_reflection = text_prediction
    final = text_prediction
    errors = list(text_errors)
    raw_visual = ""
    visual_errors: list[str] = []
    visual_gate_triggered = False
    visual_changes_accepted = 0
    visual_changes_rejected = 0

    if variant in {"multimodal", "full"} and text_prediction and case.image_valid:
        visual_gate_triggered = True
        visual_prompt = twitter_visual_prompt(schema, case, text_prediction)
        raw_visual, visual_provider_errors = await _provider_vlm_json(
            settings,
            ledger,
            visual_prompt,
            Path(case.image_path),
            f"{prefix}:visual",
            "ablation-v4-twitter-type-evidence",
        )
        evidence, visual_errors = _parse_twitter_visual(
            raw_visual, visual_provider_errors, len(text_prediction)
        )
        final, visual_changes_accepted, visual_changes_rejected = (
            apply_twitter_visual_gate(text_prediction, evidence)
        )
        errors.extend(visual_errors)
        pre_reflection = final

    raw_reflection = ""
    reflection_triggered = False
    reflection_accepted = False
    if variant == "full":
        reflection_triggered = True
        reflect_prompt = twitter_reflection_prompt(schema, case, final, errors)
        raw_reflection, reflection_provider_errors = await v1._provider_json(
            settings,
            ledger,
            reflect_prompt,
            f"{prefix}:reflection",
            "ablation-v4-twitter-bounded-reflection",
        )
        reflected, reflected_errors = _parse_twitter_prediction_v4(
            case, raw_reflection, reflection_provider_errors
        )
        fatal_reflection_errors = [
            item for item in reflected_errors if item != "empty_shape_repaired"
        ]
        if not fatal_reflection_errors and _span_signature(reflected) == _span_signature(final):
            final = reflected
            errors = [item for item in errors if item.startswith("provider_")]
            reflection_accepted = True
        else:
            errors.append("reflection_rejected")

    result = {
        "id": case.id,
        "dataset": "twitter2017",
        "variant": variant,
        "stage": stage,
        "retrieved_case_ids": retrieved_ids,
        "gold": [item.model_dump(mode="json") for item in case.entities],
        "text_predicted": [item.model_dump(mode="json") for item in text_prediction],
        "pre_reflection_predicted": [
            item.model_dump(mode="json") for item in pre_reflection
        ],
        "predicted": [item.model_dump(mode="json") for item in final],
        "metrics": twitter._result_metrics(case, final),
        "errors": errors,
        "text_errors": text_errors,
        "visual_errors": visual_errors,
        "visual_gate_triggered": visual_gate_triggered,
        "visual_changes_accepted": visual_changes_accepted,
        "visual_changes_rejected": visual_changes_rejected,
        "span_mutations": int(_span_signature(final) != _span_signature(text_prediction)),
        "reflection_triggered": reflection_triggered,
        "reflection_accepted": reflection_accepted,
        "image_valid": case.image_valid,
        "prompt_hash": canonical_hash(prompt),
        "raw_text": raw_text,
        "raw_visual": raw_visual,
        "raw_reflection": raw_reflection,
        "scoring_version": SCORING_VERSION,
    }
    v1.atomic_json(target, result)
    return result


async def _run_mnre_one(
    source: Path,
    schema: dict[str, Any],
    case: mnre.MNRECase,
    variant: VariantName,
    stage: StageName,
    settings: Settings,
    ledger: v1.AblationBudgetLedger,
    target: Path,
) -> dict[str, Any]:
    if target.exists():
        return dict(v1.load_json(target))
    retrieved_ids: list[str] = []
    examples: list[dict[str, Any]] = []
    if variant == "full":
        retrieved_ids, examples = _mnre_examples(source, case, stage)
    prompt = mnre_text_prompt(variant, schema, case, examples)
    prefix = f"ablation-v4:mnre-v2:{stage}:{variant}:{case.id}"
    raw_text, provider_errors = await v1._provider_json(
        settings, ledger, prompt, f"{prefix}:text", f"ablation-v4-mnre-{variant}-text"
    )
    text_prediction, text_errors = v1._parse_mnre_prediction(raw_text, provider_errors)
    final = text_prediction
    errors = list(text_errors)
    raw_visual = ""
    raw_fusion = ""
    visual_errors: list[str] = []
    visual_gate_triggered = False
    fusion_triggered = False
    fusion_accepted = False
    evidence: dict[str, str] | None = None

    if variant in {"multimodal", "full"} and text_prediction in VISUALLY_ELIGIBLE_RELATIONS:
        visual_gate_triggered = True
        visual_prompt = mnre_visual_prompt(schema, case, text_prediction)
        raw_visual, visual_provider_errors = await _provider_vlm_json(
            settings,
            ledger,
            visual_prompt,
            Path(case.image_path),
            f"{prefix}:visual",
            "ablation-v4-mnre-pair-evidence",
        )
        evidence, visual_errors = _parse_mnre_visual(raw_visual, visual_provider_errors)
        errors.extend(visual_errors)
        if (
            evidence
            and evidence["head_visible"] == "yes"
            and evidence["tail_visible"] == "yes"
            and evidence["visual_support"] == "contradicts"
            and evidence["confidence"] == "high"
        ):
            fusion_triggered = True
            fusion_prompt = mnre_fusion_prompt(schema, case, text_prediction, evidence)
            raw_fusion, fusion_provider_errors = await v1._provider_json(
                settings,
                ledger,
                fusion_prompt,
                f"{prefix}:fusion",
                "ablation-v4-mnre-conservative-fusion",
            )
            fused, fusion_errors = v1._parse_mnre_prediction(
                raw_fusion, fusion_provider_errors
            )
            if not fusion_errors:
                final = fused
                fusion_accepted = True
            else:
                errors.extend(fusion_errors)
                errors.append("fusion_rejected")

    pre_reflection = final
    raw_reflection = ""
    reflection_triggered = False
    reflection_accepted = False
    if variant == "full" and errors:
        reflection_triggered = True
        reflect_prompt = mnre_reflection_prompt(schema, case, final, errors)
        raw_reflection, reflection_provider_errors = await v1._provider_json(
            settings,
            ledger,
            reflect_prompt,
            f"{prefix}:reflection",
            "ablation-v4-mnre-failure-only-reflection",
        )
        reflected, reflected_errors = v1._parse_mnre_prediction(
            raw_reflection, reflection_provider_errors
        )
        if not reflected_errors:
            final = reflected
            errors = []
            reflection_accepted = True
        else:
            errors.append("reflection_rejected")

    result = {
        "id": case.id,
        "dataset": "mnre-v2",
        "variant": variant,
        "stage": stage,
        "retrieved_case_ids": retrieved_ids,
        "gold": case.relation,
        "gold_dataset_label": case.dataset_label,
        "text_predicted": text_prediction,
        "pre_reflection_predicted": pre_reflection,
        "predicted": final,
        "metrics": mnre._result_metrics(case, final),
        "errors": errors,
        "text_errors": text_errors,
        "visual_errors": visual_errors,
        "visual_gate_triggered": visual_gate_triggered,
        "visual_evidence": evidence,
        "fusion_triggered": fusion_triggered,
        "fusion_accepted": fusion_accepted,
        "endpoint_swaps": 0,
        "reflection_triggered": reflection_triggered,
        "reflection_accepted": reflection_accepted,
        "prompt_hash": canonical_hash(prompt),
        "raw_text": raw_text,
        "raw_visual": raw_visual,
        "raw_fusion": raw_fusion,
        "raw_reflection": raw_reflection,
        "scoring_version": SCORING_VERSION,
    }
    v1.atomic_json(target, result)
    return result


def _stage_cases(
    output: Path, source: Path, dataset: DatasetName, stage: StageName
) -> list[twitter.TwitterCase] | list[mnre.MNRECase]:
    split = dict(v1.load_json(output / "validation-splits.json"))
    ids: set[str] | None = None
    if stage == "smoke":
        ids = set(v1.load_json(output / "smoke-split.json")["ids"][dataset])
    elif stage == "dev":
        ids = set(split[dataset]["prompt_dev"])
    elif stage == "holdout":
        ids = set(split[dataset]["prompt_holdout"])
    if dataset == "twitter2017":
        twitter_cases = (
            _twitter_cases(output / "twitter2017" / "test_cases.json")
            if stage == "main"
            else _twitter_cases(source / "validation_cases.json")
        )
        if ids is None:
            return twitter_cases
        return [case for case in twitter_cases if case.id in ids]
    mnre_cases = _mnre_cases(
        source / ("test_cases.json" if stage == "main" else "validation_cases.json")
    )
    if ids is None:
        return mnre_cases
    return [case for case in mnre_cases if case.id in ids]


def _report_directory(
    output: Path, stage: StageName, dataset: DatasetName, variant: VariantName
) -> Path:
    return output / stage / dataset / variant


def _usage_for(
    ledger: v1.AblationBudgetLedger,
    dataset: DatasetName,
    stage: StageName,
    variant: VariantName,
) -> dict[str, Any]:
    prefix = f"ablation-v4:{dataset}:{stage}:{variant}:"
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


async def run_variant(
    output: Path,
    dataset: DatasetName,
    variant: VariantName,
    stage: StageName,
    settings: Settings,
    *,
    concurrency: int = 2,
    budget_limit_cny: float = 30.0,
) -> dict[str, Any]:
    if concurrency not in {1, 2}:
        raise ValueError("prediction concurrency must be 1 or 2")
    manifest = dict(v1.load_json(output / "manifest.json"))
    source = Path(
        manifest["twitter_source"] if dataset == "twitter2017" else manifest["mnre_source"]
    )
    schema = (
        twitter.load_schema(Path(manifest["schemas"][dataset]["path"]))
        if dataset == "twitter2017"
        else mnre.load_schema(Path(manifest["schemas"][dataset]["path"]))
    )
    cases = _stage_cases(output, source, dataset, stage)
    expected = {
        ("twitter2017", "smoke"): 20,
        ("twitter2017", "dev"): 100,
        ("twitter2017", "holdout"): 623,
        ("twitter2017", "main"): 723,
        ("mnre-v2", "smoke"): 20,
        ("mnre-v2", "dev"): 200,
        ("mnre-v2", "holdout"): 1423,
        ("mnre-v2", "main"): 1614,
    }[(dataset, stage)]
    if len(cases) != expected:
        raise RuntimeError(f"unexpected {dataset} {stage} case count: {len(cases)}")
    ledger = v1.AblationBudgetLedger(output / "budget.json", budget_limit_cny)
    directory = _report_directory(output, stage, dataset, variant)
    results: list[dict[str, Any]] = []
    next_index = 0
    first_error: BaseException | None = None

    async def worker() -> None:
        nonlocal next_index, first_error
        while first_error is None and next_index < len(cases):
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
    metrics = (
        v1.aggregate_twitter(results)
        if dataset == "twitter2017"
        else v1.aggregate_mnre(results)
    )
    report = {
        "dataset": dataset,
        "variant": variant,
        "variant_label": VARIANT_LABELS[variant],
        "stage": stage,
        "configuration": {
            "model": settings.llm_model,
            "vlm_model": settings.vlm_model,
            "temperature": 0,
            "schema_hash": manifest["schemas"][dataset]["hash"],
            "settings_hash": manifest["settings_hash"],
            "code_commit": manifest["code_commit"],
        },
        "metrics": metrics,
        "usage": _usage_for(ledger, dataset, stage, variant),
        "visual_gate": {
            "triggered": sum(bool(item["visual_gate_triggered"]) for item in results),
            "changes_accepted": sum(
                int(item.get("visual_changes_accepted", 0)) for item in results
            ),
            "changes_rejected": sum(
                int(item.get("visual_changes_rejected", 0)) for item in results
            ),
            "fusion_triggered": sum(bool(item.get("fusion_triggered")) for item in results),
            "fusion_accepted": sum(bool(item.get("fusion_accepted")) for item in results),
        },
        "reflection": {
            "triggered": sum(bool(item["reflection_triggered"]) for item in results),
            "accepted": sum(bool(item["reflection_accepted"]) for item in results),
        },
        "span_mutations": sum(int(item.get("span_mutations", 0)) for item in results),
        "endpoint_swaps": sum(int(item.get("endpoint_swaps", 0)) for item in results),
    }
    v1.atomic_json(directory / "report.json", report)
    return report


def _structural_gate(report: dict[str, Any]) -> None:
    dataset = str(report["dataset"])
    cases = int(report["metrics"]["cases"])
    errors = dict(report["metrics"]["errors"])
    invalid = int(errors.get("invalid_json_shape", 0))
    if invalid > math.ceil(cases * 0.01):
        raise RuntimeError(f"{dataset} exceeds the 1% invalid JSON gate")
    if dataset == "twitter2017" and int(report["span_mutations"]):
        raise RuntimeError("Twitter V4 changed a text-stage entity span")
    if dataset == "mnre-v2":
        if int(report["endpoint_swaps"]):
            raise RuntimeError("MNRE V4 swapped ordered endpoints")
        if int(errors.get("forbidden_relation_field", 0)):
            raise RuntimeError("MNRE visual evidence returned a forbidden relation field")


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
            _structural_gate(report)
            reports.append(report)
    manifest = dict(v1.load_json(output / "manifest.json"))
    frozen = {
        "experiment_version": EXPERIMENT_VERSION,
        "manifest_hash": canonical_hash(manifest),
        "validation_split_hash": canonical_hash(v1.load_json(output / "validation-splits.json")),
        "smoke_split_hash": canonical_hash(v1.load_json(output / "smoke-split.json")),
        "prompt_policy_hash": canonical_hash(
            {
                "twitter_text": twitter_text_prompt.__doc__,
                "twitter_visual": twitter_visual_prompt.__doc__,
                "twitter_reflection": twitter_reflection_prompt.__doc__,
                "mnre_text": mnre_text_prompt.__doc__,
                "mnre_visual": mnre_visual_prompt.__doc__,
                "mnre_fusion": mnre_fusion_prompt.__doc__,
                "mnre_reflection": mnre_reflection_prompt.__doc__,
                "visual_relations": sorted(VISUALLY_ELIGIBLE_RELATIONS),
            }
        ),
        "smoke_reports": reports,
    }
    v1.atomic_json(output / "frozen-config.json", frozen)
    return frozen


def _require_frozen(output: Path) -> None:
    frozen = dict(v1.load_json(output / "frozen-config.json"))
    if frozen["manifest_hash"] != canonical_hash(v1.load_json(output / "manifest.json")):
        raise RuntimeError("experiment manifest changed after V4 freeze")
    if frozen["validation_split_hash"] != canonical_hash(
        v1.load_json(output / "validation-splits.json")
    ):
        raise RuntimeError("validation splits changed after V4 freeze")


async def _run_validation_and_main(
    output: Path,
    dataset: DatasetName,
    settings: Settings,
    *,
    concurrency: int,
    budget_limit_cny: float,
) -> dict[str, Any]:
    _require_frozen(output)
    validation_reports = []
    for stage in ("dev", "holdout"):
        for variant in ("schema", "multimodal", "full"):
            report = await run_variant(
                output,
                dataset,
                variant,
                stage,
                settings,
                concurrency=concurrency,
                budget_limit_cny=budget_limit_cny,
            )
            _structural_gate(report)
            validation_reports.append(report)
    main_reports = []
    for variant in VARIANTS:
        report = await run_variant(
            output,
            dataset,
            variant,
            "main",
            settings,
            concurrency=concurrency,
            budget_limit_cny=budget_limit_cny,
        )
        _structural_gate(report)
        main_reports.append(report)
    payload = {
        "dataset": dataset,
        "validation_reports": validation_reports,
        "main_reports": main_reports,
        "gate": "passed",
    }
    v1.atomic_json(output / f"{dataset}-summary.json", payload)
    return payload


async def run_mner(
    output: Path,
    settings: Settings,
    *,
    concurrency: int = 2,
    budget_limit_cny: float = 30.0,
) -> dict[str, Any]:
    """Run validation and the complete Twitter-2017 V4 main experiment."""
    twitter_caption = await v1.prepare_twitter_test_captions(
        output,
        settings,
        concurrency=concurrency,
        budget_limit_cny=budget_limit_cny,
    )
    vector_path = output / "twitter2017" / "vectors" / "test.json"
    twitter_vectors = (
        v1.load_json(vector_path)
        if vector_path.exists()
        else await v1.prepare_twitter_test_vectors(output, settings)
    )
    payload = await _run_validation_and_main(
        output,
        "twitter2017",
        settings,
        concurrency=concurrency,
        budget_limit_cny=budget_limit_cny,
    )
    payload["twitter_test_captions"] = twitter_caption
    payload["twitter_test_vectors"] = twitter_vectors
    v1.atomic_json(output / "twitter2017-summary.json", payload)
    return payload


async def run_mre(
    output: Path,
    settings: Settings,
    *,
    concurrency: int = 2,
    budget_limit_cny: float = 30.0,
) -> dict[str, Any]:
    """Run validation and the complete MNRE-V2 V4 main experiment."""
    return await _run_validation_and_main(
        output,
        "mnre-v2",
        settings,
        concurrency=concurrency,
        budget_limit_cny=budget_limit_cny,
    )


async def run_all(
    output: Path,
    settings: Settings,
    *,
    concurrency: int = 2,
    budget_limit_cny: float = 30.0,
) -> dict[str, Any]:
    """Run MNER first and automatically continue to MRE only after its gate passes."""
    mner = await run_mner(
        output,
        settings,
        concurrency=concurrency,
        budget_limit_cny=budget_limit_cny,
    )
    if mner["gate"] != "passed":
        raise RuntimeError("MNER gate did not pass; MRE was not started")
    mre = await run_mre(
        output,
        settings,
        concurrency=concurrency,
        budget_limit_cny=budget_limit_cny,
    )
    summary = {"mner": mner, "mre": mre}
    v1.atomic_json(output / "main-summary.json", summary)
    return summary


def _prediction_records(
    output: Path, dataset: DatasetName, variant: VariantName
) -> list[dict[str, Any]]:
    directory = _report_directory(output, "main", dataset, variant) / "predictions"
    return sorted(
        [dict(v1.load_json(path)) for path in directory.glob("*.json")],
        key=lambda item: str(item["id"]),
    )


def export_results(output: Path) -> dict[str, Any]:
    """Export V4 JSON and CSV results without any paid stability repetition."""
    rows: list[dict[str, Any]] = []
    paired: list[dict[str, Any]] = []
    for dataset in DATASETS:
        records_by_variant = {
            variant: _prediction_records(output, dataset, variant) for variant in VARIANTS
        }
        expected = 723 if dataset == "twitter2017" else 1614
        if any(len(items) != expected for items in records_by_variant.values()):
            raise RuntimeError(f"{dataset} main results are incomplete")
        for variant in VARIANTS:
            report = dict(
                v1.load_json(_report_directory(output, "main", dataset, variant) / "report.json")
            )
            metrics = dict(report["metrics"])
            rows.append(
                {
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
                    "visual_gate": report["visual_gate"],
                    "reflection": report["reflection"],
                    "errors": metrics["errors"],
                }
            )
        for left, right in zip(VARIANTS[:-1], VARIANTS[1:], strict=True):
            paired.append(
                {
                    "dataset": dataset,
                    "left": left,
                    "right": right,
                    **v1._paired_bootstrap_delta(
                        records_by_variant[left], records_by_variant[right]
                    ),
                }
            )
    payload = {
        "experiment_version": EXPERIMENT_VERSION,
        "rows": rows,
        "paired_bootstrap": paired,
        "paid_stability_repetitions": 0,
        "manifest": v1.load_json(output / "manifest.json"),
    }
    v1.atomic_json(output / "results.json", payload)
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
        lines.append(",".join(str(row.get(header, "")) for header in headers))
    csv_path = output / "results.csv"
    temporary = csv_path.with_name(f".{csv_path.name}.{os.getpid()}.tmp")
    temporary.write_text("\n".join(lines) + "\n", encoding="utf-8")
    os.replace(temporary, csv_path)
    return payload


def evaluation_status(output: Path) -> dict[str, Any]:
    """Return resumable phase progress, budget, failures, and frozen hashes."""
    def optional(path: Path) -> Any:
        return v1.load_json(path) if path.exists() else None

    cells = []
    for stage in ("smoke", "dev", "holdout", "main"):
        for dataset in DATASETS:
            for variant in VARIANTS:
                cells.append(
                    {
                        "stage": stage,
                        "dataset": dataset,
                        "variant": variant,
                        "predictions": sum(
                            1
                            for _ in (
                                output / stage / dataset / variant / "predictions"
                            ).glob("*.json")
                        ),
                    }
                )
    return {
        "manifest": optional(output / "manifest.json"),
        "frozen": optional(output / "frozen-config.json"),
        "cells": cells,
        "budget": optional(output / "budget.json"),
        "mner_complete": (output / "twitter2017-summary.json").exists(),
        "mre_complete": (output / "mnre-v2-summary.json").exists(),
        "results": optional(output / "results.json"),
        "error_counts": dict(
            Counter(
                str(error)
                for path in output.glob("**/predictions/*.json")
                for error in dict(v1.load_json(path)).get("errors", [])
            )
        ),
    }
