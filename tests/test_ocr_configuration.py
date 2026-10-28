from __future__ import annotations

from collections.abc import Iterator
from types import SimpleNamespace

import pytest

from src.core.settings import Settings
from src.providers.ocr import (
    PaddleOCRProvider,
    detect_ocr_device,
    ensure_ocr_device_available,
    resolve_ocr_device,
    resolve_ocr_language,
)


@pytest.fixture(autouse=True)
def clear_device_detection_cache() -> Iterator[None]:
    detect_ocr_device.cache_clear()
    yield
    detect_ocr_device.cache_clear()


def test_auto_device_prefers_paddle_cuda(monkeypatch: pytest.MonkeyPatch) -> None:
    paddle = SimpleNamespace(
        device=SimpleNamespace(
            is_compiled_with_cuda=lambda: True,
            cuda=SimpleNamespace(device_count=lambda: 1),
        )
    )
    monkeypatch.setattr("src.providers.ocr.import_module", lambda _: paddle)

    assert detect_ocr_device() == "gpu:0"
    assert resolve_ocr_device("auto") == "gpu:0"
    assert PaddleOCRProvider(device="auto").device == "gpu:0"


def test_settings_default_to_auto_mixed_ocr() -> None:
    settings = Settings(_env_file=None)
    assert settings.ocr_device == "auto"
    assert settings.ocr_lang == "mixed"


@pytest.mark.parametrize(
    "paddle",
    [
        SimpleNamespace(
            device=SimpleNamespace(
                is_compiled_with_cuda=lambda: False,
                cuda=SimpleNamespace(device_count=lambda: 1),
            )
        ),
        SimpleNamespace(
            device=SimpleNamespace(
                is_compiled_with_cuda=lambda: True,
                cuda=SimpleNamespace(device_count=lambda: 0),
            )
        ),
    ],
)
def test_auto_device_falls_back_to_cpu(
    monkeypatch: pytest.MonkeyPatch, paddle: SimpleNamespace
) -> None:
    monkeypatch.setattr("src.providers.ocr.import_module", lambda _: paddle)
    assert resolve_ocr_device("auto") == "cpu"


def test_auto_device_handles_missing_or_broken_paddle(monkeypatch: pytest.MonkeyPatch) -> None:
    def unavailable(_: str) -> object:
        raise ImportError("paddle unavailable")

    monkeypatch.setattr("src.providers.ocr.import_module", unavailable)
    assert resolve_ocr_device("auto") == "cpu"


def test_explicit_ocr_device_bypasses_detection(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "src.providers.ocr.import_module",
        lambda _: (_ for _ in ()).throw(AssertionError("must not detect")),
    )
    assert resolve_ocr_device("cpu") == "cpu"
    assert resolve_ocr_device("gpu:0") == "gpu:0"
    assert resolve_ocr_device("gpu:2") == "gpu:2"
    with pytest.raises(ValueError, match="ocr_device"):
        resolve_ocr_device("cuda:0")


def test_explicit_gpu_provider_blocks_when_paddle_has_no_cuda(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    paddle = SimpleNamespace(
        device=SimpleNamespace(
            is_compiled_with_cuda=lambda: False,
            cuda=SimpleNamespace(device_count=lambda: 0),
        )
    )
    monkeypatch.setattr("src.providers.ocr.import_module", lambda _: paddle)
    with pytest.raises(RuntimeError, match="OCR_GPU_UNAVAILABLE"):
        PaddleOCRProvider(device="gpu:0")
    with pytest.raises(RuntimeError, match="OCR_GPU_UNAVAILABLE"):
        ensure_ocr_device_available("gpu:0")


@pytest.mark.parametrize(
    ("configured", "engine"),
    [("mixed", "ch"), ("zh", "ch"), ("ch", "ch"), ("en", "en")],
)
def test_ocr_language_modes(configured: str, engine: str) -> None:
    assert resolve_ocr_language(configured) == engine
    assert PaddleOCRProvider(device="cpu", lang=configured).lang == engine


def test_equivalent_chinese_modes_keep_provider_fingerprint() -> None:
    fingerprints = {
        PaddleOCRProvider(device="cpu", lang=mode).fingerprint() for mode in ("mixed", "zh", "ch")
    }
    assert len(fingerprints) == 1
