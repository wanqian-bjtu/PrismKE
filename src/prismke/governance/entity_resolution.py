"""Deterministic and semantic entity linking with conservative governance."""

from __future__ import annotations

import math
from dataclasses import dataclass
from difflib import SequenceMatcher

from prismke.core.errors import SchemaValidationError
from prismke.core.ids import stable_id
from prismke.domain import (
    CanonicalEntity,
    EntityCandidate,
    EntityMention,
    EntityResolutionDecision,
    EntityReviewTask,
    SchemaIndex,
    normalize_label,
)
from prismke.persistence.base import GraphStore
from prismke.providers.base import EmbeddingProvider


@dataclass(frozen=True)
class ResolutionBundle:
    entities: list[CanonicalEntity]
    mention_to_entity: dict[str, str]
    review_reasons: dict[str, list[str]]
    decisions: list[EntityResolutionDecision] | None = None
    review_tasks: list[EntityReviewTask] | None = None


class EntityResolver:
    def __init__(self, schema: SchemaIndex, existing: list[CanonicalEntity]) -> None:
        self.schema = schema
        self.entities = {item.id: item for item in existing}
        self.lookup: dict[tuple[str, str], CanonicalEntity] = {}
        for entity in existing:
            self._index(entity)
        for item in schema.schema.entity_catalog:
            entity = CanonicalEntity(
                id=item.id, name=item.name, entity_type=item.type, aliases=item.aliases
            )
            self.entities.setdefault(entity.id, entity)
            self._index(entity)

    def _index(self, entity: CanonicalEntity) -> None:
        for name in [entity.name, *entity.aliases]:
            self.lookup[(normalize_label(name), entity.entity_type)] = entity

    def resolve(self, mentions: list[EntityMention]) -> ResolutionBundle:
        mapping: dict[str, str] = {}
        review_reasons: dict[str, list[str]] = {}
        for mention in mentions:
            entity_type = self.schema.entity_type(mention.entity_type)
            if entity_type is None:
                if self.schema.schema.strict:
                    raise SchemaValidationError(f"unknown entity type: {mention.entity_type}")
                entity_type = mention.entity_type
                review_reasons[mention.id] = ["ontology_addition"]
            key = (normalize_label(mention.name), entity_type)
            entity = self.lookup.get(key)
            if entity is None:
                entity = CanonicalEntity(
                    id=stable_id("entity", entity_type, key[0]),
                    name=mention.name.strip(),
                    entity_type=entity_type,
                )
                self.entities[entity.id] = entity
                self._index(entity)
            mapping[mention.id] = entity.id
        return ResolutionBundle(
            entities=list(self.entities.values()),
            mention_to_entity=mapping,
            review_reasons=review_reasons,
        )


def entity_embedding_text(entity: CanonicalEntity) -> str:
    attributes = " ".join(
        f"{key}: {value}" for key, value in sorted(entity.attributes.items())
    )
    return "\n".join(
        item
        for item in (
            f"name: {entity.name}",
            f"aliases: {', '.join(entity.aliases)}" if entity.aliases else "",
            f"type: {entity.entity_type}",
            f"attributes: {attributes}" if attributes else "",
            f"context: {entity.context_summary}" if entity.context_summary else "",
        )
        if item
    )


def mention_embedding_text(mention: EntityMention, entity_type: str) -> str:
    return "\n".join(
        item
        for item in (
            f"name: {mention.name.strip()}",
            f"type: {entity_type}",
            f"context: {mention.context.strip()}" if mention.context.strip() else "",
        )
        if item
    )


