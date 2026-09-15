from __future__ import annotations

import os
from pathlib import Path

import pytest

from prismke.core.errors import ProviderConfigurationError
from prismke.core.settings import Settings
from prismke.workflow import PrismKEService


def test_openai_provider_requires_explicit_configuration(tmp_path: Path) -> None:
    service = PrismKEService(Settings(runtime_dir=tmp_path / "runtime"))
    with pytest.raises(ProviderConfigurationError, match="PRISMKE_LLM_API_KEY"):
        service.provider("openai-compatible")


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
