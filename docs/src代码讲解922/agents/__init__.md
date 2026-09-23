源码：[__init__.py:1](../../../src/agents/__init__.py#L1) | 基准：`dev/v0.10@f2f34d7` | 本文件符号数：0

**模块职责**：Bounded semantic agents; the LangGraph coordinator remains deterministic.
**在系统中的位置**：三个语义 Agent 及其预算、轨迹工具；把抽取、治理、融合审核的职责显式化，但不直接写图。
**直接依赖**：无显式项目内模块导入；外部/标准库：无。
**主要调用方（静态导入）**：[agents/entity_governance_agent.py](entity_governance_agent.md)、[agents/fusion_review_agent.py](fusion_review_agent.md)、[agents/multimodal_extraction_agent.py](multimodal_extraction_agent.md)、[workflow/nodes.py](../workflow/nodes.md)、[workflow/service.py](../workflow/service.md)。
**阅读提示**：下列流程根据当前源码控制流整理；`self`/接口对象的实际类型可能在运行时注入，未能静态解析的调用会明确标注。链接指向源码行或对应讲解文件。

---

# 模块导出与初始化 ⭐

**重要性**：包适配或常量导出；本文件未定义类或函数。

**行为**：阅读 [__init__.py:1](../../../src/agents/__init__.py#L1) 中的导入、`__all__` 与模块级赋值；导入该模块时模块级语句仍会执行。
