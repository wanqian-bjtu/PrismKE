"""Four-stage PrismKE agent-progression evaluation for Twitter-2017 and MNRE-V2."""

from __future__ import annotations

import asyncio
import json
import os
from collections import Counter
from pathlib import Path
from statistics import mean
from typing import Any, Literal, cast

from src.core.ids import canonical_hash, file_sha256
from src.core.settings import Settings
from src.domain import ProviderCallRecord
from src.evaluation import component_ablation as v1
from src.evaluation import component_ablation_v4 as v4
from src.evaluation import mnre_v2 as mnre
from src.evaluation import twitter2017 as twitter
from src.providers.common import parse_json_object

DatasetName = Literal["twitter2017", "mnre-v2"]
VariantName = Literal["vanilla", "extraction", "governance", "fusion_review"]
StageName = Literal["dev", "holdout", "main"]
PromptVersion = Literal["v1", "v2", "v3"]

EXPERIMENT_VERSION = "agent-progression-v1"
SCORING_VERSION = "agent-progression-scoring-v1"
GATE_POLICY_VERSION = "agent-progression-gate-v2"
SEED = 2027
BOOTSTRAP_SAMPLES = 10_000
TWITTER_TOP_K = 3
MNRE_TOP_K = 5
VARIANTS: tuple[VariantName, ...] = (
    "vanilla",
    "extraction",
    "governance",
    "fusion_review",
)
DATASETS: tuple[DatasetName, ...] = ("twitter2017", "mnre-v2")
PROMPT_VERSIONS: tuple[PromptVersion, ...] = ("v1", "v2", "v3")
BASE_VARIANTS: tuple[VariantName, ...] = ("vanilla", "extraction")
VARIANT_LABELS: dict[VariantName, str] = {
    "vanilla": "Vanilla",
    "extraction": "Extraction Agent Only",
    "governance": "+ Entity and Fact Governance Agent",
    "fusion_review": "+ Knowledge Fusion and Review Agent",
}


