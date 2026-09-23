# workflow 目录导读

**职责**：应用服务、LangGraph 编排、执行状态、审核接续、图提交及纠正流程。

**上下游**：依赖领域契约及本目录所列导入；上层 CLI/API/工作流可经应用服务或协议调用。跨层调用请以逐文件导入与调用点为准，不将动态注入写成静态依赖。

## 文件

- [__init__.py](__init__.md)：PrismKE application workflow.（0 个符号）。
- [cases.py](cases.md)：Review-case projection, semantic retrieval and index maintenance.（15 个符号）。
- [corrections.py](corrections.md)：Review correction previews and tail-only, auditable compensation workflows.（6 个符号）。
- [execution.py](execution.md)：One durable worker per workspace, with conservative restart reconciliation.（43 个符号）。
- [graph.py](graph.md)：Persistent LangGraph execution and exact-node recovery.（23 个符号）。
- [nodes.py](nodes.md)：Workflow node implementations.（18 个符号）。
- [reflection.py](reflection.md)：Case-assisted, budget-bounded candidate Reflection.（4 个符号）。
- [review_details.py](review_details.md)：Source-backed review views; risk flags are prompts, never automatic verdicts.（5 个符号）。
- [review_workspace.py](review_workspace.md)：Verified, offline-only copies of completed extraction checkpoints.（4 个符号）。
- [reviews.py](reviews.md)：Review decisions, immutable events and recoverable checkpoint projections.（8 个符号）。
- [service.py](service.md)：Application service shared by CLI and future API/UI adapters.（50 个符号）。

返回[总索引](../README.md)。
