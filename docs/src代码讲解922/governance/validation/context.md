源码：[context.py:1](../../../../src/governance/validation/context.py#L1) | 基准：`dev/v0.10@f2f34d7` | 本文件符号数：3

**模块职责**：Reuse recorded schema provenance; never infer a schema from graph data.
**在系统中的位置**：候选及提交前的统一结构、Schema、引用和证据校验。
**直接依赖**：[src.core.ids](../../core/ids.md)、[src.domain](../../domain/__init__.md)；外部/标准库：`collections`。
**主要调用方（静态导入）**：[governance/entity_operations.py](../entity_operations.md)、[persistence/json_graph.py](../../persistence/json_graph.md)、[persistence/neo4j_graph.py](../../persistence/neo4j_graph.md)。
**阅读提示**：下列流程根据当前源码控制流整理；`self`/接口对象的实际类型可能在运行时注入，未能静态解析的调用会明确标注。链接指向源码行或对应讲解文件。

---

# bind_commit_provenance ⭐⭐

**位置与等级**：[context.py:15](../../../../src/governance/validation/context.py#L15)；局部辅助逻辑，需理解其调用条件与失败传播。

**签名**：`def bind_commit_provenance(transaction: GraphCommit) -> None`。

**作用**：处理 `bind_commit_provenance` 对应步骤；下列步骤依据函数体的实际控制流和调用点整理。

**输入与输出**：
- 输入：`transaction`（GraphCommit；待提交 GraphCommit；必须在最终写入边界重新校验）。
- 输出类型：`None`；具体返回路径见流程步骤。

**处理流程**：
1. 更新 `transaction.revision.validation_context`，值来自 `transaction.validation_context`。
2. 更新 `payload`，值来自 `transaction.model_dump(mode='json', exclude={'revision': {'commit_fingerprint'}})`。
3. 遍历 `('documents', 'evidence', 'entities', 'claims', 'conflicts', 'entity_operations', 'e…`，逐项处理 `field`。
4. 更新 `transaction.revision.commit_fingerprint`，值来自 `canonical_hash(payload)`。

**调用与被调用**：
- `transaction.model_dump`（[context.py:17](../../../../src/governance/validation/context.py#L17)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `sorted`（[context.py:27](../../../../src/governance/validation/context.py#L27)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `canonical_hash`（调用点 [context.py:30](../../../../src/governance/validation/context.py#L30)）→ [canonical_hash](../../core/ids.md)，静态可定位。
- 静态可定位的调用方：[JSONGraphStore.commit](../../persistence/json_graph.md)、[JSONGraphStore.rollback_revision](../../persistence/json_graph.md)、[Neo4jGraphStore.commit](../../persistence/neo4j_graph.md)。

**状态、副作用与异常**：
- 显式状态/容器赋值：`transaction.revision.validation_context`、`payload[field]`、`transaction.revision.commit_fingerprint`。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：未见 `raise`；下游异常可能继续上抛。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。


---

# final_state_commit ⭐⭐

**位置与等级**：[context.py:33](../../../../src/governance/validation/context.py#L33)；局部辅助逻辑，需理解其调用条件与失败传播。

**签名**：`def final_state_commit(transaction: GraphCommit, claims: dict[str, Claim], previous_entities: dict[str, CanonicalEntity], revisions: Iterable[GraphRevision]) -> GraphCommit`。

**作用**：处理 `final_state_commit` 对应步骤；下列步骤依据函数体的实际控制流和调用点整理。

**输入与输出**：
- 输入：`transaction`（GraphCommit；待提交 GraphCommit；必须在最终写入边界重新校验）；`claims`（dict[str, Claim]；待处理的规范事实集合）；`previous_entities`（dict[str, CanonicalEntity]）；`revisions`（Iterable[GraphRevision]）。
- 输出类型：`GraphCommit`；具体返回路径见流程步骤。

**处理流程**：
1. 更新 `changed`，值来自 `{e.id for e in transaction.entities if e.id in previous_entities and (e.entity_type != previous_ent…`。
2. 更新 `submitted_ids`，值来自 `{c.id for c in transaction.claims}`。
3. 更新 `additional`，值来自 `{c.id for c in claims.values() if c.tx_to is None and c.id not in submitted_ids and changed.interse…`。
4. 更新 `context`，值来自 `context_for_claims(revisions, additional)`。
5. 检查 `transaction.validation_context is not None`；按条件分流，else 分支不存在。
6. 返回 `transaction.model_copy(update={'validation_context': context, 'claims': [claims[cid] for cid in sorted(s…`。

**关键条件与保护**：
- [context.py:57](../../../../src/governance/validation/context.py#L57)：`transaction.validation_context is not None`，不满足时跳过本分支。

**调用与被调用**：
- `claims.values`（[context.py:51](../../../../src/governance/validation/context.py#L51)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `changed.intersection`（[context.py:54](../../../../src/governance/validation/context.py#L54)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `context_for_claims`（调用点 [context.py:56](../../../../src/governance/validation/context.py#L56)）→ [context_for_claims](context.md)，静态可定位。
- `context.schemas.update`（[context.py:59](../../../../src/governance/validation/context.py#L59)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `context.claim_schema_ids.update`（[context.py:60](../../../../src/governance/validation/context.py#L60)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `context.document_asset_ids.update`（[context.py:61](../../../../src/governance/validation/context.py#L61)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `transaction.model_copy`（[context.py:62](../../../../src/governance/validation/context.py#L62)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `sorted`（[context.py:65](../../../../src/governance/validation/context.py#L65)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- 静态可定位的调用方：[JSONGraphStore.commit](../../persistence/json_graph.md)、[JSONGraphStore.rollback_revision](../../persistence/json_graph.md)、[Neo4jGraphStore._commit_tx](../../persistence/neo4j_graph.md)。

**状态、副作用与异常**：
- 显式状态/容器赋值：`context.policy_version`。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：未见 `raise`；下游异常可能继续上抛。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。


---

# context_for_claims ⭐⭐

**位置与等级**：[context.py:70](../../../../src/governance/validation/context.py#L70)；局部辅助逻辑，需理解其调用条件与失败传播。

**签名**：`def context_for_claims(revisions: Iterable[GraphRevision], claim_ids: set[str]) -> CommitValidationContext`。

**作用**：处理 `context_for_claims` 对应步骤；下列步骤依据函数体的实际控制流和调用点整理。

**输入与输出**：
- 输入：`revisions`（Iterable[GraphRevision]）；`claim_ids`（set[str]）。
- 输出类型：`CommitValidationContext`；具体返回路径见流程步骤。

**处理流程**：
1. 更新 `result`，值来自 `CommitValidationContext()`。
2. 遍历 `revisions`，逐项处理 `revision`。
3. 返回 `result`。

**关键条件与保护**：
- [context.py:76](../../../../src/governance/validation/context.py#L76)：`context is None or context.policy_version != 'validation-v1'`，不满足时跳过本分支。
- [context.py:81](../../../../src/governance/validation/context.py#L81)：`sid and sid in context.schemas and (claim_id not in result.claim_schema_ids)`，不满足时跳过本分支。

**调用与被调用**：
- `CommitValidationContext`（[context.py:73](../../../../src/governance/validation/context.py#L73)）：来自 `src.domain.CommitValidationContext`；具体实现可能由依赖注入或运行时分派决定。
- `result.document_asset_ids.update`（[context.py:78](../../../../src/governance/validation/context.py#L78)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `context.claim_schema_ids.get`（[context.py:80](../../../../src/governance/validation/context.py#L80)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- 静态可定位的调用方：[EntityGovernanceService._apply](../entity_operations.md)、[final_state_commit](context.md)、[JSONGraphStore.rollback_revision](../../persistence/json_graph.md)、[Neo4jGraphStore.rollback_revision](../../persistence/neo4j_graph.md)。

**状态、副作用与异常**：
- 显式状态/容器赋值：`result.claim_schema_ids[claim_id]`、`result.schemas[sid]`。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：未见 `raise`；下游异常可能继续上抛。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。


---
