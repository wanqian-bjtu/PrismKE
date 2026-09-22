源码：[__init__.py:1](../../../src/governance/__init__.py#L1) | 基准：`dev/v0.10@f2f34d7` | 本文件符号数：0

**模块职责**：Entity and claim governance services.
**在系统中的位置**：实体解析、事实规范化、冲突、风险、审核及实体操作的确定性规则。
**直接依赖**：[src.governance.alignment](alignment.md)、[src.governance.claim_normalization](claim_normalization.md)、[src.governance.conflicts](conflicts.md)、[src.governance.entity_index](entity_index.md)、[src.governance.entity_operations](entity_operations.md)、[src.governance.entity_resolution](entity_resolution.md)、[src.governance.risk](risk.md)；外部/标准库：无。
**主要调用方（静态导入）**：[agents/entity_governance_agent.py](../agents/entity_governance_agent.md)、[agents/fusion_review_agent.py](../agents/fusion_review_agent.md)、[agents/multimodal_extraction_agent.py](../agents/multimodal_extraction_agent.md)、[cli.py](../cli.md)、[evaluation/document_validation.py](../evaluation/document_validation.md)、[evaluation/entity_linking.py](../evaluation/entity_linking.md)、[governance/entity_index.py](entity_index.md)、[governance/entity_operations.py](entity_operations.md)、[governance/validation/__init__.py](validation/__init__.md)、[governance/validation/service.py](validation/service.md)、[persistence/json_graph.py](../persistence/json_graph.md)、[persistence/neo4j_graph.py](../persistence/neo4j_graph.md)。
**阅读提示**：下列流程根据当前源码控制流整理；`self`/接口对象的实际类型可能在运行时注入，未能静态解析的调用会明确标注。链接指向源码行或对应讲解文件。

---

# 模块导出与初始化 ⭐

**重要性**：包适配或常量导出；本文件未定义类或函数。

**行为**：阅读 [__init__.py:1](../../../src/governance/__init__.py#L1) 中的导入、`__all__` 与模块级赋值；导入该模块时模块级语句仍会执行。
