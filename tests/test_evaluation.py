from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.core.settings import Settings
from src.evaluation import evaluate_manifest
from src.workflow import PrismKEService


@pytest.mark.asyncio
async def test_evaluation_manifest_reports_claim_metrics(tmp_path: Path, schema_path: Path) -> None:
    sample = tmp_path / "sample.md"
    sample.write_text(
        "PrismKE | developed_by | OpenAI | Software | Organization | 0.92\n",
        encoding="utf-8",
    )
    manifest = tmp_path / "manifest.json"
    manifest.write_text(
        json.dumps(
            {
                "version": "test-1",
                "schema_path": schema_path.name,
                "cases": [
                    {
                        "id": "exact-claim",
                        "input": sample.name,
                        "language": "en",
                        "claims": [
                            {
                                "subject": "PrismKE",
                                "relation": "developed_by",
                                "object": "OpenAI",
                            }
                        ],
                        "expected_alignment_decisions": ["independent"],
                        "expected_localization_levels": ["text_span"],
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    report = await evaluate_manifest(
        manifest,
        PrismKEService(Settings(runtime_dir=tmp_path / "runtime")),
        provider_name="mock",
        ocr_provider_name="disabled",
        vlm_provider_name="disabled",
    )
    assert report.completed_cases == 1
    assert report.failed_cases == 0
    assert report.claim_f1 == 1.0
    assert report.entity_f1 == 1.0
    assert report.evidence_coverage == 1.0
    assert report.scenario_pass_rate == 1.0


@pytest.mark.asyncio
async def test_evaluation_keeps_case_failures_isolated(tmp_path: Path, schema_path: Path) -> None:
    valid = tmp_path / "valid.md"
    valid.write_text("no mock claims", encoding="utf-8")
    manifest = tmp_path / "manifest.json"
    manifest.write_text(
        json.dumps(
            {
                "version": "test-1",
                "schema_path": schema_path.name,
                "cases": [
                    {"id": "missing", "input": "missing.md", "language": "en"},
                    {"id": "valid", "input": valid.name, "language": "en"},
                ],
            }
        ),
        encoding="utf-8",
    )
    report = await evaluate_manifest(
        manifest,
        PrismKEService(Settings(runtime_dir=tmp_path / "runtime")),
        provider_name="mock",
        ocr_provider_name="disabled",
        vlm_provider_name="disabled",
    )
    assert report.completed_cases == 1
    assert report.failed_cases == 1
    assert report.cases[0].error is not None


@pytest.mark.asyncio
async def test_evaluation_redacts_provider_keys(
    tmp_path: Path, schema_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    secret = "sk-test-secret-value"
    sample = tmp_path / "sample.md"
    sample.write_text("content", encoding="utf-8")
    manifest = tmp_path / "manifest.json"
    manifest.write_text(
        json.dumps(
            {
                "version": "test-1",
                "schema_path": schema_path.name,
                "cases": [{"id": "redaction", "input": sample.name, "language": "en"}],
            }
        ),
        encoding="utf-8",
    )
    service = PrismKEService(Settings(runtime_dir=tmp_path / "runtime", llm_api_key=secret))

    async def fail(*args: object, **kwargs: object) -> object:
        raise RuntimeError(f"request failed with {secret}")

    monkeypatch.setattr(service, "run", fail)
    report = await evaluate_manifest(
        manifest,
        service,
        provider_name="mock",
        ocr_provider_name="disabled",
        vlm_provider_name="disabled",
    )
    assert report.cases[0].error == "RuntimeError:request failed with ***"


def test_public_evaluation_manifest_has_twelve_reproducible_cases() -> None:
    root = Path(__file__).resolve().parents[1] / "examples" / "eval_v0_2"
    payload = json.loads((root / "manifest.json").read_text(encoding="utf-8"))
    assert len(payload["cases"]) == 12
    assert all((root / case["input"]).is_file() for case in payload["cases"])


@pytest.mark.asyncio
async def test_evaluation_treats_inverse_relations_and_aliases_as_same_fact(
    tmp_path: Path,
) -> None:
    sample = tmp_path / "sample.md"
    sample.write_text(
        "Northstar Labs | develops | AuroraGraph | Organization | Software | 0.92\n",
        encoding="utf-8",
    )
    schema = tmp_path / "schema.yaml"
    schema.write_text(
        """
schema_id: inverse-evaluation
version: "1"
strict: true
entity_types:
  - id: Software
  - id: Organization
relations:
  - id: developed_by
    domain: [Software]
    range: [Organization]
    inverse_relation: develops
  - id: develops
    domain: [Organization]
    range: [Software]
    inverse_relation: developed_by
entity_catalog:
  - id: entity:northstar
    name: Northstar Labs
    type: Organization
    aliases: [北辰实验室]
  - id: entity:auroragraph
    name: AuroraGraph
    type: Software
""".strip(),
        encoding="utf-8",
    )
    manifest = tmp_path / "manifest.json"
    manifest.write_text(
        json.dumps(
            {
                "version": "test-inverse",
                "schema_path": schema.name,
                "cases": [
                    {
                        "id": "inverse-alias",
                        "input": sample.name,
                        "language": "en",
                        "claims": [
                            {
                                "subject": "AuroraGraph",
                                "relation": "developed_by",
                                "object": "北辰实验室",
                            }
                        ],
                        "expected_alignment_decisions": ["independent"],
                        "expected_localization_levels": ["text_span"],
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    report = await evaluate_manifest(
        manifest,
        PrismKEService(Settings(runtime_dir=tmp_path / "runtime")),
        provider_name="mock",
        ocr_provider_name="disabled",
        vlm_provider_name="disabled",
    )
    assert report.claim_f1 == 1.0
    assert report.entity_f1 == 1.0
