"""Auditable merge and split operations for canonical entities."""

from __future__ import annotations

from collections.abc import Mapping
from uuid import uuid4

from src.core.errors import GraphIntegrityError
from src.core.ids import canonical_hash, stable_id
from src.domain import (
    CanonicalEntity,
    Claim,
    EntityEmbedding,
    EntityOperation,
    EntityReviewTask,
    GraphChange,
    GraphCommit,
    GraphRevision,
    utc_now,
)
from src.governance.entity_resolution import entity_embedding_text
from src.governance.validation.context import context_for_claims
from src.persistence.base import GraphStore
from src.persistence.entity_governance import EntityGovernanceRepository
from src.providers.base import EmbeddingProvider


class EntityGovernanceService:
    def __init__(
        self,
        graph_store: GraphStore,
        repository: EntityGovernanceRepository,
        embedding_provider: EmbeddingProvider,
    ) -> None:
        self.graph_store = graph_store
        self.repository = repository
        self.embedding_provider = embedding_provider

    async def propose_merge(
        self,
        source_entity_ids: list[str],
        target_entity_id: str,
        reasons: list[str],
    ) -> EntityReviewTask:
        source_ids = list(dict.fromkeys(source_entity_ids))
        if len(source_ids) < 2 or target_entity_id not in source_ids:
            raise ValueError("merge requires at least two entities and a target among them")
        entities = await self.graph_store.list_entities()
        selected = {item.id: item for item in entities if item.id in source_ids}
        if set(selected) != set(source_ids):
            raise KeyError("one or more merge entities do not exist")
        if any(not item.active for item in selected.values()):
            raise ValueError("merge sources must be active entities")
        if len({item.entity_type for item in selected.values()}) != 1:
            raise ValueError("entities with different types cannot be merged")
        claims = [
            item
            for item in await self.graph_store.list_claims()
            if item.tx_to is None and ({item.subject_id, item.object_entity_id} & set(source_ids))
        ]
        operation = EntityOperation(
            id=stable_id(
                "entity-operation", "merge", *sorted(source_ids), target_entity_id, uuid4().hex
            ),
            operation_type="merge",
            source_entity_ids=source_ids,
            target_entity_ids=[target_entity_id],
            affected_claim_ids=sorted(item.id for item in claims),
            before={
                "entities": {item.id: item.model_dump(mode="json") for item in selected.values()},
                "claims": {item.id: item.model_dump(mode="json") for item in claims},
            },
            after={"survivor_entity_id": target_entity_id},
            reasons=reasons or ["manual_merge_proposal"],
            evidence_ids=sorted({evidence for item in claims for evidence in item.evidence_ids}),
        )
        task = EntityReviewTask(
            id=stable_id("entity-review", operation.id),
            run_id="governance",
            operation_id=operation.id,
            task_type="merge",
            reasons=operation.reasons,
        )
        self.repository.save(task, operation)
        return task

    async def propose_split(
        self,
        source_entity_id: str,
        target_entities: list[CanonicalEntity],
        claim_assignments: Mapping[str, str],
        reasons: list[str],
    ) -> EntityReviewTask:
        source = await self.graph_store.get_entity(source_entity_id)
        if source is None:
            raise KeyError(f"entity not found: {source_entity_id}")
        if not source.active:
            raise ValueError("split source must be active")
        if not target_entities:
            raise ValueError("split requires at least one target entity")
        targets = {item.id: item for item in target_entities}
        if len(targets) != len(target_entities):
            raise ValueError("split target entity ids must be unique")
        existing_ids = {item.id for item in await self.graph_store.list_entities()}
        if set(targets) & existing_ids:
            raise ValueError("split targets must have new entity ids")
        if any(item.entity_type != source.entity_type for item in targets.values()):
            raise ValueError("split target types must match the source entity type")
        if not set(claim_assignments.values()) <= set(targets):
            raise ValueError("claim assignment references an unknown split target")
        claims = {
            item.id: item
            for item in await self.graph_store.list_claims()
            if item.tx_to is None and source_entity_id in {item.subject_id, item.object_entity_id}
        }
        if not claim_assignments or not set(claim_assignments) <= set(claims):
            raise ValueError("split assignments must reference active claims of the source")
        evidence_ids = sorted(
            {
                evidence
                for claim_id in claim_assignments
                for evidence in claims[claim_id].evidence_ids
            }
        )
        if not evidence_ids:
            raise ValueError("split requires claim-level evidence")
        operation = EntityOperation(
            id=stable_id(
                "entity-operation",
                "split",
                source_entity_id,
                canonical_hash(dict(sorted(claim_assignments.items()))),
                uuid4().hex,
            ),
            operation_type="split",
            source_entity_ids=[source_entity_id],
            target_entity_ids=sorted(targets),
            affected_claim_ids=sorted(claim_assignments),
            before={
                "entities": {source.id: source.model_dump(mode="json")},
                "claims": {
                    claim_id: claims[claim_id].model_dump(mode="json")
                    for claim_id in claim_assignments
                },
            },
            after={
                "target_entities": {
                    item.id: item.model_dump(mode="json") for item in targets.values()
                },
                "claim_assignments": dict(claim_assignments),
            },
            reasons=reasons or ["manual_split_proposal"],
            evidence_ids=evidence_ids,
        )
        task = EntityReviewTask(
            id=stable_id("entity-review", operation.id),
            run_id="governance",
            operation_id=operation.id,
            task_type="split",
            reasons=operation.reasons,
        )
        self.repository.save(task, operation)
        return task

    async def resolve_operation(
        self, task_id: str, approve: bool, reviewer: str | None = None
    ) -> GraphRevision | None:
        task = self.repository.get_task(task_id)
        if task is None or task.operation_id is None:
            raise KeyError(f"entity governance task not found: {task_id}")
        operation = self.repository.get_operation(task.operation_id)
        if operation is None:
            raise GraphIntegrityError(f"entity operation not found: {task.operation_id}")
        if task.status == "resolved":
            if operation.status == "applied":
                revisions = await self.graph_store.list_revisions(limit=1000)
                return next(
                    (item for item in revisions if item.run_id == f"governance:{operation.id}"),
                    None,
                )
            return None
        task.status = "resolved"
        task.decision = "approve" if approve else "reject"
        task.resolved_at = utc_now()
        operation.reviewer = reviewer
        operation.reviewed_at = task.resolved_at
        if not approve:
            operation.status = "rejected"
            self.repository.update(task, operation)
            return None
        operation.status = "approved"
        revision = await self._apply(operation)
        operation.status = "applied"
        self.repository.update(task, operation)
        return revision

    async def _embedding(self, entity: CanonicalEntity) -> EntityEmbedding | None:
        if self.embedding_provider.fingerprint() == "embedding:disabled":
            return None
        text = entity_embedding_text(entity)
        vector = (await self.embedding_provider.encode([text]))[0]
        return EntityEmbedding(
            entity_id=entity.id,
            model_fingerprint=self.embedding_provider.fingerprint(),
            text_hash=canonical_hash(text),
            dimension=len(vector),
            vector=vector,
        )

    async def _apply(self, operation: EntityOperation) -> GraphRevision:
        parent = await self.graph_store.latest_revision()
        entities = {item.id: item for item in await self.graph_store.list_entities()}
        claims = {item.id: item for item in await self.graph_store.list_claims()}
        if operation.operation_type == "split" and set(operation.target_entity_ids) & set(entities):
            raise GraphIntegrityError("split target ids were created after the proposal")
        for resource_type, current in (("entities", entities), ("claims", claims)):
            for resource_id, expected in operation.before.get(resource_type, {}).items():
                resource = current.get(resource_id)
                if resource is None or canonical_hash(resource.model_dump(mode="json")) != (
                    canonical_hash(expected)
                ):
                    raise GraphIntegrityError(
                        f"entity proposal is stale for {resource_type}:{resource_id}; "
                        "create a new proposal before approval"
                    )
        changed_entities: dict[str, CanonicalEntity] = {}
        changed_claims: dict[str, Claim] = {}
        changes: list[GraphChange] = []
        if operation.operation_type == "merge":
            target_id = operation.target_entity_ids[0]
            target = entities[target_id]
            sources = [entities[item] for item in operation.source_entity_ids]
            merged = target.model_copy(
                update={
                    "aliases": sorted(
                        {
                            alias
                            for item in sources
                            for alias in [item.name, *item.aliases]
                            if alias != target.name
                        }
                    ),
                    "attributes": {
                        key: value for item in sources for key, value in item.attributes.items()
                    }
                    | target.attributes,
                    "source_evidence_ids": sorted(
                        {evidence for item in sources for evidence in item.source_evidence_ids}
                    ),
                    "active": True,
                }
            )
            changed_entities[target_id] = merged
            for source in sources:
                replacement_entity = (
                    merged
                    if source.id == target_id
                    else source.model_copy(update={"active": False})
                )
                changed_entities[source.id] = replacement_entity
                changes.append(
                    GraphChange(
                        resource_type="entity",
                        resource_id=source.id,
                        action="update",
                        before=source.model_dump(mode="json"),
                        after=replacement_entity.model_dump(mode="json"),
                    )
                )
            for claim_id in operation.affected_claim_ids:
                claim = claims[claim_id]
                replacement_claim = claim.model_copy(
                    update={
                        "subject_id": (
                            target_id
                            if claim.subject_id in operation.source_entity_ids
                            else claim.subject_id
                        ),
                        "object_entity_id": (
                            target_id
                            if claim.object_entity_id in operation.source_entity_ids
                            else claim.object_entity_id
                        ),
                    }
                )
                changed_claims[claim.id] = replacement_claim
                changes.append(
                    GraphChange(
                        resource_type="claim",
                        resource_id=claim.id,
                        action="update",
                        before=claim.model_dump(mode="json"),
                        after=replacement_claim.model_dump(mode="json"),
                    )
                )
        else:
            source_id = operation.source_entity_ids[0]
            source = entities[source_id]
            target_payloads = operation.after["target_entities"]
            targets = {
                item_id: CanonicalEntity.model_validate(payload)
                for item_id, payload in target_payloads.items()
            }
            changed_entities.update(targets)
            assignments = operation.after["claim_assignments"]
            for claim_id, target_id in assignments.items():
                claim = claims[claim_id]
                replacement_claim = claim.model_copy(
                    update={
                        "subject_id": (
                            target_id if claim.subject_id == source_id else claim.subject_id
                        ),
                        "object_entity_id": (
                            target_id
                            if claim.object_entity_id == source_id
                            else claim.object_entity_id
                        ),
                    }
                )
                changed_claims[claim.id] = replacement_claim
                changes.append(
                    GraphChange(
                        resource_type="claim",
                        resource_id=claim.id,
                        action="update",
                        before=claim.model_dump(mode="json"),
                        after=replacement_claim.model_dump(mode="json"),
                    )
                )
            active_refs = [
                item
                for item in claims.values()
                if item.tx_to is None
                and item.id not in assignments
                and source_id in {item.subject_id, item.object_entity_id}
            ]
            replacement_source = source.model_copy(update={"active": bool(active_refs)})
            changed_entities[source_id] = replacement_source
            changes.append(
                GraphChange(
                    resource_type="entity",
                    resource_id=source_id,
                    action="update",
                    before=source.model_dump(mode="json"),
                    after=replacement_source.model_dump(mode="json"),
                )
            )
            for target in targets.values():
                changes.append(
                    GraphChange(
                        resource_type="entity",
                        resource_id=target.id,
                        action="create" if target.id not in entities else "update",
                        before=(
                            entities[target.id].model_dump(mode="json")
                            if target.id in entities
                            else None
                        ),
                        after=target.model_dump(mode="json"),
                    )
                )

        applied = operation.model_copy(update={"status": "applied"})
        changes.append(
            GraphChange(
                resource_type="entity_operation",
                resource_id=operation.id,
                action="create",
                after=applied.model_dump(mode="json"),
            )
        )
        revision = GraphRevision(
            id=stable_id(
                "revision", "entity-governance", operation.id, parent.id if parent else "root"
            ),
            run_id=f"governance:{operation.id}",
            parent_id=parent.id if parent else None,
            entity_ids=sorted(changed_entities),
            claim_ids=sorted(changed_claims),
            changes=changes,
        )
        embeddings = [
            result
            for result in [
                await self._embedding(item) for item in changed_entities.values() if item.active
            ]
            if result is not None
        ]
        context = context_for_claims(
            await self.graph_store.list_revisions(limit=100000), set(claims)
        )
        await self.graph_store.commit(
            GraphCommit(
                entities=list(changed_entities.values()),
                claims=list(changed_claims.values()),
                entity_operations=[applied],
                entity_embeddings=embeddings,
                revision=revision,
                validation_context=context,
            )
        )
        return revision
