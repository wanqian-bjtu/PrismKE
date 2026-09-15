"""Public HTTP request and response models."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel

from prismke.domain import ReviewDecision


class RunAccepted(BaseModel):
    run_id: str
    status: str
    created: bool


class ReviewRequest(BaseModel):
    decision: ReviewDecision


class RollbackRequest(BaseModel):
    confirm: Literal[True]
