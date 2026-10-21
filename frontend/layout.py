"""Shared layout primitives for the PrismKE research workspace."""

from __future__ import annotations

from pathlib import Path
from typing import Any

TAGLINE = "An auditable and traceable multimodal knowledge graph construction system."

NAVIGATION_GROUPS: dict[str, tuple[str, tuple[tuple[str, str], ...]]] = {
    "overview": ("总览", (("总览", "overview"),)),
    "build-execution": (
        "构建与执行",
        (("新建构建", "build"), ("执行任务", "execution")),
    ),
    "review-validation": (
        "审核与校验",
        (
            ("实体审核", "entity-review"),
            ("事实审核", "claim-review"),
            ("校验问题", "validation"),
        ),
    ),
    "evidence-graph": ("证据与图谱", (("证据", "evidence"), ("图谱", "graph"))),
    "media-knowledge": (
        "媒体知识",
        (("媒体资产", "media"), ("视觉审核", "visual-review")),
    ),
    "governance": ("实体治理", (("实体治理", "governance"),)),
    "history": (
        "历史与版本",
        (("审核历史与纠正", "corrections"), ("版本管理", "revisions")),
    ),
    "cases-reflection": (
        "案例与反思",
        (("案例库", "cases"), ("Reflection", "reflection")),
    ),
    "agents": ("Agent 协作", (("Agent 协作", "agents"),)),
    "health": ("系统状态", (("系统状态", "health"),)),
}

PAGE_META: dict[str, tuple[str, str]] = {
    "overview": ("总览", "运行、审核、校验和图存储状态"),
    "build": ("新建抽取与构建", "批量提交文档并选择可追溯的抽取或知识构建任务"),
    "execution": ("执行任务", "分支进度、执行时间线与安全恢复"),
    "entity-review": ("实体审核", "核对实体候选、证据与链接决定"),
    "claim-review": ("事实审核", "核对规范事实、冲突与原始证据"),
    "validation": ("校验问题", "检查阻断问题并保留排除审计"),
    "corrections": ("审核历史与纠正", "预览并应用可追溯的历史决定纠正"),
    "evidence": ("证据", "按运行和事实定位文本或视觉证据"),
    "graph": ("图谱", "检索实体并浏览有限邻域"),
    "media": ("媒体资产", "查看可校验的图片、图表、表格和公式出现记录"),
    "visual-review": ("视觉审核", "审核图片描绘关系、视觉属性与区域证据"),
    "governance": ("实体治理", "管理候选、合并、拆分与实体历史"),
    "cases": ("案例库", "查询审核案例及其索引状态"),
    "reflection": ("Reflection", "查看问题修复、案例使用与预算记录"),
    "agents": ("Agent 协作", "查看三 Agent 的结构化决策与交接轨迹"),
    "revisions": ("版本管理", "比较 Revision 并执行补偿回滚"),
    "health": ("系统状态", "检查应用、工作器与存储连接"),
}


def logo_path() -> Path:
    """Return the packaged branding asset used by the Gradio workspace."""
    path = Path(__file__).resolve().parents[1] / "assets" / "branding" / "prismke-logo-4k.png"
    if not path.is_file():
        raise RuntimeError(f"PrismKE logo is missing: {path}")
    return path


def group_choices() -> list[tuple[str, str]]:
    return [(label, group_id) for group_id, (label, _) in NAVIGATION_GROUPS.items()]


def page_choices(group_id: str) -> list[tuple[str, str]]:
    return list(NAVIGATION_GROUPS.get(group_id, NAVIGATION_GROUPS["overview"])[1])


def first_page(group_id: str) -> str:
    return page_choices(group_id)[0][1]


def all_page_ids() -> tuple[str, ...]:
    return tuple(page_id for _, pages in NAVIGATION_GROUPS.values() for _, page_id in pages)


def build_brand_header(gr: Any, version: str) -> Any:
    with gr.Column(elem_id="workspace-header", elem_classes="workspace-header"):
        with gr.Row(elem_id="workspace-topbar", elem_classes="workspace-topbar"):
            language_switch = gr.Checkbox(
                value=False,
                label="EN / CH",
                show_label=False,
                container=False,
                elem_id="language-switch",
                elem_classes="language-switch",
            )
        with gr.Column(elem_id="workspace-brand", elem_classes="workspace-brand-band"):
            gr.Image(
                value=str(logo_path()),
                format="png",
                image_mode="RGBA",
                interactive=False,
                show_label=False,
                buttons=[],
                container=False,
                elem_id="workspace-logo",
                alt_text="PrismKE",
            )
            gr.HTML(
                f'<p class="workspace-tagline">{TAGLINE}</p>'
                f'<p class="workspace-version">Development build · {version}</p>'
            )
    return language_switch


def page_header(gr: Any, page_id: str) -> None:
    title, description = PAGE_META[page_id]
    gr.HTML(f'<header class="workspace-page-header"><h1>{title}</h1><p>{description}</p></header>')
