"""Schema contracts and canonical vocabulary lookup."""

from __future__ import annotations

import json
from pathlib import Path

import yaml
from pydantic import BaseModel, Field, ValidationError, model_validator

from src.core.errors import SchemaValidationError


def normalize_label(value: str) -> str:
    return " ".join(value.casefold().replace("_", " ").split())


class EntityTypeDef(BaseModel):
    id: str
    aliases: list[str] = Field(default_factory=list)


class RelationDef(BaseModel):
    id: str
    aliases: list[str] = Field(default_factory=list)
    domain: list[str] = Field(default_factory=list)
    range: list[str] = Field(default_factory=list)
    functional: bool = False
    min_cardinality: int = Field(default=0, ge=0)
    max_cardinality: int | None = Field(default=None, ge=1)
    symmetric: bool = False
    inverse_relation: str | None = None

    @model_validator(mode="after")
    def normalize_cardinality(self) -> RelationDef:
        if self.functional:
            if self.max_cardinality not in (None, 1):
                raise ValueError("functional relations require max_cardinality=1")
            self.max_cardinality = 1
        if self.max_cardinality is not None and self.min_cardinality > self.max_cardinality:
            raise ValueError("min_cardinality must not exceed max_cardinality")
        if self.symmetric and self.inverse_relation not in (None, self.id):
            raise ValueError("a symmetric relation can only be its own inverse")
        return self


class EntityCatalogItem(BaseModel):
    id: str
    name: str
    type: str
    aliases: list[str] = Field(default_factory=list)


class OutputSchema(BaseModel):
    schema_id: str
    version: str
    strict: bool = True
    entity_types: list[EntityTypeDef]
    relations: list[RelationDef]
    entity_catalog: list[EntityCatalogItem] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_references(self) -> OutputSchema:
        type_ids = [item.id for item in self.entity_types]
        relation_ids = [item.id for item in self.relations]
        if len(type_ids) != len(set(type_ids)):
            raise ValueError("entity type ids must be unique")
        if len(relation_ids) != len(set(relation_ids)):
            raise ValueError("relation ids must be unique")
        known_types = set(type_ids)
        known_relations = {item.id: item for item in self.relations}
        for relation in self.relations:
            unknown_types = (set(relation.domain) | set(relation.range)) - known_types
            if unknown_types:
                raise ValueError(
                    f"relation {relation.id} references unknown types: {sorted(unknown_types)}"
                )
            if relation.inverse_relation is not None:
                inverse = known_relations.get(relation.inverse_relation)
                if inverse is None:
                    raise ValueError(f"relation {relation.id} references unknown inverse relation")
                if inverse.inverse_relation != relation.id:
                    raise ValueError(
                        f"inverse relation {inverse.id} must point back to {relation.id}"
                    )
        for entity in self.entity_catalog:
            if entity.type not in known_types:
                raise ValueError(f"catalog entity {entity.id} has unknown type {entity.type}")
        return self


def load_schema(path: Path) -> OutputSchema:
    try:
        raw = path.read_text(encoding="utf-8")
        payload = json.loads(raw) if path.suffix.lower() == ".json" else yaml.safe_load(raw)
        return OutputSchema.model_validate(payload)
    except (OSError, ValueError, ValidationError, yaml.YAMLError) as exc:
        raise SchemaValidationError(f"invalid schema {path}: {exc}") from exc


class SchemaIndex:
    def __init__(self, schema: OutputSchema) -> None:
        self.schema = schema
        self._types = {
            normalize_label(name): item.id
            for item in schema.entity_types
            for name in [item.id, *item.aliases]
        }
        self._relations = {
            normalize_label(name): item
            for item in schema.relations
            for name in [item.id, *item.aliases]
        }
        self._relations_by_id = {item.id: item for item in schema.relations}
        self._entities = {
            (normalize_label(name), item.type): item
            for item in schema.entity_catalog
            for name in [item.name, *item.aliases]
        }

    def entity_type(self, value: str) -> str | None:
        return self._types.get(normalize_label(value))

    def relation(self, value: str) -> RelationDef | None:
        return self._relations.get(normalize_label(value))

    def relation_by_id(self, relation_id: str) -> RelationDef | None:
        return self._relations_by_id.get(relation_id)

    def catalog_entity(self, name: str, entity_type: str) -> EntityCatalogItem | None:
        return self._entities.get((normalize_label(name), entity_type))
