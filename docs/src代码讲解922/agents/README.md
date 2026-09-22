# agents 目录导读

**职责**：三个语义 Agent 及其预算、轨迹工具；把抽取、治理、融合审核的职责显式化，但不直接写图。

**上下游**：依赖领域契约及本目录所列导入；上层 CLI/API/工作流可经应用服务或协议调用。跨层调用请以逐文件导入与调用点为准，不将动态注入写成静态依赖。

## 文件

- [__init__.py](__init__.md)：Bounded semantic agents; the LangGraph coordinator remains deterministic.（0 个符号）。
- [budget.py](budget.md)：Shared conservative budget accounting for optional semantic advice.（4 个符号）。
- [entity_governance_agent.py](entity_governance_agent.md)：EntityGovernanceAgent with guarded gray-zone advice.（5 个符号）。
- [fusion_review_agent.py](fusion_review_agent.md)：FusionReviewAgent; graph writes remain outside this agent.（6 个符号）。
- [multimodal_extraction_agent.py](multimodal_extraction_agent.md)：MultimodalExtractionAgent with explicit tool choice and evidence handoff.（8 个符号）。
- [trace.py](trace.md)：Compact, idempotent agent handoffs and decision traces.（3 个符号）。

返回[总索引](../README.md)。
