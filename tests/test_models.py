from __future__ import annotations

import pytest
from pydantic import ValidationError

from prismke.models import Claim


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