class AgentProgressionBudgetLedger(v1.AblationBudgetLedger):
    """Independent ledger with the authorized 12/18 CNY progress milestones."""

    def record(self, operation_id: str, record: ProviderCallRecord) -> list[float]:
        before = self.cost
        crossed = super().record(operation_id, record)
        for milestone in (12.0, 18.0):
            if before < milestone <= self.cost and milestone not in self.payload["milestones"]:
                self.payload["milestones"].append(milestone)
                crossed.append(milestone)
        self.persist()
        return sorted(crossed)


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
    component_v4_output: Path,
    twitter_dataset: Path,
    twitter_schema_path: Path,
    mnre_schema_path: Path,
    invalid_images_path: Path,
    settings: Settings,
) -> dict[str, Any]:
    """Freeze non-model assets while explicitly refusing to reuse V4 predictions."""
    twitter_schema = twitter.load_schema(twitter_schema_path)
    mnre_schema = mnre.load_schema(mnre_schema_path)
    twitter_manifest = dict(v1.load_json(twitter_source / "manifest.json"))
    mnre_manifest = dict(v1.load_json(mnre_source / "manifest.json"))
    twitter_frozen = dict(v1.load_json(twitter_source / "frozen-config.json"))
    mnre_frozen = dict(v1.load_json(mnre_source / "frozen-config.json"))
    if int(twitter_frozen["top_k"]) != TWITTER_TOP_K:
        raise RuntimeError("Twitter source experiment does not use top-k=3")
    if int(mnre_frozen["top_k"]) != MNRE_TOP_K:
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

    twitter_test_vectors = component_v4_output / "twitter2017" / "vectors" / "test.json"
    if not twitter_test_vectors.exists():
        raise RuntimeError("V4 Twitter test query vectors are unavailable")

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
    settings_payload = _settings_fingerprint(settings)
    manifest = {
        "experiment_version": EXPERIMENT_VERSION,
        "code_commit": v1._git_commit(),
        "settings": settings_payload,
        "settings_hash": canonical_hash(settings_payload),
        "twitter_source": twitter_source.resolve().as_posix(),
        "mnre_source": mnre_source.resolve().as_posix(),
        "component_v4_output": component_v4_output.resolve().as_posix(),
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
        "asset_hashes": {
            "twitter_case_library": twitter_manifest["case_library_hash"],
            "twitter_frozen_config": canonical_hash(twitter_frozen),
            "twitter_test_vectors": file_sha256(twitter_test_vectors),
            "mnre_final_case_library": mnre_manifest["final_case_library_hash"],
            "mnre_frozen_config": canonical_hash(mnre_frozen),
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
        "prompt_versions": list(PROMPT_VERSIONS),
        "retrieval_top_k": {"twitter2017": TWITTER_TOP_K, "mnre-v2": MNRE_TOP_K},
        "bootstrap_samples": BOOTSTRAP_SAMPLES,
        "seed": SEED,
        "budget_limit_cny": 20.0,
        "paid_stability_repetitions": 0,
        "prediction_reuse": False,
        "system_progression_not_pure_agent_ablation": True,
        "gold_fields_forwarded_to_model": False,
    }
    v1.atomic_json(output / "manifest.json", manifest)
    return manifest


def twitter_vanilla_prompt(case: twitter.TwitterCase) -> str:
    """Build the label-ID-only MNER baseline without a schema or visual input."""
    return (
        "Extract named entities from SOURCE text. Return JSON only as "
        '{"entities":[{"text":"...","start":0,"end":1,"type":"PER"}]}. '
        "Offsets use the Unicode half-open interval [start,end), and text must equal "
        "SOURCE[start:end]. Use only PER, ORG, LOC, or MISC. If there are no entities, "
        'return {"entities":[]}.'
        f"\nLABEL_IDS: {json.dumps(['PER', 'ORG', 'LOC', 'MISC'])}"
        f"\nSOURCE: {json.dumps(case.text, ensure_ascii=False)}"
    )


def mnre_vanilla_prompt(case: mnre.MNRECase) -> str:
    """Build the raw-label-only MRE baseline without relation semantics or visual input."""
    labels = sorted(mnre.DATASET_TO_CANONICAL)
    return (
        "Classify the ordered HEAD-TAIL relation in SOURCE. Select exactly one LABEL_ID and "
        'return JSON only as {"relation":"LABEL_ID"}. Never exchange HEAD and TAIL.'
        f"\nLABEL_IDS: {json.dumps(labels, ensure_ascii=False)}"
        f"\nSOURCE: {json.dumps(mnre.marked_text(case), ensure_ascii=False)}"
        f"\nHEAD: {json.dumps(case.head.model_dump(mode='json'), ensure_ascii=False)}"
        f"\nTAIL: {json.dumps(case.tail.model_dump(mode='json'), ensure_ascii=False)}"
    )


def twitter_governance_prompt(
    version: PromptVersion,
    schema: dict[str, Any],
    case: twitter.TwitterCase,
    entities: list[twitter.PredictedEntity],
    visual_evidence: object,
) -> str:
    """Review fixed MNER candidates without retrieval, fusion, or new spans."""
    policies = {
        "v1": "Review every candidate and correct only clear errors.",
        "v2": "Be conservative: change or reject only with high-confidence textual evidence.",
        "v3": "Prioritize complete proper-name boundaries and distinctions among all four types.",
    }
    payload = [item.model_dump(mode="json") for item in entities]
    return (
        "ENTITY_AND_FACT_GOVERNANCE_AGENT. "
        + policies[version]
        + " Existing text/start/end values are immutable. Do not add entities. For each "
        "candidate return one decision with candidate_id, action=keep|change_type|reject, "
        "type=null or an allowed canonical type, confidence=high|medium|low, and a short "
        "reason_code. Only high-confidence valid changes will be applied. Return JSON only as "
        '{"decisions":[...]}. Do not use or request training examples.\n'
        f"SCHEMA: {json.dumps(schema, ensure_ascii=False)}\n"
        f"SOURCE: {json.dumps(case.text, ensure_ascii=False)}\n"
        f"FIXED_EXTRACTION_ENTITIES: {json.dumps(payload, ensure_ascii=False)}\n"
        f"EXTRACTION_VISUAL_EVIDENCE: {json.dumps(visual_evidence, ensure_ascii=False)}"
    )


def twitter_fusion_prompt(
    version: PromptVersion,
    schema: dict[str, Any],
    case: twitter.TwitterCase,
    entities: list[twitter.PredictedEntity],
    examples: list[dict[str, Any]],
) -> str:
    """Run one bounded MNER evidence review with frozen retrieved training cases."""
    policies = {
        "v1": "Use examples only as task demonstrations, never as entities for this source.",
        "v2": (
            "Prefer the governed prediction unless source evidence clearly supports a correction."
        ),
        "v3": (
            "Check omissions, false positives, type confusion, and complete source boundaries once."
        ),
    }
    return (
        "KNOWLEDGE_FUSION_AND_REVIEW_AGENT. "
        + policies[version]
        + " Perform exactly one bounded review. You may keep, delete, change type, or add a "
        "missing entity. Every final entity must be an exact non-overlapping SOURCE substring, "
        "use an allowed canonical type, and preserve complete source-written names. Return JSON "
        'only as {"entities":[{"text":"...","start":0,"end":1,"type":"Person"}]}.\n'
        f"SCHEMA: {json.dumps(schema, ensure_ascii=False)}\n"
        f"SOURCE: {json.dumps(case.text, ensure_ascii=False)}\n"
        "GOVERNED_ENTITIES: "
        + json.dumps([item.model_dump(mode="json") for item in entities], ensure_ascii=False)
        + "\nGOLD_TRAINING_EXAMPLES: "
        + json.dumps(examples, ensure_ascii=False)
    )


def mnre_governance_prompt(
    version: PromptVersion,
    schema: dict[str, Any],
    case: mnre.MNRECase,
    relation: str,
    visual_evidence: object,
) -> str:
    """Review one fixed ordered-pair relation without retrieval or endpoint changes."""
    policies = {
        "v1": "Review the relation against the schema and source evidence.",
        "v2": "Be conservative and change only clear high-confidence errors.",
        "v3": "Check direction, symmetry, domain/range semantics, and NoRelation carefully.",
    }
    return (
        "ENTITY_AND_FACT_GOVERNANCE_AGENT. "
        + policies[version]
        + " HEAD and TAIL are immutable and ordered. Do not use training examples. Return JSON "
        "only with action=keep|change_relation|reject_to_NoRelation, relation as an allowed "
        "canonical relation or null, confidence=high|medium|low, and reason_code. Only valid "
        "high-confidence changes will be applied.\n"
        f"SCHEMA: {json.dumps(schema, ensure_ascii=False)}\n"
        f"SOURCE: {json.dumps(mnre.marked_text(case), ensure_ascii=False)}\n"
        f"HEAD: {json.dumps(case.head.model_dump(mode='json'), ensure_ascii=False)}\n"
        f"TAIL: {json.dumps(case.tail.model_dump(mode='json'), ensure_ascii=False)}\n"
        f"EXTRACTION_RELATION: {json.dumps(relation)}\n"
        f"EXTRACTION_VISUAL_EVIDENCE: {json.dumps(visual_evidence, ensure_ascii=False)}"
    )


def mnre_fusion_prompt(
    version: PromptVersion,
    schema: dict[str, Any],
    case: mnre.MNRECase,
    relation: str,
    examples: list[dict[str, Any]],
) -> str:
    """Run one bounded MRE evidence review with frozen retrieved cases."""
    policies = {
        "v1": "Use examples only as relation demonstrations and verify against this source.",
        "v2": "Prefer the governed relation unless source evidence clearly supports a correction.",
        "v3": "Check relation semantics, ordered direction, NoRelation, and conflicts once.",
    }
    return (
        "KNOWLEDGE_FUSION_AND_REVIEW_AGENT. "
        + policies[version]
        + " Perform exactly one bounded review. HEAD and TAIL are immutable and must not be "
        "exchanged. Select one allowed canonical relation. Return JSON only as "
        '{"relation":"MemberOf"}.\n'
        f"SCHEMA: {json.dumps(schema, ensure_ascii=False)}\n"
        f"SOURCE: {json.dumps(mnre.marked_text(case), ensure_ascii=False)}\n"
        f"HEAD: {json.dumps(case.head.model_dump(mode='json'), ensure_ascii=False)}\n"
        f"TAIL: {json.dumps(case.tail.model_dump(mode='json'), ensure_ascii=False)}\n"
        f"GOVERNED_RELATION: {json.dumps(relation)}\n"
        f"GOLD_TRAINING_EXAMPLES: {json.dumps(examples, ensure_ascii=False)}"
    )


def _parse_twitter_vanilla(
    case: twitter.TwitterCase, raw: str, provider_errors: list[str]
) -> tuple[list[twitter.PredictedEntity], list[str]]:
    if provider_errors:
        return [], [*provider_errors, "invalid_json_shape"]
    try:
        payload = parse_json_object(raw)
    except (TypeError, json.JSONDecodeError):
        return [], ["invalid_json_shape"]
    entities = payload.get("entities")
    if not isinstance(entities, list):
        return [], ["invalid_json_shape"]
    converted: list[dict[str, Any]] = []
    errors: list[str] = []
    for item in entities:
        if not isinstance(item, dict):
            errors.append("invalid_entity_structure")
            continue
        label = item.get("type")
        if label not in twitter.CANONICAL_TYPES:
            errors.append("type_not_in_label_inventory")
            continue
        converted.append({**item, "type": twitter.CANONICAL_TYPES[str(label)]})
    predicted, validation_errors = twitter.validate_prediction(case, {"entities": converted})
    return predicted, [*errors, *validation_errors]


def _parse_mnre_vanilla(raw: str, provider_errors: list[str]) -> tuple[str, list[str]]:
    if provider_errors:
        return mnre.NO_RELATION, [*provider_errors, "invalid_json_shape"]
    try:
        payload = parse_json_object(raw)
    except (TypeError, json.JSONDecodeError):
        return mnre.NO_RELATION, ["invalid_json_shape"]
    label = payload.get("relation")
    if not isinstance(label, str) or label not in mnre.DATASET_TO_CANONICAL:
        return mnre.NO_RELATION, ["relation_not_in_label_inventory"]
    return mnre.DATASET_TO_CANONICAL[label], []


def _parse_twitter_governance(
    raw: str, provider_errors: list[str], candidate_count: int
) -> tuple[dict[int, dict[str, Any]], list[str]]:
    if provider_errors:
        return {}, [*provider_errors, "invalid_governance_json"]
    try:
        payload = parse_json_object(raw)
    except (TypeError, json.JSONDecodeError):
        return {}, ["invalid_governance_json"]
    decisions = payload.get("decisions")
    if not isinstance(decisions, list):
        return {}, ["invalid_governance_shape"]
    parsed: dict[int, dict[str, Any]] = {}
    errors: list[str] = []
    for item in decisions:
        if not isinstance(item, dict) or type(item.get("candidate_id")) is not int:
            errors.append("invalid_governance_decision")
            continue
        candidate_id = int(item["candidate_id"])
        if candidate_id < 0 or candidate_id >= candidate_count or candidate_id in parsed:
            errors.append("invalid_governance_decision")
            continue
        action = item.get("action")
        entity_type = item.get("type")
        confidence = item.get("confidence")
        if action not in {"keep", "change_type", "reject"}:
            errors.append("invalid_governance_action")
            continue
        if confidence not in {"high", "medium", "low"}:
            errors.append("invalid_governance_confidence")
            continue
        if action == "change_type" and entity_type not in twitter.DATASET_LABELS:
            errors.append("type_not_in_schema")
            continue
        parsed[candidate_id] = {
            "action": action,
            "type": entity_type,
            "confidence": confidence,
            "reason_code": str(item.get("reason_code") or "unspecified")[:80],
        }
    return parsed, errors


def apply_twitter_governance(
    candidates: list[twitter.PredictedEntity], decisions: dict[int, dict[str, Any]]
) -> tuple[list[twitter.PredictedEntity], int, int]:
    """Apply only high-confidence type/reject decisions and deterministically deduplicate."""
    output: list[twitter.PredictedEntity] = []
    accepted = rejected = 0
    for index, candidate in enumerate(candidates):
        decision = decisions.get(index)
        if not decision or decision["confidence"] != "high" or decision["action"] == "keep":
            output.append(candidate)
            continue
        if decision["action"] == "reject":
            accepted += 1
            continue
        entity_type = decision.get("type")
        if isinstance(entity_type, str) and entity_type in twitter.DATASET_LABELS:
            output.append(candidate.model_copy(update={"type": entity_type}))
            accepted += int(entity_type != candidate.type)
        else:
            output.append(candidate)
            rejected += 1
    unique: list[twitter.PredictedEntity] = []
    seen: set[tuple[str, int, int, str]] = set()
    for item in output:
        key = (item.text, item.start, item.end, item.type)
        if key in seen:
            accepted += 1
            continue
        seen.add(key)
        unique.append(item)
    return unique, accepted, rejected


def _parse_mnre_governance(
    raw: str, provider_errors: list[str]
) -> tuple[dict[str, Any] | None, list[str]]:
    if provider_errors:
        return None, [*provider_errors, "invalid_governance_json"]
    try:
        payload = parse_json_object(raw)
    except (TypeError, json.JSONDecodeError):
        return None, ["invalid_governance_json"]
    action = payload.get("action")
    relation = payload.get("relation")
    confidence = payload.get("confidence")
    if action not in {"keep", "change_relation", "reject_to_NoRelation"}:
        return None, ["invalid_governance_action"]
    if confidence not in {"high", "medium", "low"}:
        return None, ["invalid_governance_confidence"]
    if action == "change_relation" and relation not in mnre.CANONICAL_TO_DATASET:
        return None, ["relation_not_in_schema"]
    return {
        "action": action,
        "relation": relation,
        "confidence": confidence,
        "reason_code": str(payload.get("reason_code") or "unspecified")[:80],
    }, []


def apply_mnre_governance(relation: str, decision: dict[str, Any] | None) -> tuple[str, bool]:
    if not decision or decision["confidence"] != "high" or decision["action"] == "keep":
        return relation, False
    if decision["action"] == "reject_to_NoRelation":
        return mnre.NO_RELATION, relation != mnre.NO_RELATION
    candidate = decision.get("relation")
    if isinstance(candidate, str) and candidate in mnre.CANONICAL_TO_DATASET:
        return candidate, candidate != relation
    return relation, False


def _twitter_examples(
    output: Path, source: Path, case: twitter.TwitterCase, stage: StageName
) -> tuple[list[str], list[dict[str, Any]]]:
    manifest = dict(v1.load_json(output / "manifest.json"))
    v4_output = Path(str(manifest["component_v4_output"]))
    return v4._twitter_examples(v4_output, source, case, "main" if stage == "main" else "dev")


def _mnre_examples(
    source: Path, case: mnre.MNRECase, stage: StageName
) -> tuple[list[str], list[dict[str, Any]]]:
    return v4._mnre_examples(source, case, "main" if stage == "main" else "dev")


def _prediction_hash(value: object) -> str:
    return canonical_hash(value)


def _twitter_payload(items: list[twitter.PredictedEntity]) -> list[dict[str, Any]]:
    return [item.model_dump(mode="json") for item in items]


def _json_keyed_visual_evidence(
    evidence: dict[int, dict[str, str | None]],
) -> dict[str, dict[str, str | None]]:
    """Convert candidate indexes to JSON object keys before durable storage."""
    return {str(candidate_id): value for candidate_id, value in evidence.items()}


def _twitter_final_output_invalid(
    case: twitter.TwitterCase, predicted: object
) -> bool:
    """Return whether the durable final MNER output violates its strict contract."""
    if not isinstance(predicted, list):
        return True
    spans: list[tuple[int, int]] = []
    for value in predicted:
        if not isinstance(value, dict):
            return True
        text = value.get("text")
        start = value.get("start")
        end = value.get("end")
        entity_type = value.get("type")
        if (
            not isinstance(text, str)
            or type(start) is not int
            or type(end) is not int
            or entity_type not in twitter.DATASET_LABELS
            or start < 0
            or end <= start
            or end > len(case.text)
            or case.text[start:end] != text
        ):
            return True
        spans.append((start, end))
    spans.sort()
    return any(
        current[0] < previous[1]
        for previous, current in zip(spans, spans[1:], strict=False)
    )


def _governance_audit(
    source: list[twitter.PredictedEntity],
    final: list[twitter.PredictedEntity],
    decisions: dict[int, dict[str, Any]],
) -> dict[str, int]:
    """Separate immutable-span violations from permitted reject/dedup removals."""
    source_spans = Counter((item.text, item.start, item.end) for item in source)
    retained_span_mutations = 0
    remaining = source_spans.copy()
    for item in final:
        span = (item.text, item.start, item.end)
        if remaining[span] <= 0:
            retained_span_mutations += 1
        else:
            remaining[span] -= 1

    governance_rejections = sum(
        decision.get("action") == "reject" and decision.get("confidence") == "high"
        for decision in decisions.values()
    )
    provisional: list[twitter.PredictedEntity] = []
    for index, candidate in enumerate(source):
        decision = decisions.get(index)
        if (
            decision
            and decision.get("confidence") == "high"
            and decision.get("action") == "reject"
        ):
            continue
        if (
            decision
            and decision.get("confidence") == "high"
            and decision.get("action") == "change_type"
            and decision.get("type") in twitter.DATASET_LABELS
        ):
            candidate = candidate.model_copy(update={"type": decision["type"]})
        provisional.append(candidate)
    unique_keys = {(item.text, item.start, item.end, item.type) for item in provisional}
    return {
        "retained_span_mutations": retained_span_mutations,
        "governance_rejections": governance_rejections,
        "governance_deduplications": len(provisional) - len(unique_keys),
    }


def _record_twitter(
    case: twitter.TwitterCase,
    variant: VariantName,
    stage: StageName,
    predicted: list[twitter.PredictedEntity],
    errors: list[str],
    **extra: Any,
) -> dict[str, Any]:
    return {
        "id": case.id,
        "dataset": "twitter2017",
        "variant": variant,
        "stage": stage,
        "gold": [item.model_dump(mode="json") for item in case.entities],
        "predicted": _twitter_payload(predicted),
        "metrics": twitter._result_metrics(case, predicted),
        "errors": errors,
        "image_valid": case.image_valid,
        "scoring_version": SCORING_VERSION,
        **extra,
    }


def _record_mnre(
    case: mnre.MNRECase,
    variant: VariantName,
    stage: StageName,
    predicted: str,
    errors: list[str],
    **extra: Any,
) -> dict[str, Any]:
    return {
        "id": case.id,
        "dataset": "mnre-v2",
        "variant": variant,
        "stage": stage,
        "gold": case.relation,
        "gold_dataset_label": case.dataset_label,
        "predicted": predicted,
        "metrics": mnre._result_metrics(case, predicted),
        "errors": errors,
        "endpoint_swaps": 0,
        "scoring_version": SCORING_VERSION,
        **extra,
    }


async def _twitter_vanilla_one(
    case: twitter.TwitterCase,
    stage: StageName,
    settings: Settings,
    ledger: AgentProgressionBudgetLedger,
    target: Path,
) -> dict[str, Any]:
    if target.exists():
        return dict(v1.load_json(target))
    prompt = twitter_vanilla_prompt(case)
    prefix = f"agent-progression:twitter2017:{stage}:vanilla:{case.id}"
    raw, provider_errors = await v1._provider_json(
        settings, ledger, prompt, f"{prefix}:predict", "agent-progression-twitter-vanilla-v1"
    )
    predicted, errors = _parse_twitter_vanilla(case, raw, provider_errors)
    result = _record_twitter(
        case,
        "vanilla",
        stage,
        predicted,
        errors,
        prompt_hash=canonical_hash(prompt),
        raw=raw,
    )
    v1.atomic_json(target, result)
    return result


async def _twitter_extraction_one(
    schema: dict[str, Any],
    case: twitter.TwitterCase,
    stage: StageName,
    settings: Settings,
    ledger: AgentProgressionBudgetLedger,
    target: Path,
) -> dict[str, Any]:
    if target.exists():
        return dict(v1.load_json(target))
    prompt = v4.twitter_text_prompt("multimodal", schema, case)
    prefix = f"agent-progression:twitter2017:{stage}:extraction:{case.id}"
    raw_text, provider_errors = await v1._provider_json(
        settings, ledger, prompt, f"{prefix}:text", "agent-progression-twitter-extraction-text-v1"
    )
    text_prediction, text_errors = v4._parse_twitter_prediction_v4(
        case, raw_text, provider_errors
    )
    final = text_prediction
    errors = list(text_errors)
    raw_visual = ""
    visual_evidence: dict[int, dict[str, str | None]] = {}
    visual_errors: list[str] = []
    accepted = rejected = 0
    if text_prediction and case.image_valid:
        visual_prompt = v4.twitter_visual_prompt(schema, case, text_prediction)
        raw_visual, visual_provider_errors = await v4._provider_vlm_json(
            settings,
            ledger,
            visual_prompt,
            Path(case.image_path),
            f"{prefix}:visual",
            "agent-progression-twitter-extraction-visual-v1",
        )
        visual_evidence, visual_errors = v4._parse_twitter_visual(
            raw_visual, visual_provider_errors, len(text_prediction)
        )
        errors.extend(visual_errors)
        final, accepted, rejected = v4.apply_twitter_visual_gate(
            text_prediction, visual_evidence
        )
    result = _record_twitter(
        case,
        "extraction",
        stage,
        final,
        errors,
        text_predicted=_twitter_payload(text_prediction),
        visual_evidence=_json_keyed_visual_evidence(visual_evidence),
        visual_changes_accepted=accepted,
        visual_changes_rejected=rejected,
        span_mutations=int(v4._span_signature(final) != v4._span_signature(text_prediction)),
        prompt_hash=canonical_hash(prompt),
        raw_text=raw_text,
        raw_visual=raw_visual,
    )
    v1.atomic_json(target, result)
    return result


async def _mnre_vanilla_one(
    case: mnre.MNRECase,
    stage: StageName,
    settings: Settings,
    ledger: AgentProgressionBudgetLedger,
    target: Path,
) -> dict[str, Any]:
    if target.exists():
        return dict(v1.load_json(target))
    prompt = mnre_vanilla_prompt(case)
    prefix = f"agent-progression:mnre-v2:{stage}:vanilla:{case.id}"
    raw, provider_errors = await v1._provider_json(
        settings, ledger, prompt, f"{prefix}:predict", "agent-progression-mnre-vanilla-v1"
    )
    predicted, errors = _parse_mnre_vanilla(raw, provider_errors)
    result = _record_mnre(
        case,
        "vanilla",
        stage,
        predicted,
        errors,
        prompt_hash=canonical_hash(prompt),
        raw=raw,
    )
    v1.atomic_json(target, result)
    return result


async def _mnre_extraction_one(
    schema: dict[str, Any],
    case: mnre.MNRECase,
    stage: StageName,
    settings: Settings,
    ledger: AgentProgressionBudgetLedger,
    target: Path,
) -> dict[str, Any]:
    if target.exists():
        return dict(v1.load_json(target))
    prompt = v4.mnre_text_prompt("multimodal", schema, case)
    prefix = f"agent-progression:mnre-v2:{stage}:extraction:{case.id}"
    raw_text, provider_errors = await v1._provider_json(
        settings, ledger, prompt, f"{prefix}:text", "agent-progression-mnre-extraction-text-v1"
    )
    text_prediction, text_errors = v1._parse_mnre_prediction(raw_text, provider_errors)
    final = text_prediction
    errors = list(text_errors)
    raw_visual = ""
    raw_fusion = ""
    evidence: dict[str, str] | None = None
    fusion_accepted = False
    if text_prediction in v4.VISUALLY_ELIGIBLE_RELATIONS:
        visual_prompt = v4.mnre_visual_prompt(schema, case, text_prediction)
        raw_visual, visual_provider_errors = await v4._provider_vlm_json(
            settings,
            ledger,
            visual_prompt,
            Path(case.image_path),
            f"{prefix}:visual",
            "agent-progression-mnre-extraction-visual-v1",
        )
        evidence, visual_errors = v4._parse_mnre_visual(raw_visual, visual_provider_errors)
        errors.extend(visual_errors)
        if (
            evidence
            and evidence["head_visible"] == "yes"
            and evidence["tail_visible"] == "yes"
            and evidence["visual_support"] == "contradicts"
            and evidence["confidence"] == "high"
        ):
            fusion_prompt = v4.mnre_fusion_prompt(schema, case, text_prediction, evidence)
            raw_fusion, fusion_provider_errors = await v1._provider_json(
                settings,
                ledger,
                fusion_prompt,
                f"{prefix}:visual-fusion",
                "agent-progression-mnre-extraction-fusion-v1",
            )
            fused, fusion_errors = v1._parse_mnre_prediction(
                raw_fusion, fusion_provider_errors
            )
            if not fusion_errors:
                final = fused
                fusion_accepted = final != text_prediction
            else:
                errors.extend(fusion_errors)
                errors.append("visual_fusion_rejected")
    result = _record_mnre(
        case,
        "extraction",
        stage,
        final,
        errors,
        text_predicted=text_prediction,
        visual_evidence=evidence,
        fusion_accepted=fusion_accepted,
        prompt_hash=canonical_hash(prompt),
        raw_text=raw_text,
        raw_visual=raw_visual,
        raw_fusion=raw_fusion,
    )
    v1.atomic_json(target, result)
    return result


async def _twitter_governance_one(
    schema: dict[str, Any],
    case: twitter.TwitterCase,
    stage: StageName,
    version: PromptVersion,
    input_record: dict[str, Any],
    settings: Settings,
    ledger: AgentProgressionBudgetLedger,
    target: Path,
) -> dict[str, Any]:
    if target.exists():
        return dict(v1.load_json(target))
    source_entities = [
        twitter.PredictedEntity.model_validate(item) for item in input_record["predicted"]
    ]
    prompt = twitter_governance_prompt(
        version,
        schema,
        case,
        source_entities,
        input_record.get("visual_evidence"),
    )
    prefix = f"agent-progression:twitter2017:{stage}:governance:{version}:{case.id}"
    raw, provider_errors = await v1._provider_json(
        settings,
        ledger,
        prompt,
        f"{prefix}:review",
        f"agent-progression-twitter-governance-{version}",
    )
    decisions, errors = _parse_twitter_governance(
        raw, provider_errors, len(source_entities)
    )
    final, accepted, rejected = apply_twitter_governance(source_entities, decisions)
    audit = _governance_audit(source_entities, final, decisions)
    input_hash = _prediction_hash(input_record["predicted"])
    result = _record_twitter(
        case,
        "governance",
        stage,
        final,
        errors,
        prompt_version=version,
        input_variant="extraction",
        input_prediction_hash=input_hash,
        modifications_accepted=accepted,
        modifications_rejected=rejected,
        span_mutations=audit["retained_span_mutations"],
        **audit,
        prompt_hash=canonical_hash(prompt),
        raw=raw,
    )
    v1.atomic_json(target, result)
    return result


async def _twitter_fusion_one(
    output: Path,
    source: Path,
    schema: dict[str, Any],
    case: twitter.TwitterCase,
    stage: StageName,
    version: PromptVersion,
    input_record: dict[str, Any],
    settings: Settings,
    ledger: AgentProgressionBudgetLedger,
    target: Path,
) -> dict[str, Any]:
    if target.exists():
        return dict(v1.load_json(target))
    source_entities = [
        twitter.PredictedEntity.model_validate(item) for item in input_record["predicted"]
    ]
    retrieved_ids, examples = _twitter_examples(output, source, case, stage)
    prompt = twitter_fusion_prompt(version, schema, case, source_entities, examples)
    prefix = f"agent-progression:twitter2017:{stage}:fusion_review:{version}:{case.id}"
    raw, provider_errors = await v1._provider_json(
        settings,
        ledger,
        prompt,
        f"{prefix}:review",
        f"agent-progression-twitter-fusion-review-{version}",
    )
    reviewed, errors = v4._parse_twitter_prediction_v4(case, raw, provider_errors)
    accepted = not errors
    final = reviewed if accepted else source_entities
    if not accepted:
        errors.append("fusion_review_rejected")
    result = _record_twitter(
        case,
        "fusion_review",
        stage,
        final,
        errors,
        prompt_version=version,
        input_variant="governance",
        input_prediction_hash=_prediction_hash(input_record["predicted"]),
        retrieved_case_ids=retrieved_ids,
        review_accepted=accepted and _twitter_payload(final) != input_record["predicted"],
        prompt_hash=canonical_hash(prompt),
        raw=raw,
    )
    v1.atomic_json(target, result)
    return result


async def _mnre_governance_one(
    schema: dict[str, Any],
    case: mnre.MNRECase,
    stage: StageName,
    version: PromptVersion,
    input_record: dict[str, Any],
    settings: Settings,
    ledger: AgentProgressionBudgetLedger,
    target: Path,
) -> dict[str, Any]:
    if target.exists():
        return dict(v1.load_json(target))
    source_relation = str(input_record["predicted"])
    prompt = mnre_governance_prompt(
        version,
        schema,
        case,
        source_relation,
        input_record.get("visual_evidence"),
    )
    prefix = f"agent-progression:mnre-v2:{stage}:governance:{version}:{case.id}"
    raw, provider_errors = await v1._provider_json(
        settings,
        ledger,
        prompt,
        f"{prefix}:review",
        f"agent-progression-mnre-governance-{version}",
    )
    decision, errors = _parse_mnre_governance(raw, provider_errors)
    final, changed = apply_mnre_governance(source_relation, decision)
    result = _record_mnre(
        case,
        "governance",
        stage,
        final,
        errors,
        prompt_version=version,
        input_variant="extraction",
        input_prediction_hash=_prediction_hash(source_relation),
        modifications_accepted=int(changed),
        prompt_hash=canonical_hash(prompt),
        raw=raw,
    )
    v1.atomic_json(target, result)
    return result


async def _mnre_fusion_one(
    source: Path,
    schema: dict[str, Any],
    case: mnre.MNRECase,
    stage: StageName,
    version: PromptVersion,
    input_record: dict[str, Any],
    settings: Settings,
    ledger: AgentProgressionBudgetLedger,
    target: Path,
) -> dict[str, Any]:
    if target.exists():
        return dict(v1.load_json(target))
    source_relation = str(input_record["predicted"])
    retrieved_ids, examples = _mnre_examples(source, case, stage)
    prompt = mnre_fusion_prompt(version, schema, case, source_relation, examples)
    prefix = f"agent-progression:mnre-v2:{stage}:fusion_review:{version}:{case.id}"
    raw, provider_errors = await v1._provider_json(
        settings,
        ledger,
        prompt,
        f"{prefix}:review",
        f"agent-progression-mnre-fusion-review-{version}",
    )
    reviewed, errors = v1._parse_mnre_prediction(raw, provider_errors)
    accepted = not errors
    final = reviewed if accepted else source_relation
    if not accepted:
        errors.append("fusion_review_rejected")
    result = _record_mnre(
        case,
        "fusion_review",
        stage,
        final,
        errors,
        prompt_version=version,
        input_variant="governance",
        input_prediction_hash=_prediction_hash(source_relation),
        retrieved_case_ids=retrieved_ids,
        review_accepted=accepted and final != source_relation,
        prompt_hash=canonical_hash(prompt),
        raw=raw,
    )
    v1.atomic_json(target, result)
    return result


def _stage_cases(
    output: Path, source: Path, dataset: DatasetName, stage: StageName
) -> list[twitter.TwitterCase] | list[mnre.MNRECase]:
    split = dict(v1.load_json(output / "validation-splits.json"))
    ids: set[str] | None = None
    if stage == "dev":
        ids = set(str(item) for item in split[dataset]["prompt_dev"])
    elif stage == "holdout":
        ids = set(str(item) for item in split[dataset]["prompt_holdout"])
    if dataset == "twitter2017":
        twitter_cases = (
            _twitter_cases(output / "twitter2017" / "test_cases.json")
            if stage == "main"
            else _twitter_cases(source / "validation_cases.json")
        )
        return (
            twitter_cases
            if ids is None
            else [case for case in twitter_cases if case.id in ids]
        )
    mnre_cases = _mnre_cases(
        source / ("test_cases.json" if stage == "main" else "validation_cases.json")
    )
    return mnre_cases if ids is None else [case for case in mnre_cases if case.id in ids]


def _expected_count(dataset: DatasetName, stage: StageName) -> int:
    return {
        ("twitter2017", "dev"): 100,
        ("twitter2017", "holdout"): 623,
        ("twitter2017", "main"): 723,
        ("mnre-v2", "dev"): 200,
        ("mnre-v2", "holdout"): 1423,
        ("mnre-v2", "main"): 1614,
    }[(dataset, stage)]


def _cell_directory(
    output: Path,
    stage: StageName,
    dataset: DatasetName,
    variant: VariantName,
    version: PromptVersion | None = None,
) -> Path:
    base = output / stage / dataset / variant
    return base / f"prompt-{version}" if version else base


def _load_input_record(
    output: Path,
    stage: StageName,
    dataset: DatasetName,
    variant: VariantName,
    case_id: str,
    version: PromptVersion | None = None,
) -> dict[str, Any]:
    path = (
        _cell_directory(output, stage, dataset, variant, version)
        / "predictions"
        / _artifact_name(case_id)
    )
    if not path.exists():
        raise RuntimeError(f"missing upstream prediction: {path}")
    return dict(v1.load_json(path))


def _usage_for(
    ledger: AgentProgressionBudgetLedger,
    dataset: DatasetName,
    stage: StageName,
    variant: VariantName,
    version: PromptVersion | None,
) -> dict[str, Any]:
    prefix = f"agent-progression:{dataset}:{stage}:{variant}:"
    if version:
        prefix = f"agent-progression:{dataset}:{stage}:{variant}:{version}:"
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


def _secondary_metrics(dataset: DatasetName, records: list[dict[str, Any]]) -> dict[str, Any]:
    if dataset == "twitter2017":
        duplicate_count = total = valid = 0
        for record in records:
            seen: set[tuple[str, int, int, str]] = set()
            case_text = str(record.get("source_text") or "")
            for item in record["predicted"]:
                total += 1
                key = (str(item["text"]), int(item["start"]), int(item["end"]), str(item["type"]))
                duplicate_count += int(key in seen)
                seen.add(key)
                if not case_text or (
                    0 <= int(item["start"]) < int(item["end"]) <= len(case_text)
                    and case_text[int(item["start"]) : int(item["end"])] == item["text"]
                    and item["type"] in twitter.DATASET_LABELS
                ):
                    valid += 1
        schema_violations = sum(
            error.split(":", 1)[0] in {"type_not_in_schema", "type_not_in_label_inventory"}
            for record in records
            for error in record["errors"]
        )
        return {
            "duplicate_entity_or_fact_rate": round(duplicate_count / total, 6) if total else 0.0,
            "schema_violation_rate": round(schema_violations / max(total, 1), 6),
            "evidence_valid_rate": round(valid / total, 6) if total else 1.0,
            "direction_error_rate": None,
        }
    schema_violations = sum(
        error.split(":", 1)[0]
        in {"relation_not_in_schema", "relation_not_in_label_inventory"}
        for record in records
        for error in record["errors"]
    )
    valid = sum(record["predicted"] in mnre.CANONICAL_TO_DATASET for record in records)
    return {
        "duplicate_entity_or_fact_rate": None,
        "schema_violation_rate": round(schema_violations / max(len(records), 1), 6),
        "evidence_valid_rate": round(valid / max(len(records), 1), 6),
        "direction_error_rate": 0.0,
        "accuracy": round(
            sum(record["predicted"] == record["gold"] for record in records)
            / max(len(records), 1),
            6,
        ),
    }


async def run_cell(
    output: Path,
    dataset: DatasetName,
    variant: VariantName,
    stage: StageName,
    settings: Settings,
    *,
    prompt_version: PromptVersion | None = None,
    input_prompt_version: PromptVersion | None = None,
    concurrency: int = 2,
    budget_limit_cny: float = 20.0,
) -> dict[str, Any]:
    if concurrency not in {1, 2}:
        raise ValueError("prediction concurrency must be 1 or 2")
    if variant in {"governance", "fusion_review"} and prompt_version is None:
        raise ValueError(f"{variant} requires a prompt version")
    manifest = dict(v1.load_json(output / "manifest.json"))
    source = Path(
        str(manifest["twitter_source"] if dataset == "twitter2017" else manifest["mnre_source"])
    )
    schema = (
        twitter.load_schema(Path(str(manifest["schemas"][dataset]["path"])))
        if dataset == "twitter2017"
        else mnre.load_schema(Path(str(manifest["schemas"][dataset]["path"])))
    )
    cases = _stage_cases(output, source, dataset, stage)
    expected = _expected_count(dataset, stage)
    if len(cases) != expected:
        raise RuntimeError(f"unexpected {dataset} {stage} case count: {len(cases)}")
    ledger = AgentProgressionBudgetLedger(output / "budget.json", budget_limit_cny)
    directory = _cell_directory(output, stage, dataset, variant, prompt_version)
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
                    if variant == "vanilla":
                        result = await _twitter_vanilla_one(case, stage, settings, ledger, target)
                    elif variant == "extraction":
                        result = await _twitter_extraction_one(
                            schema, case, stage, settings, ledger, target
                        )
                    elif variant == "governance":
                        input_record = _load_input_record(
                            output, stage, dataset, "extraction", case.id
                        )
                        assert prompt_version is not None
                        result = await _twitter_governance_one(
                            schema,
                            case,
                            stage,
                            prompt_version,
                            input_record,
                            settings,
                            ledger,
                            target,
                        )
                    else:
                        input_record = _load_input_record(
                            output,
                            stage,
                            dataset,
                            "governance",
                            case.id,
                            input_prompt_version,
                        )
                        assert prompt_version is not None
                        result = await _twitter_fusion_one(
                            output,
                            source,
                            schema,
                            case,
                            stage,
                            prompt_version,
                            input_record,
                            settings,
                            ledger,
                            target,
                        )
                    result["source_text"] = case.text
                else:
                    assert isinstance(case, mnre.MNRECase)
                    if variant == "vanilla":
                        result = await _mnre_vanilla_one(case, stage, settings, ledger, target)
                    elif variant == "extraction":
                        result = await _mnre_extraction_one(
                            schema, case, stage, settings, ledger, target
                        )
                    elif variant == "governance":
                        input_record = _load_input_record(
                            output, stage, dataset, "extraction", case.id
                        )
                        assert prompt_version is not None
                        result = await _mnre_governance_one(
                            schema,
                            case,
                            stage,
                            prompt_version,
                            input_record,
                            settings,
                            ledger,
                            target,
                        )
                    else:
                        input_record = _load_input_record(
                            output,
                            stage,
                            dataset,
                            "governance",
                            case.id,
                            input_prompt_version,
                        )
                        assert prompt_version is not None
                        result = await _mnre_fusion_one(
                            source,
                            schema,
                            case,
                            stage,
                            prompt_version,
                            input_record,
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
    input_hash_mismatches = 0
    retained_span_mutations = 0
    governance_rejections = 0
    governance_deduplications = 0
    if variant in {"governance", "fusion_review"}:
        upstream_variant: VariantName = (
            "extraction" if variant == "governance" else "governance"
        )
        upstream_version = None if variant == "governance" else input_prompt_version
        for item in results:
            upstream = _load_input_record(
                output,
                stage,
                dataset,
                upstream_variant,
                str(item["id"]),
                upstream_version,
            )
            input_hash_mismatches += int(
                item.get("input_prediction_hash")
                != _prediction_hash(upstream["predicted"])
            )
            if dataset == "twitter2017" and variant == "governance":
                source_entities = [
                    twitter.PredictedEntity.model_validate(value)
                    for value in upstream["predicted"]
                ]
                final_entities = [
                    twitter.PredictedEntity.model_validate(value)
                    for value in item["predicted"]
                ]
                decisions, _ = _parse_twitter_governance(
                    str(item.get("raw") or ""), [], len(source_entities)
                )
                audit = _governance_audit(
                    source_entities, final_entities, decisions
                )
                retained_span_mutations += audit["retained_span_mutations"]
                governance_rejections += audit["governance_rejections"]
                governance_deduplications += audit["governance_deduplications"]
    case_by_id = {case.id: case for case in cases}
    if dataset == "twitter2017":
        final_output_invalid_count = sum(
            _twitter_final_output_invalid(
                cast(twitter.TwitterCase, case_by_id[str(item["id"])]),
                item.get("predicted"),
            )
            for item in results
        )
    else:
        final_output_invalid_count = sum(
            not isinstance(item.get("predicted"), str)
            or item.get("predicted") not in mnre.CANONICAL_TO_DATASET
            for item in results
        )
    intermediate_error_counts = Counter(
        str(error).split(":", 1)[0]
        for item in results
        for error in item.get("errors", [])
        if str(error).split(":", 1)[0].startswith("invalid_visual")
    )
    report = {
        "dataset": dataset,
        "variant": variant,
        "variant_label": VARIANT_LABELS[variant],
        "stage": stage,
        "prompt_version": prompt_version,
        "input_prompt_version": input_prompt_version,
        "configuration": {
            "model": settings.llm_model,
            "vlm_model": settings.vlm_model,
            "temperature": 0,
            "schema_hash": manifest["schemas"][dataset]["hash"],
            "settings_hash": manifest["settings_hash"],
            "code_commit": manifest["code_commit"],
            "prediction_protocol_commit": manifest["code_commit"],
            "runtime_code_commit": v1._git_commit(),
            "gate_policy_version": GATE_POLICY_VERSION,
        },
        "metrics": metrics,
        "secondary_metrics": _secondary_metrics(dataset, results),
        "usage": _usage_for(ledger, dataset, stage, variant, prompt_version),
        "input_hashes_present": sum("input_prediction_hash" in item for item in results),
        "input_hash_mismatches": input_hash_mismatches,
        "final_output_invalid_count": final_output_invalid_count,
        "intermediate_error_counts": dict(sorted(intermediate_error_counts.items())),
        "retained_span_mutations": retained_span_mutations,
        "governance_rejections": governance_rejections,
        "governance_deduplications": governance_deduplications,
        "span_mutations": retained_span_mutations,
        "endpoint_swaps": sum(int(item.get("endpoint_swaps", 0)) for item in results),
    }
    v1.atomic_json(directory / "report.json", report)
    return report


def _select_prompt(reports: list[dict[str, Any]]) -> PromptVersion:
    by_version = {str(report["prompt_version"]): report for report in reports}
    return max(
        PROMPT_VERSIONS,
        key=lambda version: (
            float(by_version[version]["metrics"]["micro_f1"]),
            -PROMPT_VERSIONS.index(version),
        ),
    )


def _freeze_selection(
    output: Path,
    dataset: DatasetName,
    governance_version: PromptVersion,
    fusion_version: PromptVersion,
    dev_reports: list[dict[str, Any]],
) -> dict[str, Any]:
    path = output / "frozen-config.json"
    manifest_hash = canonical_hash(v1.load_json(output / "manifest.json"))
    payload: dict[str, Any] = (
        dict(v1.load_json(path))
        if path.exists()
        else {
            "experiment_version": EXPERIMENT_VERSION,
            "manifest_hash": manifest_hash,
            "datasets": {},
        }
    )
    if payload["manifest_hash"] != manifest_hash:
        raise RuntimeError("experiment manifest changed after prompt freeze")
    selection = {
        "governance_prompt_version": governance_version,
        "fusion_review_prompt_version": fusion_version,
        "dev_report_hash": canonical_hash(dev_reports),
    }
    existing = payload["datasets"].get(dataset)
    if existing is not None:
        if (
            existing.get("governance_prompt_version") != governance_version
            or existing.get("fusion_review_prompt_version") != fusion_version
        ):
            raise RuntimeError(f"{dataset} prompt selection is already frozen")
        return cast(dict[str, Any], existing)
    payload["datasets"][dataset] = selection
    payload["prompt_policy_hash"] = canonical_hash(
        {
            "twitter_governance": twitter_governance_prompt.__doc__,
            "twitter_fusion": twitter_fusion_prompt.__doc__,
            "mnre_governance": mnre_governance_prompt.__doc__,
            "mnre_fusion": mnre_fusion_prompt.__doc__,
        }
    )
    v1.atomic_json(path, payload)
    return selection


def _frozen_selection(output: Path, dataset: DatasetName) -> dict[str, Any]:
    frozen = dict(v1.load_json(output / "frozen-config.json"))
    if frozen["manifest_hash"] != canonical_hash(v1.load_json(output / "manifest.json")):
        raise RuntimeError("experiment manifest changed after prompt freeze")
    selection = frozen.get("datasets", {}).get(dataset)
    if not isinstance(selection, dict):
        raise RuntimeError(f"{dataset} prompt selection is not frozen")
    return selection


def _structural_gate(report: dict[str, Any]) -> None:
    cases = int(report["metrics"]["cases"])
    if int(report.get("final_output_invalid_count", 0)):
        raise RuntimeError(
            f"{report['dataset']}/{report['variant']} has invalid final outputs"
        )
    if report["variant"] == "governance" and int(
        report.get("retained_span_mutations", report.get("span_mutations", 0))
    ):
        raise RuntimeError("MNER governance mutated an existing entity span")
    if report["dataset"] == "mnre-v2" and int(report["endpoint_swaps"]):
        raise RuntimeError("MRE stage exchanged ordered endpoints")
    if report["variant"] in {"governance", "fusion_review"} and int(
        report["input_hashes_present"]
    ) != cases:
        raise RuntimeError("downstream stage is missing immutable input hashes")
    if int(report.get("input_hash_mismatches", 0)):
        raise RuntimeError("downstream stage input hash does not match upstream output")


def _prediction_snapshot_hash(output: Path, dataset: DatasetName) -> str:
    files = sorted(
        path
        for stage in ("dev", "holdout")
        for path in (output / stage / dataset).glob("**/predictions/*.json")
    )
    return canonical_hash(
        [
            {
                "path": path.relative_to(output).as_posix(),
                "sha256": file_sha256(path),
            }
            for path in files
        ]
    )


def _budget_cost(output: Path) -> float:
    path = output / "budget.json"
    if not path.exists():
        return 0.0
    return float(v1.load_json(path).get("estimated_cost_cny") or 0.0)


def _cached_validation_complete(output: Path, dataset: DatasetName) -> bool:
    try:
        selection = _frozen_selection(output, dataset)
    except (FileNotFoundError, RuntimeError):
        return False
    expected = _expected_count(dataset, "holdout")
    directories = [
        _cell_directory(output, "holdout", dataset, "vanilla"),
        _cell_directory(output, "holdout", dataset, "extraction"),
        _cell_directory(
            output,
            "holdout",
            dataset,
            "governance",
            cast(PromptVersion, selection["governance_prompt_version"]),
        ),
        _cell_directory(
            output,
            "holdout",
            dataset,
            "fusion_review",
            cast(PromptVersion, selection["fusion_review_prompt_version"]),
        ),
    ]
    return all(
        len(list((directory / "predictions").glob("*.json"))) == expected
        for directory in directories
    )


def _begin_protocol_amendment(
    output: Path, dataset: DatasetName
) -> dict[str, Any] | None:
    if not _cached_validation_complete(output, dataset):
        return None
    manifest = dict(v1.load_json(output / "manifest.json"))
    payload = {
        "experiment_version": EXPERIMENT_VERSION,
        "dataset": dataset,
        "prediction_protocol_commit": manifest["code_commit"],
        "runtime_code_commit": v1._git_commit(),
        "gate_policy_version": GATE_POLICY_VERSION,
        "frozen_config_hash": file_sha256(output / "frozen-config.json"),
        "prediction_snapshot_hash_before": _prediction_snapshot_hash(output, dataset),
        "budget_cost_before_cny": _budget_cost(output),
        "changes": [
            "gate only on deterministic final-output validity",
            "record intermediate visual parse failures as diagnostics",
            "separate retained span mutations from reject and dedup removals",
        ],
    }
    v1.atomic_json(output / "protocol-amendment.json", payload)
    return payload


def _finish_protocol_amendment(
    output: Path, dataset: DatasetName, payload: dict[str, Any] | None
) -> None:
    if payload is None:
        return
    after_hash = _prediction_snapshot_hash(output, dataset)
    after_cost = _budget_cost(output)
    payload["prediction_snapshot_hash_after"] = after_hash
    payload["budget_cost_after_cny"] = after_cost
    payload["prediction_files_unchanged"] = (
        after_hash == payload["prediction_snapshot_hash_before"]
    )
    payload["no_paid_calls_during_reaggregation"] = (
        after_cost == payload["budget_cost_before_cny"]
    )
    if not payload["prediction_files_unchanged"]:
        raise RuntimeError("cached validation prediction files changed during reaggregation")
    if not payload["no_paid_calls_during_reaggregation"]:
        raise RuntimeError("cached validation reaggregation unexpectedly used paid calls")
    v1.atomic_json(output / "protocol-amendment.json", payload)


async def run_validation(
    output: Path,
    dataset: DatasetName,
    settings: Settings,
    *,
    concurrency: int = 2,
    budget_limit_cny: float = 20.0,
) -> dict[str, Any]:
    protocol_amendment = _begin_protocol_amendment(output, dataset)
    dev_reports: list[dict[str, Any]] = []
    for variant in BASE_VARIANTS:
        dev_reports.append(
            await run_cell(
                output,
                dataset,
                variant,
                "dev",
                settings,
                concurrency=concurrency,
                budget_limit_cny=budget_limit_cny,
            )
        )
    governance_reports = []
    for version in PROMPT_VERSIONS:
        report = await run_cell(
            output,
            dataset,
            "governance",
            "dev",
            settings,
            prompt_version=version,
            concurrency=concurrency,
            budget_limit_cny=budget_limit_cny,
        )
        governance_reports.append(report)
        dev_reports.append(report)
    governance_version = _select_prompt(governance_reports)
    fusion_reports = []
    for version in PROMPT_VERSIONS:
        report = await run_cell(
            output,
            dataset,
            "fusion_review",
            "dev",
            settings,
            prompt_version=version,
            input_prompt_version=governance_version,
            concurrency=concurrency,
            budget_limit_cny=budget_limit_cny,
        )
        fusion_reports.append(report)
        dev_reports.append(report)
    fusion_version = _select_prompt(fusion_reports)
    selection = _freeze_selection(
        output, dataset, governance_version, fusion_version, dev_reports
    )

    holdout_reports = []
    for variant in BASE_VARIANTS:
        holdout_reports.append(
            await run_cell(
                output,
                dataset,
                variant,
                "holdout",
                settings,
                concurrency=concurrency,
                budget_limit_cny=budget_limit_cny,
            )
        )
    holdout_reports.append(
        await run_cell(
            output,
            dataset,
            "governance",
            "holdout",
            settings,
            prompt_version=governance_version,
            concurrency=concurrency,
            budget_limit_cny=budget_limit_cny,
        )
    )
    holdout_reports.append(
        await run_cell(
            output,
            dataset,
            "fusion_review",
            "holdout",
            settings,
            prompt_version=fusion_version,
            input_prompt_version=governance_version,
            concurrency=concurrency,
            budget_limit_cny=budget_limit_cny,
        )
    )
    for report in holdout_reports:
        _structural_gate(report)
    summary = {
        "dataset": dataset,
        "selection": selection,
        "dev_reports": dev_reports,
        "holdout_reports": holdout_reports,
        "recomputed_dev_report_hash": canonical_hash(dev_reports),
        "gate_policy_version": GATE_POLICY_VERSION,
        "passed": True,
    }
    v1.atomic_json(output / f"{dataset}-validation-summary.json", summary)
    _finish_protocol_amendment(output, dataset, protocol_amendment)
    return summary


async def run_test(
    output: Path,
    dataset: DatasetName,
    settings: Settings,
    *,
    concurrency: int = 2,
    budget_limit_cny: float = 20.0,
) -> dict[str, Any]:
    validation_path = output / f"{dataset}-validation-summary.json"
    if not validation_path.exists() or not v1.load_json(validation_path).get("passed"):
        raise RuntimeError(f"complete and pass {dataset} validation before testing")
    selection = _frozen_selection(output, dataset)
    governance_version = cast(
        PromptVersion, selection["governance_prompt_version"]
    )
    fusion_version = cast(PromptVersion, selection["fusion_review_prompt_version"])
    if governance_version not in PROMPT_VERSIONS or fusion_version not in PROMPT_VERSIONS:
        raise RuntimeError("frozen prompt selection is invalid")
    reports = []
    for variant in BASE_VARIANTS:
        reports.append(
            await run_cell(
                output,
                dataset,
                variant,
                "main",
                settings,
                concurrency=concurrency,
                budget_limit_cny=budget_limit_cny,
            )
        )
    reports.append(
        await run_cell(
            output,
            dataset,
            "governance",
            "main",
            settings,
            prompt_version=governance_version,
            concurrency=concurrency,
            budget_limit_cny=budget_limit_cny,
        )
    )
    reports.append(
        await run_cell(
            output,
            dataset,
            "fusion_review",
            "main",
            settings,
            prompt_version=fusion_version,
            input_prompt_version=governance_version,
            concurrency=concurrency,
            budget_limit_cny=budget_limit_cny,
        )
    )
    for report in reports:
        _structural_gate(report)
    summary = {"dataset": dataset, "selection": selection, "reports": reports, "passed": True}
    v1.atomic_json(output / f"{dataset}-main-summary.json", summary)
    return summary


async def run_mner_validation(
    output: Path,
    settings: Settings,
    *,
    concurrency: int = 2,
    budget_limit_cny: float = 20.0,
) -> dict[str, Any]:
    return await run_validation(
        output,
        "twitter2017",
        settings,
        concurrency=concurrency,
        budget_limit_cny=budget_limit_cny,
    )


async def run_mner_test(
    output: Path,
    settings: Settings,
    *,
    concurrency: int = 2,
    budget_limit_cny: float = 20.0,
) -> dict[str, Any]:
    return await run_test(
        output,
        "twitter2017",
        settings,
        concurrency=concurrency,
        budget_limit_cny=budget_limit_cny,
    )


async def run_mre_validation(
    output: Path,
    settings: Settings,
    *,
    concurrency: int = 2,
    budget_limit_cny: float = 20.0,
) -> dict[str, Any]:
    if not (output / "twitter2017-main-summary.json").exists():
        raise RuntimeError("MNER test gate must pass before MRE validation")
    return await run_validation(
        output,
        "mnre-v2",
        settings,
        concurrency=concurrency,
        budget_limit_cny=budget_limit_cny,
    )


async def run_mre_test(
    output: Path,
    settings: Settings,
    *,
    concurrency: int = 2,
    budget_limit_cny: float = 20.0,
) -> dict[str, Any]:
    if not (output / "twitter2017-main-summary.json").exists():
        raise RuntimeError("MNER test gate must pass before MRE test")
    return await run_test(
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
    budget_limit_cny: float = 20.0,
) -> dict[str, Any]:
    mner_validation = await run_mner_validation(
        output,
        settings,
        concurrency=concurrency,
        budget_limit_cny=budget_limit_cny,
    )
    mner_test = await run_mner_test(
        output,
        settings,
        concurrency=concurrency,
        budget_limit_cny=budget_limit_cny,
    )
    mre_validation = await run_mre_validation(
        output,
        settings,
        concurrency=concurrency,
        budget_limit_cny=budget_limit_cny,
    )
    mre_test = await run_mre_test(
        output,
        settings,
        concurrency=concurrency,
        budget_limit_cny=budget_limit_cny,
    )
    summary = {
        "experiment_version": EXPERIMENT_VERSION,
        "mner_validation": mner_validation,
        "mner_test": mner_test,
        "mre_validation": mre_validation,
        "mre_test": mre_test,
    }
    v1.atomic_json(output / "run-all-summary.json", summary)
    return summary


def _main_version(output: Path, dataset: DatasetName, variant: VariantName) -> PromptVersion | None:
    if variant not in {"governance", "fusion_review"}:
        return None
    selection = _frozen_selection(output, dataset)
    key = (
        "governance_prompt_version"
        if variant == "governance"
        else "fusion_review_prompt_version"
    )
    version = cast(PromptVersion, selection[key])
    if version not in PROMPT_VERSIONS:
        raise RuntimeError("frozen prompt selection is invalid")
    return version


def _prediction_records(
    output: Path, dataset: DatasetName, variant: VariantName
) -> list[dict[str, Any]]:
    version = _main_version(output, dataset, variant)
    directory = _cell_directory(output, "main", dataset, variant, version) / "predictions"
    records = [dict(v1.load_json(path)) for path in directory.glob("*.json")]
    return sorted(records, key=lambda item: str(item["id"]))


def _main_report(output: Path, dataset: DatasetName, variant: VariantName) -> dict[str, Any]:
    version = _main_version(output, dataset, variant)
    path = _cell_directory(output, "main", dataset, variant, version) / "report.json"
    return dict(v1.load_json(path))


def _sample_f1(record: dict[str, Any]) -> float:
    metrics = record["metrics"]
    tp = int(metrics.get("tp", metrics.get("true_positive", 0)))
    fp = int(metrics.get("fp", metrics.get("false_positive", 0)))
    fn = int(metrics.get("fn", metrics.get("false_negative", 0)))
    denominator = 2 * tp + fp + fn
    return 2 * tp / denominator if denominator else 1.0


def _transition_stats(
    left: list[dict[str, Any]], right: list[dict[str, Any]]
) -> dict[str, Any]:
    if [item["id"] for item in left] != [item["id"] for item in right]:
        raise RuntimeError("transition analysis requires identical ordered sample IDs")
    changed = improved = worsened = unchanged_score = 0
    for before, after in zip(left, right, strict=True):
        if before["predicted"] == after["predicted"]:
            continue
        changed += 1
        delta = _sample_f1(after) - _sample_f1(before)
        improved += int(delta > 0)
        worsened += int(delta < 0)
        unchanged_score += int(delta == 0)
    return {
        "changed": changed,
        "correct_modifications": improved,
        "incorrect_modifications": worsened,
        "changed_but_score_unchanged": unchanged_score,
        "net_benefit": improved - worsened,
        "correction_accuracy": round(improved / changed, 6) if changed else None,
    }


def export_results(output: Path) -> dict[str, Any]:
    for dataset in DATASETS:
        if not (output / f"{dataset}-main-summary.json").exists():
            raise RuntimeError(f"{dataset} main results are unavailable")
    rows: list[dict[str, Any]] = []
    paired: list[dict[str, Any]] = []
    transitions: list[dict[str, Any]] = []
    for dataset in DATASETS:
        records_by_variant = {
            variant: _prediction_records(output, dataset, variant) for variant in VARIANTS
        }
        for index, variant in enumerate(VARIANTS):
            report = _main_report(output, dataset, variant)
            metrics = report["metrics"]
            transition = None
            if index:
                transition = _transition_stats(
                    records_by_variant[VARIANTS[index - 1]], records_by_variant[variant]
                )
                transitions.append(
                    {
                        "dataset": dataset,
                        "left": VARIANTS[index - 1],
                        "right": variant,
                        **transition,
                    }
                )
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
                    **report["secondary_metrics"],
                    "correction_accuracy": (
                        transition["correction_accuracy"] if transition else None
                    ),
                    "cost_cny": report["usage"]["estimated_cost_cny"],
                    "average_latency_ms": report["usage"]["average_latency_ms"],
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
        "transitions": transitions,
        "manifest": v1.load_json(output / "manifest.json"),
        "frozen_config": v1.load_json(output / "frozen-config.json"),
        "paid_stability_repetitions": 0,
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
        "duplicate_entity_or_fact_rate",
        "schema_violation_rate",
        "evidence_valid_rate",
        "correction_accuracy",
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
    def optional(path: Path) -> Any:
        return v1.load_json(path) if path.exists() else None

    def count(path: Path) -> int:
        return sum(1 for _ in path.glob("*.json")) if path.exists() else 0

    cells = []
    for stage in ("dev", "holdout", "main"):
        for dataset in DATASETS:
            for variant in VARIANTS:
                versions: tuple[PromptVersion | None, ...] = (
                    PROMPT_VERSIONS
                    if variant in {"governance", "fusion_review"}
                    else (None,)
                )
                for version in versions:
                    directory = _cell_directory(output, stage, dataset, variant, version)
                    predictions = count(directory / "predictions")
                    if predictions or stage == "main" or version is None:
                        cells.append(
                            {
                                "stage": stage,
                                "dataset": dataset,
                                "variant": variant,
                                "prompt_version": version,
                                "predictions": predictions,
                            }
                        )
    budget = optional(output / "budget.json")
    return {
        "manifest": optional(output / "manifest.json"),
        "frozen_config": optional(output / "frozen-config.json"),
        "cells": cells,
        "mner_validation": optional(output / "twitter2017-validation-summary.json"),
        "mner_main": optional(output / "twitter2017-main-summary.json"),
        "mre_validation": optional(output / "mnre-v2-validation-summary.json"),
        "mre_main": optional(output / "mnre-v2-main-summary.json"),
        "budget": budget,
        "results": optional(output / "results.json"),
    }
