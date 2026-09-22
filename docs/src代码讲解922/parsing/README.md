# parsing 目录导读

**职责**：输入文档适配、格式注册与视觉资产提取，向后续抽取提供 DocumentIR。

**上下游**：依赖领域契约及本目录所列导入；上层 CLI/API/工作流可经应用服务或协议调用。跨层调用请以逐文件导入与调用点为准，不将动态注入写成静态依赖。

## 文件

- [__init__.py](__init__.md)：Document parsing adapters.（0 个符号）。
- [adapters.py](adapters.md)：Built-in document parsers with multimodal asset provenance.（31 个符号）。
- [base.py](base.md)：Parser extension boundary.（3 个符号）。
- [registry.py](registry.md)：Parser selection by media type.（3 个符号）。
- [visual_assets.py](visual_assets.md)：Select non-overlapping visual assets for OCR and VLM analysis.（1 个符号）。

返回[总索引](../README.md)。
