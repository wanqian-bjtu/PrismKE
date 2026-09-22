源码：[graph.py:1](../../../src/workflow/graph.py#L1) | 基准：`dev/v0.10@f2f34d7` | 本文件符号数：23

**模块职责**：Persistent LangGraph execution and exact-node recovery.
**在系统中的位置**：应用服务、LangGraph 编排、执行状态、审核接续、图提交及纠正流程。
**阅读重点**：LangGraph 负责节点调度、并行分支汇合、审核暂停及检查点恢复；它不是自主决策 Agent。重点跟踪状态在节点间的复制、合并与异常传播。
**直接依赖**：[src.core.execution_control](../core/execution_control.md)、[src.domain](../domain/__init__.md)、[src.governance.validation](../governance/validation/__init__.md)、[src.parsing](../parsing/__init__.md)、[src.persistence.base](../persistence/base.md)、[src.persistence.checkpoints](../persistence/checkpoints.md)、[src.persistence.reviews](../persistence/reviews.md)、[src.persistence.runs](../persistence/runs.md)、[src.providers.base](../providers/base.md)、[src.workflow.nodes](nodes.md)、[src.workflow.reflection](reflection.md)；外部/标准库：`__future__`、`collections`、`langgraph`、`pathlib`、`typing`。
**主要调用方（静态导入）**：[workflow/__init__.py](__init__.md)、[workflow/review_workspace.py](review_workspace.md)、[workflow/service.py](service.md)。
**阅读提示**：下列流程根据当前源码控制流整理；`self`/接口对象的实际类型可能在运行时注入，未能静态解析的调用会明确标注。链接指向源码行或对应讲解文件。

## 核心路径解读

- 主图按 ingest→解析→视觉资产→OCR→证据→Schema 运行，然后文本和视觉分支并行，汇合后对齐、Reflection、实体解析、事实规范化、冲突检测、风险路由、提交准备和写图。
- 实体解析和风险路由都可条件到 END，表示停在人工审核边界；停止不等于提交。`_join_modalities` 要合并两个分支状态，避免一条分支覆盖另一条。
- 隔离审核图没有解析、OCR 或模型节点；`resolve_entities` 设置了禁止重新抽取的入口。提交准备后，只有明确确认的审核工作区才可进入 `commit_graph`。
- `resume` 与记录审核的方法围绕检查点的精确节点恢复；不可把旧协议或未确认状态直接推进到写图。

---

# GraphState ⭐⭐⭐⭐

**位置与等级**：[graph.py:30](../../../src/workflow/graph.py#L30)；承担主要 Agent、应用服务或审核/执行入口，跨模块影响显著。

**职责**：字典形态的结构化状态契约；字段存在性还受 total 和继承设置影响。基类：`TypedDict`。

**字段与类级约束**：
- `payload`：`dict[str, Any]`。
- `text_branch`：`dict[str, Any]`。
- `visual_branch`：`dict[str, Any]`。

**内部成员**：此类未直接定义方法；字段/继承行为见源码。


---

# PrismKEWorkflow ⭐⭐⭐⭐

**位置与等级**：[graph.py:39](../../../src/workflow/graph.py#L39)；承担主要 Agent、应用服务或审核/执行入口，跨模块影响显著。

**职责**：本模块的对象实现或数据契约；具体语义由字段、基类和方法共同决定。基类：无显式基类。

**字段与类级约束**：
- 类体未直接声明字段；实例状态请看 `__init__` 及方法中的赋值。

**内部成员**：`PrismKEWorkflow.__init__`、`PrismKEWorkflow._state`、`PrismKEWorkflow._record_provider_failure`、`PrismKEWorkflow._node`、`PrismKEWorkflow._branch_node`、`PrismKEWorkflow._join_modalities`、`PrismKEWorkflow._after_risk`、`PrismKEWorkflow._after_entity_resolution`、`PrismKEWorkflow._build_graph`、`PrismKEWorkflow._build_review_graph`、`PrismKEWorkflow.confirm_submission`、`PrismKEWorkflow._config`、`PrismKEWorkflow.invoke`、`PrismKEWorkflow.execution_snapshot`、`PrismKEWorkflow.resume`、`PrismKEWorkflow.record_review`、`PrismKEWorkflow.record_entity_review`、`PrismKEWorkflow.record_completed_review`


---

# PrismKEWorkflow.__init__ ⭐⭐

**位置与等级**：[graph.py:40](../../../src/workflow/graph.py#L40)；局部辅助逻辑，需理解其调用条件与失败传播。

**签名**：`def __init__(self, provider: LLMProvider, ocr_provider: OCRProvider, vlm_provider: VLMProvider, graph_store: GraphStore, evidence_store: EvidenceStore, checkpoint_path: Path, runs: RunRepository, parsers: ParserRegistry | None=None, *, embedding_provider: EmbeddingProvider | None=None, entity_top_k: int=10, entity_auto_link_threshold: float=0.88, entity_review_threshold: float=0.65, entity_min_margin: float=0.08, review_only: bool=False, reflection_service: BoundedReflectionService | None=None, semantic_advisor: SemanticAdvisor | None=None) -> None`。

**作用**：初始化对象并保存依赖或配置；需检查是否创建持久化资源。

**输入与输出**：
- 输入：`provider`（LLMProvider）；`ocr_provider`（OCRProvider）；`vlm_provider`（VLMProvider）；`graph_store`（GraphStore；图持久化接口，具体实现由配置注入）；`evidence_store`（EvidenceStore；证据元数据和原始内容的存储接口）；`checkpoint_path`（Path）；`runs`（RunRepository）；`parsers`（ParserRegistry | None；默认 `None`）；`embedding_provider`（EmbeddingProvider | None；默认 `None`）；`entity_top_k`（int；默认 `10`）；`entity_auto_link_threshold`（float；默认 `0.88`）；`entity_review_threshold`（float；默认 `0.65`）；`entity_min_margin`（float；默认 `0.08`）；`review_only`（bool；默认 `False`）；`reflection_service`（BoundedReflectionService | None；默认 `None`）；`semantic_advisor`（SemanticAdvisor | None；默认 `None`）。
- 输出类型：`None`；具体返回路径见流程步骤。

**处理流程**：
1. 更新 `self.checkpoint_path`，值来自 `checkpoint_path`。
2. 更新 `self.runs`，值来自 `runs`。
3. 更新 `self.reviews`，值来自 `ReviewRepository(runs.directory.parent / 'reviews.sqlite')`。
4. 更新 `self.review_only`，值来自 `review_only`。
5. 检查 `isinstance(graph_store, (JSONGraphStore, Neo4jGraphStore))`；按条件分流，else 分支不存在。
6. 更新 `self.nodes`，值来自 `WorkflowNodes(provider, ocr_provider, vlm_provider, graph_store, evidence_store, parsers or ParserR…`。
7. 更新 `self.nodes.review_repository`，值来自 `self.reviews`。

**关键条件与保护**：
- [graph.py:67](../../../src/workflow/graph.py#L67)：`isinstance(graph_store, (JSONGraphStore, Neo4jGraphStore))`，不满足时跳过本分支。

**调用与被调用**：
- `ReviewRepository`（调用点 [graph.py:62](../../../src/workflow/graph.py#L62)）→ [ReviewRepository](../persistence/reviews.md)，静态可定位。
- `isinstance`（[graph.py:67](../../../src/workflow/graph.py#L67)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `WorkflowNodes`（调用点 [graph.py:69](../../../src/workflow/graph.py#L69)）→ [WorkflowNodes](nodes.md)，静态可定位。
- `ParserRegistry`（[graph.py:75](../../../src/workflow/graph.py#L75)）：来自 `src.parsing.ParserRegistry`；具体实现可能由依赖注入或运行时分派决定。
- 静态扫描未定位直接调用方；可能通过路由注册、LangGraph 节点、协议方法或依赖注入动态调用，不据此判断为死代码。

**状态、副作用与异常**：
- 显式状态/容器赋值：`self.checkpoint_path`、`self.runs`、`self.reviews`、`self.review_only`、`graph_store.evidence_store`、`self.nodes`、`self.nodes.review_repository`。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：未见 `raise`；下游异常可能继续上抛。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。
- 恢复/幂等性：仅在代码有检查点、事务、请求编号或显式去重时才成立；此函数不能单凭名称视为可安全重试。


---

# PrismKEWorkflow._state ⭐⭐

**位置与等级**：[graph.py:87](../../../src/workflow/graph.py#L87)；局部辅助逻辑，需理解其调用条件与失败传播。

**签名**：`def _state(graph_state: GraphState) -> WorkflowState`。

**装饰器/路由**：`staticmethod`。

**作用**：内部辅助步骤；将参数转换为本模块所需的中间对象或操作结果。

**输入与输出**：
- 输入：`graph_state`（GraphState）。
- 输出类型：`WorkflowState`；具体返回路径见流程步骤。

**处理流程**：
1. 返回 `WorkflowState.model_validate(graph_state['payload'])`。

**调用与被调用**：
- `WorkflowState.model_validate`（[graph.py:88](../../../src/workflow/graph.py#L88)）：来自 `src.domain.WorkflowState`；具体实现可能由依赖注入或运行时分派决定。
- 静态可定位的调用方：[PrismKEWorkflow._node.wrapped](graph.md)、[PrismKEWorkflow._branch_node.wrapped](graph.md)、[PrismKEWorkflow._join_modalities](graph.md)、[PrismKEWorkflow.confirm_submission](graph.md)、[PrismKEWorkflow.invoke](graph.md)、[PrismKEWorkflow.resume](graph.md)。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：未见 `raise`；下游异常可能继续上抛。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。
- 恢复/幂等性：仅在代码有检查点、事务、请求编号或显式去重时才成立；此函数不能单凭名称视为可安全重试。


---

# PrismKEWorkflow._record_provider_failure ⭐⭐

**位置与等级**：[graph.py:91](../../../src/workflow/graph.py#L91)；局部辅助逻辑，需理解其调用条件与失败传播。

**签名**：`def _record_provider_failure(state: WorkflowState, exc: Exception) -> None`。

**装饰器/路由**：`staticmethod`。

**作用**：内部辅助步骤；将参数转换为本模块所需的中间对象或操作结果。

**输入与输出**：
- 输入：`state`（WorkflowState；跨节点 WorkflowState；调用方须保持证据与状态一致）；`exc`（Exception）。
- 输出类型：`None`；具体返回路径见流程步骤。

**处理流程**：
1. 更新 `records`，值来自 `getattr(exc, 'call_records', None)`。
2. 检查 `records is None`；按条件分流，else 分支不存在。
3. 更新 `known`，值来自 `{item.id for item in state.provider_calls}`。
4. 调用 `state.provider_calls.extend`，结果未直接赋值。

**关键条件与保护**：
- [graph.py:93](../../../src/workflow/graph.py#L93)：`records is None`，不满足时跳过本分支。

**调用与被调用**：
- `getattr`（[graph.py:92](../../../src/workflow/graph.py#L92)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `state.provider_calls.extend`（[graph.py:97](../../../src/workflow/graph.py#L97)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- 静态可定位的调用方：[PrismKEWorkflow._node.wrapped](graph.md)、[PrismKEWorkflow._branch_node.wrapped](graph.md)。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：未见 `raise`；下游异常可能继续上抛。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。
- 恢复/幂等性：仅在代码有检查点、事务、请求编号或显式去重时才成立；此函数不能单凭名称视为可安全重试。


---

# PrismKEWorkflow._node ⭐⭐⭐⭐⭐

**位置与等级**：[graph.py:99](../../../src/workflow/graph.py#L99)；位于工作流推进、硬校验或原子事务的关键边界；错误可能影响审核停顿或图状态。

**签名**：`def _node(self, name: str, handler: Callable[[WorkflowState], Awaitable[WorkflowState]]) -> Node`。

**作用**：内部辅助步骤；将参数转换为本模块所需的中间对象或操作结果。

**输入与输出**：
- 输入：`name`（str）；`handler`（Callable[[WorkflowState], Awaitable[WorkflowState]]）。
- 输出类型：`Node`；具体返回路径见流程步骤。

**处理流程**：
1. 返回 `wrapped`。

**调用与被调用**：
- 无显式函数调用，或仅声明协议/常量。
- 静态可定位的调用方：[PrismKEWorkflow._build_graph](graph.md)、[PrismKEWorkflow._build_review_graph](graph.md)。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：未见 `raise`；下游异常可能继续上抛。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。
- 恢复/幂等性：仅在代码有检查点、事务、请求编号或显式去重时才成立；此函数不能单凭名称视为可安全重试。


---

# PrismKEWorkflow._node.wrapped ⭐⭐⭐⭐⭐

**位置与等级**：[graph.py:104](../../../src/workflow/graph.py#L104)；位于工作流推进、硬校验或原子事务的关键边界；错误可能影响审核停顿或图状态。

**签名**：`async def wrapped(graph_state: GraphState) -> GraphState`。

**作用**：处理 `wrapped` 对应步骤；下列步骤依据函数体的实际控制流和调用点整理。

**输入与输出**：
- 输入：`graph_state`（GraphState）。
- 输出类型：`GraphState`；具体返回路径见流程步骤。

**处理流程**：
1. 更新 `state`，值来自 `self._state(graph_state)`。
2. 捕获 ExecutionPaused, Exception；另检查 finally/else 的清理和传播。
3. 更新 `state.current_node`，值来自 `name`。
4. 更新 `state.failed_node`，值来自 `None`。
5. 调用 `self.runs.save`，结果未直接赋值。
6. 返回 `{'payload': state.model_dump(mode='json')}`。

**关键条件与保护**：
- [graph.py:108](../../../src/workflow/graph.py#L108)：`control`，不满足时跳过本分支。

**调用与被调用**：
- `self._state`（调用点 [graph.py:105](../../../src/workflow/graph.py#L105)）→ [PrismKEWorkflow._state](graph.md)，静态可定位。
- `current_execution.get`（[graph.py:107](../../../src/workflow/graph.py#L107)）：来自 `src.core.execution_control.current_execution`；具体实现可能由依赖注入或运行时分派决定。
- `control.node`（[graph.py:109](../../../src/workflow/graph.py#L109)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `handler`（[graph.py:110](../../../src/workflow/graph.py#L110)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `self._record_provider_failure`（调用点 [graph.py:114](../../../src/workflow/graph.py#L114)）→ [PrismKEWorkflow._record_provider_failure](graph.md)，静态可定位。
- `state.errors.append`（[graph.py:119](../../../src/workflow/graph.py#L119)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `type`（[graph.py:119](../../../src/workflow/graph.py#L119)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `self.runs.save`（[graph.py:120](../../../src/workflow/graph.py#L120)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `state.model_dump`（[graph.py:125](../../../src/workflow/graph.py#L125)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- 静态扫描未定位直接调用方；可能通过路由注册、LangGraph 节点、协议方法或依赖注入动态调用，不据此判断为死代码。

**状态、副作用与异常**：
- 显式状态/容器赋值：`state.status`、`state.failed_node`、`state.current_node`、`state.retry_count`。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：`重新抛出`。
- 本地捕获：`ExecutionPaused`、`Exception`。
- 恢复/幂等性：仅在代码有检查点、事务、请求编号或显式去重时才成立；此函数不能单凭名称视为可安全重试。


---

# PrismKEWorkflow._branch_node ⭐⭐⭐⭐⭐

**位置与等级**：[graph.py:129](../../../src/workflow/graph.py#L129)；位于工作流推进、硬校验或原子事务的关键边界；错误可能影响审核停顿或图状态。

**签名**：`def _branch_node(self, name: str, output_key: str, handler: Callable[[WorkflowState], Awaitable[WorkflowState]]) -> Node`。

**作用**：内部辅助步骤；将参数转换为本模块所需的中间对象或操作结果。

**输入与输出**：
- 输入：`name`（str）；`output_key`（str）；`handler`（Callable[[WorkflowState], Awaitable[WorkflowState]]）。
- 输出类型：`Node`；具体返回路径见流程步骤。

**处理流程**：
1. 返回 `wrapped`。

**调用与被调用**：
- 无显式函数调用，或仅声明协议/常量。
- 静态可定位的调用方：[PrismKEWorkflow._build_graph](graph.md)。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：未见 `raise`；下游异常可能继续上抛。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。
- 恢复/幂等性：仅在代码有检查点、事务、请求编号或显式去重时才成立；此函数不能单凭名称视为可安全重试。


---

# PrismKEWorkflow._branch_node.wrapped ⭐⭐⭐⭐⭐

**位置与等级**：[graph.py:135](../../../src/workflow/graph.py#L135)；位于工作流推进、硬校验或原子事务的关键边界；错误可能影响审核停顿或图状态。

**签名**：`async def wrapped(graph_state: GraphState) -> GraphState`。

**作用**：处理 `wrapped` 对应步骤；下列步骤依据函数体的实际控制流和调用点整理。

**输入与输出**：
- 输入：`graph_state`（GraphState）。
- 输出类型：`GraphState`；具体返回路径见流程步骤。

**处理流程**：
1. 更新 `state`，值来自 `self._state(graph_state).model_copy(deep=True)`。
2. 捕获 ExecutionPaused, Exception；另检查 finally/else 的清理和传播。
3. 返回 `cast(GraphState, {output_key: state.model_dump(mode='json')})`。

**关键条件与保护**：
- [graph.py:139](../../../src/workflow/graph.py#L139)：`control`，不满足时跳过本分支。

**调用与被调用**：
- `self._state(graph_state).model_copy`（[graph.py:136](../../../src/workflow/graph.py#L136)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `self._state`（调用点 [graph.py:136](../../../src/workflow/graph.py#L136)）→ [PrismKEWorkflow._state](graph.md)，静态可定位。
- `current_execution.get`（[graph.py:138](../../../src/workflow/graph.py#L138)）：来自 `src.core.execution_control.current_execution`；具体实现可能由依赖注入或运行时分派决定。
- `control.node`（[graph.py:140](../../../src/workflow/graph.py#L140)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `handler`（[graph.py:141](../../../src/workflow/graph.py#L141)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `self._record_provider_failure`（调用点 [graph.py:145](../../../src/workflow/graph.py#L145)）→ [PrismKEWorkflow._record_provider_failure](graph.md)，静态可定位。
- `state.errors.append`（[graph.py:150](../../../src/workflow/graph.py#L150)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `type`（[graph.py:150](../../../src/workflow/graph.py#L150)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `self.runs.save`（[graph.py:151](../../../src/workflow/graph.py#L151)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `cast`（[graph.py:153](../../../src/workflow/graph.py#L153)）：来自 `typing.cast`；具体实现可能由依赖注入或运行时分派决定。
- `state.model_dump`（[graph.py:153](../../../src/workflow/graph.py#L153)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- 静态扫描未定位直接调用方；可能通过路由注册、LangGraph 节点、协议方法或依赖注入动态调用，不据此判断为死代码。

**状态、副作用与异常**：
- 显式状态/容器赋值：`state.status`、`state.failed_node`、`state.current_node`、`state.retry_count`。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：`重新抛出`。
- 本地捕获：`ExecutionPaused`、`Exception`。
- 恢复/幂等性：仅在代码有检查点、事务、请求编号或显式去重时才成立；此函数不能单凭名称视为可安全重试。


---

# PrismKEWorkflow._join_modalities ⭐⭐⭐⭐⭐

**位置与等级**：[graph.py:157](../../../src/workflow/graph.py#L157)；位于工作流推进、硬校验或原子事务的关键边界；错误可能影响审核停顿或图状态。

**签名**：`async def _join_modalities(self, graph_state: GraphState) -> GraphState`。

**作用**：内部辅助步骤；将参数转换为本模块所需的中间对象或操作结果。

**输入与输出**：
- 输入：`graph_state`（GraphState）。
- 输出类型：`GraphState`；具体返回路径见流程步骤。

**处理流程**：
1. 更新 `state`，值来自 `self._state(graph_state)`。
2. 更新 `text_state`，值来自 `WorkflowState.model_validate(graph_state['text_branch'])`。
3. 更新 `visual_state`，值来自 `WorkflowState.model_validate(graph_state['visual_branch'])`。
4. 更新 `state.text_candidates`，值来自 `text_state.text_candidates`。
5. 更新 `state.visual_candidates`，值来自 `visual_state.visual_candidates`。
6. 更新 `state.modality_status`，值来自 `{**state.modality_status, **text_state.modality_status, **visual_state.modality_status}`。
7. 更新 `state.modality_errors`，值来自 `{**state.modality_errors, **text_state.modality_errors, **visual_state.modality_errors}`。
8. 更新 `traces`，值来自 `[*state.agent_traces, *text_state.agent_traces, *visual_state.agent_traces]`。
9. 更新 `state.agent_traces`，值来自 `list({item.id: item for item in traces}.values())`。
10. 更新 `state.document`，值来自 `visual_state.document`。
11. 更新 `state.validation`，值来自 `ValidationService.merge(state.validation, [*text_state.validation.issues, *visual_state.validation.…`。
12. 更新 `calls`，值来自 `[*state.provider_calls, *text_state.provider_calls, *visual_state.provider_calls]`。
13. 更新 `state.provider_calls`，值来自 `list({item.id: item for item in calls}.values())`。
14. 更新 `state.warnings`，值来自 `list(dict.fromkeys([*state.warnings, *text_state.warnings, *visual_state.warnings]))`。
15. 捕获 ExecutionPaused, Exception；另检查 finally/else 的清理和传播。
16. 更新 `state.current_node`，值来自 `'align_modalities'`。
17. 更新 `state.failed_node`，值来自 `None`。
18. 更新 `state.original_candidates`，值来自 `[c.model_copy(deep=True) for c in state.candidates]`。
19. 调用 `self.reviews.archive`，结果未直接赋值。
20. 调用 `self.runs.save`，结果未直接赋值。
21. 返回 `{'payload': state.model_dump(mode='json')}`。

**关键条件与保护**：
- [graph.py:190](../../../src/workflow/graph.py#L190)：`control`，不满足时跳过本分支。

**调用与被调用**：
- `self._state`（调用点 [graph.py:158](../../../src/workflow/graph.py#L158)）→ [PrismKEWorkflow._state](graph.md)，静态可定位。
- `WorkflowState.model_validate`（[graph.py:159](../../../src/workflow/graph.py#L159)）：来自 `src.domain.WorkflowState`；具体实现可能由依赖注入或运行时分派决定。
- `list`（[graph.py:174](../../../src/workflow/graph.py#L174)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `{item.id: item for item in traces}.values`（[graph.py:174](../../../src/workflow/graph.py#L174)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `ValidationService.merge`（[graph.py:176](../../../src/workflow/graph.py#L176)）：来自 `src.governance.validation.ValidationService`；具体实现可能由依赖注入或运行时分派决定。
- `{item.id: item for item in calls}.values`（[graph.py:184](../../../src/workflow/graph.py#L184)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `dict.fromkeys`（[graph.py:186](../../../src/workflow/graph.py#L186)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `current_execution.get`（[graph.py:189](../../../src/workflow/graph.py#L189)）：来自 `src.core.execution_control.current_execution`；具体实现可能由依赖注入或运行时分派决定。
- `control.node`（[graph.py:191](../../../src/workflow/graph.py#L191)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `self.nodes.align_modalities`（[graph.py:192](../../../src/workflow/graph.py#L192)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `state.errors.append`（[graph.py:200](../../../src/workflow/graph.py#L200)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `type`（[graph.py:200](../../../src/workflow/graph.py#L200)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `self.runs.save`（[graph.py:201](../../../src/workflow/graph.py#L201)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `c.model_copy`（[graph.py:205](../../../src/workflow/graph.py#L205)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `self.reviews.archive`（[graph.py:206](../../../src/workflow/graph.py#L206)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `c.model_dump`（[graph.py:206](../../../src/workflow/graph.py#L206)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `state.model_dump`（[graph.py:208](../../../src/workflow/graph.py#L208)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- 静态扫描未定位直接调用方；可能通过路由注册、LangGraph 节点、协议方法或依赖注入动态调用，不据此判断为死代码。

**状态、副作用与异常**：
- 显式状态/容器赋值：`state.text_candidates`、`state.visual_candidates`、`state.modality_status`、`state.modality_errors`、`state.agent_traces`、`state.document`、`state.validation`、`state.provider_calls`、`state.warnings`、`state.status`、`state.failed_node`、`state.current_node`。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：`重新抛出`。
- 本地捕获：`ExecutionPaused`、`Exception`。
- 恢复/幂等性：仅在代码有检查点、事务、请求编号或显式去重时才成立；此函数不能单凭名称视为可安全重试。


---

# PrismKEWorkflow._after_risk ⭐⭐

**位置与等级**：[graph.py:211](../../../src/workflow/graph.py#L211)；局部辅助逻辑，需理解其调用条件与失败传播。

**签名**：`def _after_risk(graph_state: GraphState) -> str`。

**装饰器/路由**：`staticmethod`。

**作用**：内部辅助步骤；将参数转换为本模块所需的中间对象或操作结果。

**输入与输出**：
- 输入：`graph_state`（GraphState）。
- 输出类型：`str`；具体返回路径见流程步骤。

**处理流程**：
1. 更新 `state`，值来自 `PrismKEWorkflow._state(graph_state)`。
2. 返回 `'review' if state.status == 'awaiting_review' else 'continue'`。

**调用与被调用**：
- `PrismKEWorkflow._state`（[graph.py:212](../../../src/workflow/graph.py#L212)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- 静态扫描未定位直接调用方；可能通过路由注册、LangGraph 节点、协议方法或依赖注入动态调用，不据此判断为死代码。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：未见 `raise`；下游异常可能继续上抛。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。
- 恢复/幂等性：仅在代码有检查点、事务、请求编号或显式去重时才成立；此函数不能单凭名称视为可安全重试。


---

# PrismKEWorkflow._after_entity_resolution ⭐⭐

**位置与等级**：[graph.py:216](../../../src/workflow/graph.py#L216)；局部辅助逻辑，需理解其调用条件与失败传播。

**签名**：`def _after_entity_resolution(graph_state: GraphState) -> str`。

**装饰器/路由**：`staticmethod`。

**作用**：内部辅助步骤；将参数转换为本模块所需的中间对象或操作结果。

**输入与输出**：
- 输入：`graph_state`（GraphState）。
- 输出类型：`str`；具体返回路径见流程步骤。

**处理流程**：
1. 更新 `state`，值来自 `PrismKEWorkflow._state(graph_state)`。
2. 返回 `'review' if state.status == 'awaiting_review' else 'continue'`。

**调用与被调用**：
- `PrismKEWorkflow._state`（[graph.py:217](../../../src/workflow/graph.py#L217)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- 静态扫描未定位直接调用方；可能通过路由注册、LangGraph 节点、协议方法或依赖注入动态调用，不据此判断为死代码。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：未见 `raise`；下游异常可能继续上抛。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。
- 恢复/幂等性：仅在代码有检查点、事务、请求编号或显式去重时才成立；此函数不能单凭名称视为可安全重试。


---

# PrismKEWorkflow._build_graph ⭐⭐⭐⭐⭐

**位置与等级**：[graph.py:220](../../../src/workflow/graph.py#L220)；位于工作流推进、硬校验或原子事务的关键边界；错误可能影响审核停顿或图状态。

**签名**：`def _build_graph(self, checkpointer: Any) -> Any`。

**作用**：内部辅助步骤；将参数转换为本模块所需的中间对象或操作结果。

**输入与输出**：
- 输入：`checkpointer`（Any）。
- 输出类型：`Any`；具体返回路径见流程步骤。

**处理流程**：
1. 检查 `self.review_only`；按条件分流，else 分支不存在。
2. 更新 `builder`，值来自 `StateGraph(GraphState)`。
3. 更新 `before_extraction`，值来自 `[('ingest', self.nodes.ingest), ('parse_document', self.nodes.parse_document), ('materialize_visual…`。
4. 更新 `after_resolution`，值来自 `[('normalize_claims', self.nodes.normalize_claims), ('detect_conflicts', self.nodes.detect_conflict…`。
5. 遍历 `[*before_extraction, *after_resolution]`，逐项处理 `(name, handler)`。
6. 调用 `builder.add_node`，结果未直接赋值。
7. 调用 `builder.add_node`，结果未直接赋值。
8. 调用 `builder.add_node`，结果未直接赋值。
9. 调用 `builder.add_node`，结果未直接赋值。
10. 调用 `builder.add_node`，结果未直接赋值。
11. 调用 `builder.add_node`，结果未直接赋值。
12. 调用 `builder.add_node`，结果未直接赋值。
13. 调用 `builder.add_edge`，结果未直接赋值。
14. 遍历 `zip(before_extraction, before_extraction[1:], strict=False)`，逐项处理 `((left, _), (right, _))`。
15. 调用 `builder.add_edge`，结果未直接赋值。
16. 调用 `builder.add_edge`，结果未直接赋值。
17. 调用 `builder.add_edge`，结果未直接赋值。
18. 调用 `builder.add_edge`，结果未直接赋值。
19. 调用 `builder.add_edge`，结果未直接赋值。
20. 调用 `builder.add_conditional_edges`，结果未直接赋值。
21. 遍历 `zip(after_resolution, after_resolution[1:], strict=False)`，逐项处理 `((left, _), (right, _))`。
22. 调用 `builder.add_conditional_edges`，结果未直接赋值。
23. 调用 `builder.add_edge`，结果未直接赋值。
24. 调用 `builder.add_edge`，结果未直接赋值。
后续还有 1 个语句级步骤，见源码对应行；这里优先保留主要控制流。

**关键条件与保护**：
- [graph.py:221](../../../src/workflow/graph.py#L221)：`self.review_only`，不满足时跳过本分支。

**调用与被调用**：
- `self._build_review_graph`（调用点 [graph.py:222](../../../src/workflow/graph.py#L222)）→ [PrismKEWorkflow._build_review_graph](graph.md)，静态可定位。
- `StateGraph`（[graph.py:223](../../../src/workflow/graph.py#L223)）：来自 `langgraph.graph.StateGraph`；具体实现可能由依赖注入或运行时分派决定。
- `builder.add_node`（[graph.py:238](../../../src/workflow/graph.py#L238)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `cast`（[graph.py:238](../../../src/workflow/graph.py#L238)）：来自 `typing.cast`；具体实现可能由依赖注入或运行时分派决定。
- `self._node`（调用点 [graph.py:238](../../../src/workflow/graph.py#L238)）→ [PrismKEWorkflow._node](graph.md)，静态可定位。
- `self._branch_node`（调用点 [graph.py:247](../../../src/workflow/graph.py#L247)）→ [PrismKEWorkflow._branch_node](graph.md)，静态可定位。
- `builder.add_edge`（[graph.py:275](../../../src/workflow/graph.py#L275)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `zip`（[graph.py:276](../../../src/workflow/graph.py#L276)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `builder.add_conditional_edges`（[graph.py:283](../../../src/workflow/graph.py#L283)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `builder.compile`（[graph.py:297](../../../src/workflow/graph.py#L297)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- 静态可定位的调用方：[PrismKEWorkflow.confirm_submission](graph.md)、[PrismKEWorkflow.invoke](graph.md)、[PrismKEWorkflow.execution_snapshot](graph.md)、[PrismKEWorkflow.resume](graph.md)、[PrismKEWorkflow.record_review](graph.md)、[PrismKEWorkflow.record_entity_review](graph.md)、[PrismKEWorkflow.record_completed_review](graph.md)。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：未见 `raise`；下游异常可能继续上抛。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。
- 恢复/幂等性：仅在代码有检查点、事务、请求编号或显式去重时才成立；此函数不能单凭名称视为可安全重试。


---

# PrismKEWorkflow._build_review_graph ⭐⭐

**位置与等级**：[graph.py:299](../../../src/workflow/graph.py#L299)；局部辅助逻辑，需理解其调用条件与失败传播。

**签名**：`def _build_review_graph(self, checkpointer: Any) -> Any`。

**作用**：A tail-only graph: no parser, OCR, model or entity retrieval nodes exist.

**输入与输出**：
- 输入：`checkpointer`（Any）。
- 输出类型：`Any`；具体返回路径见流程步骤。

**处理流程**：
1. 更新 `builder`，值来自 `StateGraph(GraphState)`。
2. 调用 `builder.add_node`，结果未直接赋值。
3. 遍历 `('normalize_claims', 'detect_conflicts', 'route_by_risk', 'prepare_graph_commit', 'c…`，逐项处理 `name`。
4. 调用 `builder.add_edge`，结果未直接赋值。
5. 调用 `builder.add_conditional_edges`，结果未直接赋值。
6. 调用 `builder.add_edge`，结果未直接赋值。
7. 调用 `builder.add_edge`，结果未直接赋值。
8. 调用 `builder.add_conditional_edges`，结果未直接赋值。
9. 调用 `builder.add_conditional_edges`，结果未直接赋值。
10. 调用 `builder.add_edge`，结果未直接赋值。
11. 返回 `builder.compile(checkpointer=checkpointer)`。

**调用与被调用**：
- `StateGraph`（[graph.py:301](../../../src/workflow/graph.py#L301)）：来自 `langgraph.graph.StateGraph`；具体实现可能由依赖注入或运行时分派决定。
- `builder.add_node`（[graph.py:306](../../../src/workflow/graph.py#L306)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `cast`（[graph.py:306](../../../src/workflow/graph.py#L306)）：来自 `typing.cast`；具体实现可能由依赖注入或运行时分派决定。
- `self._node`（调用点 [graph.py:314](../../../src/workflow/graph.py#L314)）→ [PrismKEWorkflow._node](graph.md)，静态可定位。
- `getattr`（[graph.py:314](../../../src/workflow/graph.py#L314)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `builder.add_edge`（[graph.py:315](../../../src/workflow/graph.py#L315)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `builder.add_conditional_edges`（[graph.py:316](../../../src/workflow/graph.py#L316)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `builder.compile`（[graph.py:344](../../../src/workflow/graph.py#L344)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- 静态可定位的调用方：[PrismKEWorkflow._build_graph](graph.md)。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：未见 `raise`；下游异常可能继续上抛。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。
- 恢复/幂等性：仅在代码有检查点、事务、请求编号或显式去重时才成立；此函数不能单凭名称视为可安全重试。


---

# PrismKEWorkflow._build_review_graph.forbidden ⭐⭐⭐⭐

**位置与等级**：[graph.py:303](../../../src/workflow/graph.py#L303)；承担主要 Agent、应用服务或审核/执行入口，跨模块影响显著。

**签名**：`async def forbidden(_: GraphState) -> GraphState`。

**作用**：处理 `forbidden` 对应步骤；下列步骤依据函数体的实际控制流和调用点整理。

**输入与输出**：
- 输入：`_`（GraphState）。
- 输出类型：`GraphState`；具体返回路径见流程步骤。

**处理流程**：
1. 抛出 `ValueError(<字符串常量>)`。

**调用与被调用**：
- `ValueError`（[graph.py:304](../../../src/workflow/graph.py#L304)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- 静态扫描未定位直接调用方；可能通过路由注册、LangGraph 节点、协议方法或依赖注入动态调用，不据此判断为死代码。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：`ValueError(<字符串常量>)`。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。
- 恢复/幂等性：仅在代码有检查点、事务、请求编号或显式去重时才成立；此函数不能单凭名称视为可安全重试。


---

# PrismKEWorkflow.confirm_submission ⭐⭐

**位置与等级**：[graph.py:346](../../../src/workflow/graph.py#L346)；局部辅助逻辑，需理解其调用条件与失败传播。

**签名**：`async def confirm_submission(self, state: WorkflowState) -> WorkflowState`。

**作用**：处理 `confirm_submission` 对应步骤；下列步骤依据函数体的实际控制流和调用点整理。

**输入与输出**：
- 输入：`state`（WorkflowState；跨节点 WorkflowState；调用方须保持证据与状态一致）。
- 输出类型：`WorkflowState`；具体返回路径见流程步骤。

**处理流程**：
1. 更新 `retry_commit`，值来自 `state.status == 'failed' and state.failed_node == 'commit_graph'`。
2. 检查 `not self.review_only or (state.current_node != 'prepare_graph_commit' and (not retry_commit))`；按条件分流，else 分支不存在。
3. 更新 `state.submission_confirmed`，值来自 `True`。
4. 进入上下文 `open_checkpointer(self.checkpoint_path)`，由上下文管理器控制资源释放或事务范围。
5. 返回 `self._state(cast(GraphState, result))`。

**关键条件与保护**：
- [graph.py:348](../../../src/workflow/graph.py#L348)：`not self.review_only or (state.current_node != 'prepare_graph_commit' and (not retry_commit))`，不满足时跳过本分支。

**调用与被调用**：
- `ValueError`（[graph.py:351](../../../src/workflow/graph.py#L351)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `open_checkpointer`（调用点 [graph.py:353](../../../src/workflow/graph.py#L353)）→ [open_checkpointer](../persistence/checkpoints.md)，静态可定位。
- `self._build_graph`（调用点 [graph.py:354](../../../src/workflow/graph.py#L354)）→ [PrismKEWorkflow._build_graph](graph.md)，静态可定位。
- `self._config`（调用点 [graph.py:355](../../../src/workflow/graph.py#L355)）→ [PrismKEWorkflow._config](graph.md)，静态可定位。
- `graph.aupdate_state`（[graph.py:356](../../../src/workflow/graph.py#L356)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `state.model_dump`（[graph.py:358](../../../src/workflow/graph.py#L358)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `graph.ainvoke`（[graph.py:361](../../../src/workflow/graph.py#L361)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `self._state`（调用点 [graph.py:362](../../../src/workflow/graph.py#L362)）→ [PrismKEWorkflow._state](graph.md)，静态可定位。
- `cast`（[graph.py:362](../../../src/workflow/graph.py#L362)）：来自 `typing.cast`；具体实现可能由依赖注入或运行时分派决定。
- 静态扫描未定位直接调用方；可能通过路由注册、LangGraph 节点、协议方法或依赖注入动态调用，不据此判断为死代码。

**状态、副作用与异常**：
- 显式状态/容器赋值：`state.submission_confirmed`。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：`ValueError(<字符串常量>)`。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。
- 恢复/幂等性：仅在代码有检查点、事务、请求编号或显式去重时才成立；此函数不能单凭名称视为可安全重试。


---

# PrismKEWorkflow._config ⭐⭐

**位置与等级**：[graph.py:365](../../../src/workflow/graph.py#L365)；局部辅助逻辑，需理解其调用条件与失败传播。

**签名**：`def _config(run_id: str) -> dict[str, dict[str, str]]`。

**装饰器/路由**：`staticmethod`。

**作用**：内部辅助步骤；将参数转换为本模块所需的中间对象或操作结果。

**输入与输出**：
- 输入：`run_id`（str；目标运行的稳定标识）。
- 输出类型：`dict[str, dict[str, str]]`；具体返回路径见流程步骤。

**处理流程**：
1. 返回 `{'configurable': {'thread_id': run_id}}`。

**调用与被调用**：
- 无显式函数调用，或仅声明协议/常量。
- 静态可定位的调用方：[PrismKEWorkflow.confirm_submission](graph.md)、[PrismKEWorkflow.invoke](graph.md)、[PrismKEWorkflow.execution_snapshot](graph.md)、[PrismKEWorkflow.resume](graph.md)、[PrismKEWorkflow.record_review](graph.md)、[PrismKEWorkflow.record_entity_review](graph.md)、[PrismKEWorkflow.record_completed_review](graph.md)。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：未见 `raise`；下游异常可能继续上抛。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。
- 恢复/幂等性：仅在代码有检查点、事务、请求编号或显式去重时才成立；此函数不能单凭名称视为可安全重试。


---

# PrismKEWorkflow.invoke ⭐⭐

**位置与等级**：[graph.py:368](../../../src/workflow/graph.py#L368)；局部辅助逻辑，需理解其调用条件与失败传播。

**签名**：`async def invoke(self, state: WorkflowState) -> WorkflowState`。

**作用**：调用已编译工作流，让状态按图节点推进或停在审核边界。

**输入与输出**：
- 输入：`state`（WorkflowState；跨节点 WorkflowState；调用方须保持证据与状态一致）。
- 输出类型：`WorkflowState`；具体返回路径见流程步骤。

**处理流程**：
1. 进入上下文 `open_checkpointer(self.checkpoint_path)`，由上下文管理器控制资源释放或事务范围。
2. 返回 `self._state(cast(GraphState, result))`。

**调用与被调用**：
- `open_checkpointer`（调用点 [graph.py:369](../../../src/workflow/graph.py#L369)）→ [open_checkpointer](../persistence/checkpoints.md)，静态可定位。
- `self._build_graph`（调用点 [graph.py:370](../../../src/workflow/graph.py#L370)）→ [PrismKEWorkflow._build_graph](graph.md)，静态可定位。
- `graph.ainvoke`（[graph.py:371](../../../src/workflow/graph.py#L371)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `state.model_dump`（[graph.py:372](../../../src/workflow/graph.py#L372)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `self._config`（调用点 [graph.py:372](../../../src/workflow/graph.py#L372)）→ [PrismKEWorkflow._config](graph.md)，静态可定位。
- `self._state`（调用点 [graph.py:374](../../../src/workflow/graph.py#L374)）→ [PrismKEWorkflow._state](graph.md)，静态可定位。
- `cast`（[graph.py:374](../../../src/workflow/graph.py#L374)）：来自 `typing.cast`；具体实现可能由依赖注入或运行时分派决定。
- 静态扫描未定位直接调用方；可能通过路由注册、LangGraph 节点、协议方法或依赖注入动态调用，不据此判断为死代码。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：未见 `raise`；下游异常可能继续上抛。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。
- 恢复/幂等性：仅在代码有检查点、事务、请求编号或显式去重时才成立；此函数不能单凭名称视为可安全重试。


---

# PrismKEWorkflow.execution_snapshot ⭐⭐

**位置与等级**：[graph.py:376](../../../src/workflow/graph.py#L376)；局部辅助逻辑，需理解其调用条件与失败传播。

**签名**：`async def execution_snapshot(self, run_id: str) -> dict[str, Any]`。

**作用**：处理 `execution_snapshot` 对应步骤；下列步骤依据函数体的实际控制流和调用点整理。

**输入与输出**：
- 输入：`run_id`（str；目标运行的稳定标识）。
- 输出类型：`dict[str, Any]`；具体返回路径见流程步骤。

**处理流程**：
1. 进入上下文 `open_checkpointer(self.checkpoint_path)`，由上下文管理器控制资源释放或事务范围。

**调用与被调用**：
- `open_checkpointer`（调用点 [graph.py:377](../../../src/workflow/graph.py#L377)）→ [open_checkpointer](../persistence/checkpoints.md)，静态可定位。
- `self._build_graph`（调用点 [graph.py:378](../../../src/workflow/graph.py#L378)）→ [PrismKEWorkflow._build_graph](graph.md)，静态可定位。
- `graph.aget_state`（[graph.py:379](../../../src/workflow/graph.py#L379)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `self._config`（调用点 [graph.py:379](../../../src/workflow/graph.py#L379)）→ [PrismKEWorkflow._config](graph.md)，静态可定位。
- `bool`（[graph.py:380](../../../src/workflow/graph.py#L380)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `list`（[graph.py:380](../../../src/workflow/graph.py#L380)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- 静态扫描未定位直接调用方；可能通过路由注册、LangGraph 节点、协议方法或依赖注入动态调用，不据此判断为死代码。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：未见 `raise`；下游异常可能继续上抛。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。
- 恢复/幂等性：仅在代码有检查点、事务、请求编号或显式去重时才成立；此函数不能单凭名称视为可安全重试。


---

# PrismKEWorkflow.resume ⭐⭐⭐⭐

**位置与等级**：[graph.py:382](../../../src/workflow/graph.py#L382)；承担主要 Agent、应用服务或审核/执行入口，跨模块影响显著。

**签名**：`async def resume(self, run_id: str) -> WorkflowState | None`。

**作用**：从已有运行/检查点继续；恢复前须核对策略、版本及安全阻断。

**输入与输出**：
- 输入：`run_id`（str；目标运行的稳定标识）。
- 输出类型：`WorkflowState | None`；具体返回路径见流程步骤。

**处理流程**：
1. 更新 `failed_summary`，值来自 `self.runs.load(run_id)`。
2. 进入上下文 `open_checkpointer(self.checkpoint_path)`，由上下文管理器控制资源释放或事务范围。
3. 更新 `state`，值来自 `self._state(cast(GraphState, result))`。
4. 更新 `state.retry_count`，值来自 `max(state.retry_count, failed_summary.retry_count)`。
5. 更新 `state.errors`，值来自 `list(dict.fromkeys([*failed_summary.errors, *state.errors]))`。
6. 调用 `self.runs.save`，结果未直接赋值。
7. 返回 `state`。

**关键条件与保护**：
- [graph.py:388](../../../src/workflow/graph.py#L388)：`not snapshot.values`，不满足时跳过本分支。
- [graph.py:390](../../../src/workflow/graph.py#L390)：`self.review_only`，不满足时跳过本分支。
- [graph.py:397](../../../src/workflow/graph.py#L397)：`set(snapshot.next) - allowed`，不满足时跳过本分支。
- [graph.py:399](../../../src/workflow/graph.py#L399)：`not snapshot.next`，不满足时跳过本分支。

**调用与被调用**：
- `self.runs.load`（[graph.py:383](../../../src/workflow/graph.py#L383)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `open_checkpointer`（调用点 [graph.py:384](../../../src/workflow/graph.py#L384)）→ [open_checkpointer](../persistence/checkpoints.md)，静态可定位。
- `self._build_graph`（调用点 [graph.py:385](../../../src/workflow/graph.py#L385)）→ [PrismKEWorkflow._build_graph](graph.md)，静态可定位。
- `self._config`（调用点 [graph.py:386](../../../src/workflow/graph.py#L386)）→ [PrismKEWorkflow._config](graph.md)，静态可定位。
- `graph.aget_state`（[graph.py:387](../../../src/workflow/graph.py#L387)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `set`（[graph.py:397](../../../src/workflow/graph.py#L397)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `ValueError`（[graph.py:398](../../../src/workflow/graph.py#L398)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `graph.ainvoke`（[graph.py:401](../../../src/workflow/graph.py#L401)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `self._state`（调用点 [graph.py:402](../../../src/workflow/graph.py#L402)）→ [PrismKEWorkflow._state](graph.md)，静态可定位。
- `cast`（[graph.py:402](../../../src/workflow/graph.py#L402)）：来自 `typing.cast`；具体实现可能由依赖注入或运行时分派决定。
- `max`（[graph.py:403](../../../src/workflow/graph.py#L403)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `list`（[graph.py:404](../../../src/workflow/graph.py#L404)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `dict.fromkeys`（[graph.py:404](../../../src/workflow/graph.py#L404)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `self.runs.save`（[graph.py:405](../../../src/workflow/graph.py#L405)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- 静态扫描未定位直接调用方；可能通过路由注册、LangGraph 节点、协议方法或依赖注入动态调用，不据此判断为死代码。

**状态、副作用与异常**：
- 显式状态/容器赋值：`state.retry_count`、`state.errors`。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：`ValueError(<字符串常量>)`。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。
- 恢复/幂等性：仅在代码有检查点、事务、请求编号或显式去重时才成立；此函数不能单凭名称视为可安全重试。


---

# PrismKEWorkflow.record_review ⭐⭐⭐⭐

**位置与等级**：[graph.py:408](../../../src/workflow/graph.py#L408)；承担主要 Agent、应用服务或审核/执行入口，跨模块影响显著。

**签名**：`async def record_review(self, state: WorkflowState) -> bool`。

**作用**：创建、更新或记录相应资源；写入/审计边界以实际调用和状态赋值为准。

**输入与输出**：
- 输入：`state`（WorkflowState；跨节点 WorkflowState；调用方须保持证据与状态一致）。
- 输出类型：`bool`；具体返回路径见流程步骤。

**处理流程**：
1. 进入上下文 `open_checkpointer(self.checkpoint_path)`，由上下文管理器控制资源释放或事务范围。
2. 调用 `self.runs.save`，结果未直接赋值。
3. 返回 `True`。

**关键条件与保护**：
- [graph.py:413](../../../src/workflow/graph.py#L413)：`not snapshot.values`，不满足时跳过本分支。

**调用与被调用**：
- `open_checkpointer`（调用点 [graph.py:409](../../../src/workflow/graph.py#L409)）→ [open_checkpointer](../persistence/checkpoints.md)，静态可定位。
- `self._build_graph`（调用点 [graph.py:410](../../../src/workflow/graph.py#L410)）→ [PrismKEWorkflow._build_graph](graph.md)，静态可定位。
- `self._config`（调用点 [graph.py:411](../../../src/workflow/graph.py#L411)）→ [PrismKEWorkflow._config](graph.md)，静态可定位。
- `graph.aget_state`（[graph.py:412](../../../src/workflow/graph.py#L412)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `graph.aupdate_state`（[graph.py:415](../../../src/workflow/graph.py#L415)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `state.model_dump`（[graph.py:417](../../../src/workflow/graph.py#L417)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `self.runs.save`（[graph.py:420](../../../src/workflow/graph.py#L420)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- 静态扫描未定位直接调用方；可能通过路由注册、LangGraph 节点、协议方法或依赖注入动态调用，不据此判断为死代码。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：未见 `raise`；下游异常可能继续上抛。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。
- 恢复/幂等性：仅在代码有检查点、事务、请求编号或显式去重时才成立；此函数不能单凭名称视为可安全重试。


---

# PrismKEWorkflow.record_entity_review ⭐⭐⭐⭐

**位置与等级**：[graph.py:423](../../../src/workflow/graph.py#L423)；承担主要 Agent、应用服务或审核/执行入口，跨模块影响显著。

**签名**：`async def record_entity_review(self, state: WorkflowState) -> bool`。

**作用**：创建、更新或记录相应资源；写入/审计边界以实际调用和状态赋值为准。

**输入与输出**：
- 输入：`state`（WorkflowState；跨节点 WorkflowState；调用方须保持证据与状态一致）。
- 输出类型：`bool`；具体返回路径见流程步骤。

**处理流程**：
1. 进入上下文 `open_checkpointer(self.checkpoint_path)`，由上下文管理器控制资源释放或事务范围。
2. 调用 `self.runs.save`，结果未直接赋值。
3. 返回 `True`。

**关键条件与保护**：
- [graph.py:428](../../../src/workflow/graph.py#L428)：`not snapshot.values`，不满足时跳过本分支。

**调用与被调用**：
- `open_checkpointer`（调用点 [graph.py:424](../../../src/workflow/graph.py#L424)）→ [open_checkpointer](../persistence/checkpoints.md)，静态可定位。
- `self._build_graph`（调用点 [graph.py:425](../../../src/workflow/graph.py#L425)）→ [PrismKEWorkflow._build_graph](graph.md)，静态可定位。
- `self._config`（调用点 [graph.py:426](../../../src/workflow/graph.py#L426)）→ [PrismKEWorkflow._config](graph.md)，静态可定位。
- `graph.aget_state`（[graph.py:427](../../../src/workflow/graph.py#L427)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `graph.aupdate_state`（[graph.py:430](../../../src/workflow/graph.py#L430)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `state.model_dump`（[graph.py:432](../../../src/workflow/graph.py#L432)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `self.runs.save`（[graph.py:435](../../../src/workflow/graph.py#L435)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- 静态扫描未定位直接调用方；可能通过路由注册、LangGraph 节点、协议方法或依赖注入动态调用，不据此判断为死代码。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：未见 `raise`；下游异常可能继续上抛。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。
- 恢复/幂等性：仅在代码有检查点、事务、请求编号或显式去重时才成立；此函数不能单凭名称视为可安全重试。


---

# PrismKEWorkflow.record_completed_review ⭐⭐⭐⭐

**位置与等级**：[graph.py:438](../../../src/workflow/graph.py#L438)；承担主要 Agent、应用服务或审核/执行入口，跨模块影响显著。

**签名**：`async def record_completed_review(self, state: WorkflowState) -> bool`。

**作用**：创建、更新或记录相应资源；写入/审计边界以实际调用和状态赋值为准。

**输入与输出**：
- 输入：`state`（WorkflowState；跨节点 WorkflowState；调用方须保持证据与状态一致）。
- 输出类型：`bool`；具体返回路径见流程步骤。

**处理流程**：
1. 进入上下文 `open_checkpointer(self.checkpoint_path)`，由上下文管理器控制资源释放或事务范围。
2. 调用 `self.runs.save`，结果未直接赋值。
3. 返回 `True`。

**关键条件与保护**：
- [graph.py:443](../../../src/workflow/graph.py#L443)：`not snapshot.values`，不满足时跳过本分支。

**调用与被调用**：
- `open_checkpointer`（调用点 [graph.py:439](../../../src/workflow/graph.py#L439)）→ [open_checkpointer](../persistence/checkpoints.md)，静态可定位。
- `self._build_graph`（调用点 [graph.py:440](../../../src/workflow/graph.py#L440)）→ [PrismKEWorkflow._build_graph](graph.md)，静态可定位。
- `self._config`（调用点 [graph.py:441](../../../src/workflow/graph.py#L441)）→ [PrismKEWorkflow._config](graph.md)，静态可定位。
- `graph.aget_state`（[graph.py:442](../../../src/workflow/graph.py#L442)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `graph.aupdate_state`（[graph.py:445](../../../src/workflow/graph.py#L445)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `state.model_dump`（[graph.py:446](../../../src/workflow/graph.py#L446)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `self.runs.save`（[graph.py:448](../../../src/workflow/graph.py#L448)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- 静态扫描未定位直接调用方；可能通过路由注册、LangGraph 节点、协议方法或依赖注入动态调用，不据此判断为死代码。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：未见 `raise`；下游异常可能继续上抛。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。
- 恢复/幂等性：仅在代码有检查点、事务、请求编号或显式去重时才成立；此函数不能单凭名称视为可安全重试。


---
