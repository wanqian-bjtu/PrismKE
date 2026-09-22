# evaluation 目录导读

**职责**：离线评测、预算账本、标注导出及报告；不等于生产工作流。

**上下游**：依赖领域契约及本目录所列导入；上层 CLI/API/工作流可经应用服务或协议调用。跨层调用请以逐文件导入与调用点为准，不将动态注入写成静态依赖。

## 文件

- [__init__.py](__init__.md)：Small, reproducible multimodal evaluation utilities.（0 个符号）。
- [annotations.py](annotations.md)：Read-only conversion of reviewed workbooks into isolated evaluation inputs.（5 个符号）。
- [baseline_report.py](baseline_report.md)：Human-readable baseline results without copying original document contexts.（1 个符号）。
- [document_review.py](document_review.md)：Evidence-aware review tables for partially annotated real documents, not full-text F1.（6 个符号）。
- [document_validation.py](document_validation.md)：Live document validation against an isolated JSON graph, without gold-assisted review.（18 个符号）。
- [entity_linking.py](entity_linking.md)：Reproducible evaluation for v0.4 entity linking and deduplication.（3 个符号）。
- [models.py](models.md)：Evaluation manifest and report models.（5 个符号）。
- [reflection.py](reflection.md)：Isolated nine-cell case retrieval and Reflection release evaluation.（10 个符号）。
- [request_budget.py](request_budget.md)：Shared, sanitized request accounting for bounded live evaluation only.（13 个符号）。
- [runner.py](runner.md)：Run a public evaluation manifest through the application service.（11 个符号）。

返回[总索引](../README.md)。
