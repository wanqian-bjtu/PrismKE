"""Human-readable baseline results without copying original document contexts."""

from __future__ import annotations

import csv
import json
from pathlib import Path

from prismke.evaluation.entity_linking import EntityLinkingEvaluationReport


def write_baseline_report(reports: list[EntityLinkingEvaluationReport], output: Path) -> None:
    rows = [
        "# 真实材料实体治理基线报告",
        "",
        "这是人工给定实体名称和类型后的BGE-M3解析评测，不是LLM/VLM抽取评测。",
        "候选排名正确不等于自动链接成功；待审核记录未用标准答案代替人工审核。",
        "本轮没有Claim邻域，不能据此证明图邻域验证、合并/拆分或回滚能力。",
        "",
        "| 协议 | 样本 | 已知Top-1 | 已知Top-10 | 自动链接覆盖 | 错误自动链接 | "
        "审核 | NIL F1 | B-Cubed F1 |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for report in reports:
        d = report.denominators
        auto = d["auto_links"]
        rows.append(
            f"| {report.protocol} | {report.cases} | {d['top_1_hits']}/{d['link_cases']} "
            f"({report.top_1_accuracy:.1%}) | {d['top_10_hits']}/{d['link_cases']} "
            f"({report.top_10_recall:.1%}) | {auto}/{report.cases} "
            f"({report.auto_link_coverage:.1%}) | {d['false_auto_links']}/{auto} | "
            f"{d['reviews']}/{report.cases} | {report.nil_f1:.3f} | {report.b_cubed_f1:.3f} |"
        )
    rows += [
        "",
        "自动链接分母为0时错误率不适用。NIL的判定相对于当时的候选库；",
        "顺序模式可能因前序待审核或错误创建而改变后续候选库，不能直接和固定模式混算。",
        "这五份资料主题相关且有论文/README复述，不是独立跨领域盲测集。",
        "",
    ]
    for report in reports:
        rows += [
            f"## {report.protocol} 明细",
            "",
            f"模型指纹：`{report.provenance.get('model_fingerprint')}`",
            f"模型版本：`{report.provenance.get('embedding_revision')}`",
            f"代码提交：`{report.provenance.get('code_commit')}`",
            f"工作簿SHA-256：`{report.provenance.get('workbook_sha256')}`",
            f"Manifest SHA-256：`{report.provenance.get('manifest_sha256')}`",
            f"耗时：{report.total_seconds:.2f}秒；新建实体：{report.created_entities}；"
            f"重复创建：{report.duplicate_creation_count}；API调用：0。",
            "",
            "模态分组：",
        ]
        for modality, group in report.modality_summary.items():
            rows.append(
                f"- {modality}：{group['cases']}条，已知实体{group['link_cases']}条，"
                f"审核{group['review_cases']}条，错误自动链接{group['false_auto_links']}条。"
            )
        rows += [
            "",
            "| 提及 | 名称 | 标准聚类 | 系统实体ID | 方法 | 结论 | 原因 | 证据 |",
            "|---|---|---|---|---|---|---|---|",
        ]
        for item in report.details:
            correct = item["decision_correct"]
            result = "待审核" if correct is None else "正确" if correct else "错误"
            evidence = item.get("evidence") or {}
            location = evidence.get("id", evidence.get("asset_file", "未附原始位置"))
            name = str(item["name"]).replace("|", "\\|")
            reasons = ", ".join(item["reasons"])
            rows.append(
                f"| {item['mention_id']} | {name} | {item['gold_cluster_id']} | "
                f"{item['predicted_entity_id'] or '未选择'} | {item['method']} | "
                f"{result} | {reasons} | {location} |"
            )
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text("\n".join(rows) + "\n", encoding="utf-8")
    for report in reports:
        fields = [
            "提及ID",
            "文档ID",
            "名称",
            "模态",
            "标准聚类ID",
            "当时正确实体ID",
            "系统实体ID",
            "解析方法",
            "置信度",
            "候选差距",
            "Top1正确",
            "自动决策正确",
            "是否待审核",
            "审核原因",
            "证据位置",
            "候选得分明细",
        ]
        with output.with_name(f"{report.protocol}-对照表.csv").open(
            "w", encoding="utf-8-sig", newline=""
        ) as stream:
            writer = csv.DictWriter(stream, fieldnames=fields)
            writer.writeheader()
            for item in report.details:
                writer.writerow(
                    dict(
                        zip(
                            fields,
                            [
                                item["mention_id"],
                                item["document_id"],
                                item["name"],
                                item["modality"],
                                item["gold_cluster_id"],
                                ", ".join(item["expected_current_entity_ids"]),
                                item["predicted_entity_id"] or "未选择",
                                item["method"],
                                item["confidence"],
                                item["margin"],
                                item["top_1_correct"],
                                item["decision_correct"],
                                item["requires_review"],
                                ", ".join(item["reasons"]),
                                json.dumps(item["evidence"], ensure_ascii=False),
                                json.dumps(item["candidates"], ensure_ascii=False),
                            ],
                            strict=True,
                        )
                    )
                )
