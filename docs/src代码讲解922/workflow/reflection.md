源码：[reflection.py:1](../../../src/workflow/reflection.py#L1) | 基准：`dev/v0.10@f2f34d7` | 本文件符号数：4

**模块职责**：Case-assisted, budget-bounded candidate Reflection.
**在系统中的位置**：应用服务、LangGraph 编排、执行状态、审核接续、图提交及纠正流程。
**直接依赖**：[src.core.ids](../core/ids.md)、[src.domain](../domain/__init__.md)、[src.governance.validation](../governance/validation/__init__.md)、[src.persistence.base](../persistence/base.md)、[src.providers.base](../providers/base.md)、[src.workflow.cases](cases.md)；外部/标准库：`__future__`、`time`。
**主要调用方（静态导入）**：[evaluation/reflection.py](../evaluation/reflection.md)、[workflow/graph.py](graph.md)、[workflow/nodes.py](nodes.md)、[workflow/service.py](service.md)。
**阅读提示**：下列流程根据当前源码控制流整理；`self`/接口对象的实际类型可能在运行时注入，未能静态解析的调用会明确标注。链接指向源码行或对应讲解文件。

---

# BoundedReflectionService ⭐⭐⭐⭐

**位置与等级**：[reflection.py:25](../../../src/workflow/reflection.py#L25)；承担主要 Agent、应用服务或审核/执行入口，跨模块影响显著。

**职责**：跨步骤服务；组合依赖并暴露可复用业务入口。基类：无显式基类。

**字段与类级约束**：
- 类体未直接声明字段；实例状态请看 `__init__` 及方法中的赋值。

**内部成员**：`BoundedReflectionService.__init__`、`BoundedReflectionService._issues`、`BoundedReflectionService.run`


---

# BoundedReflectionService.__init__ ⭐⭐⭐⭐

**位置与等级**：[reflection.py:26](../../../src/workflow/reflection.py#L26)；承担主要 Agent、应用服务或审核/执行入口，跨模块影响显著。

**签名**：`def __init__(self, provider: ReflectionProvider, retriever: CaseRetriever | None, evidence_store: EvidenceStore) -> None`。

**作用**：初始化对象并保存依赖或配置；需检查是否创建持久化资源。

**输入与输出**：
- 输入：`provider`（ReflectionProvider）；`retriever`（CaseRetriever | None）；`evidence_store`（EvidenceStore；证据元数据和原始内容的存储接口）。
- 输出类型：`None`；具体返回路径见流程步骤。

**处理流程**：
1. 更新 `self.provider`，值来自 `provider`。
2. 更新 `self.retriever`，值来自 `retriever`。
3. 更新 `self.evidence_store`，值来自 `evidence_store`。

**调用与被调用**：
- 无显式函数调用，或仅声明协议/常量。
- 静态扫描未定位直接调用方；可能通过路由注册、LangGraph 节点、协议方法或依赖注入动态调用，不据此判断为死代码。

**状态、副作用与异常**：
- 显式状态/容器赋值：`self.provider`、`self.retriever`、`self.evidence_store`。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：未见 `raise`；下游异常可能继续上抛。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。
- 恢复/幂等性：仅在代码有检查点、事务、请求编号或显式去重时才成立；此函数不能单凭名称视为可安全重试。


---

# BoundedReflectionService._issues ⭐⭐

**位置与等级**：[reflection.py:37](../../../src/workflow/reflection.py#L37)；局部辅助逻辑，需理解其调用条件与失败传播。

**签名**：`def _issues(state: WorkflowState, candidate_id: str) -> list[ValidationIssue]`。

**装饰器/路由**：`staticmethod`。

**作用**：内部辅助步骤；将参数转换为本模块所需的中间对象或操作结果。

**输入与输出**：
- 输入：`state`（WorkflowState；跨节点 WorkflowState；调用方须保持证据与状态一致）；`candidate_id`（str）。
- 输出类型：`list[ValidationIssue]`；具体返回路径见流程步骤。

**处理流程**：
1. 返回 `[issue for issue in state.validation.issues if issue.target_id == candidate_id and issue.status == 'open…`。

**调用与被调用**：
- 无显式函数调用，或仅声明协议/常量。
- 静态可定位的调用方：[BoundedReflectionService.run](reflection.md)。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：未见 `raise`；下游异常可能继续上抛。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。
- 恢复/幂等性：仅在代码有检查点、事务、请求编号或显式去重时才成立；此函数不能单凭名称视为可安全重试。


---

# BoundedReflectionService.run ⭐⭐⭐⭐

**位置与等级**：[reflection.py:47](../../../src/workflow/reflection.py#L47)；承担主要 Agent、应用服务或审核/执行入口，跨模块影响显著。

**签名**：`async def run(self, state: WorkflowState) -> WorkflowState`。

**作用**：创建并执行一次运行；具体同步/异步以及副作用以实现步骤为准。

**输入与输出**：
- 输入：`state`（WorkflowState；跨节点 WorkflowState；调用方须保持证据与状态一致）。
- 输出类型：`WorkflowState`；具体返回路径见流程步骤。

**处理流程**：
1. 断言 `state.document is not None and state.output_schema is not None`。
2. 更新 `validation`，值来自 `ValidationService()`。
3. 更新 `initial`，值来自 `await validation.candidates(state.candidates, SchemaIndex(state.output_schema), state.document, sel…`。
4. 更新 `state.validation`，值来自 `validation.merge(state.validation, initial)`。
5. 检查 `not state.reflection_enabled or state.reflection_max_attempts <= 0`；按条件分流，else 分支不存在。
6. 更新 `started`，值来自 `perf_counter()`。
7. 更新 `schema_fingerprint`，值来自 `canonical_hash(state.output_schema.model_dump(mode='json'))`。
8. 更新 `allowed_evidence`，值来自 `[item.id for item in state.document.evidence]`。
9. 更新 `case_types`，值来自 `{'good': {'good'}, 'good_bad': {'good', 'bad'}}.get(state.case_mode, set())`。
10. 遍历 `enumerate(list(state.candidates))`，逐项处理 `(position, original)`。
11. 更新 `state.validation`，值来自 `validation.merge(state.validation, [])`。
12. 返回 `state`。

**关键条件与保护**：
- [reflection.py:57](../../../src/workflow/reflection.py#L57)：`not state.reflection_enabled or state.reflection_max_attempts <= 0`，不满足时跳过本分支。
- [reflection.py:68](../../../src/workflow/reflection.py#L68)：`not issues`，不满足时跳过本分支。
- [reflection.py:74](../../../src/workflow/reflection.py#L74)：`elapsed >= state.reflection_time_budget_seconds or remaining_tokens <= 0`，不满足时跳过本分支。
- [reflection.py:94](../../../src/workflow/reflection.py#L94)：`case_types and self.retriever is not None`，不满足时跳过本分支。
- [reflection.py:159](../../../src/workflow/reflection.py#L159)：`result.total_tokens is None`，不满足时跳过本分支。
- [reflection.py:189](../../../src/workflow/reflection.py#L189)：`result.candidate is None`，不满足时有 else 分支。
- [reflection.py:239](../../../src/workflow/reflection.py#L239)：`status == 'succeeded' and replacement is not None`，不满足时跳过本分支。
- [reflection.py:246](../../../src/workflow/reflection.py#L246)：`replacement is None or len(new_issues) > len(issues)`，不满足时跳过本分支。

**调用与被调用**：
- `ValidationService`（[reflection.py:49](../../../src/workflow/reflection.py#L49)）：来自 `src.governance.validation.ValidationService`；具体实现可能由依赖注入或运行时分派决定。
- `validation.candidates`（[reflection.py:50](../../../src/workflow/reflection.py#L50)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `SchemaIndex`（[reflection.py:52](../../../src/workflow/reflection.py#L52)）：来自 `src.domain.SchemaIndex`；具体实现可能由依赖注入或运行时分派决定。
- `validation.merge`（[reflection.py:56](../../../src/workflow/reflection.py#L56)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `perf_counter`（[reflection.py:59](../../../src/workflow/reflection.py#L59)）：来自 `time.perf_counter`；具体实现可能由依赖注入或运行时分派决定。
- `canonical_hash`（调用点 [reflection.py:60](../../../src/workflow/reflection.py#L60)）→ [canonical_hash](../core/ids.md)，静态可定位。
- `state.output_schema.model_dump`（[reflection.py:60](../../../src/workflow/reflection.py#L60)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `{'good': {'good'}, 'good_bad': {'good', 'bad'}}.get`（[reflection.py:62](../../../src/workflow/reflection.py#L62)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `set`（[reflection.py:65](../../../src/workflow/reflection.py#L65)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `enumerate`（[reflection.py:66](../../../src/workflow/reflection.py#L66)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `list`（[reflection.py:66](../../../src/workflow/reflection.py#L66)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `self._issues`（调用点 [reflection.py:67](../../../src/workflow/reflection.py#L67)）→ [BoundedReflectionService._issues](reflection.md)，静态可定位。
- `range`（[reflection.py:71](../../../src/workflow/reflection.py#L71)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `state.reflection_attempts.append`（[reflection.py:75](../../../src/workflow/reflection.py#L75)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `ReflectionAttempt`（[reflection.py:76](../../../src/workflow/reflection.py#L76)）：来自 `src.domain.ReflectionAttempt`；具体实现可能由依赖注入或运行时分派决定。
- `stable_id`（调用点 [reflection.py:77](../../../src/workflow/reflection.py#L77)）→ [stable_id](../core/ids.md)，静态可定位。
- `current.model_dump`（[reflection.py:85](../../../src/workflow/reflection.py#L85)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `self.provider.fingerprint`（[reflection.py:86](../../../src/workflow/reflection.py#L86)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `state.warnings.append`（[reflection.py:91](../../../src/workflow/reflection.py#L91)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `getattr`（[reflection.py:95](../../../src/workflow/reflection.py#L95)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `<字符串常量>.join`（[reflection.py:96](../../../src/workflow/reflection.py#L96)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `str`（[reflection.py:100](../../../src/workflow/reflection.py#L100)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `self.retriever.retrieve`（[reflection.py:112](../../../src/workflow/reflection.py#L112)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `_language`（调用点 [reflection.py:116](../../../src/workflow/reflection.py#L116)）→ [_language](cases.md)，静态可定位。
- `state.retrieved_cases.extend`（[reflection.py:123](../../../src/workflow/reflection.py#L123)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `ReflectionRequest`（[reflection.py:126](../../../src/workflow/reflection.py#L126)）：来自 `src.domain.ReflectionRequest`；具体实现可能由依赖注入或运行时分派决定。
- `self.provider.reflect`（[reflection.py:137](../../../src/workflow/reflection.py#L137)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `type`（[reflection.py:153](../../../src/workflow/reflection.py#L153)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `round`（[reflection.py:158](../../../src/workflow/reflection.py#L158)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `result.candidate.model_dump`（[reflection.py:172](../../../src/workflow/reflection.py#L172)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- 此处列出前 30 个不同调用表达式，另有 5 个，需按源码继续追踪。
- 静态扫描未定位直接调用方；可能通过路由注册、LangGraph 节点、协议方法或依赖注入动态调用，不据此判断为死代码。

**状态、副作用与异常**：
- 显式状态/容器赋值：`state.validation`、`state.reflection_elapsed_ms`、`state.reflection_token_usage`、`state.candidates[position]`、`issue.status`。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：未见 `raise`；下游异常可能继续上抛。
- 本地捕获：`Exception`。
- 恢复/幂等性：仅在代码有检查点、事务、请求编号或显式去重时才成立；此函数不能单凭名称视为可安全重试。


---
