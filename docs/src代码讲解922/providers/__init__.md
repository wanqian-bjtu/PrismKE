源码：[__init__.py:1](../../../src/providers/__init__.py#L1) | 基准：`dev/v0.10@f2f34d7` | 本文件符号数：0

**模块职责**：Model provider implementations.
**在系统中的位置**：LLM、OCR、VLM、Embedding、Reflection 与语义建议的外部能力接口和实现。
**直接依赖**：[src.providers.embedding](embedding.md)、[src.providers.mock](mock.md)、[src.providers.ocr](ocr.md)、[src.providers.openai_compatible](openai_compatible.md)、[src.providers.reflection](reflection.md)、[src.providers.vlm](vlm.md)；外部/标准库：无。
**主要调用方（静态导入）**：[agents/entity_governance_agent.py](../agents/entity_governance_agent.md)、[agents/fusion_review_agent.py](../agents/fusion_review_agent.md)、[agents/multimodal_extraction_agent.py](../agents/multimodal_extraction_agent.md)、[cli.py](../cli.md)、[evaluation/document_validation.py](../evaluation/document_validation.md)、[evaluation/entity_linking.py](../evaluation/entity_linking.md)、[evaluation/reflection.py](../evaluation/reflection.md)、[governance/entity_index.py](../governance/entity_index.md)、[governance/entity_operations.py](../governance/entity_operations.md)、[governance/entity_resolution.py](../governance/entity_resolution.md)、[providers/http_client.py](http_client.md)、[providers/mock.py](mock.md)。
**阅读提示**：下列流程根据当前源码控制流整理；`self`/接口对象的实际类型可能在运行时注入，未能静态解析的调用会明确标注。链接指向源码行或对应讲解文件。

---

# 模块导出与初始化 ⭐

**重要性**：包适配或常量导出；本文件未定义类或函数。

**行为**：阅读 [__init__.py:1](../../../src/providers/__init__.py#L1) 中的导入、`__all__` 与模块级赋值；导入该模块时模块级语句仍会执行。
