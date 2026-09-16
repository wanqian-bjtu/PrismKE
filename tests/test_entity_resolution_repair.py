from pathlib import Path
from typing import Any

import pytest

from prismke.domain import CanonicalEntity, EntityMention, EntityTypeDef, OutputSchema, SchemaIndex
from prismke.governance.entity_resolution import SemanticEntityResolver


class ControlledProvider:
    def __init__(self, name: str, similarity: float) -> None:
        self.name = name
        self.similarity = similarity

    def fingerprint(self) -> str:
        return "embedding:controlled:test"

    async def encode(self, texts: list[str]) -> list[list[float]]:
        return [
            [self.similarity, (1 - self.similarity**2) ** 0.5] if text == self.name else [1.0, 0.0]
            for text in texts
        ]


class ControlledGraph:
    def __init__(self, entity: CanonicalEntity, score: float) -> None:
        self.entity = entity
        self.score = score
        self.search_calls = 0

    async def list_entities(self) -> list[CanonicalEntity]:
        return [self.entity]

    async def search_entities(self, *args: Any) -> list[tuple[CanonicalEntity, float]]:
        self.search_calls += 1
        return [(self.entity, self.score)]

    async def get_neighborhood(self, *args: Any) -> Any:
        raise KeyError("no claim neighborhood")


def resolver(graph: Any, provider: Any) -> SemanticEntityResolver:
    schema = SchemaIndex(
        OutputSchema(
            schema_id="repair-test",
            version="1",
            strict=True,
            entity_types=[EntityTypeDef(id="Organization")],
            relations=[],
        )
    )
    return SemanticEntityResolver(schema, graph, provider, run_id="repair-test")


def mention(name: str, identity: str = "M1", context: str = "") -> EntityMention:
    return EntityMention(
        id=identity,
        name=name,
        entity_type="Organization",
        context=context,
        evidence_ids=[f"evidence:{identity}"],
    )


@pytest.mark.asyncio
@pytest.mark.parametrize("case", range(20))
async def test_cross_script_positive_and_negative_groups(case: int) -> None:
    entity = CanonicalEntity(id="E1", name=f"Research Institute {case}", entity_type="Organization")
    positive = case < 10
    graph = ControlledGraph(entity, 0.0)
    result = await resolver(
        graph, ControlledProvider(entity.name, 0.8 if positive else -0.8)
    ).resolve([mention(f"研究机构{case}")])
    decision = result.decisions[0]
    assert decision.method == ("review" if positive else "nil")
    assert decision.candidates[0].semantic_name_score == pytest.approx(0.8 if positive else -0.8)
    assert graph.search_calls == 2
    if positive:
        assert "possible_duplicate_nil_protection" in decision.reasons


@pytest.mark.asyncio
async def test_strong_context_support_prevents_nil_without_lexical_match() -> None:
    entity = CanonicalEntity(
        id="E1", name="OpenTool", entity_type="Organization", context_summary="Shared context"
    )
    result = await resolver(
        ControlledGraph(entity, 0.98), ControlledProvider(entity.name, -0.8)
    ).resolve([mention("工具", context="Shared context")])
    assert result.decisions[0].method == "review"
    assert "possible_duplicate_nil_protection" in result.decisions[0].reasons


@pytest.mark.asyncio
async def test_unselected_nil_draft_does_not_pollute_next_exact_match() -> None:
    entity = CanonicalEntity(
        id="E1", name="International Research Labs", entity_type="Organization"
    )
    result = await resolver(
        ControlledGraph(entity, 1.0), ControlledProvider(entity.name, 0.99)
    ).resolve(
        [
            mention("International Research Lab", "M1"),
            mention("International Research Lab", "M2"),
        ]
    )
    assert [decision.method for decision in result.decisions] == ["vector", "exact"]
    assert result.mention_to_entity == {"M1": "E1", "M2": "E1"}
    assert [entity.id for entity in result.entities] == ["E1"]


@pytest.mark.asyncio
async def test_review_draft_does_not_become_exact_candidate() -> None:
    entity = CanonicalEntity(id="E1", name="Institute", entity_type="Organization")
    result = await resolver(
        ControlledGraph(entity, 0.0), ControlledProvider(entity.name, 0.8)
    ).resolve(
        [
            mention("机构", "M1"),
            mention("机构", "M2"),
        ]
    )
    assert [decision.method for decision in result.decisions] == ["review", "review"]
    assert result.mention_to_entity == {}
    assert len(result.review_tasks) == 2


@pytest.mark.asyncio
async def test_approved_new_entity_can_be_reused_by_later_batch() -> None:
    entity = CanonicalEntity(id="approved-new", name="New Institute", entity_type="Organization")
    result = await resolver(
        ControlledGraph(entity, 0.0), ControlledProvider(entity.name, 0.0)
    ).resolve(
        [
            mention(entity.name),
        ]
    )
    assert result.decisions[0].method == "exact"
    assert result.mention_to_entity["M1"] == "approved-new"


def test_legacy_policy_state_is_read_only(tmp_path: Path) -> None:
    from prismke.core.errors import LegacyCheckpointError
    from prismke.domain import WorkflowState
    from prismke.workflow.service import PrismKEService

    state = WorkflowState(run_id="legacy", input_path="x", schema_path="x")
    with pytest.raises(LegacyCheckpointError, match="read-only"):
        PrismKEService._validate_entity_policy(state)
