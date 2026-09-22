源码：[legacy_evidence.py:1](../../../src/persistence/legacy_evidence.py#L1) | 基准：`dev/v0.10@f2f34d7` | 本文件符号数：8

**模块职责**：Audited repair of historical integration-test claims in an isolated graph.
**在系统中的位置**：图、证据、运行、审计、审核与案例的持久化；JSON/Neo4j 提供同一存储协议。
**直接依赖**：[src.core.errors](../core/errors.md)、[src.core.ids](../core/ids.md)、[src.domain](../domain/__init__.md)、[src.persistence.file_evidence](file_evidence.md)、[src.persistence.neo4j_graph](neo4j_graph.md)；外部/标准库：`__future__`、`datetime`、`orjson`、`pathlib`、`typing`。
**主要调用方（静态导入）**：[cli.py](../cli.md)。
**阅读提示**：下列流程根据当前源码控制流整理；`self`/接口对象的实际类型可能在运行时注入，未能静态解析的调用会明确标注。链接指向源码行或对应讲解文件。

---

# require_isolated_database ⭐⭐

**位置与等级**：[legacy_evidence.py:22](../../../src/persistence/legacy_evidence.py#L22)；局部辅助逻辑，需理解其调用条件与失败传播。

**签名**：`async def require_isolated_database(store: Neo4jGraphStore, expected_data_dir: Path) -> None`。

**作用**：Compare Neo4j's actual data directory, not merely the connection string.

**输入与输出**：
- 输入：`store`（Neo4jGraphStore）；`expected_data_dir`（Path）。
- 输出类型：`None`；具体返回路径见流程步骤。

**处理流程**：
1. 进入上下文 `store.driver.session(database=store.database)`，由上下文管理器控制资源释放或事务范围。
2. 检查 `record is None or Path(str(record['value'])).resolve() != expected_data_dir.resolve()`；按条件分流，else 分支不存在。

**关键条件与保护**：
- [legacy_evidence.py:30](../../../src/persistence/legacy_evidence.py#L30)：`record is None or Path(str(record['value'])).resolve() != expected_data_dir.resolve()`，不满足时跳过本分支。

**调用与被调用**：
- `store.driver.session`（[legacy_evidence.py:24](../../../src/persistence/legacy_evidence.py#L24)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `session.run`（[legacy_evidence.py:25](../../../src/persistence/legacy_evidence.py#L25)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `result.single`（[legacy_evidence.py:29](../../../src/persistence/legacy_evidence.py#L29)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `Path(str(record['value'])).resolve`（[legacy_evidence.py:30](../../../src/persistence/legacy_evidence.py#L30)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `Path`（[legacy_evidence.py:30](../../../src/persistence/legacy_evidence.py#L30)）：来自 `pathlib.Path`；具体实现可能由依赖注入或运行时分派决定。
- `str`（[legacy_evidence.py:30](../../../src/persistence/legacy_evidence.py#L30)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `expected_data_dir.resolve`（[legacy_evidence.py:30](../../../src/persistence/legacy_evidence.py#L30)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `GraphIntegrityError`（调用点 [legacy_evidence.py:31](../../../src/persistence/legacy_evidence.py#L31)）→ [GraphIntegrityError](../core/errors.md)，静态可定位。
- 静态可定位的调用方：[repair_legacy_evidence.execute](../cli.md)。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：`GraphIntegrityError(<字符串常量>)`。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。
- 恢复/幂等性：仅在代码有检查点、事务、请求编号或显式去重时才成立；此函数不能单凭名称视为可安全重试。


---

# _graph_evidence ⭐⭐

**位置与等级**：[legacy_evidence.py:34](../../../src/persistence/legacy_evidence.py#L34)；局部辅助逻辑，需理解其调用条件与失败传播。

**签名**：`async def _graph_evidence(store: Neo4jGraphStore, evidence_id: str) -> EvidenceRef`。

**作用**：内部辅助步骤；将参数转换为本模块所需的中间对象或操作结果。

**输入与输出**：
- 输入：`store`（Neo4jGraphStore）；`evidence_id`（str）。
- 输出类型：`EvidenceRef`；具体返回路径见流程步骤。

**处理流程**：
1. 更新 `evidence`，值来自 `await store.get_evidence(evidence_id)`。
2. 检查 `evidence is None`；按条件分流，else 分支不存在。
3. 返回 `evidence`。

**关键条件与保护**：
- [legacy_evidence.py:36](../../../src/persistence/legacy_evidence.py#L36)：`evidence is None`，不满足时跳过本分支。

**调用与被调用**：
- `store.get_evidence`（[legacy_evidence.py:35](../../../src/persistence/legacy_evidence.py#L35)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `GraphIntegrityError`（调用点 [legacy_evidence.py:37](../../../src/persistence/legacy_evidence.py#L37)）→ [GraphIntegrityError](../core/errors.md)，静态可定位。
- 静态可定位的调用方：[legacy_snapshot](legacy_evidence.md)、[restore_sample_evidence](legacy_evidence.md)、[verify_active_claims](legacy_evidence.md)。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：`GraphIntegrityError(f<字符串常量>)`。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。
- 恢复/幂等性：仅在代码有检查点、事务、请求编号或显式去重时才成立；此函数不能单凭名称视为可安全重试。


---

# legacy_snapshot ⭐⭐

**位置与等级**：[legacy_evidence.py:41](../../../src/persistence/legacy_evidence.py#L41)；局部辅助逻辑，需理解其调用条件与失败传播。

**签名**：`async def legacy_snapshot(store: Neo4jGraphStore, source: FileEvidenceStore) -> dict[str, Any]`。

**作用**：Produce a small, non-sensitive manifest that pins every planned change.

**输入与输出**：
- 输入：`store`（Neo4jGraphStore）；`source`（FileEvidenceStore）。
- 输出类型：`dict[str, Any]`；具体返回路径见流程步骤。

**处理流程**：
1. 更新 `claims`，值来自 `await store.list_claims()`。
2. 更新 `governance`，值来自 `sorted((c for c in claims if c.id.startswith('claim:governance:')), key=lambda c: c.id)`。
3. 更新 `historical`，值来自 `sorted((c for c in claims if c.id.startswith('claim:test:')), key=lambda c: c.id)`。
4. 检查 `len(governance) != 9 or len(historical) != 16`；按条件分流，else 分支不存在。
5. 检查 `any((c.tx_to is not None or c.status.value != 'pending' for c in governance))`；按条件分流，else 分支不存在。
6. 检查 `any((c.tx_to is None for c in historical))`；按条件分流，else 分支不存在。
7. 进入上下文 `store.driver.session(database=store.database)`，由上下文管理器控制资源释放或事务范围。
8. 更新 `by_id`，值来自 `{}`。
9. 遍历 `rows`，逐项处理 `row`。
10. 遍历 `governance`，逐项处理 `claim`。
11. 遍历 `historical`，逐项处理 `claim`。
12. 更新 `sample`，值来自 `next((c for c in claims if c.id == SAMPLE_CLAIM_ID), None)`。
13. 检查 `sample is None or sample.tx_to is not None or sample.evidence_ids != [SAMPLE_EVIDENCE_ID]`；按条件分流，else 分支不存在。
14. 更新 `graph_ref`，值来自 `await _graph_evidence(store, SAMPLE_EVIDENCE_ID)`。
15. 检查 `not await source.verify(SAMPLE_EVIDENCE_ID) or await source.get(SAMPLE_EVIDENCE_ID) != graph_ref`；按条件分流，else 分支不存在。
16. 更新 `latest`，值来自 `await store.latest_revision()`。
17. 检查 `latest is None`；按条件分流，else 分支不存在。
18. 返回 `{'parent_id': latest.id, 'governance': [{'id': c.id, 'fingerprint': canonical_hash(c.model_dump(mode='js…`。

**关键条件与保护**：
- [legacy_evidence.py:50](../../../src/persistence/legacy_evidence.py#L50)：`len(governance) != 9 or len(historical) != 16`，不满足时跳过本分支。
- [legacy_evidence.py:52](../../../src/persistence/legacy_evidence.py#L52)：`any((c.tx_to is not None or c.status.value != 'pending' for c in governance))`，不满足时跳过本分支。
- [legacy_evidence.py:54](../../../src/persistence/legacy_evidence.py#L54)：`any((c.tx_to is None for c in historical))`，不满足时跳过本分支。
- [legacy_evidence.py:71](../../../src/persistence/legacy_evidence.py#L71)：`len(matching) != 1 or claim.evidence_ids != [f<字符串常量>] or matching[0]['evidence_id'] != claim.evidence_ids[0] or (…`，不满足时跳过本分支。
- [legacy_evidence.py:85](../../../src/persistence/legacy_evidence.py#L85)：`len(matching) != 1 or claim.evidence_ids != [f<字符串常量>] or matching[0]['evidence_id'] != claim.evidence_ids[0] or (…`，不满足时跳过本分支。
- [legacy_evidence.py:98](../../../src/persistence/legacy_evidence.py#L98)：`sample is None or sample.tx_to is not None or sample.evidence_ids != [SAMPLE_EVIDENCE_ID]`，不满足时跳过本分支。
- [legacy_evidence.py:101](../../../src/persistence/legacy_evidence.py#L101)：`not await source.verify(SAMPLE_EVIDENCE_ID) or await source.get(SAMPLE_EVIDENCE_ID) != graph_ref`，不满足时跳过本分支。
- [legacy_evidence.py:107](../../../src/persistence/legacy_evidence.py#L107)：`latest is None`，不满足时跳过本分支。

**调用与被调用**：
- `store.list_claims`（[legacy_evidence.py:45](../../../src/persistence/legacy_evidence.py#L45)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `sorted`（[legacy_evidence.py:46](../../../src/persistence/legacy_evidence.py#L46)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `c.id.startswith`（[legacy_evidence.py:47](../../../src/persistence/legacy_evidence.py#L47)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `len`（[legacy_evidence.py:50](../../../src/persistence/legacy_evidence.py#L50)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `GraphIntegrityError`（调用点 [legacy_evidence.py:51](../../../src/persistence/legacy_evidence.py#L51)）→ [GraphIntegrityError](../core/errors.md)，静态可定位。
- `any`（[legacy_evidence.py:52](../../../src/persistence/legacy_evidence.py#L52)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `store.driver.session`（[legacy_evidence.py:57](../../../src/persistence/legacy_evidence.py#L57)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `session.run`（[legacy_evidence.py:58](../../../src/persistence/legacy_evidence.py#L58)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `result.data`（[legacy_evidence.py:64](../../../src/persistence/legacy_evidence.py#L64)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `by_id.setdefault(str(row['claim_id']), []).append`（[legacy_evidence.py:67](../../../src/persistence/legacy_evidence.py#L67)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `by_id.setdefault`（[legacy_evidence.py:67](../../../src/persistence/legacy_evidence.py#L67)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `str`（[legacy_evidence.py:67](../../../src/persistence/legacy_evidence.py#L67)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `by_id.get`（[legacy_evidence.py:69](../../../src/persistence/legacy_evidence.py#L69)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `claim.id.removeprefix`（[legacy_evidence.py:70](../../../src/persistence/legacy_evidence.py#L70)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `EvidenceRef.model_validate`（[legacy_evidence.py:77](../../../src/persistence/legacy_evidence.py#L77)）：来自 `src.domain.EvidenceRef`；具体实现可能由依赖注入或运行时分派决定。
- `orjson.loads`（[legacy_evidence.py:77](../../../src/persistence/legacy_evidence.py#L77)）：来自 `orjson`；具体实现可能由依赖注入或运行时分派决定。
- `next`（[legacy_evidence.py:97](../../../src/persistence/legacy_evidence.py#L97)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `_graph_evidence`（调用点 [legacy_evidence.py:100](../../../src/persistence/legacy_evidence.py#L100)）→ [_graph_evidence](legacy_evidence.md)，静态可定位。
- `source.verify`（[legacy_evidence.py:102](../../../src/persistence/legacy_evidence.py#L102)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `source.get`（[legacy_evidence.py:103](../../../src/persistence/legacy_evidence.py#L103)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `store.latest_revision`（[legacy_evidence.py:106](../../../src/persistence/legacy_evidence.py#L106)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `canonical_hash`（调用点 [legacy_evidence.py:112](../../../src/persistence/legacy_evidence.py#L112)）→ [canonical_hash](../core/ids.md)，静态可定位。
- `c.model_dump`（[legacy_evidence.py:112](../../../src/persistence/legacy_evidence.py#L112)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `sum`（[legacy_evidence.py:119](../../../src/persistence/legacy_evidence.py#L119)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- 静态可定位的调用方：[repair_legacy_evidence.execute](../cli.md)。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：`GraphIntegrityError(<字符串常量>)`、`GraphIntegrityError(f<字符串常量>)`。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。
- 恢复/幂等性：仅在代码有检查点、事务、请求编号或显式去重时才成立；此函数不能单凭名称视为可安全重试。


---

# closure_commit ⭐⭐

**位置与等级**：[legacy_evidence.py:123](../../../src/persistence/legacy_evidence.py#L123)；局部辅助逻辑，需理解其调用条件与失败传播。

**签名**：`def closure_commit(manifest: dict[str, Any], claims: list[Claim]) -> GraphCommit`。

**作用**：处理 `closure_commit` 对应步骤；下列步骤依据函数体的实际控制流和调用点整理。

**输入与输出**：
- 输入：`manifest`（dict[str, Any]）；`claims`（list[Claim]；待处理的规范事实集合）。
- 输出类型：`GraphCommit`；具体返回路径见流程步骤。

**处理流程**：
1. 更新 `by_id`，值来自 `{claim.id: claim for claim in claims}`。
2. 更新 `timestamp`，值来自 `datetime.now(UTC)`。
3. 更新 `closed`，值来自 `[]`。
4. 更新 `changes`，值来自 `[]`。
5. 遍历 `manifest['governance']`，逐项处理 `item`。
6. 返回 `GraphCommit(claims=closed, revision=GraphRevision(id=stable_id('revision', MAINTENANCE_RUN_ID, manifest[…`。

**关键条件与保护**：
- [legacy_evidence.py:130](../../../src/persistence/legacy_evidence.py#L130)：`claim is None or claim.tx_to is not None or canonical_hash(claim.model_dump(mode='json')) != item['fingerprint']`，不满足时跳过本分支。

**调用与被调用**：
- `datetime.now`（[legacy_evidence.py:125](../../../src/persistence/legacy_evidence.py#L125)）：来自 `datetime.datetime`；具体实现可能由依赖注入或运行时分派决定。
- `by_id.get`（[legacy_evidence.py:129](../../../src/persistence/legacy_evidence.py#L129)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `canonical_hash`（调用点 [legacy_evidence.py:133](../../../src/persistence/legacy_evidence.py#L133)）→ [canonical_hash](../core/ids.md)，静态可定位。
- `claim.model_dump`（[legacy_evidence.py:133](../../../src/persistence/legacy_evidence.py#L133)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `GraphIntegrityError`（调用点 [legacy_evidence.py:135](../../../src/persistence/legacy_evidence.py#L135)）→ [GraphIntegrityError](../core/errors.md)，静态可定位。
- `claim.model_copy`（[legacy_evidence.py:136](../../../src/persistence/legacy_evidence.py#L136)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `closed.append`（[legacy_evidence.py:137](../../../src/persistence/legacy_evidence.py#L137)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `changes.append`（[legacy_evidence.py:138](../../../src/persistence/legacy_evidence.py#L138)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `GraphChange`（[legacy_evidence.py:139](../../../src/persistence/legacy_evidence.py#L139)）：来自 `src.domain.GraphChange`；具体实现可能由依赖注入或运行时分派决定。
- `updated.model_dump`（[legacy_evidence.py:144](../../../src/persistence/legacy_evidence.py#L144)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `GraphCommit`（[legacy_evidence.py:147](../../../src/persistence/legacy_evidence.py#L147)）：来自 `src.domain.GraphCommit`；具体实现可能由依赖注入或运行时分派决定。
- `GraphRevision`（[legacy_evidence.py:149](../../../src/persistence/legacy_evidence.py#L149)）：来自 `src.domain.GraphRevision`；具体实现可能由依赖注入或运行时分派决定。
- `stable_id`（调用点 [legacy_evidence.py:150](../../../src/persistence/legacy_evidence.py#L150)）→ [stable_id](../core/ids.md)，静态可定位。
- 静态可定位的调用方：[repair_legacy_evidence.execute](../cli.md)。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：`GraphIntegrityError(<字符串常量>)`。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。
- 恢复/幂等性：仅在代码有检查点、事务、请求编号或显式去重时才成立；此函数不能单凭名称视为可安全重试。


---

# restore_sample_evidence ⭐⭐

**位置与等级**：[legacy_evidence.py:159](../../../src/persistence/legacy_evidence.py#L159)；局部辅助逻辑，需理解其调用条件与失败传播。

**签名**：`async def restore_sample_evidence(store: Neo4jGraphStore, source: FileEvidenceStore, target: FileEvidenceStore) -> None`。

**作用**：处理 `restore_sample_evidence` 对应步骤；下列步骤依据函数体的实际控制流和调用点整理。

**输入与输出**：
- 输入：`store`（Neo4jGraphStore）；`source`（FileEvidenceStore）；`target`（FileEvidenceStore）。
- 输出类型：`None`；具体返回路径见流程步骤。

**处理流程**：
1. 更新 `evidence`，值来自 `await _graph_evidence(store, SAMPLE_EVIDENCE_ID)`。
2. 检查 `not await source.verify(evidence.id) or await source.get(evidence.id) != evidence`；按条件分流，else 分支不存在。
3. 更新 `blob`，值来自 `await source.get_blob(evidence.source_hash)`。
4. 检查 `await target.put_blob(blob, 'application/octet-stream') != evidence.source_hash`；按条件分流，else 分支不存在。
5. 等待 `target.put_ref(evidence)` 完成。
6. 检查 `not await target.verify(evidence.id) or await target.get(evidence.id) != evidence`；按条件分流，else 分支不存在。

**关键条件与保护**：
- [legacy_evidence.py:163](../../../src/persistence/legacy_evidence.py#L163)：`not await source.verify(evidence.id) or await source.get(evidence.id) != evidence`，不满足时跳过本分支。
- [legacy_evidence.py:166](../../../src/persistence/legacy_evidence.py#L166)：`await target.put_blob(blob, 'application/octet-stream') != evidence.source_hash`，不满足时跳过本分支。
- [legacy_evidence.py:169](../../../src/persistence/legacy_evidence.py#L169)：`not await target.verify(evidence.id) or await target.get(evidence.id) != evidence`，不满足时跳过本分支。

**调用与被调用**：
- `_graph_evidence`（调用点 [legacy_evidence.py:162](../../../src/persistence/legacy_evidence.py#L162)）→ [_graph_evidence](legacy_evidence.md)，静态可定位。
- `source.verify`（[legacy_evidence.py:163](../../../src/persistence/legacy_evidence.py#L163)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `source.get`（[legacy_evidence.py:163](../../../src/persistence/legacy_evidence.py#L163)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `GraphIntegrityError`（调用点 [legacy_evidence.py:164](../../../src/persistence/legacy_evidence.py#L164)）→ [GraphIntegrityError](../core/errors.md)，静态可定位。
- `source.get_blob`（[legacy_evidence.py:165](../../../src/persistence/legacy_evidence.py#L165)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `target.put_blob`（[legacy_evidence.py:166](../../../src/persistence/legacy_evidence.py#L166)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `target.put_ref`（[legacy_evidence.py:168](../../../src/persistence/legacy_evidence.py#L168)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `target.verify`（[legacy_evidence.py:169](../../../src/persistence/legacy_evidence.py#L169)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `target.get`（[legacy_evidence.py:169](../../../src/persistence/legacy_evidence.py#L169)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- 静态可定位的调用方：[repair_legacy_evidence.execute](../cli.md)。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：`GraphIntegrityError(<字符串常量>)`。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。
- 恢复/幂等性：仅在代码有检查点、事务、请求编号或显式去重时才成立；此函数不能单凭名称视为可安全重试。


---

# verify_active_claims ⭐⭐

**位置与等级**：[legacy_evidence.py:173](../../../src/persistence/legacy_evidence.py#L173)；局部辅助逻辑，需理解其调用条件与失败传播。

**签名**：`async def verify_active_claims(store: Neo4jGraphStore, target: FileEvidenceStore, *, exclude_ids: set[str] | None=None) -> int`。

**作用**：处理 `verify_active_claims` 对应步骤；下列步骤依据函数体的实际控制流和调用点整理。

**输入与输出**：
- 输入：`store`（Neo4jGraphStore）；`target`（FileEvidenceStore）；`exclude_ids`（set[str] | None；默认 `None`）。
- 输出类型：`int`；具体返回路径见流程步骤。

**处理流程**：
1. 更新 `active`，值来自 `[claim for claim in await store.list_claims() if claim.tx_to is None and claim.id not in (exclude_i…`。
2. 遍历 `active`，逐项处理 `claim`。
3. 返回 `len(active)`。

**关键条件与保护**：
- [legacy_evidence.py:186](../../../src/persistence/legacy_evidence.py#L186)：`not await target.verify(evidence_id) or await target.get(evidence_id) != graph_ref`，不满足时跳过本分支。

**调用与被调用**：
- `store.list_claims`（[legacy_evidence.py:180](../../../src/persistence/legacy_evidence.py#L180)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `set`（[legacy_evidence.py:181](../../../src/persistence/legacy_evidence.py#L181)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `_graph_evidence`（调用点 [legacy_evidence.py:185](../../../src/persistence/legacy_evidence.py#L185)）→ [_graph_evidence](legacy_evidence.md)，静态可定位。
- `target.verify`（[legacy_evidence.py:186](../../../src/persistence/legacy_evidence.py#L186)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `target.get`（[legacy_evidence.py:186](../../../src/persistence/legacy_evidence.py#L186)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `GraphIntegrityError`（调用点 [legacy_evidence.py:187](../../../src/persistence/legacy_evidence.py#L187)）→ [GraphIntegrityError](../core/errors.md)，静态可定位。
- `len`（[legacy_evidence.py:188](../../../src/persistence/legacy_evidence.py#L188)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- 静态可定位的调用方：[repair_legacy_evidence.execute](../cli.md)。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：`GraphIntegrityError(f<字符串常量>)`。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。
- 恢复/幂等性：仅在代码有检查点、事务、请求编号或显式去重时才成立；此函数不能单凭名称视为可安全重试。


---

# existing_maintenance ⭐⭐

**位置与等级**：[legacy_evidence.py:191](../../../src/persistence/legacy_evidence.py#L191)；局部辅助逻辑，需理解其调用条件与失败传播。

**签名**：`async def existing_maintenance(store: Neo4jGraphStore) -> GraphRevision | None`。

**作用**：处理 `existing_maintenance` 对应步骤；下列步骤依据函数体的实际控制流和调用点整理。

**输入与输出**：
- 输入：`store`（Neo4jGraphStore）。
- 输出类型：`GraphRevision | None`；具体返回路径见流程步骤。

**处理流程**：
1. 进入上下文 `store.driver.session(database=store.database)`，由上下文管理器控制资源释放或事务范围。
2. 检查 `len(records) > 1`；按条件分流，else 分支不存在。
3. 返回 `GraphRevision.model_validate(orjson.loads(records[0]['payload'])) if records else None`。

**关键条件与保护**：
- [legacy_evidence.py:198](../../../src/persistence/legacy_evidence.py#L198)：`len(records) > 1`，不满足时跳过本分支。

**调用与被调用**：
- `store.driver.session`（[legacy_evidence.py:192](../../../src/persistence/legacy_evidence.py#L192)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `session.run`（[legacy_evidence.py:193](../../../src/persistence/legacy_evidence.py#L193)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `result.data`（[legacy_evidence.py:197](../../../src/persistence/legacy_evidence.py#L197)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `len`（[legacy_evidence.py:198](../../../src/persistence/legacy_evidence.py#L198)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `GraphIntegrityError`（调用点 [legacy_evidence.py:199](../../../src/persistence/legacy_evidence.py#L199)）→ [GraphIntegrityError](../core/errors.md)，静态可定位。
- `GraphRevision.model_validate`（[legacy_evidence.py:200](../../../src/persistence/legacy_evidence.py#L200)）：来自 `src.domain.GraphRevision`；具体实现可能由依赖注入或运行时分派决定。
- `orjson.loads`（[legacy_evidence.py:200](../../../src/persistence/legacy_evidence.py#L200)）：来自 `orjson`；具体实现可能由依赖注入或运行时分派决定。
- 静态可定位的调用方：[repair_legacy_evidence.execute](../cli.md)。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：`GraphIntegrityError(<字符串常量>)`。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。
- 恢复/幂等性：仅在代码有检查点、事务、请求编号或显式去重时才成立；此函数不能单凭名称视为可安全重试。


---

# read_manifest ⭐⭐

**位置与等级**：[legacy_evidence.py:203](../../../src/persistence/legacy_evidence.py#L203)；局部辅助逻辑，需理解其调用条件与失败传播。

**签名**：`def read_manifest(path: Path) -> dict[str, Any]`。

**作用**：读取或组装对应资源；是否纯只读及异常行为需结合下方显式调用与状态写入判断。

**输入与输出**：
- 输入：`path`（Path）。
- 输出类型：`dict[str, Any]`；具体返回路径见流程步骤。

**处理流程**：
1. 更新 `value`，值来自 `orjson.loads(path.read_bytes())`。
2. 检查 `not isinstance(value, dict)`；按条件分流，else 分支不存在。
3. 返回 `value`。

**关键条件与保护**：
- [legacy_evidence.py:205](../../../src/persistence/legacy_evidence.py#L205)：`not isinstance(value, dict)`，不满足时跳过本分支。

**调用与被调用**：
- `orjson.loads`（[legacy_evidence.py:204](../../../src/persistence/legacy_evidence.py#L204)）：来自 `orjson`；具体实现可能由依赖注入或运行时分派决定。
- `path.read_bytes`（[legacy_evidence.py:204](../../../src/persistence/legacy_evidence.py#L204)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `isinstance`（[legacy_evidence.py:205](../../../src/persistence/legacy_evidence.py#L205)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `GraphIntegrityError`（调用点 [legacy_evidence.py:206](../../../src/persistence/legacy_evidence.py#L206)）→ [GraphIntegrityError](../core/errors.md)，静态可定位。
- 静态可定位的调用方：[repair_legacy_evidence.execute](../cli.md)。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：`GraphIntegrityError(<字符串常量>)`。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。
- 恢复/幂等性：仅在代码有检查点、事务、请求编号或显式去重时才成立；此函数不能单凭名称视为可安全重试。


---
