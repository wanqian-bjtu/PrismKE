源码：[entity_governance_agent.py:1](../../../src/agents/entity_governance_agent.py#L1) | 基准：`dev/v0.10@f2f34d7` | 本文件符号数：5

**模块职责**：EntityGovernanceAgent with guarded gray-zone advice.
**在系统中的位置**：三个语义 Agent 及其预算、轨迹工具；把抽取、治理、融合审核的职责显式化，但不直接写图。
**阅读重点**：治理 Agent 先执行确定性候选校验/召回与阈值约束。灰区语义建议只可在已有候选与审核/NIL 中选择，不能单凭模型建议自动放行。
**直接依赖**：[src.agents.budget](budget.md)、[src.agents.trace](trace.md)、[src.core.errors](../core/errors.md)、[src.core.ids](../core/ids.md)、[src.domain](../domain/__init__.md)、[src.governance](../governance/__init__.md)、[src.governance.validation](../governance/validation/__init__.md)、[src.persistence.base](../persistence/base.md)、[src.providers.base](../providers/base.md)；外部/标准库：`__future__`、`time`。
**主要调用方（静态导入）**：[workflow/nodes.py](../workflow/nodes.md)。
**阅读提示**：下列流程根据当前源码控制流整理；`self`/接口对象的实际类型可能在运行时注入，未能静态解析的调用会明确标注。链接指向源码行或对应讲解文件。

## 核心路径解读

- `resolve` 先校验候选，屏蔽阻断项，再收集提及并执行实体解析；解析结果仍需通过审核路由。模型灰区建议不能跳过类型约束、自动链接阈值或人工任务。
- `normalize` 在实体审核尚未完成时不应产生正式 Claim；使用 Schema、实体映射与证据把可用候选转为规范事实。

---

# EntityGovernanceAgent ⭐⭐⭐⭐

**位置与等级**：[entity_governance_agent.py:18](../../../src/agents/entity_governance_agent.py#L18)；承担主要 Agent、应用服务或审核/执行入口，跨模块影响显著。

**职责**：语义 Agent；通过受控工具和结构化状态交接完成本阶段任务，不能绕过硬校验。基类：无显式基类。

**字段与类级约束**：
- 类体未直接声明字段；实例状态请看 `__init__` 及方法中的赋值。

**内部成员**：`EntityGovernanceAgent.__init__`、`EntityGovernanceAgent.resolve`、`EntityGovernanceAgent._advise_gray_zone`、`EntityGovernanceAgent.normalize`


---

# EntityGovernanceAgent.__init__ ⭐⭐

**位置与等级**：[entity_governance_agent.py:19](../../../src/agents/entity_governance_agent.py#L19)；局部辅助逻辑，需理解其调用条件与失败传播。

**签名**：`def __init__(self, graph_store: GraphStore, evidence_store: EvidenceStore, embedding_provider: EmbeddingProvider, advisor: SemanticAdvisor, *, top_k: int, auto_link_threshold: float, review_threshold: float, min_margin: float) -> None`。

**作用**：初始化对象并保存依赖或配置；需检查是否创建持久化资源。

**输入与输出**：
- 输入：`graph_store`（GraphStore；图持久化接口，具体实现由配置注入）；`evidence_store`（EvidenceStore；证据元数据和原始内容的存储接口）；`embedding_provider`（EmbeddingProvider）；`advisor`（SemanticAdvisor）；`top_k`（int；候选召回数量上限）；`auto_link_threshold`（float）；`review_threshold`（float）；`min_margin`（float）。
- 输出类型：`None`；具体返回路径见流程步骤。

**处理流程**：
1. 更新 `self.graph_store`，值来自 `graph_store`。
2. 更新 `self.evidence_store`，值来自 `evidence_store`。
3. 更新 `self.embedding_provider`，值来自 `embedding_provider`。
4. 更新 `self.advisor`，值来自 `advisor`。
5. 更新 `self.top_k`，值来自 `top_k`。
6. 更新 `self.auto_link_threshold`，值来自 `auto_link_threshold`。
7. 更新 `self.review_threshold`，值来自 `review_threshold`。
8. 更新 `self.min_margin`，值来自 `min_margin`。

**调用与被调用**：
- 无显式函数调用，或仅声明协议/常量。
- 静态扫描未定位直接调用方；可能通过路由注册、LangGraph 节点、协议方法或依赖注入动态调用，不据此判断为死代码。

**状态、副作用与异常**：
- 显式状态/容器赋值：`self.graph_store`、`self.evidence_store`、`self.embedding_provider`、`self.advisor`、`self.top_k`、`self.auto_link_threshold`、`self.review_threshold`、`self.min_margin`。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：未见 `raise`；下游异常可能继续上抛。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。
- 恢复/幂等性：仅在代码有检查点、事务、请求编号或显式去重时才成立；此函数不能单凭名称视为可安全重试。


---

# EntityGovernanceAgent.resolve ⭐⭐⭐⭐

**位置与等级**：[entity_governance_agent.py:40](../../../src/agents/entity_governance_agent.py#L40)；承担主要 Agent、应用服务或审核/执行入口，跨模块影响显著。

**签名**：`async def resolve(self, state: WorkflowState) -> WorkflowState`。

**作用**：根据类型、名称、语义候选和上下文形成实体解析结果及审核路由。

**输入与输出**：
- 输入：`state`（WorkflowState；跨节点 WorkflowState；调用方须保持证据与状态一致）。
- 输出类型：`WorkflowState`；具体返回路径见流程步骤。

**处理流程**：
1. 断言 `state.output_schema is not None and state.document is not None`。
2. 更新 `started`，值来自 `perf_counter()`。
3. 更新 `issues`，值来自 `await ValidationService().candidates(state.candidates, SchemaIndex(state.output_schema), state.docu…`。
4. 更新 `state.validation`，值来自 `ValidationService.merge(state.validation, issues)`。
5. 更新 `excluded`，值来自 `ValidationService.blocked_candidate_ids(state.candidates, state.validation)`。
6. 更新 `mentions`，值来自 `collect_mentions([c for c in state.candidates if c.id not in excluded])`。
7. 更新 `resolver`，值来自 `SemanticEntityResolver(SchemaIndex(state.output_schema), self.graph_store, self.embedding_provider,…`。
8. 更新 `resolution`，值来自 `await resolver.resolve(mentions)`。
9. 更新 `state.entities`，值来自 `resolution.entities`。
10. 更新 `state.mention_to_entity`，值来自 `resolution.mention_to_entity`。
11. 更新 `state.entity_resolution_decisions`，值来自 `resolution.decisions or []`。
12. 更新 `resolved`，值来自 `{item.mention_id: item for item in state.entity_review_tasks if item.status == 'resolved' and item.…`。
13. 更新 `state.entity_review_tasks`，值来自 `[resolved.get(item.mention_id, item) if item.mention_id is not None else item for item in resolutio…`。
14. 调用 `state.warnings.extend`，结果未直接赋值。
15. 等待 `self._advise_gray_zone(state, mentions)` 完成。
16. 更新 `state.status`，值来自 `'awaiting_review' if any((item.status == 'pending' for item in state.entity_review_tasks)) or state…`。
17. 调用 `trace_step`，结果未直接赋值。
18. 调用 `handoff`，结果未直接赋值。
19. 返回 `state`。

**调用与被调用**：
- `perf_counter`（[entity_governance_agent.py:42](../../../src/agents/entity_governance_agent.py#L42)）：来自 `time.perf_counter`；具体实现可能由依赖注入或运行时分派决定。
- `ValidationService().candidates`（[entity_governance_agent.py:43](../../../src/agents/entity_governance_agent.py#L43)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `ValidationService`（[entity_governance_agent.py:43](../../../src/agents/entity_governance_agent.py#L43)）：来自 `src.governance.validation.ValidationService`；具体实现可能由依赖注入或运行时分派决定。
- `SchemaIndex`（[entity_governance_agent.py:44](../../../src/agents/entity_governance_agent.py#L44)）：来自 `src.domain.SchemaIndex`；具体实现可能由依赖注入或运行时分派决定。
- `ValidationService.merge`（[entity_governance_agent.py:46](../../../src/agents/entity_governance_agent.py#L46)）：来自 `src.governance.validation.ValidationService`；具体实现可能由依赖注入或运行时分派决定。
- `ValidationService.blocked_candidate_ids`（[entity_governance_agent.py:47](../../../src/agents/entity_governance_agent.py#L47)）：来自 `src.governance.validation.ValidationService`；具体实现可能由依赖注入或运行时分派决定。
- `collect_mentions`（[entity_governance_agent.py:48](../../../src/agents/entity_governance_agent.py#L48)）：来自 `src.governance.collect_mentions`；具体实现可能由依赖注入或运行时分派决定。
- `SemanticEntityResolver`（[entity_governance_agent.py:49](../../../src/agents/entity_governance_agent.py#L49)）：来自 `src.governance.SemanticEntityResolver`；具体实现可能由依赖注入或运行时分派决定。
- `resolver.resolve`（[entity_governance_agent.py:59](../../../src/agents/entity_governance_agent.py#L59)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `resolved.get`（[entity_governance_agent.py:69](../../../src/agents/entity_governance_agent.py#L69)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `state.warnings.extend`（[entity_governance_agent.py:72](../../../src/agents/entity_governance_agent.py#L72)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `<字符串常量>.join`（[entity_governance_agent.py:73](../../../src/agents/entity_governance_agent.py#L73)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `resolution.review_reasons.items`（[entity_governance_agent.py:74](../../../src/agents/entity_governance_agent.py#L74)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `self._advise_gray_zone`（调用点 [entity_governance_agent.py:76](../../../src/agents/entity_governance_agent.py#L76)）→ [EntityGovernanceAgent._advise_gray_zone](entity_governance_agent.md)，静态可定位。
- `any`（[entity_governance_agent.py:79](../../../src/agents/entity_governance_agent.py#L79)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `trace_step`（调用点 [entity_governance_agent.py:83](../../../src/agents/entity_governance_agent.py#L83)）→ [trace_step](trace.md)，静态可定位。
- `tuple`（[entity_governance_agent.py:89](../../../src/agents/entity_governance_agent.py#L89)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `handoff`（调用点 [entity_governance_agent.py:94](../../../src/agents/entity_governance_agent.py#L94)）→ [handoff](trace.md)，静态可定位。
- `sorted`（[entity_governance_agent.py:99](../../../src/agents/entity_governance_agent.py#L99)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- 静态扫描未定位直接调用方；可能通过路由注册、LangGraph 节点、协议方法或依赖注入动态调用，不据此判断为死代码。

**状态、副作用与异常**：
- 显式状态/容器赋值：`state.validation`、`state.entities`、`state.mention_to_entity`、`state.entity_resolution_decisions`、`state.entity_review_tasks`、`state.status`。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：未见 `raise`；下游异常可能继续上抛。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。
- 恢复/幂等性：仅在代码有检查点、事务、请求编号或显式去重时才成立；此函数不能单凭名称视为可安全重试。


---

# EntityGovernanceAgent._advise_gray_zone ⭐⭐

**位置与等级**：[entity_governance_agent.py:106](../../../src/agents/entity_governance_agent.py#L106)；局部辅助逻辑，需理解其调用条件与失败传播。

**签名**：`async def _advise_gray_zone(self, state: WorkflowState, mentions: list[EntityMention]) -> None`。

**作用**：内部辅助步骤；将参数转换为本模块所需的中间对象或操作结果。

**输入与输出**：
- 输入：`state`（WorkflowState；跨节点 WorkflowState；调用方须保持证据与状态一致）；`mentions`（list[EntityMention]）。
- 输出类型：`None`；具体返回路径见流程步骤。

**处理流程**：
1. 检查 `state.semantic_advisor_name == 'disabled'`；按条件分流，else 分支不存在。
2. 更新 `mention_by_id`，值来自 `{item.id: item for item in mentions}`。
3. 更新 `entities`，值来自 `{item.id: item for item in state.entities}`。
4. 断言 `state.output_schema is not None`。
5. 更新 `schema`，值来自 `SchemaIndex(state.output_schema)`。
6. 更新 `decisions`，值来自 `{item.mention_id: item for item in state.entity_resolution_decisions}`。
7. 遍历 `state.entity_review_tasks`，逐项处理 `task`。

**关键条件与保护**：
- [entity_governance_agent.py:109](../../../src/agents/entity_governance_agent.py#L109)：`state.semantic_advisor_name == 'disabled'`，不满足时跳过本分支。
- [entity_governance_agent.py:118](../../../src/agents/entity_governance_agent.py#L118)：`task.status != 'pending' or mention_id is None or mention_id not in mention_by_id or (not task.candidates)`，不满足时跳过本分支。
- [entity_governance_agent.py:133](../../../src/agents/entity_governance_agent.py#L133)：`not same_type_candidates`，不满足时跳过本分支。
- [entity_governance_agent.py:135](../../../src/agents/entity_governance_agent.py#L135)：`not can_request(state)`，不满足时跳过本分支。
- [entity_governance_agent.py:166](../../../src/agents/entity_governance_agent.py#L166)：`advice.action == 'link' and selected is None`，不满足时跳过本分支。
- [entity_governance_agent.py:175](../../../src/agents/entity_governance_agent.py#L175)：`decision is not None`，不满足时跳过本分支。

**调用与被调用**：
- `SchemaIndex`（[entity_governance_agent.py:114](../../../src/agents/entity_governance_agent.py#L114)）：来自 `src.domain.SchemaIndex`；具体实现可能由依赖注入或运行时分派决定。
- `schema.entity_type`（[entity_governance_agent.py:126](../../../src/agents/entity_governance_agent.py#L126)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `can_request`（调用点 [entity_governance_agent.py:135](../../../src/agents/entity_governance_agent.py#L135)）→ [can_request](budget.md)，静态可定位。
- `state.warnings.append`（[entity_governance_agent.py:136](../../../src/agents/entity_governance_agent.py#L136)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `EntityAdviceRequest`（[entity_governance_agent.py:138](../../../src/agents/entity_governance_agent.py#L138)）：来自 `src.domain.EntityAdviceRequest`；具体实现可能由依赖注入或运行时分派决定。
- `perf_counter`（[entity_governance_agent.py:146](../../../src/agents/entity_governance_agent.py#L146)）：来自 `time.perf_counter`；具体实现可能由依赖注入或运行时分派决定。
- `self.advisor.advise_entity`（[entity_governance_agent.py:148](../../../src/agents/entity_governance_agent.py#L148)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `record_call`（调用点 [entity_governance_agent.py:149](../../../src/agents/entity_governance_agent.py#L149)）→ [record_call](budget.md)，静态可定位。
- `record_response_failure`（调用点 [entity_governance_agent.py:151](../../../src/agents/entity_governance_agent.py#L151)）→ [record_response_failure](budget.md)，静态可定位。
- `task.reasons.append`（[entity_governance_agent.py:152](../../../src/agents/entity_governance_agent.py#L152)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `trace_step`（调用点 [entity_governance_agent.py:153](../../../src/agents/entity_governance_agent.py#L153)）→ [trace_step](trace.md)，静态可定位。
- `safe_reason_code`（调用点 [entity_governance_agent.py:173](../../../src/agents/entity_governance_agent.py#L173)）→ [safe_reason_code](trace.md)，静态可定位。
- `decisions.get`（[entity_governance_agent.py:174](../../../src/agents/entity_governance_agent.py#L174)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `decision.reasons.append`（[entity_governance_agent.py:178](../../../src/agents/entity_governance_agent.py#L178)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `tuple`（[entity_governance_agent.py:185](../../../src/agents/entity_governance_agent.py#L185)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `self.advisor.fingerprint`（[entity_governance_agent.py:188](../../../src/agents/entity_governance_agent.py#L188)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- 静态可定位的调用方：[EntityGovernanceAgent.resolve](entity_governance_agent.md)。

**状态、副作用与异常**：
- 显式状态/容器赋值：`task.advised_action`、`task.advised_entity_id`、`decision.advised_action`、`decision.advised_entity_id`。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：未见 `raise`；下游异常可能继续上抛。
- 本地捕获：`ProviderResponseError`。
- 恢复/幂等性：仅在代码有检查点、事务、请求编号或显式去重时才成立；此函数不能单凭名称视为可安全重试。


---

# EntityGovernanceAgent.normalize ⭐⭐⭐⭐

**位置与等级**：[entity_governance_agent.py:193](../../../src/agents/entity_governance_agent.py#L193)；承担主要 Agent、应用服务或审核/执行入口，跨模块影响显著。

**签名**：`async def normalize(self, state: WorkflowState) -> WorkflowState`。

**作用**：处理 `normalize` 对应步骤；下列步骤依据函数体的实际控制流和调用点整理。

**输入与输出**：
- 输入：`state`（WorkflowState；跨节点 WorkflowState；调用方须保持证据与状态一致）。
- 输出类型：`WorkflowState`；具体返回路径见流程步骤。

**处理流程**：
1. 断言 `state.output_schema is not None and state.document is not None`。
2. 更新 `entities`，值来自 `{item.id: item for item in state.entities}`。
3. 更新 `blocked`，值来自 `ValidationService.blocked_candidate_ids(state.candidates, state.validation)`。
4. 更新 `eligible`，值来自 `[c for c in state.candidates if c.id not in blocked]`。
5. 更新 `issues`，值来自 `await ValidationService().candidates(eligible, SchemaIndex(state.output_schema), state.document, se…`。
6. 更新 `state.validation`，值来自 `ValidationService.merge(state.validation, issues, canonical_hash([c.model_dump(mode='json') for c i…`。
7. 调用 `blocked.update`，结果未直接赋值。
8. 更新 `state.claims`，值来自 `normalize_claims([c for c in eligible if c.id not in blocked], SchemaIndex(state.output_schema), en…`。
9. 更新 `state.validation.passed_count`，值来自 `len(state.claims)`。
10. 调用 `trace_step`，结果未直接赋值。
11. 调用 `handoff`，结果未直接赋值。
12. 返回 `state`。

**调用与被调用**：
- `ValidationService.blocked_candidate_ids`（[entity_governance_agent.py:196](../../../src/agents/entity_governance_agent.py#L196)）：来自 `src.governance.validation.ValidationService`；具体实现可能由依赖注入或运行时分派决定。
- `ValidationService().candidates`（[entity_governance_agent.py:198](../../../src/agents/entity_governance_agent.py#L198)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `ValidationService`（[entity_governance_agent.py:198](../../../src/agents/entity_governance_agent.py#L198)）：来自 `src.governance.validation.ValidationService`；具体实现可能由依赖注入或运行时分派决定。
- `SchemaIndex`（[entity_governance_agent.py:200](../../../src/agents/entity_governance_agent.py#L200)）：来自 `src.domain.SchemaIndex`；具体实现可能由依赖注入或运行时分派决定。
- `ValidationService.merge`（[entity_governance_agent.py:206](../../../src/agents/entity_governance_agent.py#L206)）：来自 `src.governance.validation.ValidationService`；具体实现可能由依赖注入或运行时分派决定。
- `canonical_hash`（调用点 [entity_governance_agent.py:209](../../../src/agents/entity_governance_agent.py#L209)）→ [canonical_hash](../core/ids.md)，静态可定位。
- `c.model_dump`（[entity_governance_agent.py:209](../../../src/agents/entity_governance_agent.py#L209)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `blocked.update`（[entity_governance_agent.py:211](../../../src/agents/entity_governance_agent.py#L211)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `normalize_claims`（[entity_governance_agent.py:212](../../../src/agents/entity_governance_agent.py#L212)）：来自 `src.governance.normalize_claims`；具体实现可能由依赖注入或运行时分派决定。
- `len`（[entity_governance_agent.py:218](../../../src/agents/entity_governance_agent.py#L218)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `trace_step`（调用点 [entity_governance_agent.py:219](../../../src/agents/entity_governance_agent.py#L219)）→ [trace_step](trace.md)，静态可定位。
- `tuple`（[entity_governance_agent.py:225](../../../src/agents/entity_governance_agent.py#L225)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `handoff`（调用点 [entity_governance_agent.py:228](../../../src/agents/entity_governance_agent.py#L228)）→ [handoff](trace.md)，静态可定位。
- `sorted`（[entity_governance_agent.py:233](../../../src/agents/entity_governance_agent.py#L233)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- 静态扫描未定位直接调用方；可能通过路由注册、LangGraph 节点、协议方法或依赖注入动态调用，不据此判断为死代码。

**状态、副作用与异常**：
- 显式状态/容器赋值：`state.validation`、`state.claims`、`state.validation.passed_count`。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：未见 `raise`；下游异常可能继续上抛。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。
- 恢复/幂等性：仅在代码有检查点、事务、请求编号或显式去重时才成立；此函数不能单凭名称视为可安全重试。


---
