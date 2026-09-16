"""Source-backed review views; risk flags are prompts, never automatic verdicts."""

from __future__ import annotations

import re
from typing import Any

from prismke.domain import CandidateClaim, EntityMention, WorkflowState


def candidate_mentions(candidate: CandidateClaim) -> list[EntityMention]:
    return [
        candidate.subject,
        *([candidate.object] if isinstance(candidate.object, EntityMention) else []),
    ]


def risk_flags(names: list[str], relations: list[str], reasons: list[str]) -> list[str]:
    flags: list[str] = []
    if any(re.fullmatch(r"[po]\d+", name.strip(), re.IGNORECASE) for name in names):
        flags.append("疑似占位名称：请对照原文确认，不自动改名")
    if any("cross_language" in reason or "cross-lingual" in reason for reason in reasons):
        flags.append("跨语言身份待核查：名称相似不等于同一对象")
    if any(
        relation in {"authored_by", "developed_by", "author", "developer"} for relation in relations
    ):
        flags.append("关系待核查：论文作者不等于系统开发者")
    return flags


def entity_task_base(state: WorkflowState, task_id: str) -> dict[str, Any]:
    task = next((item for item in state.entity_review_tasks if item.id == task_id), None)
    if task is None:
        raise KeyError("entity review task not found")
    all_candidates = {
        item.id: item
        for item in [
            *state.text_candidates,
            *state.visual_candidates,
            *state.candidates,
        ]
    }
    related = [
        item
        for item in all_candidates.values()
        if task.mention_id in {mention.id for mention in candidate_mentions(item)}
    ]
    mention = next(
        (
            mention
            for item in related
            for mention in candidate_mentions(item)
            if mention.id == task.mention_id
        ),
        None,
    )
    return {
        "run_id": state.run_id,
        "task": task.model_dump(mode="json"),
        "mention": mention.model_dump(mode="json") if mention else None,
        "related_candidates": [
            {
                "id": item.id,
                "subject": item.subject.name,
                "relation": item.relation,
                "object": item.object.name
                if isinstance(item.object, EntityMention)
                else item.object,
                "confidence": item.confidence,
                "evidence_ids": item.evidence_ids,
            }
            for item in related
        ],
        "risk_flags": risk_flags(
            [mention.name] if mention else [],
            [item.relation for item in related],
            task.reasons,
        ),
        "evidence_ids": list(dict.fromkeys(eid for item in related for eid in item.evidence_ids)),
    }


def claim_task_detail(state: WorkflowState, task_id: str) -> dict[str, Any]:
    task = next((item for item in state.review_tasks if item.id == task_id), None)
    if task is None:
        raise KeyError("claim review task not found")
    if task.claim_id in state.normalization_issues:
        candidate = next(item for item in state.candidates if item.id == task.claim_id)
        return {
            "run_id": state.run_id,
            "task": task.model_dump(mode="json"),
            "claim": {
                "id": candidate.id,
                "subject_name": candidate.subject.name,
                "object_name": candidate.object.name
                if isinstance(candidate.object, EntityMention)
                else candidate.object,
                "relation_id": candidate.relation,
                "confidence": candidate.confidence,
                "status": "schema_blocked",
                "evidence_ids": candidate.evidence_ids,
            },
            "risk_flags": [
                "Schema硬约束不满足：仅可拒绝；不得批准写图或自动改写",
                state.normalization_issues[candidate.id],
            ],
            "allowed_actions": ["reject"],
            "conflicts": [],
            "conflict_peers": [],
            "evidence_ids": candidate.evidence_ids,
        }
    entities = {item.id: item for item in state.entities}

    def describe(claim: Any) -> dict[str, Any]:
        names = [
            entities[eid].name if eid in entities else eid
            for eid in (claim.subject_id, claim.object_entity_id)
            if eid
        ]
        return {
            **claim.model_dump(mode="json"),
            "subject_name": names[0],
            "object_name": names[1] if len(names) > 1 else claim.object_literal,
            "risk_flags": risk_flags(names, [claim.relation_id], task.reasons),
        }

    claim = next(item for item in state.claims if item.id == task.claim_id)
    conflicts = [item for item in state.conflicts if claim.id in item.claim_ids]
    peer_ids = {cid for item in conflicts for cid in item.claim_ids} - {claim.id}
    return {
        "run_id": state.run_id,
        "task": task.model_dump(mode="json"),
        "claim": describe(claim),
        "risk_flags": describe(claim)["risk_flags"],
        "conflicts": [item.model_dump(mode="json") for item in conflicts],
        "conflict_peers": [describe(item) for item in state.claims if item.id in peer_ids],
        "evidence_ids": claim.evidence_ids,
    }
