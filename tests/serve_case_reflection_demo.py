"""Loopback-only v0.9 browser fixture with synthetic case and Reflection data."""

from __future__ import annotations

import os
from pathlib import Path

import uvicorn

from src.api import create_app
from src.core.ids import canonical_hash
from src.core.settings import Settings
from src.domain import CaseRecord, EntityTypeDef, OutputSchema, RelationDef
from src.workflow import PrismKEService


def main() -> None:
    root = Path(os.environ["PRISMKE_CASE_BROWSER_RUNTIME"]).resolve()
    project = Path(__file__).resolve().parents[1]
    if not root.is_relative_to(project / "runtime") or root.exists():
        raise ValueError("fixture requires a fresh directory inside project runtime")
    settings = Settings(
        _env_file=None,
        runtime_dir=root,
        graph_store="json",
        embedding_provider="mock",
        api_host="127.0.0.1",
        api_port=8007,
    )
    service = PrismKEService(settings)
    schema = OutputSchema(
        schema_id="case-browser",
        version="1",
        entity_types=[EntityTypeDef(id="Software"), EntityTypeDef(id="Organization")],
        relations=[
            RelationDef(
                id="developed_by",
                domain=["Software"],
                range=["Organization"],
            )
        ],
    )
    service.case_repository.add(
        CaseRecord(
            id="case:browser-good",
            run_id="run:browser-source",
            case_type="good",
            task_type="claim",
            schema_fingerprint=canonical_hash(schema.model_dump(mode="json")),
            language="en",
            input_summary="PrismKE developed_by Example Lab",
            candidate_snapshot={"relation": "developed_by", "synthetic": True},
            decision="approve",
            reasons=["synthetic browser acceptance fixture"],
            source_review_event_id="review-event:browser-good",
        )
    )
    app = create_app(settings, service)
    uvicorn.run(app, host="127.0.0.1", port=8007)


if __name__ == "__main__":
    main()
