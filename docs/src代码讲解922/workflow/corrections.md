源码：[corrections.py:1](../../../src/workflow/corrections.py#L1) | 基准：`dev/v0.10@f2f34d7` | 本文件符号数：6

**模块职责**：Review correction previews and tail-only, auditable compensation workflows.
**在系统中的位置**：应用服务、LangGraph 编排、执行状态、审核接续、图提交及纠正流程。
**直接依赖**：[src.core.ids](../core/ids.md)、[src.domain](../domain/__init__.md)、[src.domain.reviews](../domain/reviews.md)、[src.persistence.reviews](../persistence/reviews.md)；外部/标准库：`typing`。
**主要调用方（静态导入）**：未见静态直接导入；可能由包入口、框架注册或动态加载。
**阅读提示**：下列流程根据当前源码控制流整理；`self`/接口对象的实际类型可能在运行时注入，未能静态解析的调用会明确标注。链接指向源码行或对应讲解文件。

---

# compensation_commit ⭐⭐

**位置与等级**：[corrections.py:24](../../../src/workflow/corrections.py#L24)；局部辅助逻辑，需理解其调用条件与失败传播。

**签名**：`def compensation_commit(state: WorkflowState, transaction: GraphCommit, proposal: ReviewCorrection, current_claims: dict[str, Claim], current_entities: dict[str, Any]) -> GraphCommit`。

**作用**：Replace only affected resources, never apply ordinary append/merge semantics.

**输入与输出**：
- 输入：`state`（WorkflowState；跨节点 WorkflowState；调用方须保持证据与状态一致）；`transaction`（GraphCommit；待提交 GraphCommit；必须在最终写入边界重新校验）；`proposal`（ReviewCorrection）；`current_claims`（dict[str, Claim]）；`current_entities`（dict[str, Any]）。
- 输出类型：`GraphCommit`；具体返回路径见流程步骤。

**处理流程**：
1. 更新 `candidate_ids`，值来自 `set(proposal.preview['candidate_ids'])`。
2. 更新 `now`，值来自 `utc_now()`。
3. 更新 `replacements`，值来自 `{c.id: c.model_copy(deep=True) for c in transaction.claims if set(c.source_candidate_ids) & candida…`。
4. 遍历 `replacements.values()`，逐项处理 `claim`。
5. 遍历 `proposal.affected_claim_ids`，逐项处理 `claim_id`。
6. 更新 `transaction.claims`，值来自 `list(replacements.values())`。
7. 更新 `needed`，值来自 `{e for c in replacements.values() if c.tx_to is None for e in (c.subject_id, c.object_entity_id) if…`。
8. 更新 `transaction.entities`，值来自 `[e for e in state.entities if e.id in needed and e.id not in current_entities]`。
9. 更新 `transaction.conflicts`，值来自 `[]`。
10. 更新 `changes`，值来自 `[GraphChange(resource_type='claim', resource_id=c.id, action='update' if c.id in current_claims els…`。
11. 调用 `changes.extend`，结果未直接赋值。
12. 更新 `expected`，值来自 `dict(proposal.preview['expected_resources'])`。
13. 遍历 `changes`，逐项处理 `change`。
14. 更新 `guard`，值来自 `CorrectionGuard(source_event_id=proposal.source_event_id, reviewer=proposal.reviewer, reason=propos…`。
15. 更新 `transaction.correction_guard`，值来自 `guard`。
16. 更新 `revision`，值来自 `transaction.revision`。
17. 更新 `revision.id`，值来自 `stable_id('revision', 'correction', proposal.id)`。
18. 更新 `revision.parent_id`，值来自 `proposal.parent_revision_id`。
19. 更新 `revision.changes`，值来自 `changes`。
20. 更新 `revision.claim_ids`，值来自 `sorted(replacements)`。
21. 更新 `revision.entity_ids`，值来自 `sorted(needed)`。
22. 更新 `revision.conflict_ids`，值来自 `[]`。
23. 更新 `revision.correction_guard`，值来自 `guard`。
24. 更新 `revision.created_at`，值来自 `now`。
后续还有 1 个语句级步骤，见源码对应行；这里优先保留主要控制流。

**关键条件与保护**：
- [corrections.py:42](../../../src/workflow/corrections.py#L42)：`claim_id not in replacements`，不满足时跳过本分支。
- [corrections.py:81](../../../src/workflow/corrections.py#L81)：`key not in expected`，不满足时跳过本分支。
- [corrections.py:82](../../../src/workflow/corrections.py#L82)：`change.before is not None`，不满足时跳过本分支。

**调用与被调用**：
- `set`（[corrections.py:32](../../../src/workflow/corrections.py#L32)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `utc_now`（[corrections.py:33](../../../src/workflow/corrections.py#L33)）：来自 `src.domain.utc_now`；具体实现可能由依赖注入或运行时分派决定。
- `c.model_copy`（[corrections.py:35](../../../src/workflow/corrections.py#L35)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `replacements.values`（[corrections.py:39](../../../src/workflow/corrections.py#L39)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `current_claims[claim_id].model_copy`（[corrections.py:43](../../../src/workflow/corrections.py#L43)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `list`（[corrections.py:46](../../../src/workflow/corrections.py#L46)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `GraphChange`（[corrections.py:60](../../../src/workflow/corrections.py#L60)）：来自 `src.domain.GraphChange`；具体实现可能由依赖注入或运行时分派决定。
- `current_claims[c.id].model_dump`（[corrections.py:64](../../../src/workflow/corrections.py#L64)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `c.model_dump`（[corrections.py:65](../../../src/workflow/corrections.py#L65)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `changes.extend`（[corrections.py:69](../../../src/workflow/corrections.py#L69)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `e.model_dump`（[corrections.py:74](../../../src/workflow/corrections.py#L74)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `dict`（[corrections.py:78](../../../src/workflow/corrections.py#L78)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `ValueError`（[corrections.py:83](../../../src/workflow/corrections.py#L83)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `CorrectionGuard`（调用点 [corrections.py:85](../../../src/workflow/corrections.py#L85)）→ [CorrectionGuard](../domain/reviews.md)，静态可定位。
- `stable_id`（调用点 [corrections.py:93](../../../src/workflow/corrections.py#L93)）→ [stable_id](../core/ids.md)，静态可定位。
- `sorted`（[corrections.py:96](../../../src/workflow/corrections.py#L96)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- 静态可定位的调用方：[WorkflowNodes.prepare_graph_commit](nodes.md)。

**状态、副作用与异常**：
- 显式状态/容器赋值：`old.tx_to`、`replacements[claim_id]`、`transaction.claims`、`transaction.entities`、`transaction.conflicts`、`expected[key]`、`transaction.correction_guard`、`revision.id`、`revision.parent_id`、`revision.changes`、`revision.claim_ids`、`revision.entity_ids`。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：`ValueError(<字符串常量>)`。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。
- 恢复/幂等性：仅在代码有检查点、事务、请求编号或显式去重时才成立；此函数不能单凭名称视为可安全重试。


---

# CorrectionService ⭐⭐⭐⭐

**位置与等级**：[corrections.py:104](../../../src/workflow/corrections.py#L104)；承担主要 Agent、应用服务或审核/执行入口，跨模块影响显著。

**职责**：跨步骤服务；组合依赖并暴露可复用业务入口。基类：无显式基类。

**字段与类级约束**：
- 类体未直接声明字段；实例状态请看 `__init__` 及方法中的赋值。

**内部成员**：`CorrectionService.__init__`、`CorrectionService.propose`、`CorrectionService.apply`、`CorrectionService.confirm`


---

# CorrectionService.__init__ ⭐⭐

**位置与等级**：[corrections.py:105](../../../src/workflow/corrections.py#L105)；局部辅助逻辑，需理解其调用条件与失败传播。

**签名**：`def __init__(self, service: 'PrismKEService') -> None`。

**作用**：初始化对象并保存依赖或配置；需检查是否创建持久化资源。

**输入与输出**：
- 输入：`service`（'PrismKEService'）。
- 输出类型：`None`；具体返回路径见流程步骤。

**处理流程**：
1. 更新 `self.service`，值来自 `service`。
2. 更新 `self.reviews`，值来自 `service.reviews`。
3. 更新 `self.repository`，值来自 `self.reviews.repository`。

**调用与被调用**：
- 无显式函数调用，或仅声明协议/常量。
- 静态扫描未定位直接调用方；可能通过路由注册、LangGraph 节点、协议方法或依赖注入动态调用，不据此判断为死代码。

**状态、副作用与异常**：
- 显式状态/容器赋值：`self.service`、`self.reviews`、`self.repository`。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：未见 `raise`；下游异常可能继续上抛。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。
- 恢复/幂等性：仅在代码有检查点、事务、请求编号或显式去重时才成立；此函数不能单凭名称视为可安全重试。


---

# CorrectionService.propose ⭐⭐

**位置与等级**：[corrections.py:110](../../../src/workflow/corrections.py#L110)；局部辅助逻辑，需理解其调用条件与失败传播。

**签名**：`async def propose(self, run_id: str, source_event_id: str, action: str, selected_entity_id: str | None, expected_version: int, reviewer: str, reason: str, request_id: str) -> ReviewCorrection`。

**作用**：处理 `propose` 对应步骤；下列步骤依据函数体的实际控制流和调用点整理。

**输入与输出**：
- 输入：`run_id`（str；目标运行的稳定标识）；`source_event_id`（str）；`action`（str）；`selected_entity_id`（str | None）；`expected_version`（int；乐观并发版本；过期提交应拒绝）；`reviewer`（str；审核操作者，形成审计归属）；`reason`（str；人工操作或审核的理由）；`request_id`（str；幂等请求标识，避免重复动作）。
- 输出类型：`ReviewCorrection`；具体返回路径见流程步骤。

**处理流程**：
1. 检查 `not reviewer.strip() or not reason.strip() or (not request_id.strip())`；按条件分流，else 分支不存在。
2. 调用 `self.reviews.compatible`，结果未直接赋值。
3. 进入上下文 `self.service.runs.mutation_lock(run_id)`，由上下文管理器控制资源释放或事务范围。

**关键条件与保护**：
- [corrections.py:121](../../../src/workflow/corrections.py#L121)：`not reviewer.strip() or not reason.strip() or (not request_id.strip())`，不满足时跳过本分支。
- [corrections.py:131](../../../src/workflow/corrections.py#L131)：`prior`，不满足时跳过本分支。
- [corrections.py:132](../../../src/workflow/corrections.py#L132)：`(prior.source_event_id, prior.action, prior.selected_entity_id, prior.expected_version, prior.reviewer, prior.reas…`，不满足时跳过本分支。
- [corrections.py:150](../../../src/workflow/corrections.py#L150)：`state.pending_correction_id`，不满足时跳过本分支。
- [corrections.py:155](../../../src/workflow/corrections.py#L155)：`source is None or source.action in {'defer', 'commit_correction'}`，不满足时跳过本分支。
- [corrections.py:164](../../../src/workflow/corrections.py#L164)：`task is None or task.status != 'resolved' or (not final_events) or (final_events[-1].id != source.id)`，不满足时跳过本分支。
- [corrections.py:171](../../../src/workflow/corrections.py#L171)：`task.version != expected_version`，不满足时跳过本分支。
- [corrections.py:177](../../../src/workflow/corrections.py#L177)：`action not in allowed`，不满足时跳过本分支。
- [corrections.py:179](../../../src/workflow/corrections.py#L179)：`source.kind == 'entity'`，不满足时有 else 分支。
- [corrections.py:188](../../../src/workflow/corrections.py#L188)：`action == 'link' and selected_entity_id not in {c.entity_id for c in entity_task.candidates}`，不满足时跳过本分支。
- [corrections.py:200](../../../src/workflow/corrections.py#L200)：`not claim.source_run_ids`，不满足时有 else 分支。
- [corrections.py:202](../../../src/workflow/corrections.py#L202)：`set(claim.source_run_ids) != {run_id}`，不满足时跳过本分支。
- 另有 5 个条件判断，参见源码；不要将本列表当作全部分支。

**调用与被调用**：
- `reviewer.strip`（[corrections.py:121](../../../src/workflow/corrections.py#L121)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `reason.strip`（[corrections.py:121](../../../src/workflow/corrections.py#L121)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `request_id.strip`（[corrections.py:121](../../../src/workflow/corrections.py#L121)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `ValueError`（[corrections.py:122](../../../src/workflow/corrections.py#L122)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `self.reviews.compatible`（[corrections.py:123](../../../src/workflow/corrections.py#L123)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `self.service.show_run`（[corrections.py:123](../../../src/workflow/corrections.py#L123)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `self.service.runs.mutation_lock`（[corrections.py:124](../../../src/workflow/corrections.py#L124)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `self.reviews.recover`（[corrections.py:125](../../../src/workflow/corrections.py#L125)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `stable_id`（调用点 [corrections.py:126](../../../src/workflow/corrections.py#L126)）→ [stable_id](../core/ids.md)，静态可定位。
- `self.repository.correction`（[corrections.py:128](../../../src/workflow/corrections.py#L128)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `next`（[corrections.py:152](../../../src/workflow/corrections.py#L152)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `self.repository.events`（[corrections.py:153](../../../src/workflow/corrections.py#L153)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `CandidateClaim.model_validate`（[corrections.py:173](../../../src/workflow/corrections.py#L173)）：来自 `src.domain.CandidateClaim`；具体实现可能由依赖注入或运行时分派决定。
- `self.repository.original`（[corrections.py:173](../../../src/workflow/corrections.py#L173)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `cast`（[corrections.py:180](../../../src/workflow/corrections.py#L180)）：来自 `typing.cast`；具体实现可能由依赖注入或运行时分派决定。
- `isinstance`（[corrections.py:185](../../../src/workflow/corrections.py#L185)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `set`（[corrections.py:194](../../../src/workflow/corrections.py#L194)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `self.service.graph_store.list_claims`（[corrections.py:195](../../../src/workflow/corrections.py#L195)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `blocked.append`（[corrections.py:201](../../../src/workflow/corrections.py#L201)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `self.service.graph_store.get_evidence`（[corrections.py:207](../../../src/workflow/corrections.py#L207)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `self.service.evidence_store.get`（[corrections.py:209](../../../src/workflow/corrections.py#L209)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `self.service.graph_store.latest_revision`（[corrections.py:212](../../../src/workflow/corrections.py#L212)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `any`（[corrections.py:214](../../../src/workflow/corrections.py#L214)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `canonical_hash`（调用点 [corrections.py:222](../../../src/workflow/corrections.py#L222)）→ [canonical_hash](../core/ids.md)，静态可定位。
- `c.model_dump`（[corrections.py:222](../../../src/workflow/corrections.py#L222)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `self.service.graph_store.get_entity`（[corrections.py:225](../../../src/workflow/corrections.py#L225)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `current.model_dump`（[corrections.py:228](../../../src/workflow/corrections.py#L228)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `ReviewCorrection`（调用点 [corrections.py:230](../../../src/workflow/corrections.py#L230)）→ [ReviewCorrection](../domain/reviews.md)，静态可定位。
- `sorted`（[corrections.py:243](../../../src/workflow/corrections.py#L243)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `self.repository.propose`（[corrections.py:256](../../../src/workflow/corrections.py#L256)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- 静态扫描未定位直接调用方；可能通过路由注册、LangGraph 节点、协议方法或依赖注入动态调用，不据此判断为死代码。

**状态、副作用与异常**：
- 显式状态/容器赋值：`expected[f<字符串常量>]`。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：`ValueError(<字符串常量>)`。
- 本地捕获：`KeyError`。
- 恢复/幂等性：仅在代码有检查点、事务、请求编号或显式去重时才成立；此函数不能单凭名称视为可安全重试。


---

# CorrectionService.apply ⭐⭐

**位置与等级**：[corrections.py:259](../../../src/workflow/corrections.py#L259)；局部辅助逻辑，需理解其调用条件与失败传播。

**签名**：`async def apply(self, correction_id: str, confirm: bool) -> WorkflowState`。

**作用**：处理 `apply` 对应步骤；下列步骤依据函数体的实际控制流和调用点整理。

**输入与输出**：
- 输入：`correction_id`（str）；`confirm`（bool）。
- 输出类型：`WorkflowState`；具体返回路径见流程步骤。

**处理流程**：
1. 检查 `not confirm`；按条件分流，else 分支不存在。
2. 更新 `proposal`，值来自 `self.repository.correction(correction_id)`。
3. 进入上下文 `self.service.runs.mutation_lock(proposal.run_id)`，由上下文管理器控制资源释放或事务范围。

**关键条件与保护**：
- [corrections.py:260](../../../src/workflow/corrections.py#L260)：`not confirm`，不满足时跳过本分支。
- [corrections.py:268](../../../src/workflow/corrections.py#L268)：`self.repository.request(state.run_id, request_id)`，不满足时跳过本分支。
- [corrections.py:270](../../../src/workflow/corrections.py#L270)：`proposal.blocked_reasons`，不满足时跳过本分支。
- [corrections.py:273](../../../src/workflow/corrections.py#L273)：`(parent.id if parent else None) != proposal.parent_revision_id`，不满足时跳过本分支。
- [corrections.py:283](../../../src/workflow/corrections.py#L283)：`actual != expected`，不满足时跳过本分支。
- [corrections.py:287](../../../src/workflow/corrections.py#L287)：`task.version != proposal.expected_version or task.last_event_id != proposal.preview['expected_last_event_id']`，不满足时跳过本分支。
- [corrections.py:294](../../../src/workflow/corrections.py#L294)：`proposal.kind == 'entity'`，不满足时有 else 分支。
- [corrections.py:300](../../../src/workflow/corrections.py#L300)：`proposal.action != 'reject'`，不满足时跳过本分支。
- [corrections.py:301](../../../src/workflow/corrections.py#L301)：`target is None`，不满足时跳过本分支。
- [corrections.py:304](../../../src/workflow/corrections.py#L304)：`entity is None`，不满足时跳过本分支。
- [corrections.py:306](../../../src/workflow/corrections.py#L306)：`entity is None or not entity.active`，不满足时跳过本分支。
- [corrections.py:308](../../../src/workflow/corrections.py#L308)：`entity.id not in {e.id for e in state.entities}`，不满足时跳过本分支。
- 另有 1 个条件判断，参见源码；不要将本列表当作全部分支。

**调用与被调用**：
- `ValueError`（[corrections.py:261](../../../src/workflow/corrections.py#L261)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `self.repository.correction`（[corrections.py:262](../../../src/workflow/corrections.py#L262)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `self.service.runs.mutation_lock`（[corrections.py:263](../../../src/workflow/corrections.py#L263)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `self.reviews.recover`（[corrections.py:264](../../../src/workflow/corrections.py#L264)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `self.service.show_run`（[corrections.py:265](../../../src/workflow/corrections.py#L265)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `self.reviews.compatible`（[corrections.py:266](../../../src/workflow/corrections.py#L266)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `self.repository.request`（[corrections.py:268](../../../src/workflow/corrections.py#L268)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `<字符串常量>.join`（[corrections.py:271](../../../src/workflow/corrections.py#L271)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `self.service.graph_store.latest_revision`（[corrections.py:272](../../../src/workflow/corrections.py#L272)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `proposal.preview['expected_resources'].items`（[corrections.py:275](../../../src/workflow/corrections.py#L275)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `key.split`（[corrections.py:276](../../../src/workflow/corrections.py#L276)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `self.service.graph_store.get_claim`（[corrections.py:278](../../../src/workflow/corrections.py#L278)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `self.service.graph_store.get_entity`（[corrections.py:280](../../../src/workflow/corrections.py#L280)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `canonical_hash`（调用点 [corrections.py:282](../../../src/workflow/corrections.py#L282)）→ [canonical_hash](../core/ids.md)，静态可定位。
- `current.model_dump`（[corrections.py:282](../../../src/workflow/corrections.py#L282)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `cast`（[corrections.py:286](../../../src/workflow/corrections.py#L286)）：来自 `typing.cast`；具体实现可能由依赖注入或运行时分派决定。
- `next`（[corrections.py:286](../../../src/workflow/corrections.py#L286)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `task.model_dump`（[corrections.py:292](../../../src/workflow/corrections.py#L292)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `state.entities.append`（[corrections.py:309](../../../src/workflow/corrections.py#L309)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `self.reviews.filtered_candidates`（[corrections.py:313](../../../src/workflow/corrections.py#L313)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `set`（[corrections.py:314](../../../src/workflow/corrections.py#L314)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `state.superseded_review_tasks.extend`（[corrections.py:318](../../../src/workflow/corrections.py#L318)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `t.model_copy`（[corrections.py:319](../../../src/workflow/corrections.py#L319)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `ReviewDecision`（[corrections.py:329](../../../src/workflow/corrections.py#L329)）：来自 `src.domain.ReviewDecision`；具体实现可能由依赖注入或运行时分派决定。
- `utc_now`（[corrections.py:337](../../../src/workflow/corrections.py#L337)）：来自 `src.domain.utc_now`；具体实现可能由依赖注入或运行时分派决定。
- `stable_id`（调用点 [corrections.py:338](../../../src/workflow/corrections.py#L338)）→ [stable_id](../core/ids.md)，静态可定位。
- `self.reviews.update_status`（[corrections.py:340](../../../src/workflow/corrections.py#L340)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `ReviewEvent`（调用点 [corrections.py:343](../../../src/workflow/corrections.py#L343)）→ [ReviewEvent](../domain/reviews.md)，静态可定位。
- `self.repository.append`（[corrections.py:358](../../../src/workflow/corrections.py#L358)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `state.model_dump`（[corrections.py:358](../../../src/workflow/corrections.py#L358)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- 此处列出前 30 个不同调用表达式，另有 1 个，需按源码继续追踪。
- 静态扫描未定位直接调用方；可能通过路由注册、LangGraph 节点、协议方法或依赖注入动态调用，不据此判断为死代码。

**状态、副作用与异常**：
- 显式状态/容器赋值：`state.correction_tail_only`、`state.mention_to_entity[task.mention_id]`、`task.selected_entity_id`、`task.decision`、`state.candidates`、`state.review_tasks`、`state.current_node`、`claim.status`、`task.version`、`task.resolved_at`、`task.last_event_id`、`state.pending_correction_id`。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：`ValueError(<字符串常量>)`、`ValueError(<字符串常量>.join(proposal.blocked_reasons))`、`ValueError(f<字符串常量>)`。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。
- 恢复/幂等性：仅在代码有检查点、事务、请求编号或显式去重时才成立；此函数不能单凭名称视为可安全重试。


---

# CorrectionService.confirm ⭐⭐

**位置与等级**：[corrections.py:361](../../../src/workflow/corrections.py#L361)；局部辅助逻辑，需理解其调用条件与失败传播。

**签名**：`async def confirm(self, state: WorkflowState, reviewer: str) -> WorkflowState`。

**作用**：处理 `confirm` 对应步骤；下列步骤依据函数体的实际控制流和调用点整理。

**输入与输出**：
- 输入：`state`（WorkflowState；跨节点 WorkflowState；调用方须保持证据与状态一致）；`reviewer`（str；审核操作者，形成审计归属）。
- 输出类型：`WorkflowState`；具体返回路径见流程步骤。

**处理流程**：
1. 断言 `state.pending_correction_id and state.graph_commit`。
2. 更新 `proposal`，值来自 `self.repository.correction(state.pending_correction_id)`。
3. 更新 `tasks`，值来自 `state.entity_review_tasks if proposal.kind == 'entity' else state.review_tasks`。
4. 更新 `task`，值来自 `cast(Any, next((t for t in tasks if t.id == proposal.task_id)))`。
5. 更新 `before`，值来自 `task.model_dump(mode='json')`。
6. 更新 `request_id`，值来自 `f<字符串常量>`。
7. 检查 `self.repository.request(state.run_id, request_id)`；按条件分流，else 分支不存在。
8. 更新 `old_version`，值来自 `task.version`。
9. 更新 `task.version`，值来自 `1`。
10. 更新 `event_id`，值来自 `stable_id('review-event', state.run_id, request_id)`。
11. 更新 `task.last_event_id`，值来自 `event_id`。
12. 更新 `event`，值来自 `ReviewEvent(id=event_id, request_id=request_id, run_id=state.run_id, task_id=task.id, kind=proposal…`。
13. 更新 `state.graph_commit.revision.review_events`，值来自 `[e.model_dump(mode='json') for e in [*self.repository.events(state.run_id), event]]`。
14. 更新 `state.revision`，值来自 `state.graph_commit.revision`。
15. 更新 `(state.status, state.current_node)`，值来自 `('completed', 'commit_graph')`。
16. 更新 `state.pending_correction_id`，值来自 `None`。
17. 更新 `state.submission_confirmed`，值来自 `True`。
18. 调用 `self.repository.append`，结果未直接赋值。
19. 返回 `await self.reviews.project(event, state.model_dump(mode='json'))`。

**关键条件与保护**：
- [corrections.py:368](../../../src/workflow/corrections.py#L368)：`self.repository.request(state.run_id, request_id)`，不满足时跳过本分支。

**调用与被调用**：
- `self.repository.correction`（[corrections.py:363](../../../src/workflow/corrections.py#L363)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `cast`（[corrections.py:365](../../../src/workflow/corrections.py#L365)）：来自 `typing.cast`；具体实现可能由依赖注入或运行时分派决定。
- `next`（[corrections.py:365](../../../src/workflow/corrections.py#L365)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `task.model_dump`（[corrections.py:366](../../../src/workflow/corrections.py#L366)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `self.repository.request`（[corrections.py:368](../../../src/workflow/corrections.py#L368)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `self.service.show_run`（[corrections.py:369](../../../src/workflow/corrections.py#L369)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `stable_id`（调用点 [corrections.py:372](../../../src/workflow/corrections.py#L372)）→ [stable_id](../core/ids.md)，静态可定位。
- `ReviewEvent`（调用点 [corrections.py:374](../../../src/workflow/corrections.py#L374)）→ [ReviewEvent](../domain/reviews.md)，静态可定位。
- `reviewer.strip`（[corrections.py:382](../../../src/workflow/corrections.py#L382)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `e.model_dump`（[corrections.py:390](../../../src/workflow/corrections.py#L390)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `self.repository.events`（[corrections.py:390](../../../src/workflow/corrections.py#L390)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `self.repository.append`（[corrections.py:396](../../../src/workflow/corrections.py#L396)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `state.model_dump`（[corrections.py:396](../../../src/workflow/corrections.py#L396)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `self.reviews.project`（[corrections.py:397](../../../src/workflow/corrections.py#L397)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- 静态扫描未定位直接调用方；可能通过路由注册、LangGraph 节点、协议方法或依赖注入动态调用，不据此判断为死代码。

**状态、副作用与异常**：
- 显式状态/容器赋值：`task.version`、`task.last_event_id`、`state.graph_commit.revision.review_events`、`state.revision`、`state.pending_correction_id`、`state.submission_confirmed`。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：未见 `raise`；下游异常可能继续上抛。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。
- 恢复/幂等性：仅在代码有检查点、事务、请求编号或显式去重时才成立；此函数不能单凭名称视为可安全重试。


---
