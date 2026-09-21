"""Generate the isolated v0.9 text-only case/Reflection evaluation corpus."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1] / "examples" / "eval_v0_9"

SCHEMA = {
    "schema_id": "reflection-eval-v1",
    "version": "1",
    "strict": True,
    "entity_types": [
        {"id": "Software"},
        {"id": "Organization"},
        {"id": "Person"},
    ],
    "relations": [
        {
            "id": "developed_by",
            "domain": ["Software"],
            "range": ["Organization"],
        },
        {
            "id": "authored_by",
            "domain": ["Software"],
            "range": ["Person"],
        },
    ],
}


def mention(
    sample_id: str,
    role: str,
    name: str,
    entity_type: str,
    evidence_id: str,
    context: str,
) -> dict[str, Any]:
    return {
        "id": f"mention:{sample_id}:{role}",
        "name": name,
        "entity_type": entity_type,
        "context": context,
        "modality": "text",
        "evidence_ids": [evidence_id],
    }


def claim(
    sample_id: str,
    text: str,
    relation: str,
    subject_type: str,
    evidence_id: str,
) -> dict[str, Any]:
    zh = sample_id.endswith("zh") or "zh-" in sample_id
    category = next(
        (item for item in ("relation", "domain", "evidence") if item in sample_id),
        "relation",
    )
    names = {
        "relation": (("星图引擎", "北辰实验室"), ("AtlasFlow", "Northstar Labs")),
        "domain": (("流云数据库", "乾元科技"), ("RiverDB", "Contoso Data")),
        "evidence": (("新星图谱", "兰庭系统"), ("NovaGraph", "Orchid Systems")),
    }
    subject, organization = names[category][0 if zh else 1]
    return {
        "id": f"candidate:{sample_id}",
        "subject": mention(sample_id, "subject", subject, subject_type, evidence_id, text),
        "relation": relation,
        "object": mention(sample_id, "object", organization, "Organization", evidence_id, text),
        "confidence": 0.84,
        "evidence_ids": [evidence_id],
        "modalities": ["text"],
        "source_tool": "reflection_eval",
    }


def repair_sample(
    sample_id: str,
    split: str,
    language: str,
    category: str,
    text: str,
) -> dict[str, Any]:
    actual = f"evidence:{sample_id}"
    if category == "relation":
        original = claim(sample_id, text, "built_by", "Software", actual)
        corrected = claim(sample_id, text, "developed_by", "Software", actual)
    elif category == "domain":
        original = claim(sample_id, text, "developed_by", "Organization", actual)
        corrected = claim(sample_id, text, "developed_by", "Software", actual)
    else:
        original = claim(sample_id, text, "developed_by", "Software", "evidence:missing")
        corrected = claim(sample_id, text, "developed_by", "Software", actual)
    return {
        "id": sample_id,
        "split": split,
        "language": language,
        "category": category,
        "text": text,
        "candidate": original,
        "expected_candidate": corrected,
        "repairable": True,
        "relevant_case_key": f"{category}:{language}",
    }


def ordinary_sample(
    sample_id: str,
    language: str,
    text: str,
    *,
    valid: bool,
) -> dict[str, Any]:
    evidence_id = f"evidence:{sample_id}"
    relation = "developed_by" if valid else "invented_fact_about"
    original = claim(sample_id, text, relation, "Software", evidence_id)
    return {
        "id": sample_id,
        "split": "test",
        "language": language,
        "category": "valid" if valid else "unrepairable",
        "text": text,
        "candidate": original,
        "expected_candidate": original if valid else None,
        "repairable": False,
        "relevant_case_key": None,
    }


def corpus() -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    dev = [
        repair_sample(
            "dev-relation-en", "dev", "en", "relation", "AtlasFlow was developed by Northstar Labs."
        ),
        repair_sample("dev-relation-zh", "dev", "zh", "relation", "星图引擎由北辰实验室开发。"),
        repair_sample(
            "dev-domain-en", "dev", "en", "domain", "RiverDB was developed by Contoso Data."
        ),
        repair_sample("dev-domain-zh", "dev", "zh", "domain", "流云数据库由乾元科技开发。"),
        repair_sample(
            "dev-evidence-en",
            "dev",
            "en",
            "evidence",
            "NovaGraph was developed by Orchid Systems.",
        ),
        repair_sample("dev-evidence-zh", "dev", "zh", "evidence", "新星图谱由兰庭系统开发。"),
    ]
    test = [
        repair_sample(
            "test-relation-en",
            "test",
            "en",
            "relation",
            "AtlasFlow is developed by Northstar Labs.",
        ),
        repair_sample(
            "test-relation-zh", "test", "zh", "relation", "星图引擎的开发机构是北辰实验室。"
        ),
        repair_sample(
            "test-domain-en",
            "test",
            "en",
            "domain",
            "Contoso Data develops the RiverDB software.",
        ),
        repair_sample("test-domain-zh", "test", "zh", "domain", "乾元科技开发了流云数据库软件。"),
        repair_sample(
            "test-evidence-en",
            "test",
            "en",
            "evidence",
            "NovaGraph was developed by Orchid Systems.",
        ),
        repair_sample("test-evidence-zh", "test", "zh", "evidence", "新星图谱由兰庭系统开发。"),
        repair_sample(
            "test-relation-en-2",
            "test",
            "en",
            "relation",
            "The developer of AtlasFlow is Northstar Labs.",
        ),
        repair_sample(
            "test-domain-zh-2", "test", "zh", "domain", "流云数据库是一款由乾元科技开发的软件。"
        ),
        repair_sample(
            "test-evidence-en-2",
            "test",
            "en",
            "evidence",
            "Orchid Systems developed NovaGraph.",
        ),
        ordinary_sample(
            "test-valid-en", "en", "AtlasFlow was developed by Northstar Labs.", valid=True
        ),
        ordinary_sample("test-valid-zh", "zh", "星图引擎由北辰实验室开发。", valid=True),
        ordinary_sample(
            "test-unrepairable-en", "en", "The document does not identify a developer.", valid=False
        ),
    ]
    return dev, test


def main() -> None:
    dev, test = corpus()
    for split, samples in (("dev", dev), ("test", test)):
        directory = ROOT / split
        directory.mkdir(parents=True, exist_ok=True)
        for sample in samples:
            (directory / f"{sample['id']}.json").write_text(
                json.dumps(sample, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
    (ROOT / "schema.json").write_text(
        json.dumps(SCHEMA, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    manifest = {
        "version": "reflection-eval-v1",
        "schema": "schema.json",
        "development": [f"dev/{item['id']}.json" for item in dev],
        "test": [f"test/{item['id']}.json" for item in test],
    }
    (ROOT / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )


if __name__ == "__main__":
    main()
