源码：[migration.py:1](../../../src/persistence/migration.py#L1) | 基准：`dev/v0.10@f2f34d7` | 本文件符号数：2

**模块职责**：Idempotent JSON graph migration helpers.
**在系统中的位置**：图、证据、运行、审计、审核与案例的持久化；JSON/Neo4j 提供同一存储协议。
**直接依赖**：[src.core.errors](../core/errors.md)、[src.domain](../domain/__init__.md)、[src.persistence.base](base.md)；外部/标准库：`__future__`、`orjson`、`pathlib`、`pydantic`、`typing`。
**主要调用方（静态导入）**：[persistence/__init__.py](__init__.md)。
**阅读提示**：下列流程根据当前源码控制流整理；`self`/接口对象的实际类型可能在运行时注入，未能静态解析的调用会明确标注。链接指向源码行或对应讲解文件。

---

# MigrationReport ⭐⭐⭐⭐

**位置与等级**：[migration.py:25](../../../src/persistence/migration.py#L25)；承担主要 Agent、应用服务或审核/执行入口，跨模块影响显著。

**职责**：输出契约，供后续节点、API 或报告消费。基类：`BaseModel`。

**字段与类级约束**：
- `source`：`str`。
- `dry_run`：`bool`。
- `documents`：`int`。
- `evidence`：`int`。
- `entities`：`int`。
- `claims`：`int`。
- `conflicts`：`int`。
- `revisions`：`int`。
- `committed_revisions`：`int`；默认 `0`。
- `warnings`：`list[str]`；默认 `Field(default_factory=list)`。
- `blocked_claim_ids`：`list[str]`；默认 `Field(default_factory=list)`。

**内部成员**：此类未直接定义方法；字段/继承行为见源码。


---

# migrate_json_graph ⭐⭐

**位置与等级**：[migration.py:39](../../../src/persistence/migration.py#L39)；局部辅助逻辑，需理解其调用条件与失败传播。

**签名**：`async def migrate_json_graph(source: Path, target: GraphStore | None, *, evidence_store: EvidenceStore | None=None, dry_run: bool=False) -> MigrationReport`。

**作用**：处理 `migrate_json_graph` 对应步骤；下列步骤依据函数体的实际控制流和调用点整理。

**输入与输出**：
- 输入：`source`（Path）；`target`（GraphStore | None）；`evidence_store`（EvidenceStore | None；默认 `None`；证据元数据和原始内容的存储接口）；`dry_run`（bool；默认 `False`）。
- 输出类型：`MigrationReport`；具体返回路径见流程步骤。

**处理流程**：
1. 更新 `payload`，值来自 `orjson.loads(source.read_bytes())`。
2. 更新 `documents`，值来自 `{item_id: GraphDocument.model_validate(item) for item_id, item in payload.get('documents', {}).item…`。
3. 更新 `evidence`，值来自 `{item_id: EvidenceRef.model_validate(item) for item_id, item in payload.get('evidence', {}).items()}`。
4. 更新 `entities`，值来自 `{item_id: CanonicalEntity.model_validate(item) for item_id, item in payload.get('entities', {}).ite…`。
5. 更新 `claims`，值来自 `{item_id: Claim.model_validate(item) for item_id, item in payload.get('claims', {}).items()}`。
6. 更新 `conflicts`，值来自 `{item_id: ConflictSet.model_validate(item) for item_id, item in payload.get('conflicts', {}).items(…`。
7. 更新 `revisions`，值来自 `[GraphRevision.model_validate(item) for item in payload.get('revisions', [])]`。
8. 更新 `warnings`，值来自 `[]`。
9. 检查 `evidence_store is not None`；按条件分流，else 分支不存在。
10. 更新 `historical_claims`，值来自 `{(revision.id, change.resource_id): Claim.model_validate(change.after) for revision in revisions fo…`。
11. 更新 `blocked`，值来自 `{cid for revision in revisions for cid in revision.claim_ids if cid in claims and historical_claims…`。
12. 调用 `warnings.extend`，结果未直接赋值。
13. 更新 `report`，值来自 `MigrationReport(source=str(source.resolve()), dry_run=dry_run, documents=len(documents), evidence=l…`。
14. 检查 `dry_run`；按条件分流，else 分支不存在。
15. 检查 `target is None`；按条件分流，else 分支不存在。
16. 检查 `blocked`；按条件分流，else 分支不存在。
17. 遍历 `enumerate(revisions)`，逐项处理 `(index, revision)`。
18. 返回 `report`。

**关键条件与保护**：
- [migration.py:69](../../../src/persistence/migration.py#L69)：`evidence_store is not None`，不满足时跳过本分支。
- [migration.py:72](../../../src/persistence/migration.py#L72)：`evidence_id in evidence`，不满足时跳过本分支。
- [migration.py:121](../../../src/persistence/migration.py#L121)：`dry_run`，不满足时跳过本分支。
- [migration.py:123](../../../src/persistence/migration.py#L123)：`target is None`，不满足时跳过本分支。
- [migration.py:125](../../../src/persistence/migration.py#L125)：`blocked`，不满足时跳过本分支。
- [migration.py:138](../../../src/persistence/migration.py#L138)：`change.after is None`，不满足时跳过本分支。
- [migration.py:140](../../../src/persistence/migration.py#L140)：`change.resource_type == 'claim'`，不满足时有 else 分支。
- [migration.py:143](../../../src/persistence/migration.py#L143)：`change.resource_type == 'entity'`，不满足时有 else 分支。
- [migration.py:146](../../../src/persistence/migration.py#L146)：`change.resource_type == 'conflict'`，不满足时有 else 分支。
- [migration.py:149](../../../src/persistence/migration.py#L149)：`change.resource_type == 'entity_operation'`，不满足时跳过本分支。

**调用与被调用**：
- `orjson.loads`（[migration.py:46](../../../src/persistence/migration.py#L46)）：来自 `orjson`；具体实现可能由依赖注入或运行时分派决定。
- `source.read_bytes`（[migration.py:46](../../../src/persistence/migration.py#L46)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `GraphDocument.model_validate`（[migration.py:48](../../../src/persistence/migration.py#L48)）：来自 `src.domain.GraphDocument`；具体实现可能由依赖注入或运行时分派决定。
- `payload.get('documents', {}).items`（[migration.py:49](../../../src/persistence/migration.py#L49)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `payload.get`（[migration.py:49](../../../src/persistence/migration.py#L49)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `EvidenceRef.model_validate`（[migration.py:52](../../../src/persistence/migration.py#L52)）：来自 `src.domain.EvidenceRef`；具体实现可能由依赖注入或运行时分派决定。
- `payload.get('evidence', {}).items`（[migration.py:53](../../../src/persistence/migration.py#L53)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `CanonicalEntity.model_validate`（[migration.py:56](../../../src/persistence/migration.py#L56)）：来自 `src.domain.CanonicalEntity`；具体实现可能由依赖注入或运行时分派决定。
- `payload.get('entities', {}).items`（[migration.py:57](../../../src/persistence/migration.py#L57)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `Claim.model_validate`（[migration.py:60](../../../src/persistence/migration.py#L60)）：来自 `src.domain.Claim`；具体实现可能由依赖注入或运行时分派决定。
- `payload.get('claims', {}).items`（[migration.py:60](../../../src/persistence/migration.py#L60)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `ConflictSet.model_validate`（[migration.py:63](../../../src/persistence/migration.py#L63)）：来自 `src.domain.ConflictSet`；具体实现可能由依赖注入或运行时分派决定。
- `payload.get('conflicts', {}).items`（[migration.py:64](../../../src/persistence/migration.py#L64)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `GraphRevision.model_validate`（[migration.py:66](../../../src/persistence/migration.py#L66)）：来自 `src.domain.GraphRevision`；具体实现可能由依赖注入或运行时分派决定。
- `claims.values`（[migration.py:70](../../../src/persistence/migration.py#L70)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `evidence_store.get`（[migration.py:75](../../../src/persistence/migration.py#L75)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `warnings.append`（[migration.py:77](../../../src/persistence/migration.py#L77)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `documents.setdefault`（[migration.py:80](../../../src/persistence/migration.py#L80)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `GraphDocument`（[migration.py:82](../../../src/persistence/migration.py#L82)）：来自 `src.domain.GraphDocument`；具体实现可能由依赖注入或运行时分派决定。
- `historical_claims.get`（[migration.py:101](../../../src/persistence/migration.py#L101)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `warnings.extend`（[migration.py:108](../../../src/persistence/migration.py#L108)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `sorted`（[migration.py:108](../../../src/persistence/migration.py#L108)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `MigrationReport`（调用点 [migration.py:109](../../../src/persistence/migration.py#L109)）→ [MigrationReport](migration.md)，静态可定位。
- `str`（[migration.py:110](../../../src/persistence/migration.py#L110)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `source.resolve`（[migration.py:110](../../../src/persistence/migration.py#L110)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `len`（[migration.py:112](../../../src/persistence/migration.py#L112)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `set`（[migration.py:118](../../../src/persistence/migration.py#L118)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `ValueError`（[migration.py:124](../../../src/persistence/migration.py#L124)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `GraphIntegrityError`（调用点 [migration.py:126](../../../src/persistence/migration.py#L126)）→ [GraphIntegrityError](../core/errors.md)，静态可定位。
- `enumerate`（[migration.py:128](../../../src/persistence/migration.py#L128)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- 此处列出前 30 个不同调用表达式，另有 7 个，需按源码继续追踪。
- 静态扫描未定位直接调用方；可能通过路由注册、LangGraph 节点、协议方法或依赖注入动态调用，不据此判断为死代码。

**状态、副作用与异常**：
- 显式状态/容器赋值：`evidence[item.id]`、`report.committed_revisions`。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：`ValueError(<字符串常量>)`、`GraphIntegrityError(f<字符串常量>)`。
- 本地捕获：`EvidenceIntegrityError`。
- 恢复/幂等性：仅在代码有检查点、事务、请求编号或显式去重时才成立；此函数不能单凭名称视为可安全重试。


---
