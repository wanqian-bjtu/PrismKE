from __future__ import annotations

import os
from pathlib import Path

import pytest


def pytest_sessionstart(session: pytest.Session) -> None:
    """Reject live graph tests unless the dedicated Neo4j instance is proven isolated."""
    del session
    if os.getenv("PRISMKE_TEST_NEO4J") != "1":
        return
    expected_workspace = Path(__file__).resolve().parents[1] / "runtime/review-neo4j-test"
    workspace = os.getenv("PRISMKE_TEST_NEO4J_WORKSPACE")
    marker = os.getenv("PRISMKE_TEST_NEO4J_INSTANCE_ID")
    uri = os.getenv("PRISMKE_NEO4J_URI")
    if (
        uri != "bolt://127.0.0.1:17687"
        or not workspace
        or Path(workspace).resolve() != expected_workspace.resolve()
        or not marker
    ):
        raise pytest.UsageError("live Neo4j tests require the isolated test runner")

    from neo4j import GraphDatabase

    try:
        auth = (os.getenv("PRISMKE_NEO4J_USER", "neo4j"), os.getenv("PRISMKE_NEO4J_PASSWORD", ""))
        with (
            GraphDatabase.driver(uri, auth=auth) as driver,
            driver.session(database="neo4j") as connection,
        ):
            config = connection.run(
                "CALL dbms.listConfig() YIELD name, value "
                "WHERE name = 'server.directories.data' RETURN value"
            ).single()
            record = connection.run(
                "MATCH (n:PrismKETestInstance {id: $id}) RETURN n.workspace AS workspace",
                id=marker,
            ).single()
        actual_data = Path(str(config["value"])).resolve() if config else None
        marked_workspace = Path(str(record["workspace"])).resolve() if record else None
        if (
            actual_data != (expected_workspace / "data").resolve()
            or marked_workspace != expected_workspace.resolve()
        ):
            raise ValueError("test instance marker or data directory mismatch")
    except Exception as exc:
        raise pytest.UsageError("live Neo4j target is not the dedicated test instance") from exc


@pytest.fixture(autouse=True)
def isolate_default_graph_backend(monkeypatch: pytest.MonkeyPatch) -> None:
    """Unit tests never inherit a developer machine's live graph backend."""
    monkeypatch.setenv("PRISMKE_GRAPH_STORE", "json")


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
