源码：[neo4j_graph.py:1](../../../src/persistence/neo4j_graph.py#L1) | 基准：`dev/v0.10@f2f34d7` | 本文件符号数：25

**模块职责**：Neo4j graph store using one managed transaction per GraphCommit.
**在系统中的位置**：图、证据、运行、审计、审核与案例的持久化；JSON/Neo4j 提供同一存储协议。
**阅读重点**：Neo4jGraphStore 使用官方异步驱动及 managed transaction。实体、Claim、证据、冲突和 Revision 同事务提交；向量是派生索引数据。
**直接依赖**：[src.core.errors](../core/errors.md)、[src.core.ids](../core/ids.md)、[src.domain](../domain/__init__.md)、[src.governance.validation](../governance/validation/__init__.md)、[src.governance.validation.context](../governance/validation/context.md)、[src.persistence.base](base.md)；外部/标准库：`__future__`、`asyncio`、`datetime`、`math`、`orjson`、`typing`。
**主要调用方（静态导入）**：[persistence/__init__.py](__init__.md)、[persistence/legacy_evidence.py](legacy_evidence.md)。
**阅读提示**：下列流程根据当前源码控制流整理；`self`/接口对象的实际类型可能在运行时注入，未能静态解析的调用会明确标注。链接指向源码行或对应讲解文件。

## 核心路径解读

- `commit` 保证约束已建立后，调用 async session 的 `execute_write(_commit_tx, transaction)`；管理事务内核对图头父版本并提交实体、证据、事实、冲突、变更与 Revision。失败应由 Neo4j 回滚整次事务。
- `search_entities` 使用向量索引召回候选，但向量是可重建派生数据；索引查询与正式 GraphCommit 是不同边界。
- `rollback_revision` 保留历史并写补偿 Revision；事务内再核对当前图头与资源，不能以旧预览覆盖更新后的事实。

---

# _dump ⭐⭐

**位置与等级**：[neo4j_graph.py:37](../../../src/persistence/neo4j_graph.py#L37)；局部辅助逻辑，需理解其调用条件与失败传播。

**签名**：`def _dump(model: Any) -> str`。

**作用**：内部辅助步骤；将参数转换为本模块所需的中间对象或操作结果。

**输入与输出**：
- 输入：`model`（Any）。
- 输出类型：`str`；具体返回路径见流程步骤。

**处理流程**：
1. 返回 `orjson.dumps(model.model_dump(mode='json')).decode('utf-8')`。

**调用与被调用**：
- `orjson.dumps(model.model_dump(mode='json')).decode`（[neo4j_graph.py:38](../../../src/persistence/neo4j_graph.py#L38)）：来自 `orjson`；具体实现可能由依赖注入或运行时分派决定。
- `orjson.dumps`（[neo4j_graph.py:38](../../../src/persistence/neo4j_graph.py#L38)）：来自 `orjson`；具体实现可能由依赖注入或运行时分派决定。
- `model.model_dump`（[neo4j_graph.py:38](../../../src/persistence/neo4j_graph.py#L38)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- 静态可定位的调用方：[Neo4jGraphStore._commit_tx](neo4j_graph.md)。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：未见 `raise`；下游异常可能继续上抛。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。
- 恢复/幂等性：仅在代码有检查点、事务、请求编号或显式去重时才成立；此函数不能单凭名称视为可安全重试。


---

# _load ⭐⭐

**位置与等级**：[neo4j_graph.py:41](../../../src/persistence/neo4j_graph.py#L41)；局部辅助逻辑，需理解其调用条件与失败传播。

**签名**：`def _load(payload: str, model: Any) -> Any`。

**作用**：内部辅助步骤；将参数转换为本模块所需的中间对象或操作结果。

**输入与输出**：
- 输入：`payload`（str）；`model`（Any）。
- 输出类型：`Any`；具体返回路径见流程步骤。

**处理流程**：
1. 返回 `model.model_validate(orjson.loads(payload))`。

**调用与被调用**：
- `model.model_validate`（[neo4j_graph.py:42](../../../src/persistence/neo4j_graph.py#L42)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `orjson.loads`（[neo4j_graph.py:42](../../../src/persistence/neo4j_graph.py#L42)）：来自 `orjson`；具体实现可能由依赖注入或运行时分派决定。
- 静态可定位的调用方：[Neo4jGraphStore._commit_tx](neo4j_graph.md)、[Neo4jGraphStore.list_entities](neo4j_graph.md)、[Neo4jGraphStore.search_entities](neo4j_graph.md)、[Neo4jGraphStore.list_claims](neo4j_graph.md)、[Neo4jGraphStore.list_revisions](neo4j_graph.md)、[Neo4jGraphStore._get](neo4j_graph.md)、[Neo4jGraphStore.get_neighborhood](neo4j_graph.md)。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：未见 `raise`；下游异常可能继续上抛。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。
- 恢复/幂等性：仅在代码有检查点、事务、请求编号或显式去重时才成立；此函数不能单凭名称视为可安全重试。


---

# Neo4jGraphStore ⭐⭐⭐⭐

**位置与等级**：[neo4j_graph.py:45](../../../src/persistence/neo4j_graph.py#L45)；承担主要 Agent、应用服务或审核/执行入口，跨模块影响显著。

**职责**：存储接口或实现；方法决定数据读取、持久化与并发边界。基类：无显式基类。

**字段与类级约束**：
- 类体未直接声明字段；实例状态请看 `__init__` 及方法中的赋值。

**内部成员**：`Neo4jGraphStore.__init__`、`Neo4jGraphStore._ensure_schema`、`Neo4jGraphStore.healthcheck`、`Neo4jGraphStore._commit_tx`、`Neo4jGraphStore.commit`、`Neo4jGraphStore._list_payloads`、`Neo4jGraphStore.list_entities`、`Neo4jGraphStore.get_entity`、`Neo4jGraphStore.search_entities`、`Neo4jGraphStore.list_entity_embeddings`、`Neo4jGraphStore.upsert_entity_embeddings`、`Neo4jGraphStore.list_claims`、`Neo4jGraphStore.latest_revision`、`Neo4jGraphStore.list_revisions`、`Neo4jGraphStore._get`、`Neo4jGraphStore.get_claim`、`Neo4jGraphStore.get_evidence`、`Neo4jGraphStore.get_neighborhood`、`Neo4jGraphStore.diff_revisions`、`Neo4jGraphStore.rollback_revision`、`Neo4jGraphStore.close`


---

# Neo4jGraphStore.__init__ ⭐⭐

**位置与等级**：[neo4j_graph.py:46](../../../src/persistence/neo4j_graph.py#L46)；局部辅助逻辑，需理解其调用条件与失败传播。

**签名**：`def __init__(self, uri: str, user: str, password: str, database: str='neo4j', *, driver: Any | None=None, evidence_store: EvidenceStore | None=None) -> None`。

**作用**：初始化对象并保存依赖或配置；需检查是否创建持久化资源。

**输入与输出**：
- 输入：`uri`（str）；`user`（str）；`password`（str）；`database`（str；默认 `'neo4j'`）；`driver`（Any | None；默认 `None`）；`evidence_store`（EvidenceStore | None；默认 `None`；证据元数据和原始内容的存储接口）。
- 输出类型：`None`；具体返回路径见流程步骤。

**处理流程**：
1. 更新 `self.evidence_store`，值来自 `evidence_store`。
2. 检查 `driver is None`；按条件分流，else 分支不存在。
3. 更新 `self.driver`，值来自 `driver`。
4. 更新 `self.database`，值来自 `database`。
5. 更新 `self._schema_ready`，值来自 `False`。
6. 更新 `self._schema_lock`，值来自 `asyncio.Lock()`。

**关键条件与保护**：
- [neo4j_graph.py:57](../../../src/persistence/neo4j_graph.py#L57)：`driver is None`，不满足时跳过本分支。

**调用与被调用**：
- `RuntimeError`（[neo4j_graph.py:61](../../../src/persistence/neo4j_graph.py#L61)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `AsyncGraphDatabase.driver`（[neo4j_graph.py:64](../../../src/persistence/neo4j_graph.py#L64)）：来自 `neo4j.AsyncGraphDatabase`；具体实现可能由依赖注入或运行时分派决定。
- `asyncio.Lock`（[neo4j_graph.py:68](../../../src/persistence/neo4j_graph.py#L68)）：来自 `asyncio`；具体实现可能由依赖注入或运行时分派决定。
- 静态扫描未定位直接调用方；可能通过路由注册、LangGraph 节点、协议方法或依赖注入动态调用，不据此判断为死代码。

**状态、副作用与异常**：
- 显式状态/容器赋值：`self.evidence_store`、`self.driver`、`self.database`、`self._schema_ready`、`self._schema_lock`。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：`RuntimeError(<字符串常量>)`。
- 本地捕获：`ImportError`。
- 恢复/幂等性：仅在代码有检查点、事务、请求编号或显式去重时才成立；此函数不能单凭名称视为可安全重试。


---

# Neo4jGraphStore._ensure_schema ⭐⭐

**位置与等级**：[neo4j_graph.py:70](../../../src/persistence/neo4j_graph.py#L70)；局部辅助逻辑，需理解其调用条件与失败传播。

**签名**：`async def _ensure_schema(self) -> None`。

**作用**：内部辅助步骤；将参数转换为本模块所需的中间对象或操作结果。

**输入与输出**：
- 输入：无业务参数（或仅隐式接收实例）。
- 输出类型：`None`；具体返回路径见流程步骤。

**处理流程**：
1. 检查 `self._schema_ready`；按条件分流，else 分支不存在。
2. 进入上下文 `self._schema_lock`，由上下文管理器控制资源释放或事务范围。

**关键条件与保护**：
- [neo4j_graph.py:71](../../../src/persistence/neo4j_graph.py#L71)：`self._schema_ready`，不满足时跳过本分支。
- [neo4j_graph.py:74](../../../src/persistence/neo4j_graph.py#L74)：`self._schema_ready`，不满足时跳过本分支。
- [neo4j_graph.py:113](../../../src/persistence/neo4j_graph.py#L113)：`record is not None and record['state'] == 'ONLINE'`，不满足时跳过本分支。

**调用与被调用**：
- `label.lower`（[neo4j_graph.py:77](../../../src/persistence/neo4j_graph.py#L77)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `statements.extend`（[neo4j_graph.py:90](../../../src/persistence/neo4j_graph.py#L90)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `self.driver.session`（[neo4j_graph.py:103](../../../src/persistence/neo4j_graph.py#L103)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `session.run`（[neo4j_graph.py:105](../../../src/persistence/neo4j_graph.py#L105)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `range`（[neo4j_graph.py:106](../../../src/persistence/neo4j_graph.py#L106)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `result.single`（[neo4j_graph.py:112](../../../src/persistence/neo4j_graph.py#L112)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `asyncio.sleep`（[neo4j_graph.py:115](../../../src/persistence/neo4j_graph.py#L115)）：来自 `asyncio`；具体实现可能由依赖注入或运行时分派决定。
- `GraphIntegrityError`（调用点 [neo4j_graph.py:117](../../../src/persistence/neo4j_graph.py#L117)）→ [GraphIntegrityError](../core/errors.md)，静态可定位。
- 静态可定位的调用方：[Neo4jGraphStore.healthcheck](neo4j_graph.md)、[Neo4jGraphStore.commit](neo4j_graph.md)、[Neo4jGraphStore.search_entities](neo4j_graph.md)、[Neo4jGraphStore.upsert_entity_embeddings](neo4j_graph.md)。

**状态、副作用与异常**：
- 显式状态/容器赋值：`self._schema_ready`。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：`GraphIntegrityError(<字符串常量>)`。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。
- 恢复/幂等性：仅在代码有检查点、事务、请求编号或显式去重时才成立；此函数不能单凭名称视为可安全重试。


---

# Neo4jGraphStore.healthcheck ⭐⭐

**位置与等级**：[neo4j_graph.py:122](../../../src/persistence/neo4j_graph.py#L122)；局部辅助逻辑，需理解其调用条件与失败传播。

**签名**：`async def healthcheck(self) -> GraphHealth`。

**作用**：查询当前后端是否可用并构造健康状态。

**输入与输出**：
- 输入：无业务参数（或仅隐式接收实例）。
- 输出类型：`GraphHealth`；具体返回路径见流程步骤。

**处理流程**：
1. 捕获 Exception；另检查 finally/else 的清理和传播。
2. 返回 `GraphHealth(backend='neo4j', healthy=True)`。

**调用与被调用**：
- `self.driver.verify_connectivity`（[neo4j_graph.py:124](../../../src/persistence/neo4j_graph.py#L124)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `self._ensure_schema`（调用点 [neo4j_graph.py:125](../../../src/persistence/neo4j_graph.py#L125)）→ [Neo4jGraphStore._ensure_schema](neo4j_graph.md)，静态可定位。
- `GraphHealth`（[neo4j_graph.py:127](../../../src/persistence/neo4j_graph.py#L127)）：来自 `src.domain.GraphHealth`；具体实现可能由依赖注入或运行时分派决定。
- `type`（[neo4j_graph.py:127](../../../src/persistence/neo4j_graph.py#L127)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- 静态扫描未定位直接调用方；可能通过路由注册、LangGraph 节点、协议方法或依赖注入动态调用，不据此判断为死代码。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：未见 `raise`；下游异常可能继续上抛。
- 本地捕获：`Exception`。
- 恢复/幂等性：仅在代码有检查点、事务、请求编号或显式去重时才成立；此函数不能单凭名称视为可安全重试。


---

# Neo4jGraphStore._commit_tx ⭐⭐⭐⭐⭐

**位置与等级**：[neo4j_graph.py:130](../../../src/persistence/neo4j_graph.py#L130)；位于工作流推进、硬校验或原子事务的关键边界；错误可能影响审核停顿或图状态。

**签名**：`async def _commit_tx(self, tx: Any, transaction: GraphCommit) -> None`。

**作用**：内部辅助步骤；将参数转换为本模块所需的中间对象或操作结果。

**输入与输出**：
- 输入：`tx`（Any）；`transaction`（GraphCommit；待提交 GraphCommit；必须在最终写入边界重新校验）。
- 输出类型：`None`；具体返回路径见流程步骤。

**处理流程**：
1. 更新 `result`，值来自 `await tx.run(<字符串常量>)`。
2. 更新 `head`，值来自 `await result.single()`。
3. 更新 `result`，值来自 `await tx.run(<字符串常量>, id=transaction.revision.id)`。
4. 更新 `record`，值来自 `await result.single()`。
5. 检查 `record is not None`；按条件分流，else 分支不存在。
6. 更新 `latest_id`，值来自 `head['latest_id'] if head is not None else None`。
7. 检查 `latest_id is None`；按条件分流，else 分支不存在。
8. 检查 `transaction.revision.parent_id != latest_id`；按条件分流，else 分支不存在。
9. 更新 `entity_result`，值来自 `await tx.run(<字符串常量>)`。
10. 更新 `entities`，值来自 `{_load(r['payload'], CanonicalEntity).id: _load(r['payload'], CanonicalEntity) async for r in entit…`。
11. 更新 `previous_entities`，值来自 `dict(entities)`。
12. 调用 `entities.update`，结果未直接赋值。
13. 更新 `evidence_result`，值来自 `await tx.run(<字符串常量>)`。
14. 更新 `evidence_map`，值来自 `{_load(r['payload'], EvidenceRef).id: _load(r['payload'], EvidenceRef) async for r in evidence_resu…`。
15. 调用 `evidence_map.update`，结果未直接赋值。
16. 更新 `document_result`，值来自 `await tx.run(<字符串常量>)`。
17. 更新 `document_ids`，值来自 `{r['id'] async for r in document_result} | {d.id for d in transaction.documents}`。
18. 更新 `claim_result`，值来自 `await tx.run(<字符串常量>)`。
19. 更新 `current_claims`，值来自 `{_load(r['payload'], Claim).id: _load(r['payload'], Claim) async for r in claim_result}`。
20. 更新 `exact_maintenance`，值来自 `transaction.revision.run_id == 'maintenance:legacy-evidence-v092'`。
21. 检查 `transaction.revision.run_id.startswith('rollback:') or exact_maintenance`；按条件分流，else 分支不存在。
22. 调用 `verify_correction`，结果未直接赋值。
23. 更新 `transaction.claims`，值来自 `[JSONGraphStore._merge_claim(current_claims[c.id].model_dump(mode='json'), c) if c.id in current_cl…`。
24. 调用 `current_claims.update`，结果未直接赋值。
后续还有 14 个语句级步骤，见源码对应行；这里优先保留主要控制流。

**关键条件与保护**：
- [neo4j_graph.py:140](../../../src/persistence/neo4j_graph.py#L140)：`record is not None`，不满足时跳过本分支。
- [neo4j_graph.py:141](../../../src/persistence/neo4j_graph.py#L141)：`_load(record['payload'], GraphRevision) != transaction.revision`，不满足时跳过本分支。
- [neo4j_graph.py:147](../../../src/persistence/neo4j_graph.py#L147)：`latest_id is None`，不满足时跳过本分支。
- [neo4j_graph.py:153](../../../src/persistence/neo4j_graph.py#L153)：`transaction.revision.parent_id != latest_id`，不满足时跳过本分支。
- [neo4j_graph.py:181](../../../src/persistence/neo4j_graph.py#L181)：`transaction.revision.run_id.startswith('rollback:') or exact_maintenance`，不满足时跳过本分支。
- [neo4j_graph.py:196](../../../src/persistence/neo4j_graph.py#L196)：`exact_maintenance and change.resource_type == 'claim' and (payload is not None)`，不满足时跳过本分支。
- [neo4j_graph.py:198](../../../src/persistence/neo4j_graph.py#L198)：`payload != change.before`，不满足时跳过本分支。
- [neo4j_graph.py:263](../../../src/persistence/neo4j_graph.py#L263)：`previous_record is not None and _load(previous_record['payload'], CanonicalEntity).embedding_source() != entity.em…`，不满足时跳过本分支。
- [neo4j_graph.py:273](../../../src/persistence/neo4j_graph.py#L273)：`not entity.active`，不满足时跳过本分支。
- [neo4j_graph.py:283](../../../src/persistence/neo4j_graph.py#L283)：`record is not None and record['active_count']`，不满足时跳过本分支。
- [neo4j_graph.py:317](../../../src/persistence/neo4j_graph.py#L317)：`refs is None or (claim.object_entity_id is not None and refs['object_id'] is None)`，不满足时跳过本分支。
- [neo4j_graph.py:319](../../../src/persistence/neo4j_graph.py#L319)：`transaction.evidence`，不满足时跳过本分支。
- 另有 5 个条件判断，参见源码；不要将本列表当作全部分支。

**调用与被调用**：
- `tx.run`（[neo4j_graph.py:131](../../../src/persistence/neo4j_graph.py#L131)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `result.single`（[neo4j_graph.py:135](../../../src/persistence/neo4j_graph.py#L135)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `_load`（调用点 [neo4j_graph.py:141](../../../src/persistence/neo4j_graph.py#L141)）→ [_load](neo4j_graph.md)，静态可定位。
- `GraphIntegrityError`（调用点 [neo4j_graph.py:142](../../../src/persistence/neo4j_graph.py#L142)）→ [GraphIntegrityError](../core/errors.md)，静态可定位。
- `dict`（[neo4j_graph.py:164](../../../src/persistence/neo4j_graph.py#L164)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `entities.update`（[neo4j_graph.py:165](../../../src/persistence/neo4j_graph.py#L165)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `evidence_map.update`（[neo4j_graph.py:171](../../../src/persistence/neo4j_graph.py#L171)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `transaction.revision.run_id.startswith`（[neo4j_graph.py:181](../../../src/persistence/neo4j_graph.py#L181)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `orjson.loads`（[neo4j_graph.py:195](../../../src/persistence/neo4j_graph.py#L195)）：来自 `orjson`；具体实现可能由依赖注入或运行时分派决定。
- `Claim.model_validate(payload).model_dump`（[neo4j_graph.py:197](../../../src/persistence/neo4j_graph.py#L197)）：来自 `src.domain.Claim`；具体实现可能由依赖注入或运行时分派决定。
- `Claim.model_validate`（[neo4j_graph.py:197](../../../src/persistence/neo4j_graph.py#L197)）：来自 `src.domain.Claim`；具体实现可能由依赖注入或运行时分派决定。
- `verify_correction`（调用点 [neo4j_graph.py:208](../../../src/persistence/neo4j_graph.py#L208)）→ [verify_correction](../governance/review_guards.md)，静态可定位。
- `e.model_dump`（[neo4j_graph.py:211](../../../src/persistence/neo4j_graph.py#L211)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `previous_entities.items`（[neo4j_graph.py:211](../../../src/persistence/neo4j_graph.py#L211)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `c.model_dump`（[neo4j_graph.py:212](../../../src/persistence/neo4j_graph.py#L212)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `current_claims.items`（[neo4j_graph.py:212](../../../src/persistence/neo4j_graph.py#L212)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `JSONGraphStore._merge_claim`（[neo4j_graph.py:217](../../../src/persistence/neo4j_graph.py#L217)）：来自 `src.persistence.json_graph.JSONGraphStore`；具体实现可能由依赖注入或运行时分派决定。
- `current_claims[c.id].model_dump`（[neo4j_graph.py:217](../../../src/persistence/neo4j_graph.py#L217)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `current_claims.update`（[neo4j_graph.py:225](../../../src/persistence/neo4j_graph.py#L225)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `ValidationService().commit`（[neo4j_graph.py:230](../../../src/persistence/neo4j_graph.py#L230)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `ValidationService`（[neo4j_graph.py:230](../../../src/persistence/neo4j_graph.py#L230)）：来自 `src.governance.validation.ValidationService`；具体实现可能由依赖注入或运行时分派决定。
- `final_state_commit`（调用点 [neo4j_graph.py:231](../../../src/persistence/neo4j_graph.py#L231)）→ [final_state_commit](../governance/validation/context.md)，静态可定位。
- `_dump`（调用点 [neo4j_graph.py:246](../../../src/persistence/neo4j_graph.py#L246)）→ [_dump](neo4j_graph.md)，静态可定位。
- `previous_result.single`（[neo4j_graph.py:262](../../../src/persistence/neo4j_graph.py#L262)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `_load(previous_record['payload'], CanonicalEntity).embedding_source`（[neo4j_graph.py:264](../../../src/persistence/neo4j_graph.py#L264)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `entity.embedding_source`（[neo4j_graph.py:265](../../../src/persistence/neo4j_graph.py#L265)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `set`（[neo4j_graph.py:324](../../../src/persistence/neo4j_graph.py#L324)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `claim.tx_from.isoformat`（[neo4j_graph.py:339](../../../src/persistence/neo4j_graph.py#L339)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `claim.tx_to.isoformat`（[neo4j_graph.py:340](../../../src/persistence/neo4j_graph.py#L340)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `sorted`（[neo4j_graph.py:373](../../../src/persistence/neo4j_graph.py#L373)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- 此处列出前 30 个不同调用表达式，另有 3 个，需按源码继续追踪。
- 静态扫描未定位直接调用方；可能通过路由注册、LangGraph 节点、协议方法或依赖注入动态调用，不据此判断为死代码。

**状态、副作用与异常**：
- 显式状态/容器赋值：`transaction.claims`。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：`GraphIntegrityError(f<字符串常量>)`、`GraphIntegrityError(reason)`。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。
- 恢复/幂等性：仅在代码有检查点、事务、请求编号或显式去重时才成立；此函数不能单凭名称视为可安全重试。


---

# Neo4jGraphStore.commit ⭐⭐⭐⭐⭐

**位置与等级**：[neo4j_graph.py:446](../../../src/persistence/neo4j_graph.py#L446)；位于工作流推进、硬校验或原子事务的关键边界；错误可能影响审核停顿或图状态。

**签名**：`async def commit(self, transaction: GraphCommit) -> None`。

**作用**：执行图谱提交；这是写入边界，需核对父版本、引用完整性和原子性。

**输入与输出**：
- 输入：`transaction`（GraphCommit；待提交 GraphCommit；必须在最终写入边界重新校验）。
- 输出类型：`None`；具体返回路径见流程步骤。

**处理流程**：
1. 调用 `bind_commit_provenance`，结果未直接赋值。
2. 更新 `transaction`，值来自 `transaction.model_copy(deep=True)`。
3. 等待 `self._ensure_schema()` 完成。
4. 进入上下文 `self.driver.session(database=self.database)`，由上下文管理器控制资源释放或事务范围。

**调用与被调用**：
- `bind_commit_provenance`（调用点 [neo4j_graph.py:447](../../../src/persistence/neo4j_graph.py#L447)）→ [bind_commit_provenance](../governance/validation/context.md)，静态可定位。
- `transaction.model_copy`（[neo4j_graph.py:448](../../../src/persistence/neo4j_graph.py#L448)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `self._ensure_schema`（调用点 [neo4j_graph.py:449](../../../src/persistence/neo4j_graph.py#L449)）→ [Neo4jGraphStore._ensure_schema](neo4j_graph.md)，静态可定位。
- `self.driver.session`（[neo4j_graph.py:450](../../../src/persistence/neo4j_graph.py#L450)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `session.execute_write`（[neo4j_graph.py:451](../../../src/persistence/neo4j_graph.py#L451)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- 静态可定位的调用方：[Neo4jGraphStore.rollback_revision](neo4j_graph.md)。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：未见 `raise`；下游异常可能继续上抛。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。
- 恢复/幂等性：仅在代码有检查点、事务、请求编号或显式去重时才成立；此函数不能单凭名称视为可安全重试。


---

# Neo4jGraphStore._list_payloads ⭐⭐

**位置与等级**：[neo4j_graph.py:453](../../../src/persistence/neo4j_graph.py#L453)；局部辅助逻辑，需理解其调用条件与失败传播。

**签名**：`async def _list_payloads(self, label: str, limit: int | None=None) -> list[str]`。

**作用**：内部辅助步骤；将参数转换为本模块所需的中间对象或操作结果。

**输入与输出**：
- 输入：`label`（str）；`limit`（int | None；默认 `None`；查询或展示的最大条数）。
- 输出类型：`list[str]`；具体返回路径见流程步骤。

**处理流程**：
1. 更新 `query`，值来自 `f<字符串常量>`。
2. 更新 `parameters`，值来自 `{}`。
3. 检查 `limit is not None`；按条件分流，else 分支不存在。
4. 进入上下文 `self.driver.session(database=self.database)`，由上下文管理器控制资源释放或事务范围。
5. 返回 `[record['payload'] for record in records]`。

**关键条件与保护**：
- [neo4j_graph.py:456](../../../src/persistence/neo4j_graph.py#L456)：`limit is not None`，不满足时跳过本分支。

**调用与被调用**：
- `self.driver.session`（[neo4j_graph.py:459](../../../src/persistence/neo4j_graph.py#L459)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `session.run`（[neo4j_graph.py:460](../../../src/persistence/neo4j_graph.py#L460)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `result.data`（[neo4j_graph.py:461](../../../src/persistence/neo4j_graph.py#L461)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- 静态可定位的调用方：[Neo4jGraphStore.list_entities](neo4j_graph.md)、[Neo4jGraphStore.list_claims](neo4j_graph.md)、[Neo4jGraphStore.list_revisions](neo4j_graph.md)。

**状态、副作用与异常**：
- 显式状态/容器赋值：`parameters['limit']`。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：未见 `raise`；下游异常可能继续上抛。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。
- 恢复/幂等性：仅在代码有检查点、事务、请求编号或显式去重时才成立；此函数不能单凭名称视为可安全重试。


---

# Neo4jGraphStore.list_entities ⭐⭐

**位置与等级**：[neo4j_graph.py:464](../../../src/persistence/neo4j_graph.py#L464)；局部辅助逻辑，需理解其调用条件与失败传播。

**签名**：`async def list_entities(self) -> list[CanonicalEntity]`。

**作用**：读取或组装对应资源；是否纯只读及异常行为需结合下方显式调用与状态写入判断。

**输入与输出**：
- 输入：无业务参数（或仅隐式接收实例）。
- 输出类型：`list[CanonicalEntity]`；具体返回路径见流程步骤。

**处理流程**：
1. 返回 `[_load(item, CanonicalEntity) for item in await self._list_payloads('Entity')]`。

**调用与被调用**：
- `_load`（调用点 [neo4j_graph.py:465](../../../src/persistence/neo4j_graph.py#L465)）→ [_load](neo4j_graph.md)，静态可定位。
- `self._list_payloads`（调用点 [neo4j_graph.py:465](../../../src/persistence/neo4j_graph.py#L465)）→ [Neo4jGraphStore._list_payloads](neo4j_graph.md)，静态可定位。
- 静态扫描未定位直接调用方；可能通过路由注册、LangGraph 节点、协议方法或依赖注入动态调用，不据此判断为死代码。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：未见 `raise`；下游异常可能继续上抛。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。
- 恢复/幂等性：仅在代码有检查点、事务、请求编号或显式去重时才成立；此函数不能单凭名称视为可安全重试。


---

# Neo4jGraphStore.get_entity ⭐⭐

**位置与等级**：[neo4j_graph.py:467](../../../src/persistence/neo4j_graph.py#L467)；局部辅助逻辑，需理解其调用条件与失败传播。

**签名**：`async def get_entity(self, entity_id: str) -> CanonicalEntity | None`。

**作用**：读取或组装对应资源；是否纯只读及异常行为需结合下方显式调用与状态写入判断。

**输入与输出**：
- 输入：`entity_id`（str）。
- 输出类型：`CanonicalEntity | None`；具体返回路径见流程步骤。

**处理流程**：
1. 返回 `await self._get('Entity', entity_id, CanonicalEntity)`。

**调用与被调用**：
- `self._get`（调用点 [neo4j_graph.py:468](../../../src/persistence/neo4j_graph.py#L468)）→ [Neo4jGraphStore._get](neo4j_graph.md)，静态可定位。
- 静态扫描未定位直接调用方；可能通过路由注册、LangGraph 节点、协议方法或依赖注入动态调用，不据此判断为死代码。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：未见 `raise`；下游异常可能继续上抛。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。
- 恢复/幂等性：仅在代码有检查点、事务、请求编号或显式去重时才成立；此函数不能单凭名称视为可安全重试。


---

# Neo4jGraphStore.search_entities ⭐⭐

**位置与等级**：[neo4j_graph.py:470](../../../src/persistence/neo4j_graph.py#L470)；局部辅助逻辑，需理解其调用条件与失败传播。

**签名**：`async def search_entities(self, vector: list[float], entity_type: str, top_k: int, model_fingerprint: str | None=None) -> list[tuple[CanonicalEntity, float]]`。

**作用**：处理 `search_entities` 对应步骤；下列步骤依据函数体的实际控制流和调用点整理。

**输入与输出**：
- 输入：`vector`（list[float]）；`entity_type`（str）；`top_k`（int；候选召回数量上限）；`model_fingerprint`（str | None；默认 `None`）。
- 输出类型：`list[tuple[CanonicalEntity, float]]`；具体返回路径见流程步骤。

**处理流程**：
1. 检查 `not vector or top_k < 1`；按条件分流，else 分支不存在。
2. 等待 `self._ensure_schema()` 完成。
3. 检查 `len(vector) == 1024`；按条件分流，else 分支不存在。
4. 进入上下文 `self.driver.session(database=self.database)`，由上下文管理器控制资源释放或事务范围。
5. 更新 `query_norm`，值来自 `math.sqrt(sum((value * value for value in vector))) or 1.0`。
6. 更新 `matches`，值来自 `[]`。
7. 遍历 `records`，逐项处理 `record`。
8. 返回 `sorted(matches, key=lambda item: (-round(item[1], 12), item[0].id))[:top_k]`。

**关键条件与保护**：
- [neo4j_graph.py:477](../../../src/persistence/neo4j_graph.py#L477)：`not vector or top_k < 1`，不满足时跳过本分支。
- [neo4j_graph.py:480](../../../src/persistence/neo4j_graph.py#L480)：`len(vector) == 1024`，不满足时跳过本分支。
- [neo4j_graph.py:488](../../../src/persistence/neo4j_graph.py#L488)：`total == 0`，不满足时跳过本分支。
- [neo4j_graph.py:505](../../../src/persistence/neo4j_graph.py#L505)：`len(records) >= top_k or candidate_limit >= total`，不满足时跳过本分支。
- [neo4j_graph.py:534](../../../src/persistence/neo4j_graph.py#L534)：`len(candidate) != len(vector)`，不满足时跳过本分支。

**调用与被调用**：
- `self._ensure_schema`（调用点 [neo4j_graph.py:479](../../../src/persistence/neo4j_graph.py#L479)）→ [Neo4jGraphStore._ensure_schema](neo4j_graph.md)，静态可定位。
- `len`（[neo4j_graph.py:480](../../../src/persistence/neo4j_graph.py#L480)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `self.driver.session`（[neo4j_graph.py:481](../../../src/persistence/neo4j_graph.py#L481)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `session.run`（[neo4j_graph.py:482](../../../src/persistence/neo4j_graph.py#L482)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `count_result.single`（[neo4j_graph.py:486](../../../src/persistence/neo4j_graph.py#L486)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `int`（[neo4j_graph.py:487](../../../src/persistence/neo4j_graph.py#L487)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `min`（[neo4j_graph.py:490](../../../src/persistence/neo4j_graph.py#L490)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `max`（[neo4j_graph.py:490](../../../src/persistence/neo4j_graph.py#L490)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `result.data`（[neo4j_graph.py:504](../../../src/persistence/neo4j_graph.py#L504)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `math.sqrt`（[neo4j_graph.py:509](../../../src/persistence/neo4j_graph.py#L509)）：来自 `math`；具体实现可能由依赖注入或运行时分派决定。
- `sum`（[neo4j_graph.py:509](../../../src/persistence/neo4j_graph.py#L509)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `float`（[neo4j_graph.py:511](../../../src/persistence/neo4j_graph.py#L511)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `zip`（[neo4j_graph.py:513](../../../src/persistence/neo4j_graph.py#L513)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `matches.append`（[neo4j_graph.py:516](../../../src/persistence/neo4j_graph.py#L516)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `_load`（调用点 [neo4j_graph.py:517](../../../src/persistence/neo4j_graph.py#L517)）→ [_load](neo4j_graph.md)，静态可定位。
- `sorted`（[neo4j_graph.py:519](../../../src/persistence/neo4j_graph.py#L519)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- 静态扫描未定位直接调用方；可能通过路由注册、LangGraph 节点、协议方法或依赖注入动态调用，不据此判断为死代码。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：未见 `raise`；下游异常可能继续上抛。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。
- 恢复/幂等性：仅在代码有检查点、事务、请求编号或显式去重时才成立；此函数不能单凭名称视为可安全重试。


---

# Neo4jGraphStore.list_entity_embeddings ⭐⭐

**位置与等级**：[neo4j_graph.py:543](../../../src/persistence/neo4j_graph.py#L543)；局部辅助逻辑，需理解其调用条件与失败传播。

**签名**：`async def list_entity_embeddings(self) -> list[EntityEmbedding]`。

**作用**：读取或组装对应资源；是否纯只读及异常行为需结合下方显式调用与状态写入判断。

**输入与输出**：
- 输入：无业务参数（或仅隐式接收实例）。
- 输出类型：`list[EntityEmbedding]`；具体返回路径见流程步骤。

**处理流程**：
1. 进入上下文 `self.driver.session(database=self.database)`，由上下文管理器控制资源释放或事务范围。
2. 返回 `[EntityEmbedding(entity_id=record['entity_id'], model_fingerprint=record['model'], text_hash=record['tex…`。

**调用与被调用**：
- `self.driver.session`（[neo4j_graph.py:544](../../../src/persistence/neo4j_graph.py#L544)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `session.run`（[neo4j_graph.py:545](../../../src/persistence/neo4j_graph.py#L545)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `result.data`（[neo4j_graph.py:551](../../../src/persistence/neo4j_graph.py#L551)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `EntityEmbedding`（[neo4j_graph.py:553](../../../src/persistence/neo4j_graph.py#L553)）：来自 `src.domain.EntityEmbedding`；具体实现可能由依赖注入或运行时分派决定。
- `int`（[neo4j_graph.py:557](../../../src/persistence/neo4j_graph.py#L557)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `float`（[neo4j_graph.py:558](../../../src/persistence/neo4j_graph.py#L558)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- 静态扫描未定位直接调用方；可能通过路由注册、LangGraph 节点、协议方法或依赖注入动态调用，不据此判断为死代码。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：未见 `raise`；下游异常可能继续上抛。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。
- 恢复/幂等性：仅在代码有检查点、事务、请求编号或显式去重时才成立；此函数不能单凭名称视为可安全重试。


---

# Neo4jGraphStore.upsert_entity_embeddings ⭐⭐

**位置与等级**：[neo4j_graph.py:563](../../../src/persistence/neo4j_graph.py#L563)；局部辅助逻辑，需理解其调用条件与失败传播。

**签名**：`async def upsert_entity_embeddings(self, embeddings: list[EntityEmbedding]) -> None`。

**作用**：创建、更新或记录相应资源；写入/审计边界以实际调用和状态赋值为准。

**输入与输出**：
- 输入：`embeddings`（list[EntityEmbedding]）。
- 输出类型：`None`；具体返回路径见流程步骤。

**处理流程**：
1. 等待 `self._ensure_schema()` 完成。
2. 进入上下文 `self.driver.session(database=self.database)`，由上下文管理器控制资源释放或事务范围。

**调用与被调用**：
- `self._ensure_schema`（调用点 [neo4j_graph.py:564](../../../src/persistence/neo4j_graph.py#L564)）→ [Neo4jGraphStore._ensure_schema](neo4j_graph.md)，静态可定位。
- `self.driver.session`（[neo4j_graph.py:565](../../../src/persistence/neo4j_graph.py#L565)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `session.execute_write`（[neo4j_graph.py:585](../../../src/persistence/neo4j_graph.py#L585)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- 静态扫描未定位直接调用方；可能通过路由注册、LangGraph 节点、协议方法或依赖注入动态调用，不据此判断为死代码。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：未见 `raise`；下游异常可能继续上抛。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。
- 恢复/幂等性：仅在代码有检查点、事务、请求编号或显式去重时才成立；此函数不能单凭名称视为可安全重试。


---

# Neo4jGraphStore.upsert_entity_embeddings.write ⭐⭐

**位置与等级**：[neo4j_graph.py:567](../../../src/persistence/neo4j_graph.py#L567)；局部辅助逻辑，需理解其调用条件与失败传播。

**签名**：`async def write(tx: Any) -> None`。

**作用**：处理 `write` 对应步骤；下列步骤依据函数体的实际控制流和调用点整理。

**输入与输出**：
- 输入：`tx`（Any）。
- 输出类型：`None`；具体返回路径见流程步骤。

**处理流程**：
1. 遍历 `embeddings`，逐项处理 `embedding`。

**关键条件与保护**：
- [neo4j_graph.py:580](../../../src/persistence/neo4j_graph.py#L580)：`await result.single() is None`，不满足时跳过本分支。

**调用与被调用**：
- `tx.run`（[neo4j_graph.py:569](../../../src/persistence/neo4j_graph.py#L569)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `result.single`（[neo4j_graph.py:580](../../../src/persistence/neo4j_graph.py#L580)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `GraphIntegrityError`（调用点 [neo4j_graph.py:581](../../../src/persistence/neo4j_graph.py#L581)）→ [GraphIntegrityError](../core/errors.md)，静态可定位。
- 静态扫描未定位直接调用方；可能通过路由注册、LangGraph 节点、协议方法或依赖注入动态调用，不据此判断为死代码。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：`GraphIntegrityError(f<字符串常量>)`。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。
- 恢复/幂等性：仅在代码有检查点、事务、请求编号或显式去重时才成立；此函数不能单凭名称视为可安全重试。


---

# Neo4jGraphStore.list_claims ⭐⭐

**位置与等级**：[neo4j_graph.py:587](../../../src/persistence/neo4j_graph.py#L587)；局部辅助逻辑，需理解其调用条件与失败传播。

**签名**：`async def list_claims(self) -> list[Claim]`。

**作用**：读取或组装对应资源；是否纯只读及异常行为需结合下方显式调用与状态写入判断。

**输入与输出**：
- 输入：无业务参数（或仅隐式接收实例）。
- 输出类型：`list[Claim]`；具体返回路径见流程步骤。

**处理流程**：
1. 返回 `[_load(item, Claim) for item in await self._list_payloads('Claim')]`。

**调用与被调用**：
- `_load`（调用点 [neo4j_graph.py:588](../../../src/persistence/neo4j_graph.py#L588)）→ [_load](neo4j_graph.md)，静态可定位。
- `self._list_payloads`（调用点 [neo4j_graph.py:588](../../../src/persistence/neo4j_graph.py#L588)）→ [Neo4jGraphStore._list_payloads](neo4j_graph.md)，静态可定位。
- 静态可定位的调用方：[Neo4jGraphStore.rollback_revision](neo4j_graph.md)。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：未见 `raise`；下游异常可能继续上抛。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。
- 恢复/幂等性：仅在代码有检查点、事务、请求编号或显式去重时才成立；此函数不能单凭名称视为可安全重试。


---

# Neo4jGraphStore.latest_revision ⭐⭐

**位置与等级**：[neo4j_graph.py:590](../../../src/persistence/neo4j_graph.py#L590)；局部辅助逻辑，需理解其调用条件与失败传播。

**签名**：`async def latest_revision(self) -> GraphRevision | None`。

**作用**：处理 `latest_revision` 对应步骤；下列步骤依据函数体的实际控制流和调用点整理。

**输入与输出**：
- 输入：无业务参数（或仅隐式接收实例）。
- 输出类型：`GraphRevision | None`；具体返回路径见流程步骤。

**处理流程**：
1. 更新 `revisions`，值来自 `await self.list_revisions(limit=1)`。
2. 返回 `revisions[0] if revisions else None`。

**调用与被调用**：
- `self.list_revisions`（调用点 [neo4j_graph.py:591](../../../src/persistence/neo4j_graph.py#L591)）→ [Neo4jGraphStore.list_revisions](neo4j_graph.md)，静态可定位。
- 静态可定位的调用方：[Neo4jGraphStore.rollback_revision](neo4j_graph.md)。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：未见 `raise`；下游异常可能继续上抛。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。
- 恢复/幂等性：仅在代码有检查点、事务、请求编号或显式去重时才成立；此函数不能单凭名称视为可安全重试。


---

# Neo4jGraphStore.list_revisions ⭐⭐

**位置与等级**：[neo4j_graph.py:594](../../../src/persistence/neo4j_graph.py#L594)；局部辅助逻辑，需理解其调用条件与失败传播。

**签名**：`async def list_revisions(self, limit: int=50) -> list[GraphRevision]`。

**作用**：读取或组装对应资源；是否纯只读及异常行为需结合下方显式调用与状态写入判断。

**输入与输出**：
- 输入：`limit`（int；默认 `50`；查询或展示的最大条数）。
- 输出类型：`list[GraphRevision]`；具体返回路径见流程步骤。

**处理流程**：
1. 返回 `[_load(item, GraphRevision) for item in await self._list_payloads('Revision', max(limit, 0))]`。

**调用与被调用**：
- `_load`（调用点 [neo4j_graph.py:596](../../../src/persistence/neo4j_graph.py#L596)）→ [_load](neo4j_graph.md)，静态可定位。
- `self._list_payloads`（调用点 [neo4j_graph.py:597](../../../src/persistence/neo4j_graph.py#L597)）→ [Neo4jGraphStore._list_payloads](neo4j_graph.md)，静态可定位。
- `max`（[neo4j_graph.py:597](../../../src/persistence/neo4j_graph.py#L597)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- 静态可定位的调用方：[Neo4jGraphStore.latest_revision](neo4j_graph.md)、[Neo4jGraphStore.diff_revisions](neo4j_graph.md)、[Neo4jGraphStore.rollback_revision](neo4j_graph.md)。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：未见 `raise`；下游异常可能继续上抛。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。
- 恢复/幂等性：仅在代码有检查点、事务、请求编号或显式去重时才成立；此函数不能单凭名称视为可安全重试。


---

# Neo4jGraphStore._get ⭐⭐

**位置与等级**：[neo4j_graph.py:600](../../../src/persistence/neo4j_graph.py#L600)；局部辅助逻辑，需理解其调用条件与失败传播。

**签名**：`async def _get(self, label: str, resource_id: str, model: Any) -> Any | None`。

**作用**：内部辅助步骤；将参数转换为本模块所需的中间对象或操作结果。

**输入与输出**：
- 输入：`label`（str）；`resource_id`（str）；`model`（Any）。
- 输出类型：`Any | None`；具体返回路径见流程步骤。

**处理流程**：
1. 进入上下文 `self.driver.session(database=self.database)`，由上下文管理器控制资源释放或事务范围。
2. 返回 `_load(record['payload'], model) if record is not None else None`。

**调用与被调用**：
- `self.driver.session`（[neo4j_graph.py:601](../../../src/persistence/neo4j_graph.py#L601)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `session.run`（[neo4j_graph.py:602](../../../src/persistence/neo4j_graph.py#L602)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `result.single`（[neo4j_graph.py:605](../../../src/persistence/neo4j_graph.py#L605)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `_load`（调用点 [neo4j_graph.py:606](../../../src/persistence/neo4j_graph.py#L606)）→ [_load](neo4j_graph.md)，静态可定位。
- 静态可定位的调用方：[Neo4jGraphStore.get_entity](neo4j_graph.md)、[Neo4jGraphStore.get_claim](neo4j_graph.md)、[Neo4jGraphStore.get_evidence](neo4j_graph.md)、[Neo4jGraphStore.rollback_revision](neo4j_graph.md)。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：未见 `raise`；下游异常可能继续上抛。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。
- 恢复/幂等性：仅在代码有检查点、事务、请求编号或显式去重时才成立；此函数不能单凭名称视为可安全重试。


---

# Neo4jGraphStore.get_claim ⭐⭐

**位置与等级**：[neo4j_graph.py:608](../../../src/persistence/neo4j_graph.py#L608)；局部辅助逻辑，需理解其调用条件与失败传播。

**签名**：`async def get_claim(self, claim_id: str) -> Claim | None`。

**作用**：读取或组装对应资源；是否纯只读及异常行为需结合下方显式调用与状态写入判断。

**输入与输出**：
- 输入：`claim_id`（str）。
- 输出类型：`Claim | None`；具体返回路径见流程步骤。

**处理流程**：
1. 返回 `await self._get('Claim', claim_id, Claim)`。

**调用与被调用**：
- `self._get`（调用点 [neo4j_graph.py:609](../../../src/persistence/neo4j_graph.py#L609)）→ [Neo4jGraphStore._get](neo4j_graph.md)，静态可定位。
- 静态扫描未定位直接调用方；可能通过路由注册、LangGraph 节点、协议方法或依赖注入动态调用，不据此判断为死代码。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：未见 `raise`；下游异常可能继续上抛。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。
- 恢复/幂等性：仅在代码有检查点、事务、请求编号或显式去重时才成立；此函数不能单凭名称视为可安全重试。


---

# Neo4jGraphStore.get_evidence ⭐⭐

**位置与等级**：[neo4j_graph.py:611](../../../src/persistence/neo4j_graph.py#L611)；局部辅助逻辑，需理解其调用条件与失败传播。

**签名**：`async def get_evidence(self, evidence_id: str) -> EvidenceRef | None`。

**作用**：读取或组装对应资源；是否纯只读及异常行为需结合下方显式调用与状态写入判断。

**输入与输出**：
- 输入：`evidence_id`（str）。
- 输出类型：`EvidenceRef | None`；具体返回路径见流程步骤。

**处理流程**：
1. 返回 `await self._get('Evidence', evidence_id, EvidenceRef)`。

**调用与被调用**：
- `self._get`（调用点 [neo4j_graph.py:612](../../../src/persistence/neo4j_graph.py#L612)）→ [Neo4jGraphStore._get](neo4j_graph.md)，静态可定位。
- 静态扫描未定位直接调用方；可能通过路由注册、LangGraph 节点、协议方法或依赖注入动态调用，不据此判断为死代码。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：未见 `raise`；下游异常可能继续上抛。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。
- 恢复/幂等性：仅在代码有检查点、事务、请求编号或显式去重时才成立；此函数不能单凭名称视为可安全重试。


---

# Neo4jGraphStore.get_neighborhood ⭐⭐

**位置与等级**：[neo4j_graph.py:614](../../../src/persistence/neo4j_graph.py#L614)；局部辅助逻辑，需理解其调用条件与失败传播。

**签名**：`async def get_neighborhood(self, entity_id: str, depth: int=1) -> GraphNeighborhood`。

**作用**：读取或组装对应资源；是否纯只读及异常行为需结合下方显式调用与状态写入判断。

**输入与输出**：
- 输入：`entity_id`（str）；`depth`（int；默认 `1`）。
- 输出类型：`GraphNeighborhood`；具体返回路径见流程步骤。

**处理流程**：
1. 检查 `depth < 1 or depth > 3`；按条件分流，else 分支不存在。
2. 进入上下文 `self.driver.session(database=self.database)`，由上下文管理器控制资源释放或事务范围。
3. 检查 `record is None`；按条件分流，else 分支不存在。
4. 更新 `entities`，值来自 `[_load(record['center'], CanonicalEntity)]`。
5. 调用 `entities.extend`，结果未直接赋值。
6. 返回 `GraphNeighborhood(center_entity_id=entity_id, depth=depth, entities=list({item.id: item for item in enti…`。

**关键条件与保护**：
- [neo4j_graph.py:615](../../../src/persistence/neo4j_graph.py#L615)：`depth < 1 or depth > 3`，不满足时跳过本分支。
- [neo4j_graph.py:630](../../../src/persistence/neo4j_graph.py#L630)：`record is None`，不满足时跳过本分支。

**调用与被调用**：
- `ValueError`（[neo4j_graph.py:616](../../../src/persistence/neo4j_graph.py#L616)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `self.driver.session`（[neo4j_graph.py:617](../../../src/persistence/neo4j_graph.py#L617)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `session.run`（[neo4j_graph.py:619](../../../src/persistence/neo4j_graph.py#L619)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `result.single`（[neo4j_graph.py:629](../../../src/persistence/neo4j_graph.py#L629)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `KeyError`（[neo4j_graph.py:631](../../../src/persistence/neo4j_graph.py#L631)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `_load`（调用点 [neo4j_graph.py:632](../../../src/persistence/neo4j_graph.py#L632)）→ [_load](neo4j_graph.md)，静态可定位。
- `entities.extend`（[neo4j_graph.py:633](../../../src/persistence/neo4j_graph.py#L633)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `GraphNeighborhood`（[neo4j_graph.py:634](../../../src/persistence/neo4j_graph.py#L634)）：来自 `src.domain.GraphNeighborhood`；具体实现可能由依赖注入或运行时分派决定。
- `list`（[neo4j_graph.py:637](../../../src/persistence/neo4j_graph.py#L637)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `{item.id: item for item in entities}.values`（[neo4j_graph.py:637](../../../src/persistence/neo4j_graph.py#L637)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- 静态扫描未定位直接调用方；可能通过路由注册、LangGraph 节点、协议方法或依赖注入动态调用，不据此判断为死代码。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：`ValueError(<字符串常量>)`、`KeyError(f<字符串常量>)`。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。
- 恢复/幂等性：仅在代码有检查点、事务、请求编号或显式去重时才成立；此函数不能单凭名称视为可安全重试。


---

# Neo4jGraphStore.diff_revisions ⭐⭐

**位置与等级**：[neo4j_graph.py:641](../../../src/persistence/neo4j_graph.py#L641)；局部辅助逻辑，需理解其调用条件与失败传播。

**签名**：`async def diff_revisions(self, from_id: str, to_id: str) -> RevisionDiff`。

**作用**：比较两个版本间的资源变化，不修改图谱。

**输入与输出**：
- 输入：`from_id`（str）；`to_id`（str）。
- 输出类型：`RevisionDiff`；具体返回路径见流程步骤。

**处理流程**：
1. 更新 `revisions`，值来自 `list(reversed(await self.list_revisions(limit=10000)))`。
2. 更新 `positions`，值来自 `{revision.id: index for index, revision in enumerate(revisions)}`。
3. 检查 `from_id not in positions or to_id not in positions`；按条件分流，else 分支不存在。
4. 检查 `positions[from_id] > positions[to_id]`；按条件分流，else 分支不存在。
5. 更新 `selected`，值来自 `revisions[positions[from_id] + 1:positions[to_id] + 1]`。
6. 返回 `RevisionDiff(from_revision_id=from_id, to_revision_id=to_id, changes=[change for revision in selected fo…`。

**关键条件与保护**：
- [neo4j_graph.py:644](../../../src/persistence/neo4j_graph.py#L644)：`from_id not in positions or to_id not in positions`，不满足时跳过本分支。
- [neo4j_graph.py:646](../../../src/persistence/neo4j_graph.py#L646)：`positions[from_id] > positions[to_id]`，不满足时跳过本分支。

**调用与被调用**：
- `list`（[neo4j_graph.py:642](../../../src/persistence/neo4j_graph.py#L642)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `reversed`（[neo4j_graph.py:642](../../../src/persistence/neo4j_graph.py#L642)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `self.list_revisions`（调用点 [neo4j_graph.py:642](../../../src/persistence/neo4j_graph.py#L642)）→ [Neo4jGraphStore.list_revisions](neo4j_graph.md)，静态可定位。
- `enumerate`（[neo4j_graph.py:643](../../../src/persistence/neo4j_graph.py#L643)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `KeyError`（[neo4j_graph.py:645](../../../src/persistence/neo4j_graph.py#L645)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `ValueError`（[neo4j_graph.py:647](../../../src/persistence/neo4j_graph.py#L647)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `RevisionDiff`（[neo4j_graph.py:649](../../../src/persistence/neo4j_graph.py#L649)）：来自 `src.domain.RevisionDiff`；具体实现可能由依赖注入或运行时分派决定。
- `any`（[neo4j_graph.py:653](../../../src/persistence/neo4j_graph.py#L653)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `sorted`（[neo4j_graph.py:654](../../../src/persistence/neo4j_graph.py#L654)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- 静态扫描未定位直接调用方；可能通过路由注册、LangGraph 节点、协议方法或依赖注入动态调用，不据此判断为死代码。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：`KeyError(<字符串常量>)`、`ValueError(<字符串常量>)`。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。
- 恢复/幂等性：仅在代码有检查点、事务、请求编号或显式去重时才成立；此函数不能单凭名称视为可安全重试。


---

# Neo4jGraphStore.rollback_revision ⭐⭐⭐⭐⭐

**位置与等级**：[neo4j_graph.py:659](../../../src/persistence/neo4j_graph.py#L659)；位于工作流推进、硬校验或原子事务的关键边界；错误可能影响审核停顿或图状态。

**签名**：`async def rollback_revision(self, revision_id: str) -> GraphRevision`。

**作用**：构造补偿版本恢复目标状态，保留历史记录而不是删除 Revision。

**输入与输出**：
- 输入：`revision_id`（str）。
- 输出类型：`GraphRevision`；具体返回路径见流程步骤。

**处理流程**：
1. 更新 `target`，值来自 `await self._get('Revision', revision_id, GraphRevision)`。
2. 检查 `target is None`；按条件分流，else 分支不存在。
3. 检查 `not target.changes`；按条件分流，else 分支不存在。
4. 更新 `latest`，值来自 `await self.latest_revision()`。
5. 断言 `latest is not None`。
6. 检查 `latest.run_id == f<字符串常量>`；按条件分流，else 分支不存在。
7. 更新 `entities`，值来自 `[]`。
8. 更新 `claims`，值来自 `[]`。
9. 更新 `conflicts`，值来自 `[]`。
10. 更新 `entity_operations`，值来自 `[]`。
11. 更新 `current_claims`，值来自 `{item.id: item for item in await self.list_claims()}`。
12. 更新 `inverse`，值来自 `[]`。
13. 更新 `now`，值来自 `datetime.now(UTC)`。
14. 更新 `rollback_order`，值来自 `{'entity_operation': 0, 'claim': 1, 'conflict': 2, 'entity': 3}`。
15. 更新 `ordered_changes`，值来自 `sorted(reversed(target.changes), key=lambda item: rollback_order[item.resource_type])`。
16. 遍历 `ordered_changes`，逐项处理 `change`。
17. 更新 `revision`，值来自 `GraphRevision(id=stable_id('revision', 'rollback', revision_id, latest.id), run_id=f<字符串常量>, parent…`。
18. 更新 `context`，值来自 `context_for_claims(await self.list_revisions(limit=100000), {c.id for c in claims})`。
19. 更新 `revision.validation_context`，值来自 `context`。
20. 等待 `self.commit(GraphCommit(entities=entities, claims=claims, conflicts=conflicts, entity_operations=entity_…` 完成。
21. 返回 `revision`。

**关键条件与保护**：
- [neo4j_graph.py:661](../../../src/persistence/neo4j_graph.py#L661)：`target is None`，不满足时跳过本分支。
- [neo4j_graph.py:663](../../../src/persistence/neo4j_graph.py#L663)：`not target.changes`，不满足时跳过本分支。
- [neo4j_graph.py:667](../../../src/persistence/neo4j_graph.py#L667)：`latest.run_id == f<字符串常量>`，不满足时跳过本分支。
- [neo4j_graph.py:689](../../../src/persistence/neo4j_graph.py#L689)：`change.resource_type == 'entity'`，不满足时有 else 分支。
- [neo4j_graph.py:691](../../../src/persistence/neo4j_graph.py#L691)：`change.action == 'create' and current_entity is not None`，不满足时有 else 分支。
- [neo4j_graph.py:692](../../../src/persistence/neo4j_graph.py#L692)：`any((item.tx_to is None and change.resource_id in {item.subject_id, item.object_entity_id} for item in current_cla…`，不满足时跳过本分支。
- [neo4j_graph.py:702](../../../src/persistence/neo4j_graph.py#L702)：`change.before is not None`，不满足时有 else 分支。
- [neo4j_graph.py:710](../../../src/persistence/neo4j_graph.py#L710)：`change.resource_type == 'claim'`，不满足时有 else 分支。
- [neo4j_graph.py:712](../../../src/persistence/neo4j_graph.py#L712)：`change.action == 'create' and current_claim is not None`，不满足时有 else 分支。
- [neo4j_graph.py:715](../../../src/persistence/neo4j_graph.py#L715)：`change.before is not None`，不满足时有 else 分支。
- [neo4j_graph.py:724](../../../src/persistence/neo4j_graph.py#L724)：`change.resource_type == 'conflict'`，不满足时有 else 分支。
- [neo4j_graph.py:726](../../../src/persistence/neo4j_graph.py#L726)：`change.action == 'create' and current_conflict is not None`，不满足时有 else 分支。
- 另有 4 个条件判断，参见源码；不要将本列表当作全部分支。

**调用与被调用**：
- `self._get`（调用点 [neo4j_graph.py:660](../../../src/persistence/neo4j_graph.py#L660)）→ [Neo4jGraphStore._get](neo4j_graph.md)，静态可定位。
- `KeyError`（[neo4j_graph.py:662](../../../src/persistence/neo4j_graph.py#L662)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `GraphIntegrityError`（调用点 [neo4j_graph.py:664](../../../src/persistence/neo4j_graph.py#L664)）→ [GraphIntegrityError](../core/errors.md)，静态可定位。
- `self.latest_revision`（调用点 [neo4j_graph.py:665](../../../src/persistence/neo4j_graph.py#L665)）→ [Neo4jGraphStore.latest_revision](neo4j_graph.md)，静态可定位。
- `self.list_claims`（调用点 [neo4j_graph.py:673](../../../src/persistence/neo4j_graph.py#L673)）→ [Neo4jGraphStore.list_claims](neo4j_graph.md)，静态可定位。
- `datetime.now`（[neo4j_graph.py:675](../../../src/persistence/neo4j_graph.py#L675)）：来自 `datetime.datetime`；具体实现可能由依赖注入或运行时分派决定。
- `sorted`（[neo4j_graph.py:682](../../../src/persistence/neo4j_graph.py#L682)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `reversed`（[neo4j_graph.py:683](../../../src/persistence/neo4j_graph.py#L683)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `any`（[neo4j_graph.py:692](../../../src/persistence/neo4j_graph.py#L692)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `current_claims.values`（[neo4j_graph.py:695](../../../src/persistence/neo4j_graph.py#L695)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `current_entity.model_copy`（[neo4j_graph.py:700](../../../src/persistence/neo4j_graph.py#L700)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `CanonicalEntity.model_validate`（[neo4j_graph.py:703](../../../src/persistence/neo4j_graph.py#L703)）：来自 `src.domain.CanonicalEntity`；具体实现可能由依赖注入或运行时分派决定。
- `entities.append`（[neo4j_graph.py:707](../../../src/persistence/neo4j_graph.py#L707)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `current_entity.model_dump`（[neo4j_graph.py:708](../../../src/persistence/neo4j_graph.py#L708)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `replacement_entity.model_dump`（[neo4j_graph.py:709](../../../src/persistence/neo4j_graph.py#L709)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `current_claims.get`（[neo4j_graph.py:711](../../../src/persistence/neo4j_graph.py#L711)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `current_claim.model_copy`（[neo4j_graph.py:713](../../../src/persistence/neo4j_graph.py#L713)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `Claim.model_validate`（[neo4j_graph.py:716](../../../src/persistence/neo4j_graph.py#L716)）：来自 `src.domain.Claim`；具体实现可能由依赖注入或运行时分派决定。
- `claims.append`（[neo4j_graph.py:720](../../../src/persistence/neo4j_graph.py#L720)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `current_claim.model_dump`（[neo4j_graph.py:722](../../../src/persistence/neo4j_graph.py#L722)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `replacement_claim.model_dump`（[neo4j_graph.py:723](../../../src/persistence/neo4j_graph.py#L723)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `current_conflict.model_copy`（[neo4j_graph.py:727](../../../src/persistence/neo4j_graph.py#L727)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `ConflictSet.model_validate`（[neo4j_graph.py:732](../../../src/persistence/neo4j_graph.py#L732)）：来自 `src.domain.ConflictSet`；具体实现可能由依赖注入或运行时分派决定。
- `conflicts.append`（[neo4j_graph.py:736](../../../src/persistence/neo4j_graph.py#L736)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `current_conflict.model_dump`（[neo4j_graph.py:738](../../../src/persistence/neo4j_graph.py#L738)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `replacement_conflict.model_dump`（[neo4j_graph.py:740](../../../src/persistence/neo4j_graph.py#L740)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `current_operation.model_copy`（[neo4j_graph.py:746](../../../src/persistence/neo4j_graph.py#L746)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `EntityOperation.model_validate`（[neo4j_graph.py:751](../../../src/persistence/neo4j_graph.py#L751)）：来自 `src.domain.EntityOperation`；具体实现可能由依赖注入或运行时分派决定。
- `entity_operations.append`（[neo4j_graph.py:755](../../../src/persistence/neo4j_graph.py#L755)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `current_operation.model_dump`（[neo4j_graph.py:757](../../../src/persistence/neo4j_graph.py#L757)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- 此处列出前 30 个不同调用表达式，另有 9 个，需按源码继续追踪。
- 静态扫描未定位直接调用方；可能通过路由注册、LangGraph 节点、协议方法或依赖注入动态调用，不据此判断为死代码。

**状态、副作用与异常**：
- 显式状态/容器赋值：`current_claims[replacement_claim.id]`、`revision.validation_context`。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：`KeyError(f<字符串常量>)`、`GraphIntegrityError(<字符串常量>)`、`GraphIntegrityError(f<字符串常量>)`。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。
- 恢复/幂等性：仅在代码有检查点、事务、请求编号或显式去重时才成立；此函数不能单凭名称视为可安全重试。


---

# Neo4jGraphStore.close ⭐⭐

**位置与等级**：[neo4j_graph.py:797](../../../src/persistence/neo4j_graph.py#L797)；局部辅助逻辑，需理解其调用条件与失败传播。

**签名**：`async def close(self) -> None`。

**作用**：释放该对象管理的外部资源；重复调用是否安全取决于实现。

**输入与输出**：
- 输入：无业务参数（或仅隐式接收实例）。
- 输出类型：`None`；具体返回路径见流程步骤。

**处理流程**：
1. 等待 `self.driver.close()` 完成。

**调用与被调用**：
- `self.driver.close`（[neo4j_graph.py:798](../../../src/persistence/neo4j_graph.py#L798)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- 静态扫描未定位直接调用方；可能通过路由注册、LangGraph 节点、协议方法或依赖注入动态调用，不据此判断为死代码。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：未见 `raise`；下游异常可能继续上抛。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。
- 恢复/幂等性：仅在代码有检查点、事务、请求编号或显式去重时才成立；此函数不能单凭名称视为可安全重试。


---
