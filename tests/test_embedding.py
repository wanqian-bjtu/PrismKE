from __future__ import annotations

from pathlib import Path

import pytest

from src.providers import BGEM3EmbeddingProvider


@pytest.mark.asyncio
async def test_bge_embedding_cache_is_atomic_and_recovers_corruption(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    provider = BGEM3EmbeddingProvider(
        model_name="BAAI/bge-m3",
        model_revision="test-revision",
        device="cuda:0",
        use_fp16=True,
        batch_size=32,
        max_tokens=512,
        cache_dir=tmp_path / "embeddings",
        model_cache_dir=tmp_path / "models",
    )
    calls = 0

    def encode_missing(texts: list[str]) -> list[list[float]]:
        nonlocal calls
        calls += 1
        return [[1.0, *([0.0] * 1023)] for _ in texts]

    monkeypatch.setattr(provider, "_encode_missing", encode_missing)
    first = await provider.encode(["PrismKE"])
    assert await provider.encode(["PrismKE"]) == first
    assert calls == 1
    cache = next((tmp_path / "embeddings").glob("*/*.json"))
    cache.write_text("{broken", encoding="utf-8")
    assert await provider.encode(["PrismKE"]) == first
    assert calls == 2
    assert not list((tmp_path / "embeddings").glob("*/*.tmp"))


def test_bge_fingerprint_includes_model_revision(tmp_path: Path) -> None:
    kwargs = {
        "model_name": "BAAI/bge-m3",
        "device": "cuda:0",
        "use_fp16": True,
        "batch_size": 32,
        "max_tokens": 512,
        "cache_dir": tmp_path / "embeddings",
        "model_cache_dir": tmp_path / "models",
    }
    first = BGEM3EmbeddingProvider(model_revision="revision-a", **kwargs)
    second = BGEM3EmbeddingProvider(model_revision="revision-b", **kwargs)
    assert first.fingerprint() != second.fingerprint()
