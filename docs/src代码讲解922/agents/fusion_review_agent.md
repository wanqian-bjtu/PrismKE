源码：[fusion_review_agent.py:1](../../../src/agents/fusion_review_agent.py#L1) | 基准：`dev/v0.10@f2f34d7` | 本文件符号数：6

**模块职责**：FusionReviewAgent; graph writes remain outside this agent.
**在系统中的位置**：三个语义 Agent 及其预算、轨迹工具；把抽取、治理、融合审核的职责显式化，但不直接写图。
**阅读重点**：融合审核 Agent 聚合支持/冲突、风险路由和有界建议；模型不能虚构证据、批准非法关系或直接写 Cypher。
**直接依赖**：[src.agents.budget](budget.md)、[src.agents.trace](trace.md)、[src.core.errors](../core/errors.md)、[src.core.ids](../core/ids.md)、[src.domain](../domain/__init__.md)、[src.governance](../governance/__init__.md)、[src.persistence.base](../persistence/base.md)、[src.persistence.reviews](../persistence/reviews.md)、[src.providers.base](../providers/base.md)；外部/标准库：`__future__`、`time`、`typing`。
**主要调用方（静态导入）**：[workflow/nodes.py](../workflow/nodes.md)。
**阅读提示**：下列流程根据当前源码控制流整理；`self`/接口对象的实际类型可能在运行时注入，未能静态解析的调用会明确标注。链接指向源码行或对应讲解文件。

## 核心路径解读

- `triage_candidates` 处理候选级问题并衔接有界 Reflection；原候选和尝试记录保留供追溯。
- `detect_conflicts` 组合规范 Claim 的支持/冲突判断；`route_by_risk` 生成审核路径而非默认批准。复杂组的语义建议须受已有事实和证据边界约束。

---

# FusionReviewAgent ⭐⭐⭐⭐

**位置与等级**：[fusion_review_agent.py:29](../../../src/agents/fusion_review_agent.py#L29)；承担主要 Agent、应用服务或审核/执行入口，跨模块影响显著。

**职责**：语义 Agent；通过受控工具和结构化状态交接完成本阶段任务，不能绕过硬校验。基类：无显式基类。

**字段与类级约束**：
- 类体未直接声明字段；实例状态请看 `__init__` 及方法中的赋值。

**内部成员**：`FusionReviewAgent.__init__`、`FusionReviewAgent.triage_candidates`、`FusionReviewAgent.detect_conflicts`、`FusionReviewAgent._assess_related_groups`、`FusionReviewAgent.route_by_risk`


---

# FusionReviewAgent.__init__ ⭐⭐⭐⭐

**位置与等级**：[fusion_review_agent.py:30](../../../src/agents/fusion_review_agent.py#L30)；承担主要 Agent、应用服务或审核/执行入口，跨模块影响显著。

**签名**：`def __init__(self, graph_store: GraphStore, advisor: SemanticAdvisor, reflection_service: BoundedReflectionService | None=None) -> None`。

**作用**：初始化对象并保存依赖或配置；需检查是否创建持久化资源。

**输入与输出**：
- 输入：`graph_store`（GraphStore；图持久化接口，具体实现由配置注入）；`advisor`（SemanticAdvisor）；`reflection_service`（BoundedReflectionService | None；默认 `None`）。
- 输出类型：`None`；具体返回路径见流程步骤。

**处理流程**：
1. 更新 `self.graph_store`，值来自 `graph_store`。
2. 更新 `self.advisor`，值来自 `advisor`。
3. 更新 `self.reflection_service`，值来自 `reflection_service`。
4. 更新 `self.review_repository`，值来自 `None`。

**调用与被调用**：
- 无显式函数调用，或仅声明协议/常量。
- 静态扫描未定位直接调用方；可能通过路由注册、LangGraph 节点、协议方法或依赖注入动态调用，不据此判断为死代码。

**状态、副作用与异常**：
- 显式状态/容器赋值：`self.graph_store`、`self.advisor`、`self.reflection_service`、`self.review_repository`。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：未见 `raise`；下游异常可能继续上抛。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。
- 恢复/幂等性：仅在代码有检查点、事务、请求编号或显式去重时才成立；此函数不能单凭名称视为可安全重试。


---

# FusionReviewAgent.triage_candidates ⭐⭐⭐⭐

**位置与等级**：[fusion_review_agent.py:41](../../../src/agents/fusion_review_agent.py#L41)；承担主要 Agent、应用服务或审核/执行入口，跨模块影响显著。

**签名**：`async def triage_candidates(self, state: WorkflowState) -> WorkflowState`。

**作用**：处理 `triage_candidates` 对应步骤；下列步骤依据函数体的实际控制流和调用点整理。

**输入与输出**：
- 输入：`state`（WorkflowState；跨节点 WorkflowState；调用方须保持证据与状态一致）。
- 输出类型：`WorkflowState`；具体返回路径见流程步骤。

**处理流程**：
1. 更新 `started`，值来自 `perf_counter()`。
2. 检查 `self.reflection_service is not None`；按条件分流，else 分支不存在。
3. 调用 `trace_step`，结果未直接赋值。
4. 返回 `state`。

**关键条件与保护**：
- [fusion_review_agent.py:43](../../../src/agents/fusion_review_agent.py#L43)：`self.reflection_service is not None`，不满足时跳过本分支。

**调用与被调用**：
- `perf_counter`（[fusion_review_agent.py:42](../../../src/agents/fusion_review_agent.py#L42)）：来自 `time.perf_counter`；具体实现可能由依赖注入或运行时分派决定。
- `self.reflection_service.run`（[fusion_review_agent.py:44](../../../src/agents/fusion_review_agent.py#L44)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `trace_step`（调用点 [fusion_review_agent.py:45](../../../src/agents/fusion_review_agent.py#L45)）→ [trace_step](trace.md)，静态可定位。
- `tuple`（[fusion_review_agent.py:51](../../../src/agents/fusion_review_agent.py#L51)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- 静态扫描未定位直接调用方；可能通过路由注册、LangGraph 节点、协议方法或依赖注入动态调用，不据此判断为死代码。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：未见 `raise`；下游异常可能继续上抛。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。
- 恢复/幂等性：仅在代码有检查点、事务、请求编号或显式去重时才成立；此函数不能单凭名称视为可安全重试。


---

# FusionReviewAgent.detect_conflicts ⭐⭐⭐⭐

**位置与等级**：[fusion_review_agent.py:57](../../../src/agents/fusion_review_agent.py#L57)；承担主要 Agent、应用服务或审核/执行入口，跨模块影响显著。

**签名**：`async def detect_conflicts(self, state: WorkflowState) -> WorkflowState`。

**作用**：对规范事实做支持/冲突识别，不由冲突分数直接替代人工审核。

**输入与输出**：
- 输入：`state`（WorkflowState；跨节点 WorkflowState；调用方须保持证据与状态一致）。
- 输出类型：`WorkflowState`；具体返回路径见流程步骤。

**处理流程**：
1. 断言 `state.output_schema is not None`。
2. 更新 `state.conflicts`，值来自 `detect_conflicts(state.claims, await self.graph_store.list_claims(), SchemaIndex(state.output_schem…`。
3. 调用 `trace_step`，结果未直接赋值。
4. 检查 `state.semantic_advisor_name != 'disabled'`；按条件分流，else 分支不存在。
5. 返回 `state`。

**关键条件与保护**：
- [fusion_review_agent.py:71](../../../src/agents/fusion_review_agent.py#L71)：`state.semantic_advisor_name != 'disabled'`，不满足时跳过本分支。

**调用与被调用**：
- `detect_conflicts`（[fusion_review_agent.py:59](../../../src/agents/fusion_review_agent.py#L59)）：来自 `src.governance.detect_conflicts`；具体实现可能由依赖注入或运行时分派决定。
- `self.graph_store.list_claims`（[fusion_review_agent.py:60](../../../src/agents/fusion_review_agent.py#L60)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `SchemaIndex`（[fusion_review_agent.py:60](../../../src/agents/fusion_review_agent.py#L60)）：来自 `src.domain.SchemaIndex`；具体实现可能由依赖注入或运行时分派决定。
- `trace_step`（调用点 [fusion_review_agent.py:62](../../../src/agents/fusion_review_agent.py#L62)）→ [trace_step](trace.md)，静态可定位。
- `tuple`（[fusion_review_agent.py:68](../../../src/agents/fusion_review_agent.py#L68)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `self._assess_related_groups`（调用点 [fusion_review_agent.py:72](../../../src/agents/fusion_review_agent.py#L72)）→ [FusionReviewAgent._assess_related_groups](fusion_review_agent.md)，静态可定位。
- 静态扫描未定位直接调用方；可能通过路由注册、LangGraph 节点、协议方法或依赖注入动态调用，不据此判断为死代码。

**状态、副作用与异常**：
- 显式状态/容器赋值：`state.conflicts`。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：未见 `raise`；下游异常可能继续上抛。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。
- 恢复/幂等性：仅在代码有检查点、事务、请求编号或显式去重时才成立；此函数不能单凭名称视为可安全重试。


---

# FusionReviewAgent._assess_related_groups ⭐⭐

**位置与等级**：[fusion_review_agent.py:75](../../../src/agents/fusion_review_agent.py#L75)；局部辅助逻辑，需理解其调用条件与失败传播。

**签名**：`async def _assess_related_groups(self, state: WorkflowState) -> None`。

**作用**：内部辅助步骤；将参数转换为本模块所需的中间对象或操作结果。

**输入与输出**：
- 输入：`state`（WorkflowState；跨节点 WorkflowState；调用方须保持证据与状态一致）。
- 输出类型：`None`；具体返回路径见流程步骤。

**处理流程**：
1. 更新 `candidates`，值来自 `{item.id: item for item in state.candidates}`。
2. 更新 `claims_by_candidate`，值来自 `{candidate_id: claim for claim in state.claims for candidate_id in claim.source_candidate_ids}`。
3. 更新 `known_conflicts`，值来自 `{frozenset(item.claim_ids) for item in state.conflicts}`。
4. 遍历 `state.alignment_records`，逐项处理 `alignment`。
5. 更新 `state.agent_review_claim_ids`，值来自 `sorted(set(state.agent_review_claim_ids))`。

**关键条件与保护**：
- [fusion_review_agent.py:84](../../../src/agents/fusion_review_agent.py#L84)：`alignment.decision != 'related' or len(alignment.candidate_ids) != 2`，不满足时跳过本分支。
- [fusion_review_agent.py:89](../../../src/agents/fusion_review_agent.py#L89)：`left is None or right is None or left.id == right.id or (left.subject_id != right.subject_id) or (left.relation_id…`，不满足时跳过本分支。
- [fusion_review_agent.py:98](../../../src/agents/fusion_review_agent.py#L98)：`not can_request(state)`，不满足时跳过本分支。
- [fusion_review_agent.py:122](../../../src/agents/fusion_review_agent.py#L122)：`advice.decision == 'conflict'`，不满足时有 else 分支。
- [fusion_review_agent.py:131](../../../src/agents/fusion_review_agent.py#L131)：`advice.decision == 'uncertain'`，不满足时跳过本分支。

**调用与被调用**：
- `frozenset`（[fusion_review_agent.py:82](../../../src/agents/fusion_review_agent.py#L82)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `len`（[fusion_review_agent.py:84](../../../src/agents/fusion_review_agent.py#L84)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `claims_by_candidate.get`（[fusion_review_agent.py:87](../../../src/agents/fusion_review_agent.py#L87)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `can_request`（调用点 [fusion_review_agent.py:98](../../../src/agents/fusion_review_agent.py#L98)）→ [can_request](budget.md)，静态可定位。
- `state.warnings.append`（[fusion_review_agent.py:99](../../../src/agents/fusion_review_agent.py#L99)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `state.agent_review_claim_ids.extend`（[fusion_review_agent.py:100](../../../src/agents/fusion_review_agent.py#L100)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `perf_counter`（[fusion_review_agent.py:102](../../../src/agents/fusion_review_agent.py#L102)）：来自 `time.perf_counter`；具体实现可能由依赖注入或运行时分派决定。
- `self.advisor.advise_fusion`（[fusion_review_agent.py:104](../../../src/agents/fusion_review_agent.py#L104)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `FusionAdviceRequest`（[fusion_review_agent.py:105](../../../src/agents/fusion_review_agent.py#L105)）：来自 `src.domain.FusionAdviceRequest`；具体实现可能由依赖注入或运行时分派决定。
- `record_call`（调用点 [fusion_review_agent.py:107](../../../src/agents/fusion_review_agent.py#L107)）→ [record_call](budget.md)，静态可定位。
- `record_response_failure`（调用点 [fusion_review_agent.py:109](../../../src/agents/fusion_review_agent.py#L109)）→ [record_response_failure](budget.md)，静态可定位。
- `trace_step`（调用点 [fusion_review_agent.py:111](../../../src/agents/fusion_review_agent.py#L111)）→ [trace_step](trace.md)，静态可定位。
- `sorted`（[fusion_review_agent.py:123](../../../src/agents/fusion_review_agent.py#L123)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `ConflictSet`（[fusion_review_agent.py:124](../../../src/agents/fusion_review_agent.py#L124)）：来自 `src.domain.ConflictSet`；具体实现可能由依赖注入或运行时分派决定。
- `stable_id`（调用点 [fusion_review_agent.py:125](../../../src/agents/fusion_review_agent.py#L125)）→ [stable_id](../core/ids.md)，静态可定位。
- `state.conflicts.append`（[fusion_review_agent.py:129](../../../src/agents/fusion_review_agent.py#L129)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `known_conflicts.add`（[fusion_review_agent.py:130](../../../src/agents/fusion_review_agent.py#L130)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `safe_reason_code`（调用点 [fusion_review_agent.py:141](../../../src/agents/fusion_review_agent.py#L141)）→ [safe_reason_code](trace.md)，静态可定位。
- `self.advisor.fingerprint`（[fusion_review_agent.py:142](../../../src/agents/fusion_review_agent.py#L142)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `set`（[fusion_review_agent.py:146](../../../src/agents/fusion_review_agent.py#L146)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- 静态可定位的调用方：[FusionReviewAgent.detect_conflicts](fusion_review_agent.md)。

**状态、副作用与异常**：
- 显式状态/容器赋值：`state.agent_review_claim_ids`。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：未见 `raise`；下游异常可能继续上抛。
- 本地捕获：`ProviderResponseError`。
- 恢复/幂等性：仅在代码有检查点、事务、请求编号或显式去重时才成立；此函数不能单凭名称视为可安全重试。


---

# FusionReviewAgent.route_by_risk ⭐⭐⭐⭐

**位置与等级**：[fusion_review_agent.py:148](../../../src/agents/fusion_review_agent.py#L148)；承担主要 Agent、应用服务或审核/执行入口，跨模块影响显著。

**签名**：`async def route_by_risk(self, state: WorkflowState) -> WorkflowState`。

**作用**：按风险规则决定后续审核或提交路径，不直接更改原始证据。

**输入与输出**：
- 输入：`state`（WorkflowState；跨节点 WorkflowState；调用方须保持证据与状态一致）。
- 输出类型：`WorkflowState`；具体返回路径见流程步骤。

**处理流程**：
1. 更新 `(state.claims, new_reviews)`，值来自 `route_by_risk(state.run_id, state.claims, state.conflicts)`。
2. 检查 `state.pending_correction_id and self.review_repository is not None`；按条件分流，else 分支不存在。
3. 遍历 `state.claims`，逐项处理 `claim`。
4. 更新 `resolved`，值来自 `{item.claim_id: item for item in state.review_tasks if item.status == 'resolved'}`。
5. 更新 `state.review_tasks`，值来自 `[resolved.get(item.claim_id, item) for item in new_reviews]`。
6. 检查 `self.review_repository is not None`；按条件分流，else 分支不存在。
7. 遍历 `state.review_tasks`，逐项处理 `task`。
8. 更新 `state.status`，值来自 `'awaiting_review' if any((item.status == 'pending' for item in state.review_tasks)) or state.valida…`。
9. 调用 `trace_step`，结果未直接赋值。
10. 调用 `handoff`，结果未直接赋值。
11. 返回 `state`。

**关键条件与保护**：
- [fusion_review_agent.py:150](../../../src/agents/fusion_review_agent.py#L150)：`state.pending_correction_id and self.review_repository is not None`，不满足时跳过本分支。
- [fusion_review_agent.py:152](../../../src/agents/fusion_review_agent.py#L152)：`proposal.kind == 'entity'`，不满足时跳过本分支。
- [fusion_review_agent.py:155](../../../src/agents/fusion_review_agent.py#L155)：`set(claim.source_candidate_ids) & affected and claim.status != ClaimStatus.REJECTED`，不满足时跳过本分支。
- [fusion_review_agent.py:160](../../../src/agents/fusion_review_agent.py#L160)：`claim.id not in {t.claim_id for t in new_reviews}`，不满足时跳过本分支。
- [fusion_review_agent.py:170](../../../src/agents/fusion_review_agent.py#L170)：`claim.id not in state.agent_review_claim_ids or claim.status == ClaimStatus.REJECTED`，不满足时跳过本分支。
- [fusion_review_agent.py:173](../../../src/agents/fusion_review_agent.py#L173)：`claim.id not in {task.claim_id for task in new_reviews}`，不满足时跳过本分支。
- [fusion_review_agent.py:184](../../../src/agents/fusion_review_agent.py#L184)：`self.review_repository is not None`，不满足时跳过本分支。
- [fusion_review_agent.py:188](../../../src/agents/fusion_review_agent.py#L188)：`task.status != 'resolved'`，不满足时跳过本分支。

**调用与被调用**：
- `route_by_risk`（[fusion_review_agent.py:149](../../../src/agents/fusion_review_agent.py#L149)）：来自 `src.governance.route_by_risk`；具体实现可能由依赖注入或运行时分派决定。
- `self.review_repository.correction`（[fusion_review_agent.py:151](../../../src/agents/fusion_review_agent.py#L151)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `set`（[fusion_review_agent.py:153](../../../src/agents/fusion_review_agent.py#L153)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `new_reviews.append`（[fusion_review_agent.py:161](../../../src/agents/fusion_review_agent.py#L161)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `ReviewTask`（[fusion_review_agent.py:162](../../../src/agents/fusion_review_agent.py#L162)）：来自 `src.domain.ReviewTask`；具体实现可能由依赖注入或运行时分派决定。
- `stable_id`（调用点 [fusion_review_agent.py:163](../../../src/agents/fusion_review_agent.py#L163)）→ [stable_id](../core/ids.md)，静态可定位。
- `resolved.get`（[fusion_review_agent.py:183](../../../src/agents/fusion_review_agent.py#L183)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `self.review_repository.version`（[fusion_review_agent.py:186](../../../src/agents/fusion_review_agent.py#L186)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `next`（[fusion_review_agent.py:190](../../../src/agents/fusion_review_agent.py#L190)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `any`（[fusion_review_agent.py:198](../../../src/agents/fusion_review_agent.py#L198)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `trace_step`（调用点 [fusion_review_agent.py:202](../../../src/agents/fusion_review_agent.py#L202)）→ [trace_step](trace.md)，静态可定位。
- `tuple`（[fusion_review_agent.py:208](../../../src/agents/fusion_review_agent.py#L208)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `handoff`（调用点 [fusion_review_agent.py:211](../../../src/agents/fusion_review_agent.py#L211)）→ [handoff](trace.md)，静态可定位。
- `sorted`（[fusion_review_agent.py:216](../../../src/agents/fusion_review_agent.py#L216)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- 静态扫描未定位直接调用方；可能通过路由注册、LangGraph 节点、协议方法或依赖注入动态调用，不据此判断为死代码。

**状态、副作用与异常**：
- 显式状态/容器赋值：`claim.status`、`state.review_tasks`、`task.version`、`state.status`。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：未见 `raise`；下游异常可能继续上抛。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。
- 恢复/幂等性：仅在代码有检查点、事务、请求编号或显式去重时才成立；此函数不能单凭名称视为可安全重试。


---
