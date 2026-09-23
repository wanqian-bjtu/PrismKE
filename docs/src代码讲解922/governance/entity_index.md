源码：[entity_index.py:1](../../../src/governance/entity_index.py#L1) | 基准：`dev/v0.10@f2f34d7` | 本文件符号数：2

**模块职责**：Entity embedding index preparation and idempotent rebuilds.
**在系统中的位置**：实体解析、事实规范化、冲突、风险、审核及实体操作的确定性规则。
**直接依赖**：[src.core.ids](../core/ids.md)、[src.domain](../domain/__init__.md)、[src.governance.entity_resolution](entity_resolution.md)、[src.persistence.base](../persistence/base.md)、[src.providers.base](../providers/base.md)；外部/标准库：`__future__`、`math`、`pydantic`。
**主要调用方（静态导入）**：[evaluation/document_validation.py](../evaluation/document_validation.md)、[evaluation/entity_linking.py](../evaluation/entity_linking.md)、[governance/__init__.py](__init__.md)。
**阅读提示**：下列流程根据当前源码控制流整理；`self`/接口对象的实际类型可能在运行时注入，未能静态解析的调用会明确标注。链接指向源码行或对应讲解文件。

---

# EntityIndexReport ⭐⭐⭐⭐

**位置与等级**：[entity_index.py:16](../../../src/governance/entity_index.py#L16)；承担主要 Agent、应用服务或审核/执行入口，跨模块影响显著。

**职责**：输出契约，供后续节点、API 或报告消费。基类：`BaseModel`。

**字段与类级约束**：
- `backend`：`str`。
- `model_fingerprint`：`str`。
- `active_entities`：`int`。
- `missing_or_outdated`：`int`。
- `batches`：`int`。
- `dimension`：`int | None`；默认 `None`。
- `dry_run`：`bool`。
- `indexed`：`int`；默认 `0`。

**内部成员**：此类未直接定义方法；字段/继承行为见源码。


---

# rebuild_entity_index ⭐⭐

**位置与等级**：[entity_index.py:27](../../../src/governance/entity_index.py#L27)；局部辅助逻辑，需理解其调用条件与失败传播。

**签名**：`async def rebuild_entity_index(graph_store: GraphStore, provider: EmbeddingProvider, *, backend: str, batch_size: int, dry_run: bool) -> EntityIndexReport`。

**作用**：处理 `rebuild_entity_index` 对应步骤；下列步骤依据函数体的实际控制流和调用点整理。

**输入与输出**：
- 输入：`graph_store`（GraphStore；图持久化接口，具体实现由配置注入）；`provider`（EmbeddingProvider）；`backend`（str）；`batch_size`（int）；`dry_run`（bool）。
- 输出类型：`EntityIndexReport`；具体返回路径见流程步骤。

**处理流程**：
1. 检查 `provider.fingerprint() == 'embedding:disabled'`；按条件分流，else 分支不存在。
2. 更新 `active`，值来自 `[item for item in await graph_store.list_entities() if item.active]`。
3. 更新 `existing`，值来自 `{item.entity_id: item for item in await graph_store.list_entity_embeddings()}`。
4. 更新 `pending`，值来自 `[]`。
5. 遍历 `active`，逐项处理 `entity`。
6. 更新 `report`，值来自 `EntityIndexReport(backend=backend, model_fingerprint=provider.fingerprint(), active_entities=len(ac…`。
7. 检查 `dry_run`；按条件分流，else 分支不存在。
8. 更新 `indexed`，值来自 `0`。
9. 遍历 `range(0, len(pending), batch_size)`，逐项处理 `offset`。
10. 更新 `report.indexed`，值来自 `indexed`。
11. 返回 `report`。

**关键条件与保护**：
- [entity_index.py:35](../../../src/governance/entity_index.py#L35)：`provider.fingerprint() == 'embedding:disabled'`，不满足时跳过本分支。
- [entity_index.py:43](../../../src/governance/entity_index.py#L43)：`embedding is None or embedding.model_fingerprint != provider.fingerprint() or embedding.text_hash != canonical_has…`，不满足时跳过本分支。
- [entity_index.py:58](../../../src/governance/entity_index.py#L58)：`dry_run`，不满足时跳过本分支。
- [entity_index.py:76](../../../src/governance/entity_index.py#L76)：`embeddings`，不满足时跳过本分支。

**调用与被调用**：
- `provider.fingerprint`（[entity_index.py:35](../../../src/governance/entity_index.py#L35)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `ValueError`（[entity_index.py:36](../../../src/governance/entity_index.py#L36)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `graph_store.list_entities`（[entity_index.py:37](../../../src/governance/entity_index.py#L37)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `graph_store.list_entity_embeddings`（[entity_index.py:38](../../../src/governance/entity_index.py#L38)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `entity_embedding_text`（调用点 [entity_index.py:41](../../../src/governance/entity_index.py#L41)）→ [entity_embedding_text](entity_resolution.md)，静态可定位。
- `existing.get`（[entity_index.py:42](../../../src/governance/entity_index.py#L42)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `canonical_hash`（调用点 [entity_index.py:46](../../../src/governance/entity_index.py#L46)）→ [canonical_hash](../core/ids.md)，静态可定位。
- `pending.append`（[entity_index.py:48](../../../src/governance/entity_index.py#L48)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `EntityIndexReport`（调用点 [entity_index.py:49](../../../src/governance/entity_index.py#L49)）→ [EntityIndexReport](entity_index.md)，静态可定位。
- `len`（[entity_index.py:52](../../../src/governance/entity_index.py#L52)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `math.ceil`（[entity_index.py:54](../../../src/governance/entity_index.py#L54)）：来自 `math`；具体实现可能由依赖注入或运行时分派决定。
- `next`（[entity_index.py:55](../../../src/governance/entity_index.py#L55)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `iter`（[entity_index.py:55](../../../src/governance/entity_index.py#L55)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `range`（[entity_index.py:61](../../../src/governance/entity_index.py#L61)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `provider.encode`（[entity_index.py:63](../../../src/governance/entity_index.py#L63)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `EntityEmbedding`（[entity_index.py:65](../../../src/governance/entity_index.py#L65)）：来自 `src.domain.EntityEmbedding`；具体实现可能由依赖注入或运行时分派决定。
- `zip`（[entity_index.py:72](../../../src/governance/entity_index.py#L72)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `graph_store.upsert_entity_embeddings`（[entity_index.py:74](../../../src/governance/entity_index.py#L74)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- 静态可定位的调用方：[validate_documents](../evaluation/document_validation.md)、[evaluate_entity_linking_manifest](../evaluation/entity_linking.md)。

**状态、副作用与异常**：
- 显式状态/容器赋值：`report.dimension`、`report.indexed`。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：`ValueError(<字符串常量>)`。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。


---
