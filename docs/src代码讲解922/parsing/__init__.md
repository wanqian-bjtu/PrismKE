源码：[__init__.py:1](../../../src/parsing/__init__.py#L1) | 基准：`dev/v0.10@f2f34d7` | 本文件符号数：0

**模块职责**：Document parsing adapters.
**在系统中的位置**：输入文档适配、格式注册与视觉资产提取，向后续抽取提供 DocumentIR。
**直接依赖**：[src.parsing.registry](registry.md)、[src.parsing.visual_assets](visual_assets.md)；外部/标准库：无。
**主要调用方（静态导入）**：[agents/multimodal_extraction_agent.py](../agents/multimodal_extraction_agent.md)、[evaluation/document_review.py](../evaluation/document_review.md)、[parsing/registry.py](registry.md)、[providers/ocr.py](../providers/ocr.md)、[workflow/graph.py](../workflow/graph.md)、[workflow/nodes.py](../workflow/nodes.md)、[workflow/service.py](../workflow/service.md)。
**阅读提示**：下列流程根据当前源码控制流整理；`self`/接口对象的实际类型可能在运行时注入，未能静态解析的调用会明确标注。链接指向源码行或对应讲解文件。

---

# 模块导出与初始化 ⭐

**重要性**：包适配或常量导出；本文件未定义类或函数。

**行为**：阅读 [__init__.py:1](../../../src/parsing/__init__.py#L1) 中的导入、`__all__` 与模块级赋值；导入该模块时模块级语句仍会执行。
