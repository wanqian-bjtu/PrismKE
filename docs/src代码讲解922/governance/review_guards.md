源码：[review_guards.py:1](../../../src/governance/review_guards.py#L1) | 基准：`dev/v0.10@f2f34d7` | 本文件符号数：1

**模块职责**：Exact compensation and optimistic resource guards shared by graph backends.
**在系统中的位置**：实体解析、事实规范化、冲突、风险、审核及实体操作的确定性规则。
**直接依赖**：[src.core.errors](../core/errors.md)、[src.core.ids](../core/ids.md)、[src.domain](../domain/__init__.md)；外部/标准库：`typing`。
**主要调用方（静态导入）**：[persistence/json_graph.py](../persistence/json_graph.md)。
**阅读提示**：下列流程根据当前源码控制流整理；`self`/接口对象的实际类型可能在运行时注入，未能静态解析的调用会明确标注。链接指向源码行或对应讲解文件。

---

# verify_correction ⭐⭐

**位置与等级**：[review_guards.py:10](../../../src/governance/review_guards.py#L10)；局部辅助逻辑，需理解其调用条件与失败传播。

**签名**：`def verify_correction(transaction: GraphCommit, resources: dict[str, Any]) -> None`。

**作用**：处理 `verify_correction` 对应步骤；下列步骤依据函数体的实际控制流和调用点整理。

**输入与输出**：
- 输入：`transaction`（GraphCommit；待提交 GraphCommit；必须在最终写入边界重新校验）；`resources`（dict[str, Any]）。
- 输出类型：`None`；具体返回路径见流程步骤。

**处理流程**：
1. 更新 `guard`，值来自 `transaction.correction_guard`。
2. 检查 `guard is None`；按条件分流，else 分支不存在。
3. 检查 `transaction.revision.correction_guard != guard`；按条件分流，else 分支不存在。
4. 遍历 `guard.expected_resources.items()`，逐项处理 `(key, expected)`。
5. 更新 `changed`，值来自 `{f<字符串常量>: e.model_dump(mode='json') for e in transaction.entities}`。
6. 调用 `changed.update`，结果未直接赋值。
7. 更新 `snapshots`，值来自 `{f<字符串常量>: c for c in transaction.revision.changes}`。
8. 检查 `transaction.conflicts or transaction.entity_operations or transaction.entity_embeddings`；按条件分流，else 分支不存在。
9. 检查 `set(changed) != set(snapshots)`；按条件分流，else 分支不存在。
10. 遍历 `changed.items()`，逐项处理 `(key, after)`。

**关键条件与保护**：
- [review_guards.py:12](../../../src/governance/review_guards.py#L12)：`guard is None`，不满足时跳过本分支。
- [review_guards.py:14](../../../src/governance/review_guards.py#L14)：`transaction.revision.correction_guard != guard`，不满足时跳过本分支。
- [review_guards.py:19](../../../src/governance/review_guards.py#L19)：`actual != expected`，不满足时跳过本分支。
- [review_guards.py:24](../../../src/governance/review_guards.py#L24)：`transaction.conflicts or transaction.entity_operations or transaction.entity_embeddings`，不满足时跳过本分支。
- [review_guards.py:26](../../../src/governance/review_guards.py#L26)：`set(changed) != set(snapshots)`，不满足时跳过本分支。
- [review_guards.py:29](../../../src/governance/review_guards.py#L29)：`key not in guard.expected_resources`，不满足时跳过本分支。
- [review_guards.py:32](../../../src/governance/review_guards.py#L32)：`key.startswith('claim:') and change.before is not None and (set(change.before.get('source_run_ids', [])) != {trans…`，不满足时跳过本分支。
- [review_guards.py:38](../../../src/governance/review_guards.py#L38)：`change.before != resources.get(key) or change.after != after`，不满足时跳过本分支。

**调用与被调用**：
- `GraphIntegrityError`（调用点 [review_guards.py:15](../../../src/governance/review_guards.py#L15)）→ [GraphIntegrityError](../core/errors.md)，静态可定位。
- `guard.expected_resources.items`（[review_guards.py:16](../../../src/governance/review_guards.py#L16)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `resources.get`（[review_guards.py:17](../../../src/governance/review_guards.py#L17)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `canonical_hash`（调用点 [review_guards.py:18](../../../src/governance/review_guards.py#L18)）→ [canonical_hash](../core/ids.md)，静态可定位。
- `e.model_dump`（[review_guards.py:21](../../../src/governance/review_guards.py#L21)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `changed.update`（[review_guards.py:22](../../../src/governance/review_guards.py#L22)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `c.model_dump`（[review_guards.py:22](../../../src/governance/review_guards.py#L22)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `set`（[review_guards.py:26](../../../src/governance/review_guards.py#L26)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `changed.items`（[review_guards.py:28](../../../src/governance/review_guards.py#L28)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `key.startswith`（[review_guards.py:33](../../../src/governance/review_guards.py#L33)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `change.before.get`（[review_guards.py:35](../../../src/governance/review_guards.py#L35)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- 静态可定位的调用方：[JSONGraphStore.commit](../persistence/json_graph.md)、[Neo4jGraphStore._commit_tx](../persistence/neo4j_graph.md)。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：`GraphIntegrityError('CORRECTION_GUARD_MISMATCH')`、`GraphIntegrityError(f<字符串常量>)`、`GraphIntegrityError('CORRECTION_UNSUPPORTED_RESOURCE')`、`GraphIntegrityError('CORRECTION_SNAPSHOT_MISMATCH')`。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。


---
