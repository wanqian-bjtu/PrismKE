"""Deterministic entity linking and cross-document deduplication."""

from __future__ import annotations

from dataclasses import dataclass

from prismke.core.errors import SchemaValidationError
from prismke.core.ids import stable_id
from prismke.domain import CanonicalEntity, EntityMention, SchemaIndex, normalize_label


@dataclass(frozen=True)
class ResolutionBundle:
    entities: list[CanonicalEntity]
    mention_to_entity: dict[str, str]
    review_reasons: dict[str, list[str]]


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
