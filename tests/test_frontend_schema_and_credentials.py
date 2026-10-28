from __future__ import annotations

from pathlib import Path

import pytest

from frontend.app import _batch_status_cell, normalize_session_key
from frontend.schema_input import resolve_schema, schema_summary
from src.core.ids import canonical_hash
from src.core.settings import Settings
from src.workflow import PrismKEService
from src.workflow.service import TransientProviderCredentials

SCHEMA_TEXT = """
schema_id: web-schema
version: '1'
entity_types:
  - id: Person
    aliases: [person]
relations: []
"""


def test_empty_session_api_key_safely_falls_back_to_server_configuration() -> None:
    assert normalize_session_key(None) is None
    assert normalize_session_key("") is None
    assert normalize_session_key("   ") is None
    assert normalize_session_key("  temporary-key  ") == "temporary-key"


def test_batch_status_cell_only_adds_safe_review_action_when_needed() -> None:
    review = _batch_status_cell("awaiting_review", 'run:<unsafe>&"')
    assert "Awaiting review" in review
    assert 'class="batch-inline-review-button"' in review
    assert 'data-run-id="run:&lt;unsafe&gt;&amp;&quot;"' in review
    assert "去审核" in review

    assert "batch-inline-review-button" not in _batch_status_cell("completed", "run:done")
    assert "batch-inline-review-button" not in _batch_status_cell("awaiting_review", None)


def test_schema_text_and_upload_materialize_the_same_schema(tmp_path: Path) -> None:
    uploaded = tmp_path / "schema.yaml"
    uploaded.write_text(SCHEMA_TEXT, encoding="utf-8")
    upload_path, uploaded_schema = resolve_schema("upload", str(uploaded), "", tmp_path)
    text_path, text_schema = resolve_schema("text", None, SCHEMA_TEXT, tmp_path / "normalized")

    assert upload_path == uploaded.resolve()
    assert uploaded_schema == text_schema
    assert text_path.suffix == ".json" and text_path.is_file()
    summary = schema_summary(text_schema)
    assert 'class="schema-validation-valid"' in summary
    assert "✓ Valid · Schema web-schema · Version 1 · Entity types 1 · Relations 0" in summary
    assert canonical_hash(text_schema.model_dump(mode="json")) in summary


@pytest.mark.parametrize(
    ("source", "uploaded", "text"),
    [("upload", None, ""), ("text", None, ""), ("unknown", None, SCHEMA_TEXT)],
)
def test_schema_source_rejects_missing_or_unknown_input(
    tmp_path: Path, source: str, uploaded: str | None, text: str
) -> None:
    with pytest.raises(ValueError):
        resolve_schema(source, uploaded, text, tmp_path)


def test_transient_provider_key_never_enters_run_files(tmp_path: Path) -> None:
    secret = "session-only-secret-922"
    sample = tmp_path / "sample.md"
    sample.write_text("Alice works for Example.", encoding="utf-8")
    schema = tmp_path / "schema.yaml"
    schema.write_text(SCHEMA_TEXT, encoding="utf-8")
    settings = Settings(
        _env_file=None,
        runtime_dir=tmp_path / "runtime",
        graph_store="json",
        embedding_provider="mock",
        llm_api_key=None,
        llm_model="server-model",
    )
    service = PrismKEService(settings)
    state, created = service.create_run(
        sample,
        schema,
        "openai-compatible",
        llm_base_url="https://example.invalid/v1",
        llm_model="session-model",
        credentials=TransientProviderCredentials(llm_api_key=secret),
    )

    assert created
    assert state.llm_model == "session-model"
    assert secret not in state.model_dump_json()
    assert secret.encode() not in b"".join(
        path.read_bytes() for path in settings.runtime_dir.rglob("*") if path.is_file()
    )

    restarted = PrismKEService(settings)
    restored = restarted.show_run(state.run_id)
    assert restarted.missing_run_credentials(restored)
    assert restarted.executions.view(state.run_id)["error_code"] == "CREDENTIAL_REQUIRED"

    restarted.attach_run_credentials(state.run_id, llm_api_key=secret)
    assert not restarted.missing_run_credentials(restored)
    assert restarted.provider_for_state(restored).fingerprint() == restored.provider_fingerprint
    restarted.release_run_credentials(state.run_id)
    assert restarted.missing_run_credentials(restored)
