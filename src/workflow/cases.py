"""Review-case projection, semantic retrieval and index maintenance."""

from __future__ import annotations

import math
import re
from typing import Any

from src.core.ids import canonical_hash, stable_id
from src.domain import (
    CandidateClaim,
    CaseEmbedding,
    CaseRecord,
    CaseStatusEvent,
    EntityMention,
    RetrievedCase,
    ReviewEvent,
    WorkflowState,
)
from src.persistence import CaseRepository
from src.providers.base import EmbeddingProvider

CASE_POLICY_VERSION = "review-cases-v1"
CASE_RETRIEVAL_VERSION = "case-retrieval-v1"


def _language(text: str) -> str:
    return "zh" if re.search(r"[\u3400-\u9fff]", text) else "en"


def _mention(candidate: CandidateClaim, mention_id: str) -> EntityMention | None:
    if candidate.subject.id == mention_id:
        return candidate.subject
    if isinstance(candidate.object, EntityMention) and candidate.object.id == mention_id:
        return candidate.object
    return None


class CaseService:
    def __init__(self, repository: CaseRepository, evidence_store: Any) -> None:
        self.repository = repository
        self.evidence_store = evidence_store

    async def project_review_event(
        self, event: ReviewEvent, state: WorkflowState
    ) -> CaseRecord | None:
        if self.repository.projected(event.id):
            return self.repository.by_source_event(event.id)
        decision: str = event.action
        if decision == "commit_correction":
            decision = str(event.after.get("decision") or "")
        if decision == "defer" or decision not in {
            "link",
            "create",
            "approve",
            "reject",
        }:
            self.repository.mark_projected(event.id, None)
            return None
        reason = event.reason.strip()
        if not event.reviewer.strip() or not reason or state.output_schema is None:
            self.repository.mark_projected(event.id, None)
            return None
        evidence_ids: list[str]
        input_summary: str
        snapshot: dict[str, Any]
        if event.kind == "claim":
            claim_id = str(event.after.get("claim_id") or event.before.get("claim_id") or "")
            claim = next((item for item in state.claims if item.id == claim_id), None)
            if claim is None:
                self.repository.mark_projected(event.id, None)
                return None
            source = [item for item in state.candidates if item.id in claim.source_candidate_ids]
            evidence_ids = list(claim.evidence_ids)
            input_summary = " | ".join(
                [
                    claim.subject_id,
                    claim.relation_id,
                    claim.object_entity_id or claim.object_literal or "",
                ]
            )
            snapshot = {
                "claim": claim.model_dump(mode="json"),
                "candidates": [item.model_dump(mode="json") for item in source],
            }
        else:
            mention_id = str(event.after.get("mention_id") or event.before.get("mention_id") or "")
            located = [
                (candidate, mention)
                for candidate in state.original_candidates or state.candidates
                if (mention := _mention(candidate, mention_id)) is not None
            ]
            if not located:
                self.repository.mark_projected(event.id, None)
                return None
            mention = located[0][1]
            evidence_ids = list(dict.fromkeys(mention.evidence_ids))
            input_summary = f"{mention.name} | {mention.entity_type} | {mention.context}"
            snapshot = {
                "mention": mention.model_dump(mode="json"),
                "task": event.after,
                "candidates": [item.model_dump(mode="json") for item, _ in located],
            }
        if not evidence_ids:
            self.repository.mark_projected(event.id, None)
            return None
        for evidence_id in evidence_ids:
            if not await self.evidence_store.exists(
                evidence_id
            ) or not await self.evidence_store.verify(evidence_id):
                self.repository.mark_projected(event.id, None)
                return None
        superseded = (
            self.repository.by_source_event(event.supersedes_event_id)
            if event.supersedes_event_id
            else None
        )
        record = CaseRecord(
            id=stable_id("case", event.id),
            run_id=event.run_id,
            case_type="bad" if decision == "reject" else "good",
            task_type=event.kind,
            schema_fingerprint=canonical_hash(state.output_schema.model_dump(mode="json")),
            language=_language(input_summary),
            input_summary=input_summary[:4000],
            candidate_snapshot=snapshot,
            decision=decision,
            reasons=[reason],
            evidence_ids=evidence_ids,
            source_review_event_id=event.id,
            supersedes_case_id=superseded.id if superseded else None,
            created_at=event.created_at,
        )
        self.repository.add(record)
        if superseded and self.repository.is_active(superseded.id):
            self.repository.disable(
                CaseStatusEvent(
                    id=stable_id("case-status", superseded.id, event.id, "disable"),
                    case_id=superseded.id,
                    action="disable",
                    operator=event.reviewer,
                    reason="superseded by corrected review decision",
                    source_event_id=event.id,
                )
            )
        self.repository.mark_projected(event.id, record.id)
        return record

    async def replay(self, events: list[ReviewEvent], states: dict[str, WorkflowState]) -> int:
        count = 0
        for event in events:
            if self.repository.projected(event.id) or event.run_id not in states:
                continue
            await self.project_review_event(event, states[event.run_id])
            count += 1
        return count


