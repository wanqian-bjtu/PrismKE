# domain 目录导读

**职责**：文档、知识、Schema、运行、审核、校验、案例等结构化领域契约。

**上下游**：依赖领域契约及本目录所列导入；上层 CLI/API/工作流可经应用服务或协议调用。跨层调用请以逐文件导入与调用点为准，不将动态注入写成静态依赖。

## 文件

- [__init__.py](__init__.md)：Stable public PrismKE domain contracts.（0 个符号）。
- [agents.py](agents.md)：Structured contracts exchanged by PrismKE's three semantic agents.（6 个符号）。
- [cases.py](cases.md)：Immutable review cases and bounded Reflection contracts.（7 个符号）。
- [documents.py](documents.md)：Document intermediate representation and evidence coordinates.（13 个符号）。
- [execution.py](execution.md)：Execution metadata is separate from knowledge and review state.（6 个符号）。
- [knowledge.py](knowledge.md)：Entities, claims, reviews, conflicts, and graph transactions.（25 个符号）。
- [reviews.py](reviews.md)：Immutable review history and optimistic correction contracts.（3 个符号）。
- [schema.py](schema.md)：Schema contracts and canonical vocabulary lookup.（14 个符号）。
- [validation.py](validation.md)：Portable validation reports, exclusion audit and commit provenance.（4 个符号）。
- [workflow.py](workflow.md)：Provider request contracts and persisted workflow state.（8 个符号）。

返回[总索引](../README.md)。
