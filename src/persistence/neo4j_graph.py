"""Neo4j graph store using one managed transaction per GraphCommit."""

from __future__ import annotations

import asyncio
import math
from datetime import UTC, datetime
from typing import Any

import orjson

from src.core.errors import GraphIntegrityError
from src.core.ids import stable_id
from src.domain import (
    CanonicalEntity,
    Claim,
    ConflictSet,
    EntityEmbedding,
    EntityOperation,
    EvidenceRef,
    GraphChange,
    GraphCommit,
    GraphHealth,
    GraphMediaContent,
    GraphMediaOccurrence,
    GraphMediaRelation,
    GraphNeighborhood,
    GraphRevision,
    RevisionDiff,
    VisualAssertion,
    VisualReviewEvent,
    visual_value_matches,
)
from src.governance.validation import ValidationService
from src.governance.validation.context import (
    bind_commit_provenance,
    context_for_claims,
    final_state_commit,
)
from src.persistence.base import EvidenceStore


def _dump(model: Any) -> str:
    return orjson.dumps(model.model_dump(mode="json")).decode("utf-8")


def _load(payload: str, model: Any) -> Any:
    return model.model_validate(orjson.loads(payload))


class Neo4jGraphStore:
    def __init__(
        self,
        uri: str,
        user: str,
        password: str,
        database: str = "neo4j",
        *,
        driver: Any | None = None,
        evidence_store: EvidenceStore | None = None,
    ) -> None:
        self.evidence_store = evidence_store
        if driver is None:
            try:
                from neo4j import AsyncGraphDatabase
            except ImportError as exc:
                raise RuntimeError(
                    "Neo4j support is not installed; run `uv sync --extra neo4j`"
                ) from exc
            driver = AsyncGraphDatabase.driver(uri, auth=(user, password))
        self.driver = driver
        self.database = database
        self._schema_ready = False
        self._schema_lock = asyncio.Lock()

    async def _ensure_schema(self) -> None:
        if self._schema_ready:
            return
        async with self._schema_lock:
            if self._schema_ready:
                return
            statements = [
                f"CREATE CONSTRAINT {label.lower()}_id IF NOT EXISTS "
                f"FOR (n:{label}) REQUIRE n.id IS UNIQUE"
                for label in (
                    "Document",
                    "Evidence",
                    "Entity",
                    "EntityOperation",
                    "Claim",
                    "ConflictSet",
                    "Revision",
                    "RevisionChange",
                    "MediaContent",
                    "MediaOccurrence",
                    "MediaRelation",
                    "VisualAssertion",
                    "VisualReviewEvent",
                )
            ]
            statements.extend(
                [
                    "CREATE INDEX entity_name_type IF NOT EXISTS FOR (n:Entity) "
                    "ON (n.name, n.entity_type)",
                    "CREATE INDEX claim_relation_status IF NOT EXISTS FOR (n:Claim) "
                    "ON (n.relation_id, n.status)",
                    "CREATE INDEX revision_created IF NOT EXISTS FOR (n:Revision) "
                    "ON (n.created_at)",
                    "CREATE CONSTRAINT media_content_hash IF NOT EXISTS "
                    "FOR (n:MediaContent) REQUIRE n.content_hash IS UNIQUE",
                    "CREATE VECTOR INDEX entity_embedding_bge_m3 IF NOT EXISTS "
                    "FOR (n:Entity) ON (n.embedding) OPTIONS {indexConfig: {"
                    "`vector.dimensions`: 1024, `vector.similarity_function`: 'cosine'}}",
                ]
            )
            async with self.driver.session(database=self.database) as session:
                for statement in statements:
                    await session.run(statement)
                for _ in range(60):
                    result = await session.run(
                        "SHOW VECTOR INDEXES YIELD name, state "
                        "WHERE name = 'entity_embedding_bge_m3' "
                        "RETURN state"
                    )
                    record = await result.single()
                    if record is not None and record["state"] == "ONLINE":
                        break
                    await asyncio.sleep(0.5)
                else:
                    raise GraphIntegrityError(
                        "Neo4j entity vector index did not become ONLINE within 30 seconds"
                    )
            self._schema_ready = True

    async def healthcheck(self) -> GraphHealth:
        try:
            await self.driver.verify_connectivity()
            await self._ensure_schema()
        except Exception as exc:
            return GraphHealth(backend="neo4j", healthy=False, message=type(exc).__name__)
        return GraphHealth(backend="neo4j", healthy=True)

    async def _commit_tx(self, tx: Any, transaction: GraphCommit) -> None:
        result = await tx.run(
            "MERGE (h:GraphHead {id: 'singleton'}) "
            "SET h.lock_nonce=randomUUID() RETURN h.latest_id AS latest_id"
        )
        head = await result.single()
        result = await tx.run(
            "MATCH (r:Revision {id: $id}) RETURN r.payload AS payload", id=transaction.revision.id
        )
        record = await result.single()
        if record is not None:
            if _load(record["payload"], GraphRevision) != transaction.revision:
                raise GraphIntegrityError(
                    f"revision id already exists with different content: {transaction.revision.id}"
                )
            return
        latest_id = head["latest_id"] if head is not None else None
        if latest_id is None:
            result = await tx.run(
                "MATCH (r:Revision) RETURN r.id AS id ORDER BY r.created_at DESC LIMIT 1"
            )
            latest = await result.single()
            latest_id = latest["id"] if latest is not None else None
        if transaction.revision.parent_id != latest_id:
            raise GraphIntegrityError(
                f"revision parent mismatch: expected {latest_id}, "
                f"got {transaction.revision.parent_id}"
            )

        entity_result = await tx.run("MATCH (n:Entity) RETURN n.payload AS payload")
        entities = {
            _load(r["payload"], CanonicalEntity).id: _load(r["payload"], CanonicalEntity)
            async for r in entity_result
        }
        previous_entities = dict(entities)
        entities.update({e.id: e for e in transaction.entities})
        evidence_result = await tx.run("MATCH (n:Evidence) RETURN n.payload AS payload")
        evidence_map = {
            _load(r["payload"], EvidenceRef).id: _load(r["payload"], EvidenceRef)
            async for r in evidence_result
        }
        evidence_map.update({e.id: e for e in transaction.evidence})
        document_result = await tx.run("MATCH (n:Document) RETURN n.id AS id")
        document_ids = {r["id"] async for r in document_result} | {
            d.id for d in transaction.documents
        }
        claim_result = await tx.run("MATCH (n:Claim) RETURN n.payload AS payload")
        current_claims = {
            _load(r["payload"], Claim).id: _load(r["payload"], Claim) async for r in claim_result
        }
        exact_maintenance = transaction.revision.run_id == "maintenance:legacy-evidence-v092"
        if transaction.revision.run_id.startswith("rollback:") or exact_maintenance:
            labels = {
                "entity": "Entity",
                "claim": "Claim",
                "conflict": "ConflictSet",
                "entity_operation": "EntityOperation",
                "media_content": "MediaContent",
                "media_occurrence": "MediaOccurrence",
                "media_relation": "MediaRelation",
                "visual_assertion": "VisualAssertion",
            }
            for change in transaction.revision.changes:
                result = await tx.run(
                    f"MATCH (n:{labels[change.resource_type]} {{id: $id}}) "
                    "RETURN n.payload AS payload",
                    id=change.resource_id,
                )
                row = await result.single()
                payload = orjson.loads(row["payload"]) if row else None
                if exact_maintenance and change.resource_type == "claim" and payload is not None:
                    payload = Claim.model_validate(payload).model_dump(mode="json")
                if payload != change.before:
                    reason = (
                        "STALE_MAINTENANCE_RESOURCE"
                        if exact_maintenance
                        else "STALE_ROLLBACK_RESOURCE"
                    )
                    raise GraphIntegrityError(reason)
        from src.governance.review_guards import verify_correction
        from src.persistence.json_graph import JSONGraphStore

        verify_correction(
            transaction,
            {
                **{f"entity:{k}": e.model_dump(mode="json") for k, e in previous_entities.items()},
                **{f"claim:{k}": c.model_dump(mode="json") for k, c in current_claims.items()},
            },
        )

        transaction.claims = [
            JSONGraphStore._merge_claim(current_claims[c.id].model_dump(mode="json"), c)
            if c.id in current_claims
            and transaction.correction_guard is None
            and not transaction.revision.run_id.startswith("rollback:")
            and not exact_maintenance
            else c
            for c in transaction.claims
        ]
        current_claims.update({c.id: c for c in transaction.claims})
        revision_result = await tx.run(
            "MATCH (n:Revision) RETURN n.payload AS payload ORDER BY n.created_at DESC"
        )
        revisions = [_load(r["payload"], GraphRevision) async for r in revision_result]
        await ValidationService().commit(
            final_state_commit(transaction, current_claims, previous_entities, revisions),
            entities,
            evidence_map,
            document_ids,
            self.evidence_store,
        )
        for document in transaction.documents:
            await tx.run(
                "MERGE (n:Document {id: $id}) "
                "SET n.filename=$filename, n.content_hash=$hash, n.media_type=$media_type, "
                "n.payload=$payload",
                id=document.id,
                filename=document.filename,
                hash=document.content_hash,
                media_type=document.media_type,
                payload=_dump(document),
            )
        for evidence in transaction.evidence:
            await tx.run(
                "MATCH (d:Document {id: $document_id}) "
                "MERGE (e:Evidence {id: $id}) SET e.kind=$kind, e.payload=$payload "
                "MERGE (d)-[:CONTAINS]->(e)",
                document_id=evidence.document_id,
                id=evidence.id,
                kind=evidence.kind.value,
                payload=_dump(evidence),
            )
        for entity in transaction.entities:
            previous_result = await tx.run(
                "MATCH (n:Entity {id: $id}) RETURN n.payload AS payload", id=entity.id
            )
            previous_record = await previous_result.single()
            if previous_record is not None and (
                _load(previous_record["payload"], CanonicalEntity).embedding_source()
                != entity.embedding_source()
            ):
                await tx.run(
                    "MATCH (n:Entity {id: $id}) "
                    "REMOVE n.embedding, n.embedding_model, n.embedding_text_hash, "
                    "n.embedding_dimension",
                    id=entity.id,
                )
            if not entity.active:
                closing_claim_ids = [claim.id for claim in transaction.claims]
                result = await tx.run(
                    "MATCH (e:Entity {id: $id})<-[:SUBJECT|OBJECT]-(c:Claim) "
                    "WHERE c.tx_to IS NULL AND NOT c.id IN $closing_claim_ids "
                    "RETURN count(c) AS active_count",
                    id=entity.id,
                    closing_claim_ids=closing_claim_ids,
                )
                record = await result.single()
                if record is not None and record["active_count"]:
                    raise GraphIntegrityError(
                        f"entity {entity.id} still has active claim references"
                    )
            await tx.run(
                "MERGE (n:Entity {id: $id}) "
                "SET n.name=$name, n.entity_type=$entity_type, n.active=$active, "
                "n.payload=$payload",
                id=entity.id,
                name=entity.name,
                entity_type=entity.entity_type,
                active=entity.active,
                payload=_dump(entity),
            )
        for embedding in transaction.entity_embeddings:
            await tx.run(
                "MATCH (n:Entity {id: $entity_id}) "
                "SET n.embedding=$vector, n.embedding_model=$model, "
                "n.embedding_text_hash=$text_hash, n.embedding_dimension=$dimension",
                entity_id=embedding.entity_id,
                vector=embedding.vector,
                model=embedding.model_fingerprint,
                text_hash=embedding.text_hash,
                dimension=embedding.dimension,
            )
        for claim in transaction.claims:
            result = await tx.run(
                "MATCH (s:Entity {id: $subject_id}) "
                "OPTIONAL MATCH (o:Entity {id: $object_id}) "
                "RETURN s.id AS subject_id, o.id AS object_id",
                subject_id=claim.subject_id,
                object_id=claim.object_entity_id,
            )
            refs = await result.single()
            if refs is None or (claim.object_entity_id is not None and refs["object_id"] is None):
                raise GraphIntegrityError(f"claim {claim.id} references missing entities")
            if transaction.evidence:
                result = await tx.run(
                    "MATCH (e:Evidence) WHERE e.id IN $ids RETURN collect(e.id) AS ids",
                    ids=claim.evidence_ids,
                )
                found = set((await result.single())["ids"])
                if found != set(claim.evidence_ids):
                    raise GraphIntegrityError(f"claim {claim.id} references missing evidence")
            await tx.run(
                "MATCH (s:Entity {id: $subject_id}) "
                "MERGE (c:Claim {id: $id}) "
                "SET c.relation_id=$relation_id, c.status=$status, c.tx_from=$tx_from, "
                "c.tx_to=$tx_to, c.payload=$payload "
                "WITH c, s OPTIONAL MATCH (c)-[old:SUBJECT|OBJECT|SUPPORTED_BY]->() "
                "DELETE old "
                "MERGE (c)-[:SUBJECT]->(s)",
                subject_id=claim.subject_id,
                id=claim.id,
                relation_id=claim.relation_id,
                status=claim.status.value,
                tx_from=claim.tx_from.isoformat(),
                tx_to=claim.tx_to.isoformat() if claim.tx_to else None,
                payload=_dump(claim),
            )
            if claim.object_entity_id:
                await tx.run(
                    "MATCH (c:Claim {id: $claim_id}), (o:Entity {id: $object_id}) "
                    "MERGE (c)-[:OBJECT]->(o)",
                    claim_id=claim.id,
                    object_id=claim.object_entity_id,
                )
            await tx.run(
                "MATCH (c:Claim {id: $claim_id}), (e:Evidence) WHERE e.id IN $evidence_ids "
                "MERGE (c)-[:SUPPORTED_BY]->(e)",
                claim_id=claim.id,
                evidence_ids=claim.evidence_ids,
            )
        for conflict in transaction.conflicts:
            await tx.run(
                "MERGE (n:ConflictSet {id: $id}) SET n.status=$status, n.payload=$payload",
                id=conflict.id,
                status=conflict.status,
                payload=_dump(conflict),
            )
            await tx.run(
                "MATCH (n:ConflictSet {id: $id}), (c:Claim) WHERE c.id IN $claim_ids "
                "MERGE (n)-[:CONTAINS]->(c)",
                id=conflict.id,
                claim_ids=conflict.claim_ids,
            )
        for operation in transaction.entity_operations:
            referenced_entities = set(operation.source_entity_ids + operation.target_entity_ids)
            result = await tx.run(
                "MATCH (n:Entity) WHERE n.id IN $ids RETURN collect(n.id) AS ids",
                ids=sorted(referenced_entities),
            )
            found = set((await result.single())["ids"])
            if found != referenced_entities:
                raise GraphIntegrityError(
                    f"entity operation {operation.id} references missing entities"
                )
            await tx.run(
                "MERGE (n:EntityOperation {id: $id}) "
                "SET n.operation_type=$operation_type, n.status=$status, n.payload=$payload",
                id=operation.id,
                operation_type=operation.operation_type,
                status=operation.status,
                payload=_dump(operation),
            )
            if operation.operation_type == "merge" and operation.target_entity_ids:
                if operation.status == "applied":
                    await tx.run(
                        "MATCH (target:Entity {id: $target_id}) "
                        "MATCH (source:Entity) WHERE source.id IN $source_ids "
                        "AND source.id <> $target_id "
                        "MERGE (source)-[:MERGED_INTO "
                        "{operation_id: $operation_id}]->(target)",
                        target_id=operation.target_entity_ids[0],
                        source_ids=operation.source_entity_ids,
                        operation_id=operation.id,
                    )
                else:
                    await tx.run(
                        "MATCH ()-[r:MERGED_INTO {operation_id: $operation_id}]->() DELETE r",
                        operation_id=operation.id,
                    )
        for event in transaction.visual_review_events:
            await tx.run(
                "MERGE (n:VisualReviewEvent {id: $id}) "
                "ON CREATE SET n.request_id=$request_id, n.payload=$payload "
                "ON MATCH SET n.payload=CASE WHEN n.payload=$payload THEN n.payload ELSE null END",
                id=event.id,
                request_id=event.request_id,
                payload=_dump(event),
            )
            result = await tx.run(
                "MATCH (n:VisualReviewEvent {id: $id}) RETURN n.payload AS payload", id=event.id
            )
            row = await result.single()
            if row is None or row["payload"] is None:
                raise GraphIntegrityError(
                    f"visual review event already exists with different content: {event.id}"
                )
        for content in transaction.media_contents:
            result = await tx.run(
                "OPTIONAL MATCH (same:MediaContent {content_hash: $content_hash}) "
                "RETURN same.id AS existing_id, same.payload AS existing_payload",
                content_hash=content.content_hash,
            )
            same = await result.single()
            if same is not None and same["existing_id"] not in {None, content.id}:
                raise GraphIntegrityError(f"duplicate media content hash: {content.content_hash}")
            if (
                same is not None
                and same["existing_payload"] is not None
                and _load(same["existing_payload"], GraphMediaContent) != content
            ):
                raise GraphIntegrityError(f"immutable media content changed: {content.id}")
            await tx.run(
                "MERGE (n:MediaContent {id: $id}) "
                "SET n.content_hash=$content_hash, n.asset_type=$asset_type, n.payload=$payload",
                id=content.id,
                content_hash=content.content_hash,
                asset_type=content.asset_type.value,
                payload=_dump(content),
            )
        for occurrence in transaction.media_occurrences:
            result = await tx.run(
                "MATCH (d:Document {id: $document_id}), "
                "(c:MediaContent {id: $content_id}), (e:Evidence {id: $evidence_id}) "
                "MERGE (n:MediaOccurrence {id: $id}) "
                "SET n.active=$active, n.tx_to=$tx_to, n.payload=$payload "
                "MERGE (d)-[:CONTAINS]->(n) "
                "MERGE (n)-[:INSTANCE_OF]->(c) "
                "MERGE (n)-[:SUPPORTED_BY]->(e) RETURN n.id AS id",
                document_id=occurrence.document_id,
                content_id=occurrence.media_content_id,
                evidence_id=occurrence.evidence_id,
                id=occurrence.id,
                active=occurrence.active,
                tx_to=occurrence.tx_to.isoformat() if occurrence.tx_to else None,
                payload=_dump(occurrence),
            )
            if await result.single() is None:
                raise GraphIntegrityError(
                    f"media occurrence {occurrence.id} has dangling references"
                )
        for relation in transaction.media_relations:
            target_label = "Entity" if relation.target_entity_id else "Claim"
            target_id = relation.target_entity_id or relation.target_claim_id
            if relation.relation_type.value == "DEPICTS" and not relation.approved_review_event_id:
                raise GraphIntegrityError("DEPICTS requires an approved visual review")
            if relation.approved_review_event_id:
                result = await tx.run(
                    "MATCH (e:VisualReviewEvent {id: $id}) RETURN e.payload AS payload",
                    id=relation.approved_review_event_id,
                )
                event_row = await result.single()
                if event_row is None:
                    raise GraphIntegrityError("media relation review event is missing")
                relation_event = _load(event_row["payload"], VisualReviewEvent)
                if (
                    relation_event.decision != "approve"
                    or relation_event.target_type != "media_relation"
                    or relation_event.target_id != relation.source_candidate_id
                ):
                    raise GraphIntegrityError(
                        "media relation review event does not approve relation"
                    )
            result = await tx.run(
                "MATCH (e:Evidence) WHERE e.id IN $ids RETURN collect(e.id) AS ids",
                ids=relation.evidence_ids,
            )
            found_evidence = set((await result.single())["ids"])
            if found_evidence != set(relation.evidence_ids):
                raise GraphIntegrityError(
                    f"media relation {relation.id} references missing evidence"
                )
            if relation.target_claim_id:
                target_claim = current_claims.get(relation.target_claim_id)
                if target_claim is None or target_claim.status.value not in {
                    "approved",
                    "auto_approved",
                }:
                    raise GraphIntegrityError("SUPPORTS requires an approved claim")
                support_occurrence = next(
                    (
                        item
                        for item in transaction.media_occurrences
                        if item.id == relation.occurrence_id
                    ),
                    None,
                )
                if support_occurrence is None:
                    occurrence_result = await tx.run(
                        "MATCH (o:MediaOccurrence {id: $id}) RETURN o.payload AS payload",
                        id=relation.occurrence_id,
                    )
                    occurrence_row = await occurrence_result.single()
                    support_occurrence = (
                        _load(occurrence_row["payload"], GraphMediaOccurrence)
                        if occurrence_row is not None
                        else None
                    )
                if (
                    support_occurrence is None
                    or support_occurrence.evidence_id not in target_claim.evidence_ids
                ):
                    raise GraphIntegrityError("SUPPORTS evidence does not support target claim")
            result = await tx.run(
                f"MATCH (o:MediaOccurrence {{id: $occurrence_id}}), "
                f"(target:{target_label} {{id: $target_id}}) "
                "MERGE (r:MediaRelation {id: $id}) "
                "SET r.relation_type=$relation_type, r.active=$active, r.payload=$payload "
                "MERGE (r)-[:FROM_OCCURRENCE]->(o) "
                "MERGE (r)-[:TARGET]->(target) RETURN o.id AS occurrence_id",
                occurrence_id=relation.occurrence_id,
                target_id=target_id,
                id=relation.id,
                relation_type=relation.relation_type.value,
                active=relation.active,
                payload=_dump(relation),
            )
            if await result.single() is None:
                raise GraphIntegrityError(f"media relation {relation.id} has dangling references")
            direct_type = relation.relation_type.value
            if relation.active:
                await tx.run(
                    f"MATCH (o:MediaOccurrence {{id: $occurrence_id}}), "
                    f"(target:{target_label} {{id: $target_id}}) "
                    f"MERGE (o)-[edge:{direct_type} "
                    "{relation_id: $relation_id}]->(target)",
                    occurrence_id=relation.occurrence_id,
                    target_id=target_id,
                    relation_id=relation.id,
                )
            else:
                await tx.run(
                    f"MATCH (:MediaOccurrence {{id: $occurrence_id}})-"
                    f"[edge:{direct_type} {{relation_id: $relation_id}}]->() DELETE edge",
                    occurrence_id=relation.occurrence_id,
                    relation_id=relation.id,
                )
        for assertion in transaction.visual_assertions:
            attribute_ids = {
                attribute.id
                for schema in (
                    transaction.validation_context.schemas.values()
                    if transaction.validation_context
                    else []
                )
                for attribute in schema.attributes
            }
            if assertion.predicate not in attribute_ids:
                raise GraphIntegrityError(
                    f"visual assertion predicate is not in schema: {assertion.predicate}"
                )
            definition = next(
                (
                    attribute
                    for schema in (
                        transaction.validation_context.schemas.values()
                        if transaction.validation_context
                        else []
                    )
                    for attribute in schema.attributes
                    if attribute.id == assertion.predicate
                ),
                None,
            )
            if definition is None or not visual_value_matches(
                assertion.normalized_value, definition.value_type
            ):
                raise GraphIntegrityError(
                    f"visual assertion value type is invalid: {assertion.id}"
                )
            event_result = await tx.run(
                "MATCH (event:VisualReviewEvent {id: $event_id}) "
                "RETURN event.payload AS payload",
                event_id=assertion.approved_review_event_id,
            )
            event_row = await event_result.single()
            if event_row is None:
                raise GraphIntegrityError("visual assertion review event is missing")
            assertion_event = _load(event_row["payload"], VisualReviewEvent)
            if (
                assertion_event.decision != "approve"
                or assertion_event.target_type != "visual_assertion"
                or assertion_event.target_id != assertion.source_candidate_id
            ):
                raise GraphIntegrityError(
                    "visual assertion review event does not approve assertion"
                )
            result = await tx.run(
                "MATCH (o:MediaOccurrence {id: $occurrence_id}), "
                "(entity:Entity {id: $entity_id}), "
                "(event:VisualReviewEvent {id: $event_id}) "
                "MERGE (a:VisualAssertion {id: $id}) "
                "SET a.predicate=$predicate, a.active=$active, a.tx_to=$tx_to, a.payload=$payload "
                "MERGE (o)-[:HAS_ASSERTION]->(a) "
                "MERGE (a)-[:ABOUT]->(entity) "
                "MERGE (a)-[:APPROVED_BY]->(event) RETURN a.id AS id",
                occurrence_id=assertion.occurrence_id,
                entity_id=assertion.subject_entity_id,
                event_id=assertion.approved_review_event_id,
                id=assertion.id,
                predicate=assertion.predicate,
                active=assertion.active,
                tx_to=assertion.tx_to.isoformat() if assertion.tx_to else None,
                payload=_dump(assertion),
            )
            if await result.single() is None:
                raise GraphIntegrityError(
                    f"visual assertion {assertion.id} has dangling references"
                )
        revision = transaction.revision
        await tx.run(
            "CREATE (r:Revision {id: $id, run_id: $run_id, parent_id: $parent_id, "
            "created_at: $created_at, payload: $payload})",
            id=revision.id,
            run_id=revision.run_id,
            parent_id=revision.parent_id,
            created_at=revision.created_at.isoformat(),
            payload=_dump(revision),
        )
        for index, change in enumerate(revision.changes):
            change_id = stable_id("change", revision.id, index, change.resource_id)
            await tx.run(
                "MATCH (r:Revision {id: $revision_id}) "
                "CREATE (c:RevisionChange {id: $id, resource_type: $resource_type, "
                "resource_id: $resource_id, action: $action, payload: $payload}) "
                "MERGE (r)-[:CHANGED]->(c)",
                revision_id=revision.id,
                id=change_id,
                resource_type=change.resource_type,
                resource_id=change.resource_id,
                action=change.action,
                payload=_dump(change),
            )
            label = {
                "entity": "Entity",
                "claim": "Claim",
                "conflict": "ConflictSet",
                "entity_operation": "EntityOperation",
                "media_content": "MediaContent",
                "media_occurrence": "MediaOccurrence",
                "media_relation": "MediaRelation",
                "visual_assertion": "VisualAssertion",
            }[change.resource_type]
            await tx.run(
                f"MATCH (c:RevisionChange {{id: $change_id}}), "
                f"(n:{label} {{id: $resource_id}}) MERGE (c)-[:TARGETS]->(n)",
                change_id=change_id,
                resource_id=change.resource_id,
            )
        await tx.run(
            "MATCH (h:GraphHead {id: 'singleton'}) SET h.latest_id=$revision_id",
            revision_id=revision.id,
        )

    async def commit(self, transaction: GraphCommit) -> None:
        bind_commit_provenance(transaction)
        transaction = transaction.model_copy(deep=True)
        if self.evidence_store is None and transaction.media_contents:
            raise GraphIntegrityError("media commit requires an evidence store")
        if self.evidence_store is not None:
            from hashlib import sha256

            for content in transaction.media_contents:
                payload = await self.evidence_store.get_blob(content.blob_hash)
                if sha256(payload).hexdigest() != content.content_hash:
                    raise GraphIntegrityError(
                        f"media content hash verification failed: {content.id}"
                    )
            for occurrence in transaction.media_occurrences:
                if not await self.evidence_store.verify(occurrence.evidence_id):
                    raise GraphIntegrityError(
                        f"media occurrence evidence is invalid: {occurrence.id}"
                    )
        await self._ensure_schema()
        async with self.driver.session(database=self.database) as session:
            await session.execute_write(self._commit_tx, transaction)

    async def _list_payloads(self, label: str, limit: int | None = None) -> list[str]:
        query = f"MATCH (n:{label}) RETURN n.payload AS payload"
        parameters: dict[str, Any] = {}
        if limit is not None:
            query += " ORDER BY n.created_at DESC LIMIT $limit"
            parameters["limit"] = limit
        async with self.driver.session(database=self.database) as session:
            result = await session.run(query, **parameters)
            records = await result.data()
        return [record["payload"] for record in records]

    async def list_entities(self) -> list[CanonicalEntity]:
        return [_load(item, CanonicalEntity) for item in await self._list_payloads("Entity")]

    async def get_entity(self, entity_id: str) -> CanonicalEntity | None:
        return await self._get("Entity", entity_id, CanonicalEntity)

    async def search_entities(
        self,
        vector: list[float],
        entity_type: str,
        top_k: int,
        model_fingerprint: str | None = None,
    ) -> list[tuple[CanonicalEntity, float]]:
        if not vector or top_k < 1:
            return []
        await self._ensure_schema()
        if len(vector) == 1024:
            async with self.driver.session(database=self.database) as session:
                count_result = await session.run(
                    "MATCH (n:Entity) WHERE n.embedding_dimension = 1024 "
                    "AND n.embedding IS NOT NULL RETURN count(n) AS count"
                )
                count_record = await count_result.single()
                total = int(count_record["count"]) if count_record is not None else 0
                if total == 0:
                    return []
                candidate_limit = min(total, max(top_k * 5, top_k))
                while True:
                    result = await session.run(
                        "CALL db.index.vector.queryNodes("
                        "'entity_embedding_bge_m3', $candidate_limit, $vector) "
                        "YIELD node, score "
                        "WHERE node.entity_type = $entity_type AND coalesce(node.active, true) "
                        "AND ($model IS NULL OR node.embedding_model = $model) "
                        "RETURN node.payload AS payload, node.embedding AS embedding, score",
                        candidate_limit=candidate_limit,
                        vector=vector,
                        entity_type=entity_type,
                        model=model_fingerprint,
                    )
                    records = await result.data()
                    if len(records) >= top_k or candidate_limit >= total:
                        break
                    candidate_limit = min(total, candidate_limit * 2)
            matches: list[tuple[CanonicalEntity, float]] = []
            query_norm = math.sqrt(sum(value * value for value in vector)) or 1.0
            for record in records:
                candidate = [float(value) for value in record["embedding"]]
                candidate_norm = math.sqrt(sum(value * value for value in candidate)) or 1.0
                score = sum(left * right for left, right in zip(vector, candidate, strict=True)) / (
                    query_norm * candidate_norm
                )
                matches.append(
                    (_load(record["payload"], CanonicalEntity), max(-1.0, min(1.0, score)))
                )
            return sorted(matches, key=lambda item: (-round(item[1], 12), item[0].id))[:top_k]
        async with self.driver.session(database=self.database) as session:
            result = await session.run(
                "MATCH (n:Entity {entity_type: $entity_type}) "
                "WHERE coalesce(n.active, true) AND n.embedding IS NOT NULL "
                "AND ($model IS NULL OR n.embedding_model = $model) "
                "RETURN n.payload AS payload, n.embedding AS embedding",
                entity_type=entity_type,
                model=model_fingerprint,
            )
            records = await result.data()
        query_norm = math.sqrt(sum(value * value for value in vector)) or 1.0
        matches = []
        for record in records:
            candidate = [float(value) for value in record["embedding"]]
            if len(candidate) != len(vector):
                continue
            candidate_norm = math.sqrt(sum(value * value for value in candidate)) or 1.0
            score = sum(left * right for left, right in zip(vector, candidate, strict=True)) / (
                query_norm * candidate_norm
            )
            matches.append((_load(record["payload"], CanonicalEntity), score))
        return sorted(matches, key=lambda item: (-round(item[1], 12), item[0].id))[:top_k]

    async def list_entity_embeddings(self) -> list[EntityEmbedding]:
        async with self.driver.session(database=self.database) as session:
            result = await session.run(
                "MATCH (n:Entity) WHERE n.embedding IS NOT NULL "
                "RETURN n.id AS entity_id, n.embedding_model AS model, "
                "n.embedding_text_hash AS text_hash, n.embedding_dimension AS dimension, "
                "n.embedding AS vector"
            )
            records = await result.data()
        return [
            EntityEmbedding(
                entity_id=record["entity_id"],
                model_fingerprint=record["model"],
                text_hash=record["text_hash"],
                dimension=int(record["dimension"]),
                vector=[float(value) for value in record["vector"]],
            )
            for record in records
        ]

    async def upsert_entity_embeddings(self, embeddings: list[EntityEmbedding]) -> None:
        await self._ensure_schema()
        async with self.driver.session(database=self.database) as session:

            async def write(tx: Any) -> None:
                for embedding in embeddings:
                    result = await tx.run(
                        "MATCH (n:Entity {id: $entity_id}) "
                        "SET n.embedding=$vector, n.embedding_model=$model, "
                        "n.embedding_text_hash=$text_hash, "
                        "n.embedding_dimension=$dimension RETURN n.id AS id",
                        entity_id=embedding.entity_id,
                        vector=embedding.vector,
                        model=embedding.model_fingerprint,
                        text_hash=embedding.text_hash,
                        dimension=embedding.dimension,
                    )
                    if await result.single() is None:
                        raise GraphIntegrityError(
                            f"embedding references missing entity: {embedding.entity_id}"
                        )

            await session.execute_write(write)

    async def list_claims(self) -> list[Claim]:
        return [_load(item, Claim) for item in await self._list_payloads("Claim")]

    async def list_media_occurrences(self) -> list[GraphMediaOccurrence]:
        return [
            _load(item, GraphMediaOccurrence)
            for item in await self._list_payloads("MediaOccurrence")
        ]

    async def list_media_contents(self) -> list[GraphMediaContent]:
        return [
            _load(item, GraphMediaContent) for item in await self._list_payloads("MediaContent")
        ]

    async def get_media_occurrence(self, occurrence_id: str) -> GraphMediaOccurrence | None:
        return await self._get("MediaOccurrence", occurrence_id, GraphMediaOccurrence)

    async def list_media_relations(self) -> list[GraphMediaRelation]:
        return [
            _load(item, GraphMediaRelation) for item in await self._list_payloads("MediaRelation")
        ]

    async def list_visual_assertions(self) -> list[VisualAssertion]:
        return [
            _load(item, VisualAssertion) for item in await self._list_payloads("VisualAssertion")
        ]

    async def latest_revision(self) -> GraphRevision | None:
        revisions = await self.list_revisions(limit=1)
        return revisions[0] if revisions else None

    async def list_revisions(self, limit: int = 50) -> list[GraphRevision]:
        return [
            _load(item, GraphRevision)
            for item in await self._list_payloads("Revision", max(limit, 0))
        ]

    async def _get(self, label: str, resource_id: str, model: Any) -> Any | None:
        async with self.driver.session(database=self.database) as session:
            result = await session.run(
                f"MATCH (n:{label} {{id: $id}}) RETURN n.payload AS payload", id=resource_id
            )
            record = await result.single()
        return _load(record["payload"], model) if record is not None else None

    async def get_claim(self, claim_id: str) -> Claim | None:
        return await self._get("Claim", claim_id, Claim)

    async def get_evidence(self, evidence_id: str) -> EvidenceRef | None:
        return await self._get("Evidence", evidence_id, EvidenceRef)

    async def get_neighborhood(self, entity_id: str, depth: int = 1) -> GraphNeighborhood:
        if depth < 1 or depth > 3:
            raise ValueError("depth must be between 1 and 3")
        async with self.driver.session(database=self.database) as session:
            hops = depth * 2
            result = await session.run(
                "MATCH (center:Entity {id: $id}) "
                f"OPTIONAL MATCH p=(center)-[:SUBJECT|OBJECT*1..{hops}]-(n) "
                "WHERE all(node IN nodes(p) WHERE NOT node:Claim OR node.tx_to IS NULL) "
                "WITH center, "
                "collect(DISTINCT CASE WHEN n:Entity THEN n.payload END) AS entities, "
                "collect(DISTINCT CASE WHEN n:Claim THEN n.payload END) AS claims "
                "RETURN center.payload AS center, entities, claims",
                id=entity_id,
            )
            record = await result.single()
        if record is None:
            raise KeyError(f"entity not found: {entity_id}")
        entities = [_load(record["center"], CanonicalEntity)]
        entities.extend(_load(item, CanonicalEntity) for item in record["entities"] if item)
        return GraphNeighborhood(
            center_entity_id=entity_id,
            depth=depth,
            entities=list({item.id: item for item in entities}.values()),
            claims=[_load(item, Claim) for item in record["claims"] if item],
        )

    async def diff_revisions(self, from_id: str, to_id: str) -> RevisionDiff:
        revisions = list(reversed(await self.list_revisions(limit=10_000)))
        positions = {revision.id: index for index, revision in enumerate(revisions)}
        if from_id not in positions or to_id not in positions:
            raise KeyError("revision not found")
        if positions[from_id] > positions[to_id]:
            raise ValueError("from revision must not be newer than to revision")
        selected = revisions[positions[from_id] + 1 : positions[to_id] + 1]
        return RevisionDiff(
            from_revision_id=from_id,
            to_revision_id=to_id,
            changes=[change for revision in selected for change in revision.changes],
            legacy_id_only=any(not revision.changes for revision in selected),
            entity_ids=sorted({item for revision in selected for item in revision.entity_ids}),
            claim_ids=sorted({item for revision in selected for item in revision.claim_ids}),
            conflict_ids=sorted({item for revision in selected for item in revision.conflict_ids}),
            media_content_ids=sorted(
                {item for revision in selected for item in revision.media_content_ids}
            ),
            media_occurrence_ids=sorted(
                {item for revision in selected for item in revision.media_occurrence_ids}
            ),
            media_relation_ids=sorted(
                {item for revision in selected for item in revision.media_relation_ids}
            ),
            visual_assertion_ids=sorted(
                {item for revision in selected for item in revision.visual_assertion_ids}
            ),
        )

    async def rollback_revision(self, revision_id: str) -> GraphRevision:
        target = await self._get("Revision", revision_id, GraphRevision)
        if target is None:
            raise KeyError(f"revision not found: {revision_id}")
        if not target.changes:
            raise GraphIntegrityError("legacy revision has no snapshots and cannot be rolled back")
        latest = await self.latest_revision()
        assert latest is not None
        if latest.run_id == f"rollback:{revision_id}":
            return latest
        entities: list[CanonicalEntity] = []
        claims: list[Claim] = []
        conflicts: list[ConflictSet] = []
        entity_operations: list[EntityOperation] = []
        media_contents: list[GraphMediaContent] = []
        media_occurrences: list[GraphMediaOccurrence] = []
        media_relations: list[GraphMediaRelation] = []
        visual_assertions: list[VisualAssertion] = []
        current_claims = {item.id: item for item in await self.list_claims()}
        inverse: list[GraphChange] = []
        now = datetime.now(UTC)
        rollback_order = {
            "entity_operation": 0,
            "claim": 1,
            "conflict": 2,
            "entity": 3,
            "visual_assertion": 0,
            "media_relation": 0,
            "media_occurrence": 1,
            "media_content": 4,
        }
        ordered_changes = sorted(
            reversed(target.changes),
            key=lambda item: rollback_order[item.resource_type],
        )
        for change in ordered_changes:
            current_payload: dict[str, Any] | None
            replacement_payload: dict[str, Any]
            if change.resource_type == "entity":
                current_entity = await self._get("Entity", change.resource_id, CanonicalEntity)
                if change.action == "create" and current_entity is not None:
                    if any(
                        item.tx_to is None
                        and change.resource_id in {item.subject_id, item.object_entity_id}
                        for item in current_claims.values()
                    ):
                        raise GraphIntegrityError(
                            f"entity {change.resource_id} still has active claim references"
                        )
                    replacement_entity = current_entity.model_copy(update={"active": False})
                    action = "close"
                elif change.before is not None:
                    replacement_entity = CanonicalEntity.model_validate(change.before)
                    action = "restore"
                else:
                    continue
                entities.append(replacement_entity)
                current_payload = current_entity.model_dump(mode="json") if current_entity else None
                replacement_payload = replacement_entity.model_dump(mode="json")
            elif change.resource_type == "claim":
                current_claim = current_claims.get(change.resource_id)
                if change.action == "create" and current_claim is not None:
                    replacement_claim = current_claim.model_copy(update={"tx_to": now})
                    action = "close"
                elif change.before is not None:
                    replacement_claim = Claim.model_validate(change.before)
                    action = "restore"
                else:
                    continue
                claims.append(replacement_claim)
                current_claims[replacement_claim.id] = replacement_claim
                current_payload = current_claim.model_dump(mode="json") if current_claim else None
                replacement_payload = replacement_claim.model_dump(mode="json")
            elif change.resource_type == "conflict":
                current_conflict = await self._get("ConflictSet", change.resource_id, ConflictSet)
                if change.action == "create" and current_conflict is not None:
                    replacement_conflict = current_conflict.model_copy(
                        update={"status": "resolved"}
                    )
                    action = "close"
                elif change.before is not None:
                    replacement_conflict = ConflictSet.model_validate(change.before)
                    action = "restore"
                else:
                    continue
                conflicts.append(replacement_conflict)
                current_payload = (
                    current_conflict.model_dump(mode="json") if current_conflict else None
                )
                replacement_payload = replacement_conflict.model_dump(mode="json")
            elif change.resource_type == "entity_operation":
                current_operation = await self._get(
                    "EntityOperation", change.resource_id, EntityOperation
                )
                if change.action == "create" and current_operation is not None:
                    replacement_operation = current_operation.model_copy(
                        update={"status": "rolled_back"}
                    )
                    action = "close"
                elif change.before is not None:
                    replacement_operation = EntityOperation.model_validate(change.before)
                    action = "restore"
                else:
                    continue
                entity_operations.append(replacement_operation)
                current_payload = (
                    current_operation.model_dump(mode="json") if current_operation else None
                )
                replacement_payload = replacement_operation.model_dump(mode="json")
            elif change.resource_type == "media_content":
                current_content = await self._get(
                    "MediaContent", change.resource_id, GraphMediaContent
                )
                if current_content is None:
                    continue
                if change.action == "create":
                    replacement_content = current_content
                    action = "close"
                elif change.before is not None:
                    replacement_content = GraphMediaContent.model_validate(change.before)
                    action = "restore"
                else:
                    continue
                media_contents.append(replacement_content)
                current_payload = current_content.model_dump(mode="json")
                replacement_payload = replacement_content.model_dump(mode="json")
            elif change.resource_type == "media_occurrence":
                current_occurrence = await self._get(
                    "MediaOccurrence", change.resource_id, GraphMediaOccurrence
                )
                if change.action == "create" and current_occurrence is not None:
                    replacement_occurrence = current_occurrence.model_copy(
                        update={"active": False, "tx_to": now}
                    )
                    action = "close"
                elif change.before is not None:
                    replacement_occurrence = GraphMediaOccurrence.model_validate(change.before)
                    action = "restore"
                else:
                    continue
                media_occurrences.append(replacement_occurrence)
                current_payload = (
                    current_occurrence.model_dump(mode="json") if current_occurrence else None
                )
                replacement_payload = replacement_occurrence.model_dump(mode="json")
            elif change.resource_type == "media_relation":
                current_relation = await self._get(
                    "MediaRelation", change.resource_id, GraphMediaRelation
                )
                if change.action == "create" and current_relation is not None:
                    replacement_relation = current_relation.model_copy(
                        update={"active": False, "tx_to": now}
                    )
                    action = "close"
                elif change.before is not None:
                    replacement_relation = GraphMediaRelation.model_validate(change.before)
                    action = "restore"
                else:
                    continue
                media_relations.append(replacement_relation)
                current_payload = (
                    current_relation.model_dump(mode="json") if current_relation else None
                )
                replacement_payload = replacement_relation.model_dump(mode="json")
            else:
                current_assertion = await self._get(
                    "VisualAssertion", change.resource_id, VisualAssertion
                )
                if change.action == "create" and current_assertion is not None:
                    replacement_assertion = current_assertion.model_copy(
                        update={"active": False, "tx_to": now}
                    )
                    action = "close"
                elif change.before is not None:
                    replacement_assertion = VisualAssertion.model_validate(change.before)
                    action = "restore"
                else:
                    continue
                visual_assertions.append(replacement_assertion)
                current_payload = (
                    current_assertion.model_dump(mode="json") if current_assertion else None
                )
                replacement_payload = replacement_assertion.model_dump(mode="json")
            if current_payload != change.after:
                raise GraphIntegrityError("STALE_ROLLBACK_RESOURCE: re-preview required")
            inverse.append(
                GraphChange(
                    resource_type=change.resource_type,
                    resource_id=change.resource_id,
                    action=action,
                    before=current_payload,
                    after=replacement_payload,
                )
            )
        revision = GraphRevision(
            id=stable_id("revision", "rollback", revision_id, latest.id),
            run_id=f"rollback:{revision_id}",
            parent_id=latest.id,
            entity_ids=[item.id for item in entities],
            claim_ids=[item.id for item in claims],
            conflict_ids=[item.id for item in conflicts],
            media_content_ids=[item.id for item in media_contents],
            media_occurrence_ids=[item.id for item in media_occurrences],
            media_relation_ids=[item.id for item in media_relations],
            visual_assertion_ids=[item.id for item in visual_assertions],
            changes=inverse,
            created_at=now,
        )
        context = context_for_claims(
            await self.list_revisions(limit=100000), {c.id for c in claims}
        )
        revision.validation_context = context
        await self.commit(
            GraphCommit(
                entities=entities,
                claims=claims,
                conflicts=conflicts,
                entity_operations=entity_operations,
                media_contents=media_contents,
                media_occurrences=media_occurrences,
                media_relations=media_relations,
                visual_assertions=visual_assertions,
                revision=revision,
                validation_context=context,
            )
        )
        return revision

    async def close(self) -> None:
        await self.driver.close()
