from __future__ import annotations

import json
from pathlib import Path

import pytest
import yaml

from data.tools.common import sanitize_json
from data.tools.fetch_public import _validate_url


def test_public_url_allowlist_rejects_unsafe_sources() -> None:
    _validate_url("https://nvlpubs.nist.gov/nistpubs/ai/NIST.AI.100-1.pdf")
    with pytest.raises(ValueError, match="HTTPS"):
        _validate_url("http://nvlpubs.nist.gov/report.pdf")
    with pytest.raises(ValueError, match="allowlisted"):
        _validate_url("https://example.com/report.pdf")
    with pytest.raises(ValueError, match="Credentials"):
        _validate_url("https://user:secret@aclanthology.org/paper.pdf")


def test_json_sanitizer_removes_dynamic_identity_fields_and_contact_data() -> None:
    counts: dict[str, int] = {}
    result = sanitize_json(
        {
            "username": "contributor",
            "email": "owner@example.org",
            "nested": [{"timestamp": "2026-01-01", "value": "keep"}],
        },
        counts,
    )
    assert "username" not in result
    assert result["email"] == "[REDACTED EMAIL]"
    assert result["nested"] == [{"value": "keep"}]
    assert counts["dynamic_keys_removed"] == 2
    assert counts["email"] == 1


def test_public_manifest_and_lock_cover_eight_licensed_sources() -> None:
    root = Path(__file__).resolve().parents[1]
    manifest = yaml.safe_load((root / "data/manifests/public_sources.yaml").read_text())
    lock = json.loads((root / "data/public/manifest.lock.json").read_text())
    sources = manifest["sources"]
    assert len(sources) == 8
    assert {item["id"] for item in sources} == {
        item["id"] for item in lock["sources"]
    }
    assert all(item["license_id"] for item in sources)
    assert all(item["landing_page"].startswith("https://") for item in sources)
    assert all(item["download_url"].startswith("https://") for item in sources)
