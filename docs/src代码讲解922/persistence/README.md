# persistence 目录导读

**职责**：图、证据、运行、审计、审核与案例的持久化；JSON/Neo4j 提供同一存储协议。

**上下游**：依赖领域契约及本目录所列导入；上层 CLI/API/工作流可经应用服务或协议调用。跨层调用请以逐文件导入与调用点为准，不将动态注入写成静态依赖。

## 文件

- [__init__.py](__init__.md)：Persistent graph, evidence, checkpoint, and run stores.（0 个符号）。
- [audit.py](audit.md)：Append-only audit records for review and rollback operations.（3 个符号）。
- [base.py](base.md)：Persistence extension boundaries.（26 个符号）。
- [cases.py](cases.md)：Immutable review-case store and rebuildable dense embeddings.（15 个符号）。
- [checkpoints.py](checkpoints.md)：LangGraph SQLite checkpointer lifecycle.（1 个符号）。
- [entity_governance.py](entity_governance.md)：Durable review queue for entity governance proposals.（9 个符号）。
- [execution.py](execution.md)：Durable execution state, immutable transitions and private response journal.（18 个符号）。
- [file_evidence.py](file_evidence.md)：Immutable content-addressed evidence storage.（18 个符号）。
- [json_graph.py](json_graph.md)：Atomic local graph persistence with revisions and compensating rollback.（25 个符号）。
- [legacy_evidence.py](legacy_evidence.md)：Audited repair of historical integration-test claims in an isolated graph.（8 个符号）。
- [migration.py](migration.md)：Idempotent JSON graph migration helpers.（2 个符号）。
- [neo4j_graph.py](neo4j_graph.md)：Neo4j graph store using one managed transaction per GraphCommit.（25 个符号）。
- [reviews.py](reviews.md)：Authoritative review events and transactional projection outbox.（14 个符号）。
- [runs.py](runs.md)：User-facing serialized workflow summaries.（11 个符号）。
- [runtime_config.py](runtime_config.md)：Private runtime configuration overrides with redacted public views.（6 个符号）。

返回[总索引](../README.md)。
