from __future__ import annotations

import os
from pathlib import Path

import pytest

from prismke.core.errors import ProviderConfigurationError
from prismke.core.settings import Settings
from prismke.providers import OpenAICompatibleLLMProvider, OpenAICompatibleVLMProvider
from prismke.workflow import PrismKEService


def test_openai_provider_requires_explicit_configuration(tmp_path: Path) -> None:
    service = PrismKEService(
        Settings(
            _env_file=None,
            runtime_dir=tmp_path / "runtime",
            llm_api_key=None,
            llm_model=None,
        )
    )
    with pytest.raises(ProviderConfigurationError, match="PRISMKE_LLM_API_KEY"):
        service.provider("openai-compatible")


def test_openai_provider_rejects_placeholder_base_url(tmp_path: Path) -> None:
    service = PrismKEService(
        Settings(
            runtime_dir=tmp_path / "runtime",
            llm_base_url="https://<WorkspaceId>.cn-beijing.maas.aliyuncs.com/compatible-mode/v1",
            llm_api_key="secret",
            llm_model="qwen3.7-flash",
        )
    )
    with pytest.raises(ProviderConfigurationError, match="PRISMKE_LLM_BASE_URL"):
        service.provider("openai-compatible")


def test_same_key_can_configure_text_and_visual_providers(tmp_path: Path) -> None:
    service = PrismKEService(
        Settings(
            runtime_dir=tmp_path / "runtime",
            llm_base_url="https://workspace.example.test/compatible-mode/v1",
            llm_api_key="shared-secret",
            llm_model="qwen3.7-flash",
            vlm_base_url="https://workspace.example.test/compatible-mode/v1",
            vlm_api_key="shared-secret",
            vlm_model="qwen3.7-flash",
        )
    )
    text_provider = service.provider("openai-compatible")
    visual_provider = service.vlm_provider("openai-compatible")
    assert isinstance(text_provider, OpenAICompatibleLLMProvider)
    assert isinstance(visual_provider, OpenAICompatibleVLMProvider)
    assert text_provider.model == "qwen3.7-flash"
    assert visual_provider.model == "qwen3.7-flash"


def test_service_reuses_ocr_provider_instance(tmp_path: Path) -> None:
    service = PrismKEService(Settings(runtime_dir=tmp_path / "runtime"))
    assert service.ocr_provider("paddle") is service.ocr_provider("paddle")


@pytest.mark.asyncio
async def test_run_id_depends_on_content_not_path_or_mtime(
    tmp_path: Path, schema_path: Path
) -> None:
    first = tmp_path / "first.md"
    second = tmp_path / "second.md"
    content = "PrismKE | developed_by | OpenAI | Software | Organization | 0.92\n"
    first.write_text(content, encoding="utf-8")
    second.write_text(content, encoding="utf-8")
    os.utime(second, (1_700_000_000, 1_700_000_000))
    service = PrismKEService(Settings(runtime_dir=tmp_path / "runtime"))
    first_run = await service.run(first, schema_path, "mock")
    second_run = await service.run(second, schema_path, "mock")
    assert first_run.run_id == second_run.run_id
