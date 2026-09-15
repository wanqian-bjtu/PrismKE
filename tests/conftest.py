from __future__ import annotations

from pathlib import Path

import pytest


@pytest.fixture
def schema_path(tmp_path: Path) -> Path:
    path = tmp_path / "schema.yaml"
    path.write_text(
        """
schema_id: test
version: "1"
strict: true
entity_types:
  - id: Software
    aliases: [software]
  - id: Organization
    aliases: [organization]
relations:
  - id: developed_by
    aliases: [created_by]
    domain: [Software]
    range: [Organization]
entity_catalog:
  - id: entity:prismke
    name: PrismKE
    type: Software
    aliases: [Prism KE]
""".strip(),
        encoding="utf-8",
    )
    return path
