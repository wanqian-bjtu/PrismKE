源码：[trace.py:1](../../../src/agents/trace.py#L1) | 基准：`dev/v0.10@f2f34d7` | 本文件符号数：3

**模块职责**：Compact, idempotent agent handoffs and decision traces.
**在系统中的位置**：三个语义 Agent 及其预算、轨迹工具；把抽取、治理、融合审核的职责显式化，但不直接写图。
**直接依赖**：[src.core.ids](../core/ids.md)、[src.domain.agents](../domain/agents.md)、[src.domain.workflow](../domain/workflow.md)；外部/标准库：`__future__`、`re`。
**主要调用方（静态导入）**：[agents/entity_governance_agent.py](entity_governance_agent.md)、[agents/fusion_review_agent.py](fusion_review_agent.md)、[agents/multimodal_extraction_agent.py](multimodal_extraction_agent.md)。
**阅读提示**：下列流程根据当前源码控制流整理；`self`/接口对象的实际类型可能在运行时注入，未能静态解析的调用会明确标注。链接指向源码行或对应讲解文件。

---

# safe_reason_code ⭐⭐

**位置与等级**：[trace.py:22](../../../src/agents/trace.py#L22)；局部辅助逻辑，需理解其调用条件与失败传播。

**签名**：`def safe_reason_code(value: str) -> str`。

**作用**：处理 `safe_reason_code` 对应步骤；下列步骤依据函数体的实际控制流和调用点整理。

**输入与输出**：
- 输入：`value`（str）。
- 输出类型：`str`；具体返回路径见流程步骤。

**处理流程**：
1. 更新 `normalized`，值来自 `value.strip().lower()`。
2. 检查 `re.fullmatch(<字符串常量>, normalized)`；按条件分流，else 分支不存在。
3. 返回 `'model_reason_untrusted'`。

**关键条件与保护**：
- [trace.py:24](../../../src/agents/trace.py#L24)：`re.fullmatch(<字符串常量>, normalized)`，不满足时跳过本分支。

**调用与被调用**：
- `value.strip().lower`（[trace.py:23](../../../src/agents/trace.py#L23)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `value.strip`（[trace.py:23](../../../src/agents/trace.py#L23)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `re.fullmatch`（[trace.py:24](../../../src/agents/trace.py#L24)）：来自 `re`；具体实现可能由依赖注入或运行时分派决定。
- 静态可定位的调用方：[EntityGovernanceAgent._advise_gray_zone](entity_governance_agent.md)、[FusionReviewAgent._assess_related_groups](fusion_review_agent.md)。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：未见 `raise`；下游异常可能继续上抛。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。
- 恢复/幂等性：仅在代码有检查点、事务、请求编号或显式去重时才成立；此函数不能单凭名称视为可安全重试。


---

# trace_step ⭐⭐

**位置与等级**：[trace.py:29](../../../src/agents/trace.py#L29)；局部辅助逻辑，需理解其调用条件与失败传播。

**签名**：`def trace_step(state: WorkflowState, agent: AgentRole, step: str, decision: str, *, tools: tuple[str, ...]=(), reasons: tuple[str, ...]=(), input_ids: tuple[str, ...]=(), output_ids: tuple[str, ...]=(), model_fingerprint: str | None=None, token_usage: int | None=None, latency_ms: float | None=None, status: str='succeeded') -> None`。

**作用**：处理 `trace_step` 对应步骤；下列步骤依据函数体的实际控制流和调用点整理。

**输入与输出**：
- 输入：`state`（WorkflowState；跨节点 WorkflowState；调用方须保持证据与状态一致）；`agent`（AgentRole）；`step`（str）；`decision`（str）；`tools`（tuple[str, ...]；默认 `()`）；`reasons`（tuple[str, ...]；默认 `()`）；`input_ids`（tuple[str, ...]；默认 `()`）；`output_ids`（tuple[str, ...]；默认 `()`）；`model_fingerprint`（str | None；默认 `None`）；`token_usage`（int | None；默认 `None`）；`latency_ms`（float | None；默认 `None`）；`status`（str；默认 `'succeeded'`）。
- 输出类型：`None`；具体返回路径见流程步骤。

**处理流程**：
1. 更新 `unknown`，值来自 `set(tools) - ALLOWED_TOOLS[agent]`。
2. 检查 `unknown`；按条件分流，else 分支不存在。
3. 更新 `trace`，值来自 `AgentTrace(id=stable_id('agent-trace', state.run_id, agent, step, *input_ids, *output_ids), run_id=…`。
4. 更新 `existing`，值来自 `{item.id: index for index, item in enumerate(state.agent_traces)}`。
5. 检查 `trace.id in existing`；按条件分流，else 分支存在。

**关键条件与保护**：
- [trace.py:45](../../../src/agents/trace.py#L45)：`unknown`，不满足时跳过本分支。
- [trace.py:63](../../../src/agents/trace.py#L63)：`trace.id in existing`，不满足时有 else 分支。

**调用与被调用**：
- `set`（[trace.py:44](../../../src/agents/trace.py#L44)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `ValueError`（[trace.py:46](../../../src/agents/trace.py#L46)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `sorted`（[trace.py:46](../../../src/agents/trace.py#L46)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `AgentTrace`（调用点 [trace.py:47](../../../src/agents/trace.py#L47)）→ [AgentTrace](../domain/agents.md)，静态可定位。
- `stable_id`（调用点 [trace.py:48](../../../src/agents/trace.py#L48)）→ [stable_id](../core/ids.md)，静态可定位。
- `list`（[trace.py:52](../../../src/agents/trace.py#L52)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `enumerate`（[trace.py:62](../../../src/agents/trace.py#L62)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `state.agent_traces.append`（[trace.py:66](../../../src/agents/trace.py#L66)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- 静态可定位的调用方：[EntityGovernanceAgent.resolve](entity_governance_agent.md)、[EntityGovernanceAgent._advise_gray_zone](entity_governance_agent.md)、[EntityGovernanceAgent.normalize](entity_governance_agent.md)、[FusionReviewAgent.triage_candidates](fusion_review_agent.md)、[FusionReviewAgent.detect_conflicts](fusion_review_agent.md)、[FusionReviewAgent._assess_related_groups](fusion_review_agent.md)、[FusionReviewAgent.route_by_risk](fusion_review_agent.md)、[MultimodalExtractionAgent.recognize](multimodal_extraction_agent.md)、[MultimodalExtractionAgent.extract_text](multimodal_extraction_agent.md)、[MultimodalExtractionAgent.extract_visual](multimodal_extraction_agent.md)。

**状态、副作用与异常**：
- 显式状态/容器赋值：`state.agent_traces[existing[trace.id]]`。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：`ValueError(f<字符串常量>)`。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。
- 恢复/幂等性：仅在代码有检查点、事务、请求编号或显式去重时才成立；此函数不能单凭名称视为可安全重试。


---

# handoff ⭐⭐

**位置与等级**：[trace.py:69](../../../src/agents/trace.py#L69)；局部辅助逻辑，需理解其调用条件与失败传播。

**签名**：`def handoff(state: WorkflowState, agent: AgentRole, *, input_ids: tuple[str, ...], output_ids: tuple[str, ...], evidence_ids: tuple[str, ...]=(), issue_ids: tuple[str, ...]=(), review_task_ids: tuple[str, ...]=(), next_action: str='continue') -> None`。

**作用**：处理 `handoff` 对应步骤；下列步骤依据函数体的实际控制流和调用点整理。

**输入与输出**：
- 输入：`state`（WorkflowState；跨节点 WorkflowState；调用方须保持证据与状态一致）；`agent`（AgentRole）；`input_ids`（tuple[str, ...]）；`output_ids`（tuple[str, ...]）；`evidence_ids`（tuple[str, ...]；默认 `()`）；`issue_ids`（tuple[str, ...]；默认 `()`）；`review_task_ids`（tuple[str, ...]；默认 `()`）；`next_action`（str；默认 `'continue'`）。
- 输出类型：`None`；具体返回路径见流程步骤。

**处理流程**：
1. 更新 `item`，值来自 `AgentHandoff(id=stable_id('agent-handoff', state.run_id, agent, *input_ids, *output_ids), run_id=st…`。
2. 更新 `existing`，值来自 `{record.id: index for index, record in enumerate(state.agent_handoffs)}`。
3. 检查 `item.id in existing`；按条件分流，else 分支存在。

**关键条件与保护**：
- [trace.py:92](../../../src/agents/trace.py#L92)：`item.id in existing`，不满足时有 else 分支。

**调用与被调用**：
- `AgentHandoff`（调用点 [trace.py:80](../../../src/agents/trace.py#L80)）→ [AgentHandoff](../domain/agents.md)，静态可定位。
- `stable_id`（调用点 [trace.py:81](../../../src/agents/trace.py#L81)）→ [stable_id](../core/ids.md)，静态可定位。
- `list`（[trace.py:84](../../../src/agents/trace.py#L84)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `enumerate`（[trace.py:91](../../../src/agents/trace.py#L91)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `state.agent_handoffs.append`（[trace.py:95](../../../src/agents/trace.py#L95)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- 静态可定位的调用方：[EntityGovernanceAgent.resolve](entity_governance_agent.md)、[EntityGovernanceAgent.normalize](entity_governance_agent.md)、[FusionReviewAgent.route_by_risk](fusion_review_agent.md)、[MultimodalExtractionAgent.align](multimodal_extraction_agent.md)。

**状态、副作用与异常**：
- 显式状态/容器赋值：`state.agent_handoffs[existing[item.id]]`。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：未见 `raise`；下游异常可能继续上抛。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。
- 恢复/幂等性：仅在代码有检查点、事务、请求编号或显式去重时才成立；此函数不能单凭名称视为可安全重试。


---
