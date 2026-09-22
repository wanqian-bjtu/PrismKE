源码：[review_workspace.py:1](../../../src/workflow/review_workspace.py#L1) | 基准：`dev/v0.10@f2f34d7` | 本文件符号数：4

**模块职责**：Verified, offline-only copies of completed extraction checkpoints.
**在系统中的位置**：应用服务、LangGraph 编排、执行状态、审核接续、图提交及纠正流程。
**直接依赖**：[src.core.ids](../core/ids.md)、[src.domain](../domain/__init__.md)、[src.persistence](../persistence/__init__.md)、[src.persistence.checkpoints](../persistence/checkpoints.md)、[src.providers](../providers/__init__.md)、[src.providers.mock](../providers/mock.md)、[src.workflow.graph](graph.md)；外部/标准库：`__future__`、`contextlib`、`filelock`、`orjson`、`pathlib`、`shutil`、`sqlite3`、`typing`。
**主要调用方（静态导入）**：[workflow/service.py](service.md)。
**阅读提示**：下列流程根据当前源码控制流整理；`self`/接口对象的实际类型可能在运行时注入，未能静态解析的调用会明确标注。链接指向源码行或对应讲解文件。

---

# workspace_metadata ⭐⭐

**位置与等级**：[review_workspace.py:25](../../../src/workflow/review_workspace.py#L25)；局部辅助逻辑，需理解其调用条件与失败传播。

**签名**：`def workspace_metadata(directory: Path) -> dict[str, Any] | None`。

**作用**：处理 `workspace_metadata` 对应步骤；下列步骤依据函数体的实际控制流和调用点整理。

**输入与输出**：
- 输入：`directory`（Path）。
- 输出类型：`dict[str, Any] | None`；具体返回路径见流程步骤。

**处理流程**：
1. 更新 `path`，值来自 `directory / MARKER`。
2. 返回 `dict(orjson.loads(path.read_bytes())) if path.is_file() else None`。

**调用与被调用**：
- `path.is_file`（[review_workspace.py:27](../../../src/workflow/review_workspace.py#L27)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `dict`（[review_workspace.py:27](../../../src/workflow/review_workspace.py#L27)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `orjson.loads`（[review_workspace.py:27](../../../src/workflow/review_workspace.py#L27)）：来自 `orjson`；具体实现可能由依赖注入或运行时分派决定。
- `path.read_bytes`（[review_workspace.py:27](../../../src/workflow/review_workspace.py#L27)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- 静态可定位的调用方：[validate_workspace_run](review_workspace.md)、[PrismKEService.__init__](service.md)。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：未见 `raise`；下游异常可能继续上抛。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。
- 恢复/幂等性：仅在代码有检查点、事务、请求编号或显式去重时才成立；此函数不能单凭名称视为可安全重试。


---

# validate_workspace_run ⭐⭐⭐⭐

**位置与等级**：[review_workspace.py:30](../../../src/workflow/review_workspace.py#L30)；承担主要 Agent、应用服务或审核/执行入口，跨模块影响显著。

**签名**：`def validate_workspace_run(directory: Path, state: WorkflowState) -> None`。

**作用**：处理 `validate_workspace_run` 对应步骤；下列步骤依据函数体的实际控制流和调用点整理。

**输入与输出**：
- 输入：`directory`（Path）；`state`（WorkflowState；跨节点 WorkflowState；调用方须保持证据与状态一致）。
- 输出类型：`None`；具体返回路径见流程步骤。

**处理流程**：
1. 更新 `metadata`，值来自 `workspace_metadata(directory)`。
2. 检查 `metadata is None or not state.review_workspace or metadata['run_id'] != state.run_id`；按条件分流，else 分支不存在。
3. 检查 `provenance(state) != metadata['provenance']`；按条件分流，else 分支不存在。

**关键条件与保护**：
- [review_workspace.py:32](../../../src/workflow/review_workspace.py#L32)：`metadata is None or not state.review_workspace or metadata['run_id'] != state.run_id`，不满足时跳过本分支。
- [review_workspace.py:34](../../../src/workflow/review_workspace.py#L34)：`provenance(state) != metadata['provenance']`，不满足时跳过本分支。

**调用与被调用**：
- `workspace_metadata`（调用点 [review_workspace.py:31](../../../src/workflow/review_workspace.py#L31)）→ [workspace_metadata](review_workspace.md)，静态可定位。
- `ValueError`（[review_workspace.py:33](../../../src/workflow/review_workspace.py#L33)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `provenance`（调用点 [review_workspace.py:34](../../../src/workflow/review_workspace.py#L34)）→ [provenance](review_workspace.md)，静态可定位。
- 静态可定位的调用方：[PrismKEService.review_workflow](service.md)、[PrismKEService.review_tail_workflow](service.md)。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：`ValueError(<字符串常量>)`。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。
- 恢复/幂等性：仅在代码有检查点、事务、请求编号或显式去重时才成立；此函数不能单凭名称视为可安全重试。


---

# provenance ⭐⭐

**位置与等级**：[review_workspace.py:38](../../../src/workflow/review_workspace.py#L38)；局部辅助逻辑，需理解其调用条件与失败传播。

**签名**：`def provenance(state: WorkflowState) -> dict[str, Any]`。

**作用**：处理 `provenance` 对应步骤；下列步骤依据函数体的实际控制流和调用点整理。

**输入与输出**：
- 输入：`state`（WorkflowState；跨节点 WorkflowState；调用方须保持证据与状态一致）。
- 输出类型：`dict[str, Any]`；具体返回路径见流程步骤。

**处理流程**：
1. 返回 `{'pipeline': state.pipeline_version, 'entity_policy': state.entity_resolution_policy_version, 'llm': sta…`。

**调用与被调用**：
- `canonical_hash`（调用点 [review_workspace.py:47](../../../src/workflow/review_workspace.py#L47)）→ [canonical_hash](../core/ids.md)，静态可定位。
- `state.output_schema.model_dump`（[review_workspace.py:47](../../../src/workflow/review_workspace.py#L47)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- 静态可定位的调用方：[validate_workspace_run](review_workspace.md)、[import_review_run](review_workspace.md)。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：未见 `raise`；下游异常可能继续上抛。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。
- 恢复/幂等性：仅在代码有检查点、事务、请求编号或显式去重时才成立；此函数不能单凭名称视为可安全重试。


---

# import_review_run ⭐⭐⭐⭐

**位置与等级**：[review_workspace.py:53](../../../src/workflow/review_workspace.py#L53)；承担主要 Agent、应用服务或审核/执行入口，跨模块影响显著。

**签名**：`async def import_review_run(source: Path, run_id: str, target: Path) -> WorkflowState`。

**作用**：处理 `import_review_run` 对应步骤；下列步骤依据函数体的实际控制流和调用点整理。

**输入与输出**：
- 输入：`source`（Path）；`run_id`（str；目标运行的稳定标识）；`target`（Path）。
- 输出类型：`WorkflowState`；具体返回路径见流程步骤。

**处理流程**：
1. 更新 `(source, target)`，值来自 `(source.resolve(), target.resolve())`。
2. 检查 `source == target or source in target.parents or target in source.parents`；按条件分流，else 分支不存在。
3. 检查 `target.exists()`；按条件分流，else 分支不存在。
4. 检查 `not (source / 'runs').is_dir() or not (source / 'evidence' / 'refs').is_dir()`；按条件分流，else 分支不存在。
5. 更新 `original`，值来自 `RunRepository(source / 'runs').load(run_id)`。
6. 检查 `original.pipeline_version != PIPELINE_VERSION or original.entity_resolution_policy_version != ENTITY_RES…`；按条件分流，else 分支不存在。
7. 检查 `original.status != 'awaiting_review' or original.current_node not in {'resolve_entities', 'route_by_risk…`；按条件分流，else 分支不存在。
8. 检查 `original.document is None or original.output_schema is None`；按条件分流，else 分支不存在。
9. 检查 `any((not value or value == 'legacy' for value in (original.provider_fingerprint, original.vlm_provider_f…`；按条件分流，else 分支不存在。
10. 更新 `refs`，值来自 `{item.id: item for item in original.document.evidence}`。
11. 检查 `len(refs) != len(original.document.evidence)`；按条件分流，else 分支不存在。
12. 更新 `evidence`，值来自 `FileEvidenceStore(source / 'evidence')`。
13. 遍历 `refs.values()`，逐项处理 `ref`。
14. 遍历 `original.candidates`，逐项处理 `candidate`。
15. 检查 `document_coverage(original.model_dump(mode='json'))['invalid_bbox_ids']`；按条件分流，else 分支不存在。
16. 更新 `graph_path`，值来自 `source / 'graph' / 'graph.json'`。
17. 进入上下文 `FileLock(str(graph_path.parent / 'graph.lock'))`，由上下文管理器控制资源释放或事务范围。
18. 更新 `graph`，值来自 `orjson.loads(graph_bytes)`。
19. 更新 `entity_ids`，值来自 `set(graph['entities']) | {item.id for item in original.entities}`。
20. 遍历 `graph['entities'].values()`，逐项处理 `item`。
21. 遍历 `graph['evidence'].values()`，逐项处理 `item`。
22. 遍历 `graph['claims'].values()`，逐项处理 `item`。
23. 遍历 `graph['conflicts'].values()`，逐项处理 `item`。
24. 遍历 `original.entity_review_tasks`，逐项处理 `task`。
后续还有 3 个语句级步骤，见源码对应行；这里优先保留主要控制流。

**关键条件与保护**：
- [review_workspace.py:55](../../../src/workflow/review_workspace.py#L55)：`source == target or source in target.parents or target in source.parents`，不满足时跳过本分支。
- [review_workspace.py:57](../../../src/workflow/review_workspace.py#L57)：`target.exists()`，不满足时跳过本分支。
- [review_workspace.py:59](../../../src/workflow/review_workspace.py#L59)：`not (source / 'runs').is_dir() or not (source / 'evidence' / 'refs').is_dir()`，不满足时跳过本分支。
- [review_workspace.py:65](../../../src/workflow/review_workspace.py#L65)：`original.pipeline_version != PIPELINE_VERSION or original.entity_resolution_policy_version != ENTITY_RESOLUTION_PO…`，不满足时跳过本分支。
- [review_workspace.py:70](../../../src/workflow/review_workspace.py#L70)：`original.status != 'awaiting_review' or original.current_node not in {'resolve_entities', 'route_by_risk'}`，不满足时跳过本分支。
- [review_workspace.py:75](../../../src/workflow/review_workspace.py#L75)：`original.document is None or original.output_schema is None`，不满足时跳过本分支。
- [review_workspace.py:77](../../../src/workflow/review_workspace.py#L77)：`any((not value or value == 'legacy' for value in (original.provider_fingerprint, original.vlm_provider_fingerprint…`，不满足时跳过本分支。
- [review_workspace.py:88](../../../src/workflow/review_workspace.py#L88)：`len(refs) != len(original.document.evidence)`，不满足时跳过本分支。
- [review_workspace.py:92](../../../src/workflow/review_workspace.py#L92)：`not await evidence.verify(ref.id) or await evidence.get(ref.id) != ref`，不满足时跳过本分支。
- [review_workspace.py:95](../../../src/workflow/review_workspace.py#L95)：`not candidate.evidence_ids or not set(candidate.evidence_ids) <= refs.keys()`，不满足时跳过本分支。
- [review_workspace.py:99](../../../src/workflow/review_workspace.py#L99)：`document_coverage(original.model_dump(mode='json'))['invalid_bbox_ids']`，不满足时跳过本分支。
- [review_workspace.py:110](../../../src/workflow/review_workspace.py#L110)：`not await evidence.verify(ref.id)`，不满足时跳过本分支。
- 另有 10 个条件判断，参见源码；不要将本列表当作全部分支。

**调用与被调用**：
- `source.resolve`（[review_workspace.py:54](../../../src/workflow/review_workspace.py#L54)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `target.resolve`（[review_workspace.py:54](../../../src/workflow/review_workspace.py#L54)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `ValueError`（[review_workspace.py:56](../../../src/workflow/review_workspace.py#L56)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `target.exists`（[review_workspace.py:57](../../../src/workflow/review_workspace.py#L57)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `(source / 'runs').is_dir`（[review_workspace.py:59](../../../src/workflow/review_workspace.py#L59)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `(source / 'evidence' / 'refs').is_dir`（[review_workspace.py:59](../../../src/workflow/review_workspace.py#L59)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `RunRepository(source / 'runs').load`（[review_workspace.py:61](../../../src/workflow/review_workspace.py#L61)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `RunRepository`（[review_workspace.py:61](../../../src/workflow/review_workspace.py#L61)）：来自 `src.persistence.RunRepository`；具体实现可能由依赖注入或运行时分派决定。
- `any`（[review_workspace.py:77](../../../src/workflow/review_workspace.py#L77)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `len`（[review_workspace.py:88](../../../src/workflow/review_workspace.py#L88)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `FileEvidenceStore`（[review_workspace.py:90](../../../src/workflow/review_workspace.py#L90)）：来自 `src.persistence.FileEvidenceStore`；具体实现可能由依赖注入或运行时分派决定。
- `refs.values`（[review_workspace.py:91](../../../src/workflow/review_workspace.py#L91)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `evidence.verify`（[review_workspace.py:92](../../../src/workflow/review_workspace.py#L92)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `evidence.get`（[review_workspace.py:92](../../../src/workflow/review_workspace.py#L92)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `set`（[review_workspace.py:95](../../../src/workflow/review_workspace.py#L95)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `refs.keys`（[review_workspace.py:95](../../../src/workflow/review_workspace.py#L95)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `document_coverage`（调用点 [review_workspace.py:99](../../../src/workflow/review_workspace.py#L99)）→ [document_coverage](../evaluation/document_review.md)，静态可定位。
- `original.model_dump`（[review_workspace.py:99](../../../src/workflow/review_workspace.py#L99)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `FileLock`（[review_workspace.py:102](../../../src/workflow/review_workspace.py#L102)）：来自 `filelock.FileLock`；具体实现可能由依赖注入或运行时分派决定。
- `str`（[review_workspace.py:102](../../../src/workflow/review_workspace.py#L102)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `graph_path.read_bytes`（[review_workspace.py:103](../../../src/workflow/review_workspace.py#L103)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `orjson.loads`（[review_workspace.py:104](../../../src/workflow/review_workspace.py#L104)）：来自 `orjson`；具体实现可能由依赖注入或运行时分派决定。
- `graph['entities'].values`（[review_workspace.py:106](../../../src/workflow/review_workspace.py#L106)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `CanonicalEntity.model_validate`（[review_workspace.py:107](../../../src/workflow/review_workspace.py#L107)）：来自 `src.domain.CanonicalEntity`；具体实现可能由依赖注入或运行时分派决定。
- `graph['evidence'].values`（[review_workspace.py:108](../../../src/workflow/review_workspace.py#L108)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `EvidenceRef.model_validate`（[review_workspace.py:109](../../../src/workflow/review_workspace.py#L109)）：来自 `src.domain.EvidenceRef`；具体实现可能由依赖注入或运行时分派决定。
- `graph['claims'].values`（[review_workspace.py:112](../../../src/workflow/review_workspace.py#L112)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `Claim.model_validate`（[review_workspace.py:113](../../../src/workflow/review_workspace.py#L113)）：来自 `src.domain.Claim`；具体实现可能由依赖注入或运行时分派决定。
- `graph['evidence'].keys`（[review_workspace.py:117](../../../src/workflow/review_workspace.py#L117)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `graph['conflicts'].values`（[review_workspace.py:120](../../../src/workflow/review_workspace.py#L120)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- 此处列出前 30 个不同调用表达式，另有 49 个，需按源码继续追踪。
- 静态可定位的调用方：[import_review_run_command](../cli.md)。

**状态、副作用与异常**：
- 显式状态/容器赋值：`state.review_workspace`、`state.submission_confirmed`、`state.document.source_filename`、`state.document.source_path`、`state.input_path`、`asset.path`、`state.schema_path`。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：`ValueError(<字符串常量>)`、`ValueError(f<字符串常量>)`、`重新抛出`。
- 本地捕获：`Exception`。
- 恢复/幂等性：仅在代码有检查点、事务、请求编号或显式去重时才成立；此函数不能单凭名称视为可安全重试。


---
