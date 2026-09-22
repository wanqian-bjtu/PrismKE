# governance 目录导读

**职责**：实体解析、事实规范化、冲突、风险、审核及实体操作的确定性规则。

**上下游**：依赖领域契约及本目录所列导入；上层 CLI/API/工作流可经应用服务或协议调用。跨层调用请以逐文件导入与调用点为准，不将动态注入写成静态依赖。

## 文件

- [__init__.py](__init__.md)：Entity and claim governance services.（0 个符号）。
- [alignment.py](alignment.md)：Deterministic, auditable cross-modal candidate alignment.（5 个符号）。
- [claim_normalization.py](claim_normalization.md)：Schema-aware claim normalization and supporting-evidence merging.（4 个符号）。
- [conflicts.py](conflicts.md)：Cardinality-aware and time-aware claim conflict detection.（6 个符号）。
- [entity_index.py](entity_index.md)：Entity embedding index preparation and idempotent rebuilds.（2 个符号）。
- [entity_operations.py](entity_operations.md)：Auditable merge and split operations for canonical entities.（7 个符号）。
- [entity_resolution.py](entity_resolution.md)：Deterministic and semantic entity linking with conservative governance.（19 个符号）。
- [review_guards.py](review_guards.md)：Exact compensation and optimistic resource guards shared by graph backends.（1 个符号）。
- [risk.py](risk.md)：Confidence and conflict-based review routing.（1 个符号）。

## 子目录

- [validation](validation/README.md)：候选及提交前的统一结构、Schema、引用和证据校验。

返回[总索引](../README.md)。