class SemanticEntityResolver:
    """Resolve mentions using exact aliases followed by dense semantic retrieval."""

    def __init__(
        self,
        schema: SchemaIndex,
        graph_store: GraphStore,
        embedding_provider: EmbeddingProvider,
        *,
        run_id: str,
        top_k: int = 10,
        auto_link_threshold: float = 0.88,
        review_threshold: float = 0.65,
        min_margin: float = 0.08,
    ) -> None:
        self.schema = schema
        self.graph_store = graph_store
        self.embedding_provider = embedding_provider
        self.run_id = run_id
        self.top_k = top_k
        self.auto_link_threshold = auto_link_threshold
        self.review_threshold = review_threshold
        self.min_margin = min_margin

    @staticmethod
    def _name_score(mention: EntityMention, entity: CanonicalEntity) -> float:
        needle = normalize_label(mention.name)
        values = [normalize_label(entity.name), *(normalize_label(a) for a in entity.aliases)]
        return max(SequenceMatcher(None, needle, value).ratio() for value in values)

    @staticmethod
    def _nil_entity(mention: EntityMention, entity_type: str) -> CanonicalEntity:
        normalized = normalize_label(mention.name)
        return CanonicalEntity(
            id=stable_id("entity", entity_type, normalized),
            name=mention.name.strip(),
            entity_type=entity_type,
            context_summary=mention.context.strip()[:2000] or None,
            source_evidence_ids=sorted(set(mention.evidence_ids)),
        )

    @staticmethod
    def _candidate(
        mention: EntityMention,
        entity: CanonicalEntity,
        retrieval_score: float,
        context_score: float | None = None,
    ) -> EntityCandidate:
        retrieval = max(0.0, min(1.0, (retrieval_score + 1.0) / 2.0))
        name = SemanticEntityResolver._name_score(mention, entity)
        context = retrieval if context_score is None else context_score
        neighborhood = 0.0
        final = 0.4 * retrieval + 0.3 * name + 0.2 * context + 0.1 * neighborhood
        return EntityCandidate(
            entity_id=entity.id,
            retrieval_score=retrieval_score,
            name_score=name,
            context_score=context,
            neighborhood_score=neighborhood,
            final_score=max(0.0, min(1.0, final)),
            reasons=["dense_retrieval", "type_match", "name_rerank", "context_rerank"],
        )

    async def _context_scores(
        self, mention: EntityMention, entities: list[CanonicalEntity]
    ) -> dict[str, float]:
        with_context = [item for item in entities if item.context_summary]
        if not mention.context.strip() or not with_context:
            return {}
        vectors = await self.embedding_provider.encode(
            [mention.context, *(item.context_summary or "" for item in with_context)]
        )
        query = vectors[0]
        query_norm = math.sqrt(sum(value * value for value in query)) or 1.0
        scores: dict[str, float] = {}
        for entity, vector in zip(with_context, vectors[1:], strict=True):
            norm = math.sqrt(sum(value * value for value in vector)) or 1.0
            cosine = sum(
                left * right for left, right in zip(query, vector, strict=True)
            ) / (query_norm * norm)
            scores[entity.id] = max(0.0, min(1.0, (cosine + 1.0) / 2.0))
        return scores

    async def _apply_neighborhood_score(
        self, mention: EntityMention, candidate: EntityCandidate
    ) -> EntityCandidate:
        try:
            neighborhood = await self.graph_store.get_neighborhood(candidate.entity_id)
        except (KeyError, ValueError):
            return candidate
        context = normalize_label(mention.context)
        if not context:
            return candidate
        matched = any(
            normalize_label(name) in context
            for entity in neighborhood.entities
            if entity.id != candidate.entity_id
            for name in [entity.name, *entity.aliases]
            if len(normalize_label(name)) >= 3
        )
        if not matched:
            return candidate
        return candidate.model_copy(
            update={
                "neighborhood_score": 1.0,
                "final_score": min(1.0, candidate.final_score + 0.1),
                "reasons": [*candidate.reasons, "neighborhood_context_match"],
            }
        )

    async def resolve(self, mentions: list[EntityMention]) -> ResolutionBundle:
        existing = {item.id: item for item in await self.graph_store.list_entities()}
        entities = dict(existing)
        exact: dict[tuple[str, str], list[CanonicalEntity]] = {}
        names_any_type: dict[str, list[CanonicalEntity]] = {}
        for entity in existing.values():
            if not entity.active:
                continue
            for name in [entity.name, *entity.aliases]:
                normalized = normalize_label(name)
                values = exact.setdefault((normalized, entity.entity_type), [])
                if all(existing.id != entity.id for existing in values):
                    values.append(entity)
                names_any_type.setdefault(normalized, []).append(entity)
        for item in self.schema.schema.entity_catalog:
            entity = CanonicalEntity(
                id=item.id,
                name=item.name,
                entity_type=item.type,
                aliases=item.aliases,
            )
            entities.setdefault(entity.id, entity)
            for name in [entity.name, *entity.aliases]:
                normalized = normalize_label(name)
                values = exact.setdefault((normalized, entity.entity_type), [])
                if all(existing.id != entity.id for existing in values):
                    values.append(entity)
                names_any_type.setdefault(normalized, []).append(entity)

        mapping: dict[str, str] = {}
        review_reasons: dict[str, list[str]] = {}
        decisions: list[EntityResolutionDecision] = []
        review_tasks: list[EntityReviewTask] = []
        provider_enabled = self.embedding_provider.fingerprint() != "embedding:disabled"

        for mention in mentions:
            entity_type = self.schema.entity_type(mention.entity_type)
            reasons: list[str] = []
            if entity_type is None:
                if self.schema.schema.strict:
                    raise SchemaValidationError(f"unknown entity type: {mention.entity_type}")
                entity_type = mention.entity_type
                reasons.append("ontology_addition")
            normalized = normalize_label(mention.name)
            exact_matches = exact.get((normalized, entity_type), [])
            if (
                len(exact_matches) == 1
                and provider_enabled
                and exact_matches[0].context_summary
                and mention.context.strip()
            ):
                try:
                    scores = await self._context_scores(mention, exact_matches)
                    if scores.get(exact_matches[0].id, 1.0) < 0.65:
                        reasons.append("strong_context_conflict")
                except Exception:
                    reasons.append("context_verification_unavailable")
            if len(exact_matches) == 1 and not reasons:
                mapping[mention.id] = exact_matches[0].id
                decisions.append(
                    EntityResolutionDecision(
                        mention_id=mention.id,
                        selected_entity_id=exact_matches[0].id,
                        method="exact",
                        confidence=1.0,
                        margin=1.0,
                        reasons=["exact_alias_and_type_match"],
                    )
                )
                continue

            cross_type = (
                [
                    item
                    for item in names_any_type.get(normalized, [])
                    if item.entity_type != entity_type
                ]
                if not exact_matches
                else []
            )
            vector: list[float] | None = None
            candidates: list[EntityCandidate] = []
            if provider_enabled and not cross_type:
                try:
                    vector = (await self.embedding_provider.encode(
                        [mention_embedding_text(mention, entity_type)]
                    ))[0]
                    retrieved = await self.graph_store.search_entities(
                        vector,
                        entity_type,
                        self.top_k,
                        self.embedding_provider.fingerprint(),
                    )
                    context_scores = await self._context_scores(
                        mention, [entity for entity, _ in retrieved]
                    )
                    candidates = [
                        await self._apply_neighborhood_score(
                            mention,
                            self._candidate(
                                mention, entity, score, context_scores.get(entity.id)
                            ),
                        )
                        for entity, score in retrieved
                    ]
                    candidates = sorted(
                        candidates,
                        key=lambda item: item.final_score,
                        reverse=True,
                    )
                except Exception:  # Provider and backend failures must route to review.
                    reasons.append("embedding_retrieval_unavailable")
                    candidates = [
                        EntityCandidate(
                            entity_id=item.id,
                            retrieval_score=0.0,
                            name_score=1.0,
                            context_score=0.0,
                            final_score=max(0.7, self.review_threshold),
                            reasons=["ambiguous_exact_name_and_type"],
                        )
                        for item in exact_matches
                    ]
            elif len(exact_matches) > 1:
                candidates = [
                    EntityCandidate(
                        entity_id=item.id,
                        retrieval_score=1.0,
                        name_score=1.0,
                        context_score=0.0,
                        final_score=0.7,
                        reasons=["ambiguous_exact_name_and_type"],
                    )
                    for item in exact_matches
                ]

            nil_entity = self._nil_entity(mention, entity_type)
            if nil_entity.id in existing or exact_matches:
                nil_entity = nil_entity.model_copy(
                    update={
                        "id": stable_id(
                            "entity", entity_type, normalized,
                            normalize_label(mention.context), "disambiguated-nil",
                        )
                    }
                )
            entities.setdefault(nil_entity.id, nil_entity)
            if cross_type:
                candidates = [
                    EntityCandidate(
                        entity_id=item.id,
                        retrieval_score=1.0,
                        name_score=1.0,
                        context_score=0.0,
                        final_score=0.3,
                        reasons=["exact_name_type_conflict"],
                    )
                    for item in cross_type
                ]
                reasons.extend(["entity_type_conflict", "human_review_required"])
                decision = EntityResolutionDecision(
                    mention_id=mention.id,
                    candidates=candidates,
                    method="review",
                    confidence=max(item.final_score for item in candidates),
                    requires_review=True,
                    reasons=reasons,
                )
            elif candidates:
                best = candidates[0]
                runner_up = candidates[1].final_score if len(candidates) > 1 else 0.0
                margin = best.final_score - runner_up
                if (
                    best.final_score >= self.auto_link_threshold
                    and margin >= self.min_margin
                    and not reasons
                ):
                    mapping[mention.id] = best.entity_id
                    decision = EntityResolutionDecision(
                        mention_id=mention.id,
                        candidates=candidates,
                        selected_entity_id=best.entity_id,
                        method="vector",
                        confidence=best.final_score,
                        margin=margin,
                        reasons=["high_confidence_semantic_link"],
                    )
                elif best.final_score >= self.review_threshold or reasons:
                    reasons.extend(["ambiguous_semantic_candidates", "human_review_required"])
                    decision = EntityResolutionDecision(
                        mention_id=mention.id,
                        candidates=candidates,
                        method="review",
                        confidence=best.final_score,
                        margin=margin,
                        requires_review=True,
                        reasons=reasons,
                    )
                else:
                    mapping[mention.id] = nil_entity.id
                    decision = EntityResolutionDecision(
                        mention_id=mention.id,
                        candidates=candidates,
                        selected_entity_id=nil_entity.id,
                        method="nil",
                        confidence=max(0.0, 1.0 - best.final_score),
                        margin=margin,
                        reasons=[*reasons, "semantic_score_below_review_threshold"],
                    )
            elif reasons:
                decision = EntityResolutionDecision(
                    mention_id=mention.id,
                    method="review",
                    confidence=0.0,
                    requires_review=True,
                    reasons=[*reasons, "human_review_required"],
                )
            else:
                mapping[mention.id] = nil_entity.id
                decision = EntityResolutionDecision(
                    mention_id=mention.id,
                    selected_entity_id=nil_entity.id,
                    method="nil",
                    confidence=1.0,
                    reasons=["no_existing_candidate"],
                )
            decisions.append(decision)
            if decision.requires_review:
                review_reasons[mention.id] = decision.reasons
                review_tasks.append(
                    EntityReviewTask(
                        id=stable_id("entity-review", self.run_id, mention.id),
                        run_id=self.run_id,
                        mention_id=mention.id,
                        task_type="link",
                        candidates=decision.candidates,
                        reasons=decision.reasons,
                        proposed_entity_id=nil_entity.id,
                    )
                )
            values = exact.setdefault((normalized, entity_type), [])
            if all(item.id != nil_entity.id for item in values):
                values.append(nil_entity)

        return ResolutionBundle(
            entities=list(entities.values()),
            mention_to_entity=mapping,
            review_reasons=review_reasons,
            decisions=decisions,
            review_tasks=review_tasks,
        )
