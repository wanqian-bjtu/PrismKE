# providers 目录导读

**职责**：LLM、OCR、VLM、Embedding、Reflection 与语义建议的外部能力接口和实现。

**上下游**：依赖领域契约及本目录所列导入；上层 CLI/API/工作流可经应用服务或协议调用。跨层调用请以逐文件导入与调用点为准，不将动态注入写成静态依赖。

## 文件

- [__init__.py](__init__.md)：Model provider implementations.（0 个符号）。
- [base.py](base.md)：Model provider extension boundaries.（19 个符号）。
- [common.py](common.md)：Shared conversion from provider payloads to domain claims.（3 个符号）。
- [embedding.py](embedding.md)：Local dense embedding providers used by entity resolution.（14 个符号）。
- [http_client.py](http_client.md)：Shared, sanitized OpenAI-compatible HTTP transport.（5 个符号）。
- [mock.py](mock.md)：Deterministic providers for tests and offline demonstrations.（6 个符号）。
- [ocr.py](ocr.md)：Disabled, mock, and PaddleOCR implementations.（12 个符号）。
- [openai_compatible.py](openai_compatible.md)：OpenAI-compatible text extraction provider.（5 个符号）。
- [pricing.py](pricing.md)：Versioned list-price estimates for provider call telemetry.（1 个符号）。
- [reflection.py](reflection.md)：Bounded Reflection providers for candidate repair.（11 个符号）。
- [semantic.py](semantic.md)：Bounded OpenAI-compatible advice for uncertain agent decisions.（16 个符号）。
- [validation.py](validation.md)：Per-item structure quarantine without storing raw model responses.（2 个符号）。
- [vlm.py](vlm.md)：OpenAI-compatible multimodal extraction provider.（12 个符号）。

返回[总索引](../README.md)。
