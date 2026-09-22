from __future__ import annotations

import pytest
from pydantic import ValidationError

from src.domain import Claim, GraphChange, GraphRevision


def test_claim_requires_exactly_one_object() -> None:
    with pytest.raises(ValidationError):
        Claim(
            id="claim:1",
            subject_id="entity:1",
            relation_id="related_to",
            confidence=0.9,
            evidence_ids=["ev:1"],
        )


def test_claim_requires_evidence() -> None:
    with pytest.raises(ValidationError):
        Claim(
            id="claim:1",
            subject_id="entity:1",
            relation_id="related_to",
            object_literal="value",
            confidence=0.9,
            evidence_ids=[],
        )


def test_old_revision_payload_remains_compatible() -> None:
    revision = GraphRevision.model_validate({"id": "r", "run_id": "run"})
    assert revision.changes == []
    change = GraphChange(
        resource_type="claim",
        resource_id="claim:1",
        action="create",
        after={"id": "claim:1"},
    )
    assert GraphRevision(id="r2", run_id="run", changes=[change]).changes == [change]