class CaseRetriever:
    def __init__(self, repository: CaseRepository, embedding_provider: EmbeddingProvider) -> None:
        self.repository = repository
        self.embedding_provider = embedding_provider

    @staticmethod
    def _cosine(left: list[float], right: list[float]) -> float:
        if len(left) != len(right) or not left:
            return -1.0
        dot = sum(a * b for a, b in zip(left, right, strict=True))
        norm = math.sqrt(sum(a * a for a in left) * sum(b * b for b in right))
        return dot / norm if norm else -1.0

    async def _vectors(self, records: list[CaseRecord]) -> dict[str, list[float]]:
        fingerprint = self.embedding_provider.fingerprint()
        vectors: dict[str, list[float]] = {}
        missing: list[CaseRecord] = []
        for record in records:
            text_hash = canonical_hash(record.input_summary)
            cached = self.repository.embedding(record.id)
            if cached and cached.model_fingerprint == fingerprint and cached.text_hash == text_hash:
                vectors[record.id] = cached.vector
            else:
                missing.append(record)
        if missing:
            encoded = await self.embedding_provider.encode([item.input_summary for item in missing])
            for record, vector in zip(missing, encoded, strict=True):
                embedding = CaseEmbedding(
                    case_id=record.id,
                    model_fingerprint=fingerprint,
                    text_hash=canonical_hash(record.input_summary),
                    dimension=len(vector),
                    vector=vector,
                )
                self.repository.save_embedding(embedding)
                vectors[record.id] = vector
        return vectors

    async def retrieve(
        self,
        query: str,
        *,
        task_type: str,
        schema_fingerprint: str,
        language: str,
        case_types: set[str] | None = None,
        top_k: int = 5,
        use_location: str = "validation",
        allowed_case_ids: set[str] | None = None,
    ) -> list[RetrievedCase]:
        records = self.repository.list(
            task_type=task_type,
            schema_fingerprint=schema_fingerprint,
            language=language,
            active_only=allowed_case_ids is None,
            limit=10000,
        )
        if allowed_case_ids is not None:
            records = [item for item in records if item.id in allowed_case_ids]
        if case_types is not None:
            records = [item for item in records if item.case_type in case_types]
        if not records:
            return []
        vectors = await self._vectors(records)
        query_vector = (await self.embedding_provider.encode([query]))[0]
        ranked = sorted(
            ((self._cosine(query_vector, vectors[item.id]), item) for item in records),
            key=lambda item: (-item[0], item[1].id),
        )[: max(1, min(top_k, 50))]
        return [
            RetrievedCase(
                case_id=record.id,
                case_type=record.case_type,
                task_type=record.task_type,
                score=score,
                decision=record.decision,
                input_summary=record.input_summary,
                reasons=record.reasons,
                evidence_ids=record.evidence_ids,
                use_location=use_location,
            )
            for score, record in ranked
        ]

    async def rebuild(self, *, dry_run: bool = False) -> dict[str, Any]:
        records = self.repository.list(active_only=True, limit=10000)
        fingerprint = self.embedding_provider.fingerprint()
        stale = [
            record
            for record in records
            if (
                (embedding := self.repository.embedding(record.id)) is None
                or embedding.model_fingerprint != fingerprint
                or embedding.text_hash != canonical_hash(record.input_summary)
            )
        ]
        if not dry_run:
            await self._vectors(stale)
        return {
            "active_cases": len(records),
            "stale_cases": len(stale),
            "model_fingerprint": fingerprint,
            "dry_run": dry_run,
        }

    def snapshot_fingerprint(self) -> str:
        return self.fingerprint_for(self.snapshot_ids())

    def snapshot_ids(self) -> list[str]:
        return sorted(item.id for item in self.repository.list(active_only=True, limit=10000))

    def fingerprint_for(self, case_ids: list[str]) -> str:
        return canonical_hash(
            {
                "policy": CASE_POLICY_VERSION,
                "retrieval": CASE_RETRIEVAL_VERSION,
                "embedding": self.embedding_provider.fingerprint(),
                "cases": sorted(case_ids),
            }
        )
