from __future__ import annotations

from pathlib import Path

import pytest

from frontend.schema_input import resolve_schema, schema_summary
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


def test_schema_text_and_upload_materialize_the_same_schema(tmp_path: Path) -> None:
    uploaded = tmp_path / "schema.yaml"
    uploaded.write_text(SCHEMA_TEXT, encoding="utf-8")
    upload_path, uploaded_schema = resolve_schema("upload", str(uploaded), "", tmp_path)
    text_path, text_schema = resolve_schema("text", None, SCHEMA_TEXT, tmp_path / "normalized")

    assert upload_path == uploaded.resolve()
    assert uploaded_schema == text_schema
    assert text_path.suffix == ".json" and text_path.is_file()
    assert schema_summary(text_schema) == "Schema `web-schema` · 版本 `1` · 实体类型 1 · 关系 0"


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
