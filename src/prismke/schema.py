"""Schema loading and canonical vocabulary lookup."""

from __future__ import annotations

import json
from pathlib import Path

import yaml
from pydantic import ValidationError

from prismke.errors import SchemaValidationError
from prismke.models import EntityCatalogItem, OutputSchema, RelationDef


def normalize_label(value: str) -> str:
    return " ".join(value.casefold().replace("_", " ").split())


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
        self._entities = {
            (normalize_label(name), item.type): item
            for item in schema.entity_catalog
            for name in [item.name, *item.aliases]
        }

    def entity_type(self, value: str) -> str | None:
        return self._types.get(normalize_label(value))

    def relation(self, value: str) -> RelationDef | None:
        return self._relations.get(normalize_label(value))

    def catalog_entity(self, name: str, entity_type: str) -> EntityCatalogItem | None:
        return self._entities.get((normalize_label(name), entity_type))
