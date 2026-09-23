源码：[entity_operations.py:1](../../../src/governance/entity_operations.py#L1) | 基准：`dev/v0.10@f2f34d7` | 本文件符号数：7

**模块职责**：Auditable merge and split operations for canonical entities.
**在系统中的位置**：实体解析、事实规范化、冲突、风险、审核及实体操作的确定性规则。
**直接依赖**：[src.core.errors](../core/errors.md)、[src.core.ids](../core/ids.md)、[src.domain](../domain/__init__.md)、[src.governance.entity_resolution](entity_resolution.md)、[src.governance.validation.context](validation/context.md)、[src.persistence.base](../persistence/base.md)、[src.persistence.entity_governance](../persistence/entity_governance.md)、[src.providers.base](../providers/base.md)；外部/标准库：`__future__`、`collections`、`uuid`。
**主要调用方（静态导入）**：[governance/__init__.py](__init__.md)。
**阅读提示**：下列流程根据当前源码控制流整理；`self`/接口对象的实际类型可能在运行时注入，未能静态解析的调用会明确标注。链接指向源码行或对应讲解文件。

---

# EntityGovernanceService ⭐⭐⭐⭐

**位置与等级**：[entity_operations.py:28](../../../src/governance/entity_operations.py#L28)；承担主要 Agent、应用服务或审核/执行入口，跨模块影响显著。

**职责**：跨步骤服务；组合依赖并暴露可复用业务入口。基类：无显式基类。

**字段与类级约束**：
- 类体未直接声明字段；实例状态请看 `__init__` 及方法中的赋值。

**内部成员**：`EntityGovernanceService.__init__`、`EntityGovernanceService.propose_merge`、`EntityGovernanceService.propose_split`、`EntityGovernanceService.resolve_operation`、`EntityGovernanceService._embedding`、`EntityGovernanceService._apply`


---

# EntityGovernanceService.__init__ ⭐⭐

**位置与等级**：[entity_operations.py:29](../../../src/governance/entity_operations.py#L29)；局部辅助逻辑，需理解其调用条件与失败传播。

**签名**：`def __init__(self, graph_store: GraphStore, repository: EntityGovernanceRepository, embedding_provider: EmbeddingProvider) -> None`。

**作用**：初始化对象并保存依赖或配置；需检查是否创建持久化资源。

**输入与输出**：
- 输入：`graph_store`（GraphStore；图持久化接口，具体实现由配置注入）；`repository`（EntityGovernanceRepository）；`embedding_provider`（EmbeddingProvider）。
- 输出类型：`None`；具体返回路径见流程步骤。

**处理流程**：
1. 更新 `self.graph_store`，值来自 `graph_store`。
2. 更新 `self.repository`，值来自 `repository`。
3. 更新 `self.embedding_provider`，值来自 `embedding_provider`。

**调用与被调用**：
- 无显式函数调用，或仅声明协议/常量。
- 静态扫描未定位直接调用方；可能通过路由注册、LangGraph 节点、协议方法或依赖注入动态调用，不据此判断为死代码。

**状态、副作用与异常**：
- 显式状态/容器赋值：`self.graph_store`、`self.repository`、`self.embedding_provider`。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：未见 `raise`；下游异常可能继续上抛。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。


---

# EntityGovernanceService.propose_merge ⭐⭐

**位置与等级**：[entity_operations.py:39](../../../src/governance/entity_operations.py#L39)；局部辅助逻辑，需理解其调用条件与失败传播。

**签名**：`async def propose_merge(self, source_entity_ids: list[str], target_entity_id: str, reasons: list[str]) -> EntityReviewTask`。

**作用**：处理 `propose_merge` 对应步骤；下列步骤依据函数体的实际控制流和调用点整理。

**输入与输出**：
- 输入：`source_entity_ids`（list[str]）；`target_entity_id`（str）；`reasons`（list[str]）。
- 输出类型：`EntityReviewTask`；具体返回路径见流程步骤。

**处理流程**：
1. 更新 `source_ids`，值来自 `list(dict.fromkeys(source_entity_ids))`。
2. 检查 `len(source_ids) < 2 or target_entity_id not in source_ids`；按条件分流，else 分支不存在。
3. 更新 `entities`，值来自 `await self.graph_store.list_entities()`。
4. 更新 `selected`，值来自 `{item.id: item for item in entities if item.id in source_ids}`。
5. 检查 `set(selected) != set(source_ids)`；按条件分流，else 分支不存在。
6. 检查 `any((not item.active for item in selected.values()))`；按条件分流，else 分支不存在。
7. 检查 `len({item.entity_type for item in selected.values()}) != 1`；按条件分流，else 分支不存在。
8. 更新 `claims`，值来自 `[item for item in await self.graph_store.list_claims() if item.tx_to is None and {item.subject_id, …`。
9. 更新 `operation`，值来自 `EntityOperation(id=stable_id('entity-operation', 'merge', *sorted(source_ids), target_entity_id, uu…`。
10. 更新 `task`，值来自 `EntityReviewTask(id=stable_id('entity-review', operation.id), run_id='governance', operation_id=ope…`。
11. 调用 `self.repository.save`，结果未直接赋值。
12. 返回 `task`。

**关键条件与保护**：
- [entity_operations.py:46](../../../src/governance/entity_operations.py#L46)：`len(source_ids) < 2 or target_entity_id not in source_ids`，不满足时跳过本分支。
- [entity_operations.py:50](../../../src/governance/entity_operations.py#L50)：`set(selected) != set(source_ids)`，不满足时跳过本分支。
- [entity_operations.py:52](../../../src/governance/entity_operations.py#L52)：`any((not item.active for item in selected.values()))`，不满足时跳过本分支。
- [entity_operations.py:54](../../../src/governance/entity_operations.py#L54)：`len({item.entity_type for item in selected.values()}) != 1`，不满足时跳过本分支。

**调用与被调用**：
- `list`（[entity_operations.py:45](../../../src/governance/entity_operations.py#L45)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `dict.fromkeys`（[entity_operations.py:45](../../../src/governance/entity_operations.py#L45)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `len`（[entity_operations.py:46](../../../src/governance/entity_operations.py#L46)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `ValueError`（[entity_operations.py:47](../../../src/governance/entity_operations.py#L47)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `self.graph_store.list_entities`（[entity_operations.py:48](../../../src/governance/entity_operations.py#L48)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `set`（[entity_operations.py:50](../../../src/governance/entity_operations.py#L50)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `KeyError`（[entity_operations.py:51](../../../src/governance/entity_operations.py#L51)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `any`（[entity_operations.py:52](../../../src/governance/entity_operations.py#L52)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `selected.values`（[entity_operations.py:52](../../../src/governance/entity_operations.py#L52)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `self.graph_store.list_claims`（[entity_operations.py:58](../../../src/governance/entity_operations.py#L58)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `EntityOperation`（[entity_operations.py:61](../../../src/governance/entity_operations.py#L61)）：来自 `src.domain.EntityOperation`；具体实现可能由依赖注入或运行时分派决定。
- `stable_id`（调用点 [entity_operations.py:62](../../../src/governance/entity_operations.py#L62)）→ [stable_id](../core/ids.md)，静态可定位。
- `sorted`（[entity_operations.py:63](../../../src/governance/entity_operations.py#L63)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `uuid4`（[entity_operations.py:63](../../../src/governance/entity_operations.py#L63)）：来自 `uuid.uuid4`；具体实现可能由依赖注入或运行时分派决定。
- `item.model_dump`（[entity_operations.py:70](../../../src/governance/entity_operations.py#L70)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `EntityReviewTask`（[entity_operations.py:77](../../../src/governance/entity_operations.py#L77)）：来自 `src.domain.EntityReviewTask`；具体实现可能由依赖注入或运行时分派决定。
- `self.repository.save`（[entity_operations.py:84](../../../src/governance/entity_operations.py#L84)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- 静态扫描未定位直接调用方；可能通过路由注册、LangGraph 节点、协议方法或依赖注入动态调用，不据此判断为死代码。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：`ValueError(<字符串常量>)`、`KeyError(<字符串常量>)`。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。


---

# EntityGovernanceService.propose_split ⭐⭐

**位置与等级**：[entity_operations.py:87](../../../src/governance/entity_operations.py#L87)；局部辅助逻辑，需理解其调用条件与失败传播。

**签名**：`async def propose_split(self, source_entity_id: str, target_entities: list[CanonicalEntity], claim_assignments: Mapping[str, str], reasons: list[str]) -> EntityReviewTask`。

**作用**：处理 `propose_split` 对应步骤；下列步骤依据函数体的实际控制流和调用点整理。

**输入与输出**：
- 输入：`source_entity_id`（str）；`target_entities`（list[CanonicalEntity]）；`claim_assignments`（Mapping[str, str]）；`reasons`（list[str]）。
- 输出类型：`EntityReviewTask`；具体返回路径见流程步骤。

**处理流程**：
1. 更新 `source`，值来自 `await self.graph_store.get_entity(source_entity_id)`。
2. 检查 `source is None`；按条件分流，else 分支不存在。
3. 检查 `not source.active`；按条件分流，else 分支不存在。
4. 检查 `not target_entities`；按条件分流，else 分支不存在。
5. 更新 `targets`，值来自 `{item.id: item for item in target_entities}`。
6. 检查 `len(targets) != len(target_entities)`；按条件分流，else 分支不存在。
7. 更新 `existing_ids`，值来自 `{item.id for item in await self.graph_store.list_entities()}`。
8. 检查 `set(targets) & existing_ids`；按条件分流，else 分支不存在。
9. 检查 `any((item.entity_type != source.entity_type for item in targets.values()))`；按条件分流，else 分支不存在。
10. 检查 `not set(claim_assignments.values()) <= set(targets)`；按条件分流，else 分支不存在。
11. 更新 `claims`，值来自 `{item.id: item for item in await self.graph_store.list_claims() if item.tx_to is None and source_en…`。
12. 检查 `not claim_assignments or not set(claim_assignments) <= set(claims)`；按条件分流，else 分支不存在。
13. 更新 `evidence_ids`，值来自 `sorted({evidence for claim_id in claim_assignments for evidence in claims[claim_id].evidence_ids})`。
14. 检查 `not evidence_ids`；按条件分流，else 分支不存在。
15. 更新 `operation`，值来自 `EntityOperation(id=stable_id('entity-operation', 'split', source_entity_id, canonical_hash(dict(sor…`。
16. 更新 `task`，值来自 `EntityReviewTask(id=stable_id('entity-review', operation.id), run_id='governance', operation_id=ope…`。
17. 调用 `self.repository.save`，结果未直接赋值。
18. 返回 `task`。

**关键条件与保护**：
- [entity_operations.py:95](../../../src/governance/entity_operations.py#L95)：`source is None`，不满足时跳过本分支。
- [entity_operations.py:97](../../../src/governance/entity_operations.py#L97)：`not source.active`，不满足时跳过本分支。
- [entity_operations.py:99](../../../src/governance/entity_operations.py#L99)：`not target_entities`，不满足时跳过本分支。
- [entity_operations.py:102](../../../src/governance/entity_operations.py#L102)：`len(targets) != len(target_entities)`，不满足时跳过本分支。
- [entity_operations.py:105](../../../src/governance/entity_operations.py#L105)：`set(targets) & existing_ids`，不满足时跳过本分支。
- [entity_operations.py:107](../../../src/governance/entity_operations.py#L107)：`any((item.entity_type != source.entity_type for item in targets.values()))`，不满足时跳过本分支。
- [entity_operations.py:109](../../../src/governance/entity_operations.py#L109)：`not set(claim_assignments.values()) <= set(targets)`，不满足时跳过本分支。
- [entity_operations.py:116](../../../src/governance/entity_operations.py#L116)：`not claim_assignments or not set(claim_assignments) <= set(claims)`，不满足时跳过本分支。
- [entity_operations.py:125](../../../src/governance/entity_operations.py#L125)：`not evidence_ids`，不满足时跳过本分支。

**调用与被调用**：
- `self.graph_store.get_entity`（[entity_operations.py:94](../../../src/governance/entity_operations.py#L94)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `KeyError`（[entity_operations.py:96](../../../src/governance/entity_operations.py#L96)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `ValueError`（[entity_operations.py:98](../../../src/governance/entity_operations.py#L98)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `len`（[entity_operations.py:102](../../../src/governance/entity_operations.py#L102)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `self.graph_store.list_entities`（[entity_operations.py:104](../../../src/governance/entity_operations.py#L104)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `set`（[entity_operations.py:105](../../../src/governance/entity_operations.py#L105)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `any`（[entity_operations.py:107](../../../src/governance/entity_operations.py#L107)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `targets.values`（[entity_operations.py:107](../../../src/governance/entity_operations.py#L107)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `claim_assignments.values`（[entity_operations.py:109](../../../src/governance/entity_operations.py#L109)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `self.graph_store.list_claims`（[entity_operations.py:113](../../../src/governance/entity_operations.py#L113)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `sorted`（[entity_operations.py:118](../../../src/governance/entity_operations.py#L118)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `EntityOperation`（[entity_operations.py:127](../../../src/governance/entity_operations.py#L127)）：来自 `src.domain.EntityOperation`；具体实现可能由依赖注入或运行时分派决定。
- `stable_id`（调用点 [entity_operations.py:128](../../../src/governance/entity_operations.py#L128)）→ [stable_id](../core/ids.md)，静态可定位。
- `canonical_hash`（调用点 [entity_operations.py:132](../../../src/governance/entity_operations.py#L132)）→ [canonical_hash](../core/ids.md)，静态可定位。
- `dict`（[entity_operations.py:132](../../../src/governance/entity_operations.py#L132)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `claim_assignments.items`（[entity_operations.py:132](../../../src/governance/entity_operations.py#L132)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `uuid4`（[entity_operations.py:133](../../../src/governance/entity_operations.py#L133)）：来自 `uuid.uuid4`；具体实现可能由依赖注入或运行时分派决定。
- `source.model_dump`（[entity_operations.py:140](../../../src/governance/entity_operations.py#L140)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `claims[claim_id].model_dump`（[entity_operations.py:142](../../../src/governance/entity_operations.py#L142)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `item.model_dump`（[entity_operations.py:148](../../../src/governance/entity_operations.py#L148)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `EntityReviewTask`（[entity_operations.py:155](../../../src/governance/entity_operations.py#L155)）：来自 `src.domain.EntityReviewTask`；具体实现可能由依赖注入或运行时分派决定。
- `self.repository.save`（[entity_operations.py:162](../../../src/governance/entity_operations.py#L162)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- 静态扫描未定位直接调用方；可能通过路由注册、LangGraph 节点、协议方法或依赖注入动态调用，不据此判断为死代码。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：`KeyError(f<字符串常量>)`、`ValueError(<字符串常量>)`。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。


---

# EntityGovernanceService.resolve_operation ⭐⭐⭐⭐

**位置与等级**：[entity_operations.py:165](../../../src/governance/entity_operations.py#L165)；承担主要 Agent、应用服务或审核/执行入口，跨模块影响显著。

**签名**：`async def resolve_operation(self, task_id: str, approve: bool, reviewer: str | None=None) -> GraphRevision | None`。

**作用**：处理 `resolve_operation` 对应步骤；下列步骤依据函数体的实际控制流和调用点整理。

**输入与输出**：
- 输入：`task_id`（str；待处理审核任务标识）；`approve`（bool）；`reviewer`（str | None；默认 `None`；审核操作者，形成审计归属）。
- 输出类型：`GraphRevision | None`；具体返回路径见流程步骤。

**处理流程**：
1. 更新 `task`，值来自 `self.repository.get_task(task_id)`。
2. 检查 `task is None or task.operation_id is None`；按条件分流，else 分支不存在。
3. 更新 `operation`，值来自 `self.repository.get_operation(task.operation_id)`。
4. 检查 `operation is None`；按条件分流，else 分支不存在。
5. 检查 `task.status == 'resolved'`；按条件分流，else 分支不存在。
6. 更新 `task.status`，值来自 `'resolved'`。
7. 更新 `task.decision`，值来自 `'approve' if approve else 'reject'`。
8. 更新 `task.resolved_at`，值来自 `utc_now()`。
9. 更新 `operation.reviewer`，值来自 `reviewer`。
10. 更新 `operation.reviewed_at`，值来自 `task.resolved_at`。
11. 检查 `not approve`；按条件分流，else 分支不存在。
12. 更新 `operation.status`，值来自 `'approved'`。
13. 更新 `revision`，值来自 `await self._apply(operation)`。
14. 更新 `operation.status`，值来自 `'applied'`。
15. 调用 `self.repository.update`，结果未直接赋值。
16. 返回 `revision`。

**关键条件与保护**：
- [entity_operations.py:169](../../../src/governance/entity_operations.py#L169)：`task is None or task.operation_id is None`，不满足时跳过本分支。
- [entity_operations.py:172](../../../src/governance/entity_operations.py#L172)：`operation is None`，不满足时跳过本分支。
- [entity_operations.py:174](../../../src/governance/entity_operations.py#L174)：`task.status == 'resolved'`，不满足时跳过本分支。
- [entity_operations.py:175](../../../src/governance/entity_operations.py#L175)：`operation.status == 'applied'`，不满足时跳过本分支。
- [entity_operations.py:187](../../../src/governance/entity_operations.py#L187)：`not approve`，不满足时跳过本分支。

**调用与被调用**：
- `self.repository.get_task`（[entity_operations.py:168](../../../src/governance/entity_operations.py#L168)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `KeyError`（[entity_operations.py:170](../../../src/governance/entity_operations.py#L170)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `self.repository.get_operation`（[entity_operations.py:171](../../../src/governance/entity_operations.py#L171)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `GraphIntegrityError`（调用点 [entity_operations.py:173](../../../src/governance/entity_operations.py#L173)）→ [GraphIntegrityError](../core/errors.md)，静态可定位。
- `self.graph_store.list_revisions`（[entity_operations.py:176](../../../src/governance/entity_operations.py#L176)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `next`（[entity_operations.py:177](../../../src/governance/entity_operations.py#L177)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `utc_now`（[entity_operations.py:184](../../../src/governance/entity_operations.py#L184)）：来自 `src.domain.utc_now`；具体实现可能由依赖注入或运行时分派决定。
- `self.repository.update`（[entity_operations.py:189](../../../src/governance/entity_operations.py#L189)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `self._apply`（调用点 [entity_operations.py:192](../../../src/governance/entity_operations.py#L192)）→ [EntityGovernanceService._apply](entity_operations.md)，静态可定位。
- 静态扫描未定位直接调用方；可能通过路由注册、LangGraph 节点、协议方法或依赖注入动态调用，不据此判断为死代码。

**状态、副作用与异常**：
- 显式状态/容器赋值：`task.status`、`task.decision`、`task.resolved_at`、`operation.reviewer`、`operation.reviewed_at`、`operation.status`。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：`KeyError(f<字符串常量>)`、`GraphIntegrityError(f<字符串常量>)`。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。


---

# EntityGovernanceService._embedding ⭐⭐

**位置与等级**：[entity_operations.py:197](../../../src/governance/entity_operations.py#L197)；局部辅助逻辑，需理解其调用条件与失败传播。

**签名**：`async def _embedding(self, entity: CanonicalEntity) -> EntityEmbedding | None`。

**作用**：内部辅助步骤；将参数转换为本模块所需的中间对象或操作结果。

**输入与输出**：
- 输入：`entity`（CanonicalEntity）。
- 输出类型：`EntityEmbedding | None`；具体返回路径见流程步骤。

**处理流程**：
1. 检查 `self.embedding_provider.fingerprint() == 'embedding:disabled'`；按条件分流，else 分支不存在。
2. 更新 `text`，值来自 `entity_embedding_text(entity)`。
3. 更新 `vector`，值来自 `(await self.embedding_provider.encode([text]))[0]`。
4. 返回 `EntityEmbedding(entity_id=entity.id, model_fingerprint=self.embedding_provider.fingerprint(), text_hash=…`。

**关键条件与保护**：
- [entity_operations.py:198](../../../src/governance/entity_operations.py#L198)：`self.embedding_provider.fingerprint() == 'embedding:disabled'`，不满足时跳过本分支。

**调用与被调用**：
- `self.embedding_provider.fingerprint`（[entity_operations.py:198](../../../src/governance/entity_operations.py#L198)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `entity_embedding_text`（调用点 [entity_operations.py:200](../../../src/governance/entity_operations.py#L200)）→ [entity_embedding_text](entity_resolution.md)，静态可定位。
- `self.embedding_provider.encode`（[entity_operations.py:201](../../../src/governance/entity_operations.py#L201)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `EntityEmbedding`（[entity_operations.py:202](../../../src/governance/entity_operations.py#L202)）：来自 `src.domain.EntityEmbedding`；具体实现可能由依赖注入或运行时分派决定。
- `canonical_hash`（调用点 [entity_operations.py:205](../../../src/governance/entity_operations.py#L205)）→ [canonical_hash](../core/ids.md)，静态可定位。
- `len`（[entity_operations.py:206](../../../src/governance/entity_operations.py#L206)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- 静态可定位的调用方：[EntityGovernanceService._apply](entity_operations.md)。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：未见 `raise`；下游异常可能继续上抛。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。


---

# EntityGovernanceService._apply ⭐⭐

**位置与等级**：[entity_operations.py:210](../../../src/governance/entity_operations.py#L210)；局部辅助逻辑，需理解其调用条件与失败传播。

**签名**：`async def _apply(self, operation: EntityOperation) -> GraphRevision`。

**作用**：内部辅助步骤；将参数转换为本模块所需的中间对象或操作结果。

**输入与输出**：
- 输入：`operation`（EntityOperation）。
- 输出类型：`GraphRevision`；具体返回路径见流程步骤。

**处理流程**：
1. 更新 `parent`，值来自 `await self.graph_store.latest_revision()`。
2. 更新 `entities`，值来自 `{item.id: item for item in await self.graph_store.list_entities()}`。
3. 更新 `claims`，值来自 `{item.id: item for item in await self.graph_store.list_claims()}`。
4. 检查 `operation.operation_type == 'split' and set(operation.target_entity_ids) & set(entities)`；按条件分流，else 分支不存在。
5. 遍历 `(('entities', entities), ('claims', claims))`，逐项处理 `(resource_type, current)`。
6. 更新 `changed_entities`，值来自 `{}`。
7. 更新 `changed_claims`，值来自 `{}`。
8. 更新 `changes`，值来自 `[]`。
9. 检查 `operation.operation_type == 'merge'`；按条件分流，else 分支存在。
10. 更新 `applied`，值来自 `operation.model_copy(update={'status': 'applied'})`。
11. 调用 `changes.append`，结果未直接赋值。
12. 更新 `revision`，值来自 `GraphRevision(id=stable_id('revision', 'entity-governance', operation.id, parent.id if parent else …`。
13. 更新 `embeddings`，值来自 `[result for result in [await self._embedding(item) for item in changed_entities.values() if item.ac…`。
14. 更新 `context`，值来自 `context_for_claims(await self.graph_store.list_revisions(limit=100000), set(claims))`。
15. 等待 `self.graph_store.commit(GraphCommit(entities=list(changed_entities.values()), claims=list(changed_claims…` 完成。
16. 返回 `revision`。

**关键条件与保护**：
- [entity_operations.py:214](../../../src/governance/entity_operations.py#L214)：`operation.operation_type == 'split' and set(operation.target_entity_ids) & set(entities)`，不满足时跳过本分支。
- [entity_operations.py:219](../../../src/governance/entity_operations.py#L219)：`resource is None or canonical_hash(resource.model_dump(mode='json')) != canonical_hash(expected)`，不满足时跳过本分支。
- [entity_operations.py:229](../../../src/governance/entity_operations.py#L229)：`operation.operation_type == 'merge'`，不满足时有 else 分支。

**调用与被调用**：
- `self.graph_store.latest_revision`（[entity_operations.py:211](../../../src/governance/entity_operations.py#L211)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `self.graph_store.list_entities`（[entity_operations.py:212](../../../src/governance/entity_operations.py#L212)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `self.graph_store.list_claims`（[entity_operations.py:213](../../../src/governance/entity_operations.py#L213)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `set`（[entity_operations.py:214](../../../src/governance/entity_operations.py#L214)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `GraphIntegrityError`（调用点 [entity_operations.py:215](../../../src/governance/entity_operations.py#L215)）→ [GraphIntegrityError](../core/errors.md)，静态可定位。
- `operation.before.get(resource_type, {}).items`（[entity_operations.py:217](../../../src/governance/entity_operations.py#L217)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `operation.before.get`（[entity_operations.py:217](../../../src/governance/entity_operations.py#L217)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `current.get`（[entity_operations.py:218](../../../src/governance/entity_operations.py#L218)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `canonical_hash`（调用点 [entity_operations.py:219](../../../src/governance/entity_operations.py#L219)）→ [canonical_hash](../core/ids.md)，静态可定位。
- `resource.model_dump`（[entity_operations.py:219](../../../src/governance/entity_operations.py#L219)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `target.model_copy`（[entity_operations.py:233](../../../src/governance/entity_operations.py#L233)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `sorted`（[entity_operations.py:235](../../../src/governance/entity_operations.py#L235)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `item.attributes.items`（[entity_operations.py:244](../../../src/governance/entity_operations.py#L244)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `source.model_copy`（[entity_operations.py:258](../../../src/governance/entity_operations.py#L258)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `changes.append`（[entity_operations.py:261](../../../src/governance/entity_operations.py#L261)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `GraphChange`（[entity_operations.py:262](../../../src/governance/entity_operations.py#L262)）：来自 `src.domain.GraphChange`；具体实现可能由依赖注入或运行时分派决定。
- `source.model_dump`（[entity_operations.py:266](../../../src/governance/entity_operations.py#L266)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `replacement_entity.model_dump`（[entity_operations.py:267](../../../src/governance/entity_operations.py#L267)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `claim.model_copy`（[entity_operations.py:272](../../../src/governance/entity_operations.py#L272)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `claim.model_dump`（[entity_operations.py:292](../../../src/governance/entity_operations.py#L292)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `replacement_claim.model_dump`（[entity_operations.py:293](../../../src/governance/entity_operations.py#L293)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `CanonicalEntity.model_validate`（[entity_operations.py:301](../../../src/governance/entity_operations.py#L301)）：来自 `src.domain.CanonicalEntity`；具体实现可能由依赖注入或运行时分派决定。
- `target_payloads.items`（[entity_operations.py:302](../../../src/governance/entity_operations.py#L302)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `changed_entities.update`（[entity_operations.py:304](../../../src/governance/entity_operations.py#L304)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `assignments.items`（[entity_operations.py:306](../../../src/governance/entity_operations.py#L306)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `claims.values`（[entity_operations.py:332](../../../src/governance/entity_operations.py#L332)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `bool`（[entity_operations.py:337](../../../src/governance/entity_operations.py#L337)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `replacement_source.model_dump`（[entity_operations.py:345](../../../src/governance/entity_operations.py#L345)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `targets.values`（[entity_operations.py:348](../../../src/governance/entity_operations.py#L348)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `entities[target.id].model_dump`（[entity_operations.py:355](../../../src/governance/entity_operations.py#L355)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- 此处列出前 30 个不同调用表达式，另有 13 个，需按源码继续追踪。
- 静态可定位的调用方：[EntityGovernanceService.resolve_operation](entity_operations.md)。

**状态、副作用与异常**：
- 显式状态/容器赋值：`changed_entities[target_id]`、`changed_entities[source.id]`、`changed_claims[claim.id]`、`changed_entities[source_id]`。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：`GraphIntegrityError(<字符串常量>)`、`GraphIntegrityError(f<字符串常量>)`。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。


---
