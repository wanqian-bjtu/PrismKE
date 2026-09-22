源码：[__init__.py:1](../../../src/persistence/__init__.py#L1) | 基准：`dev/v0.10@f2f34d7` | 本文件符号数：0

**模块职责**：Persistent graph, evidence, checkpoint, and run stores.
**在系统中的位置**：图、证据、运行、审计、审核与案例的持久化；JSON/Neo4j 提供同一存储协议。
**直接依赖**：[src.persistence.audit](audit.md)、[src.persistence.cases](cases.md)、[src.persistence.entity_governance](entity_governance.md)、[src.persistence.file_evidence](file_evidence.md)、[src.persistence.json_graph](json_graph.md)、[src.persistence.migration](migration.md)、[src.persistence.neo4j_graph](neo4j_graph.md)、[src.persistence.runs](runs.md)、[src.persistence.runtime_config](runtime_config.md)；外部/标准库：无。
**主要调用方（静态导入）**：[agents/entity_governance_agent.py](../agents/entity_governance_agent.md)、[agents/fusion_review_agent.py](../agents/fusion_review_agent.md)、[agents/multimodal_extraction_agent.py](../agents/multimodal_extraction_agent.md)、[api/app.py](../api/app.md)、[cli.py](../cli.md)、[evaluation/document_validation.py](../evaluation/document_validation.md)、[evaluation/entity_linking.py](../evaluation/entity_linking.md)、[evaluation/reflection.py](../evaluation/reflection.md)、[governance/entity_index.py](../governance/entity_index.md)、[governance/entity_operations.py](../governance/entity_operations.md)、[governance/entity_resolution.py](../governance/entity_resolution.md)、[governance/validation/service.py](../governance/validation/service.md)。
**阅读提示**：下列流程根据当前源码控制流整理；`self`/接口对象的实际类型可能在运行时注入，未能静态解析的调用会明确标注。链接指向源码行或对应讲解文件。

---

# 模块导出与初始化 ⭐

**重要性**：包适配或常量导出；本文件未定义类或函数。

**行为**：阅读 [__init__.py:1](../../../src/persistence/__init__.py#L1) 中的导入、`__all__` 与模块级赋值；导入该模块时模块级语句仍会执行。
