"""Neo4j graph store using one managed transaction per GraphCommit."""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime
from typing import Any

import orjson

from prismke.core.errors import GraphIntegrityError
from prismke.core.ids import stable_id
from prismke.domain import (
    CanonicalEntity,
    Claim,
    ConflictSet,
    EvidenceRef,
    GraphChange,
    GraphCommit,
    GraphHealth,
    GraphNeighborhood,
    GraphRevision,
    RevisionDiff,
)


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
    ) -> None:
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
                    "Claim",
                    "ConflictSet",
                    "Revision",
                    "RevisionChange",
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
                ]
            )
            async with self.driver.session(database=self.database) as session:
                for statement in statements:
                    await session.run(statement)
            self._schema_ready = True

    async def healthcheck(self) -> GraphHealth:
        try:
            await self.driver.verify_connectivity()
            await self._ensure_schema()
        except Exception as exc:
            return GraphHealth(backend="neo4j", healthy=False, message=type(exc).__name__)
        return GraphHealth(backend="neo4j", healthy=True)

    @staticmethod
    async def _commit_tx(tx: Any, transaction: GraphCommit) -> None:
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
            }[change.resource_type]
            await tx.run(
                f"MATCH (c:RevisionChange {{id: $change_id}}), "
                f"(n:{label} {{id: $resource_id}}) MERGE (c)-[:TARGETS]->(n)",
                change_id=change_id,
                resource_id=change.resource_id,
            )

    async def commit(self, transaction: GraphCommit) -> None:
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

    async def list_claims(self) -> list[Claim]:
        return [_load(item, Claim) for item in await self._list_payloads("Claim")]

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
            result = await session.run(
                "MATCH (center:Entity {id: $id}) "
                "OPTIONAL MATCH path=(center)<-[:SUBJECT|OBJECT]-(:Claim)"
                "-[:SUBJECT|OBJECT]->(e:Entity) "
                "WHERE length(path) <= $path_depth "
                "WITH center, collect(DISTINCT e.payload) AS entities, "
                "collect(DISTINCT nodes(path)[1].payload) AS claims "
                "RETURN center.payload AS center, entities, claims",
                id=entity_id,
                path_depth=depth * 2,
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
        )

    async def rollback_revision(self, revision_id: str) -> GraphRevision:
        target = await self._get("Revision", revision_id, GraphRevision)
        if target is None:
            raise KeyError(f"revision not found: {revision_id}")
        if not target.changes:
            raise GraphIntegrityError("legacy revision has no snapshots and cannot be rolled back")
        latest = await self.latest_revision()
        assert latest is not None
        entities: list[CanonicalEntity] = []
        claims: list[Claim] = []
        conflicts: list[ConflictSet] = []
        inverse: list[GraphChange] = []
        now = datetime.now(UTC)
        for change in reversed(target.changes):
            current_payload: dict[str, Any] | None
            replacement_payload: dict[str, Any]
            if change.resource_type == "entity":
                current_entity = await self._get("Entity", change.resource_id, CanonicalEntity)
                if change.action == "create" and current_entity is not None:
                    replacement_entity = current_entity.model_copy(update={"active": False})
                    action = "close"
                elif change.before is not None:
                    replacement_entity = CanonicalEntity.model_validate(change.before)
                    action = "restore"
                else:
                    continue
                entities.append(replacement_entity)
                current_payload = (
                    current_entity.model_dump(mode="json") if current_entity else None
                )
                replacement_payload = replacement_entity.model_dump(mode="json")
            elif change.resource_type == "claim":
                current_claim = await self._get("Claim", change.resource_id, Claim)
                if change.action == "create" and current_claim is not None:
                    replacement_claim = current_claim.model_copy(update={"tx_to": now})
                    action = "close"
                elif change.before is not None:
                    replacement_claim = Claim.model_validate(change.before)
                    action = "restore"
                else:
                    continue
                claims.append(replacement_claim)
                current_payload = current_claim.model_dump(mode="json") if current_claim else None
                replacement_payload = replacement_claim.model_dump(mode="json")
            else:
                current_conflict = await self._get(
                    "ConflictSet", change.resource_id, ConflictSet
                )
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
            changes=inverse,
            created_at=now,
        )
        await self.commit(
            GraphCommit(
                entities=entities,
                claims=claims,
                conflicts=conflicts,
                revision=revision,
            )
        )
        return revision

    async def close(self) -> None:
        await self.driver.close()
