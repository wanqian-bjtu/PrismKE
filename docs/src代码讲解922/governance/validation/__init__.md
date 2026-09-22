源码：[__init__.py:1](../../../../src/governance/validation/__init__.py#L1) | 基准：`dev/v0.10@f2f34d7` | 本文件符号数：0

**模块职责**：Shared deterministic validation, used by providers, workflows and stores.
**在系统中的位置**：候选及提交前的统一结构、Schema、引用和证据校验。
**直接依赖**：[src.governance.validation.service](service.md)；外部/标准库：无。
**主要调用方（静态导入）**：[agents/entity_governance_agent.py](../../agents/entity_governance_agent.md)、[governance/entity_operations.py](../entity_operations.md)、[persistence/json_graph.py](../../persistence/json_graph.md)、[persistence/neo4j_graph.py](../../persistence/neo4j_graph.md)、[providers/openai_compatible.py](../../providers/openai_compatible.md)、[providers/validation.py](../../providers/validation.md)、[providers/vlm.py](../../providers/vlm.md)、[workflow/graph.py](../../workflow/graph.md)、[workflow/nodes.py](../../workflow/nodes.md)、[workflow/reflection.py](../../workflow/reflection.md)、[workflow/service.py](../../workflow/service.md)。
**阅读提示**：下列流程根据当前源码控制流整理；`self`/接口对象的实际类型可能在运行时注入，未能静态解析的调用会明确标注。链接指向源码行或对应讲解文件。

---

# 模块导出与初始化 ⭐

**重要性**：包适配或常量导出；本文件未定义类或函数。

**行为**：阅读 [__init__.py:1](../../../../src/governance/validation/__init__.py#L1) 中的导入、`__all__` 与模块级赋值；导入该模块时模块级语句仍会执行。
