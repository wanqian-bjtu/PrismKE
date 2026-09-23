"""Entity embedding index preparation and idempotent rebuilds."""

from __future__ import annotations

import math

from pydantic import BaseModel

from src.core.ids import canonical_hash
from src.domain import EntityEmbedding
from src.governance.entity_resolution import entity_embedding_text
from src.persistence.base import GraphStore
from src.providers.base import EmbeddingProvider


class EntityIndexReport(BaseModel):
    backend: str
    model_fingerprint: str
    active_entities: int
    missing_or_outdated: int
    batches: int
    dimension: int | None = None
    dry_run: bool
    indexed: int = 0


async def rebuild_entity_index(
    graph_store: GraphStore,
    provider: EmbeddingProvider,
    *,
    backend: str,
    batch_size: int,
    dry_run: bool,
) -> EntityIndexReport:
    if provider.fingerprint() == "embedding:disabled":
        raise ValueError("entity index rebuild requires mock or bge-m3 embedding provider")
    active = [item for item in await graph_store.list_entities() if item.active]
    existing = {item.entity_id: item for item in await graph_store.list_entity_embeddings()}
    pending = []
    for entity in active:
        text = entity_embedding_text(entity)
        embedding = existing.get(entity.id)
        if (
            embedding is None
            or embedding.model_fingerprint != provider.fingerprint()
            or embedding.text_hash != canonical_hash(text)
        ):
            pending.append((entity, text))
    report = EntityIndexReport(
        backend=backend,
        model_fingerprint=provider.fingerprint(),
        active_entities=len(active),
        missing_or_outdated=len(pending),
        batches=math.ceil(len(pending) / batch_size) if pending else 0,
        dimension=existing[next(iter(existing))].dimension if existing else None,
        dry_run=dry_run,
    )
    if dry_run:
        return report
    indexed = 0
    for offset in range(0, len(pending), batch_size):
        batch = pending[offset : offset + batch_size]
        vectors = await provider.encode([text for _, text in batch])
        embeddings = [
            EntityEmbedding(
                entity_id=entity.id,
                model_fingerprint=provider.fingerprint(),
                text_hash=canonical_hash(text),
                dimension=len(vector),
                vector=vector,
            )
            for (entity, text), vector in zip(batch, vectors, strict=True)
        ]
        await graph_store.upsert_entity_embeddings(embeddings)
        indexed += len(embeddings)
        if embeddings:
            report.dimension = embeddings[0].dimension
    report.indexed = indexed
    return report
