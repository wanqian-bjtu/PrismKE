源码：[budget.py:1](../../../src/agents/budget.py#L1) | 基准：`dev/v0.10@f2f34d7` | 本文件符号数：4

**模块职责**：Shared conservative budget accounting for optional semantic advice.
**在系统中的位置**：三个语义 Agent 及其预算、轨迹工具；把抽取、治理、融合审核的职责显式化，但不直接写图。
**直接依赖**：[src.core.errors](../core/errors.md)、[src.domain](../domain/__init__.md)；外部/标准库：`__future__`。
**主要调用方（静态导入）**：[agents/entity_governance_agent.py](entity_governance_agent.md)、[agents/fusion_review_agent.py](fusion_review_agent.md)。
**阅读提示**：下列流程根据当前源码控制流整理；`self`/接口对象的实际类型可能在运行时注入，未能静态解析的调用会明确标注。链接指向源码行或对应讲解文件。

---

# UnknownAgentUsageError ⭐⭐⭐⭐

**位置与等级**：[budget.py:11](../../../src/agents/budget.py#L11)；承担主要 Agent、应用服务或审核/执行入口，跨模块影响显著。

**职责**：失败类型；调用方可据此区分可恢复、阻断和一般错误。基类：`RuntimeError`。
**源码说明**：A model response without verifiable usage must block further calls.

**字段与类级约束**：
- 类体未直接声明字段；实例状态请看 `__init__` 及方法中的赋值。

**内部成员**：此类未直接定义方法；字段/继承行为见源码。


---

# can_request ⭐⭐

**位置与等级**：[budget.py:15](../../../src/agents/budget.py#L15)；局部辅助逻辑，需理解其调用条件与失败传播。

**签名**：`def can_request(state: WorkflowState) -> bool`。

**作用**：处理 `can_request` 对应步骤；下列步骤依据函数体的实际控制流和调用点整理。

**输入与输出**：
- 输入：`state`（WorkflowState；跨节点 WorkflowState；调用方须保持证据与状态一致）。
- 输出类型：`bool`；具体返回路径见流程步骤。

**处理流程**：
1. 返回 `state.semantic_advisor_name != 'disabled' and state.agent_token_usage + MIN_REQUEST_RESERVE <= state.age…`。

**调用与被调用**：
- 无显式函数调用，或仅声明协议/常量。
- 静态可定位的调用方：[EntityGovernanceAgent._advise_gray_zone](entity_governance_agent.md)、[FusionReviewAgent._assess_related_groups](fusion_review_agent.md)。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：未见 `raise`；下游异常可能继续上抛。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。
- 恢复/幂等性：仅在代码有检查点、事务、请求编号或显式去重时才成立；此函数不能单凭名称视为可安全重试。


---

# record_call ⭐⭐

**位置与等级**：[budget.py:22](../../../src/agents/budget.py#L22)；局部辅助逻辑，需理解其调用条件与失败传播。

**签名**：`def record_call(state: WorkflowState, record: ProviderCallRecord | None) -> None`。

**作用**：创建、更新或记录相应资源；写入/审计边界以实际调用和状态赋值为准。

**输入与输出**：
- 输入：`state`（WorkflowState；跨节点 WorkflowState；调用方须保持证据与状态一致）；`record`（ProviderCallRecord | None）。
- 输出类型：`None`；具体返回路径见流程步骤。

**处理流程**：
1. 检查 `record is None`；按条件分流，else 分支不存在。
2. 检查 `record.id not in {item.id for item in state.provider_calls}`；按条件分流，else 分支不存在。

**关键条件与保护**：
- [budget.py:23](../../../src/agents/budget.py#L23)：`record is None`，不满足时跳过本分支。
- [budget.py:25](../../../src/agents/budget.py#L25)：`record.id not in {item.id for item in state.provider_calls}`，不满足时跳过本分支。
- [budget.py:27](../../../src/agents/budget.py#L27)：`record.total_tokens is None`，不满足时跳过本分支。

**调用与被调用**：
- `state.provider_calls.append`（[budget.py:26](../../../src/agents/budget.py#L26)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `UnknownAgentUsageError`（调用点 [budget.py:28](../../../src/agents/budget.py#L28)）→ [UnknownAgentUsageError](budget.md)，静态可定位。
- 静态可定位的调用方：[record_response_failure](budget.md)、[EntityGovernanceAgent._advise_gray_zone](entity_governance_agent.md)、[FusionReviewAgent._assess_related_groups](fusion_review_agent.md)。

**状态、副作用与异常**：
- 显式状态/容器赋值：`state.agent_token_usage`。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：`UnknownAgentUsageError(<字符串常量>)`。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。
- 恢复/幂等性：仅在代码有检查点、事务、请求编号或显式去重时才成立；此函数不能单凭名称视为可安全重试。


---

# record_response_failure ⭐⭐

**位置与等级**：[budget.py:34](../../../src/agents/budget.py#L34)；局部辅助逻辑，需理解其调用条件与失败传播。

**签名**：`def record_response_failure(state: WorkflowState, exc: ProviderResponseError) -> None`。

**作用**：创建、更新或记录相应资源；写入/审计边界以实际调用和状态赋值为准。

**输入与输出**：
- 输入：`state`（WorkflowState；跨节点 WorkflowState；调用方须保持证据与状态一致）；`exc`（ProviderResponseError）。
- 输出类型：`None`；具体返回路径见流程步骤。

**处理流程**：
1. 遍历 `getattr(exc, 'call_records', [])`，逐项处理 `record`。

**调用与被调用**：
- `getattr`（[budget.py:35](../../../src/agents/budget.py#L35)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `record_call`（调用点 [budget.py:36](../../../src/agents/budget.py#L36)）→ [record_call](budget.md)，静态可定位。
- 静态可定位的调用方：[EntityGovernanceAgent._advise_gray_zone](entity_governance_agent.md)、[FusionReviewAgent._assess_related_groups](fusion_review_agent.md)。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：未见 `raise`；下游异常可能继续上抛。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。
- 恢复/幂等性：仅在代码有检查点、事务、请求编号或显式去重时才成立；此函数不能单凭名称视为可安全重试。


---
