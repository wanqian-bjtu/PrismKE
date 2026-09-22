源码：[visual_assets.py:1](../../../src/parsing/visual_assets.py#L1) | 基准：`dev/v0.10@f2f34d7` | 本文件符号数：1

**模块职责**：Select non-overlapping visual assets for OCR and VLM analysis.
**在系统中的位置**：输入文档适配、格式注册与视觉资产提取，向后续抽取提供 DocumentIR。
**直接依赖**：[src.domain](../domain/__init__.md)；外部/标准库：无。
**主要调用方（静态导入）**：[evaluation/document_review.py](../evaluation/document_review.md)、[parsing/__init__.py](__init__.md)、[providers/ocr.py](../providers/ocr.md)。
**阅读提示**：下列流程根据当前源码控制流整理；`self`/接口对象的实际类型可能在运行时注入，未能静态解析的调用会明确标注。链接指向源码行或对应讲解文件。

---

# select_analysis_assets ⭐⭐⭐

**位置与等级**：[visual_assets.py:6](../../../src/parsing/visual_assets.py#L6)；关键支撑逻辑，影响候选、证据或接口的正确传递。

**签名**：`def select_analysis_assets(document: DocumentIR) -> list[MediaAsset]`。

**作用**：Prefer a rendered scan over embedded images from the same textless PDF page.

**输入与输出**：
- 输入：`document`（DocumentIR；解析后的文档及其文本、媒体、证据定位）。
- 输出类型：`list[MediaAsset]`；具体返回路径见流程步骤。

**处理流程**：
1. 更新 `rendered_scan_pages`，值来自 `{asset.page_number for asset in document.media_assets if asset.origin == 'pdf_page_render' and asse…`。
2. 返回 `[asset for asset in document.media_assets if not (asset.origin == 'pdf_embedded' and asset.page_number i…`。

**调用与被调用**：
- 无显式函数调用，或仅声明协议/常量。
- 静态可定位的调用方：[document_coverage](../evaluation/document_review.md)、[PaddleOCRProvider._recognize_sync](../providers/ocr.md)。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：未见 `raise`；下游异常可能继续上抛。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。


---
