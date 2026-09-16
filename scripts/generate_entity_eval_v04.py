"""Generate the public, synthetic PrismKE v0.4 entity-governance benchmark."""

from __future__ import annotations

import json
from pathlib import Path


def build_manifest() -> dict[str, object]:
    entities: list[dict[str, object]] = []
    mentions: list[dict[str, object]] = []
    governance: list[dict[str, object]] = []

    bilingual = [
        ("OpenAI", "开放人工智能研究中心"),
        ("Microsoft", "微软"),
        ("Google", "谷歌"),
        ("Amazon", "亚马逊"),
        ("Apple", "苹果公司"),
        ("NVIDIA", "英伟达"),
        ("Alibaba Cloud", "阿里云"),
        ("Tencent", "腾讯"),
        ("Baidu", "百度"),
        ("ByteDance", "字节跳动"),
        ("Neo4j", "Neo4j 图数据库"),
        ("PrismKE", "棱镜知识抽取"),
        ("LangGraph", "LangGraph 工作流"),
        ("PaddleOCR", "飞桨文字识别"),
        ("BGE-M3", "BGE 多语言嵌入模型"),
        ("Qwen", "通义千问"),
        ("PyTorch", "PyTorch 深度学习框架"),
        ("FastAPI", "FastAPI 接口框架"),
        ("Gradio", "Gradio 交互界面"),
        ("Docker", "Docker 容器"),
    ]
    for index, (name, alias) in enumerate(bilingual, start=1):
        entity_id = f"entity:alias:{index:02d}"
        entity_type = "Organization" if index <= 10 else "Software"
        entities.append(
            {"id": entity_id, "name": name, "entity_type": entity_type, "aliases": [alias]}
        )
        mentions.append(
            {
                "id": f"mention:alias:{index:02d}",
                "name": alias,
                "entity_type": entity_type,
                "context": f"{alias} 在文档中指向 {name}",
                "expected_entity_id": entity_id,
                "cluster_id": entity_id,
                "category": "bilingual_alias",
            }
        )

    for index in range(1, 16):
        name = f"Aurora {index}"
        cloud_id = f"entity:homonym:{index:02d}:cloud"
        health_id = f"entity:homonym:{index:02d}:health"
        entities.extend(
            [
                {
                    "id": cloud_id,
                    "name": name,
                    "entity_type": "Organization",
                    "context_summary": "cloud computing and distributed databases",
                },
                {
                    "id": health_id,
                    "name": name,
                    "entity_type": "Organization",
                    "context_summary": "clinical medicine and public health research",
                },
            ]
        )
        mentions.append(
            {
                "id": f"mention:homonym:{index:02d}",
                "name": name,
                "entity_type": "Organization",
                "context": "The company provides cloud database infrastructure.",
                "expected_entity_id": cloud_id,
                "cluster_id": cloud_id,
                "category": "same_name_context",
            }
        )

    for index in range(1, 11):
        entity_id = f"entity:dedup:{index:02d}"
        name = f"Northstar Labs {index}"
        entities.append(
            {
                "id": entity_id,
                "name": name,
                "entity_type": "Organization",
                "aliases": [f"Northstar {index}", f"北星实验室{index}"],
            }
        )
        mentions.append(
            {
                "id": f"mention:dedup:{index:02d}",
                "name": f"北星实验室{index}",
                "entity_type": "Organization",
                "context": "跨文档别名实体",
                "expected_entity_id": entity_id,
                "cluster_id": entity_id,
                "category": "cross_document_duplicate",
            }
        )
        mentions.append(
            {
                "id": f"mention:dedup:{index:02d}:second-document",
                "name": f"Northstar {index}",
                "entity_type": "Organization",
                "context": "The same organization appears in a second document.",
                "expected_entity_id": entity_id,
                "cluster_id": entity_id,
                "category": "cross_document_duplicate",
            }
        )

    for index in range(1, 6):
        mentions.append(
            {
                "id": f"mention:nil:{index:02d}",
                "name": f"Unseen Entity {index}",
                "entity_type": "Organization",
                "context": "A newly introduced organization without a graph record.",
                "expected_entity_id": None,
                "cluster_id": f"nil:{index:02d}",
                "category": "nil",
            }
        )

    for index in range(1, 6):
        governance.append(
            {
                "id": f"merge:{index:02d}",
                "category": "merge",
                "source_entity_ids": [
                    f"entity:merge:{index:02d}:a",
                    f"entity:merge:{index:02d}:b",
                ],
                "target_entity_id": f"entity:merge:{index:02d}:a",
                "expected_review": True,
            }
        )
        governance.append(
            {
                "id": f"split:{index:02d}",
                "category": "split",
                "source_entity_id": f"entity:split:{index:02d}:source",
                "target_entity_ids": [
                    f"entity:split:{index:02d}:a",
                    f"entity:split:{index:02d}:b",
                ],
                "expected_review": True,
            }
        )

    return {
        "version": "0.4.0",
        "description": "Synthetic public benchmark for semantic entity resolution and governance",
        "group_count": 60,
        "entities": entities,
        "mentions": mentions,
        "governance": governance,
    }


if __name__ == "__main__":
    output = Path(__file__).resolve().parents[1] / "examples" / "entity_resolution_v0_4"
    output.mkdir(parents=True, exist_ok=True)
    target = output / "manifest.json"
    target.write_text(
        json.dumps(build_manifest(), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(target)
