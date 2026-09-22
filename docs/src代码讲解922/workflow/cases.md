源码：[cases.py:1](../../../src/workflow/cases.py#L1) | 基准：`dev/v0.10@f2f34d7` | 本文件符号数：15

**模块职责**：Review-case projection, semantic retrieval and index maintenance.
**在系统中的位置**：应用服务、LangGraph 编排、执行状态、审核接续、图提交及纠正流程。
**直接依赖**：[src.core.ids](../core/ids.md)、[src.domain](../domain/__init__.md)、[src.persistence](../persistence/__init__.md)、[src.providers.base](../providers/base.md)；外部/标准库：`__future__`、`math`、`re`、`typing`。
**主要调用方（静态导入）**：[evaluation/reflection.py](../evaluation/reflection.md)、[workflow/reflection.py](reflection.md)、[workflow/service.py](service.md)。
**阅读提示**：下列流程根据当前源码控制流整理；`self`/接口对象的实际类型可能在运行时注入，未能静态解析的调用会明确标注。链接指向源码行或对应讲解文件。

---

# _language ⭐⭐

**位置与等级**：[cases.py:27](../../../src/workflow/cases.py#L27)；局部辅助逻辑，需理解其调用条件与失败传播。

**签名**：`def _language(text: str) -> str`。

**作用**：内部辅助步骤；将参数转换为本模块所需的中间对象或操作结果。

**输入与输出**：
- 输入：`text`（str）。
- 输出类型：`str`；具体返回路径见流程步骤。

**处理流程**：
1. 返回 `'zh' if re.search(<字符串常量>, text) else 'en'`。

**调用与被调用**：
- `re.search`（[cases.py:28](../../../src/workflow/cases.py#L28)）：来自 `re`；具体实现可能由依赖注入或运行时分派决定。
- 静态可定位的调用方：[CaseService.project_review_event](cases.md)、[BoundedReflectionService.run](reflection.md)。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：未见 `raise`；下游异常可能继续上抛。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。
- 恢复/幂等性：仅在代码有检查点、事务、请求编号或显式去重时才成立；此函数不能单凭名称视为可安全重试。


---

# _mention ⭐⭐

**位置与等级**：[cases.py:31](../../../src/workflow/cases.py#L31)；局部辅助逻辑，需理解其调用条件与失败传播。

**签名**：`def _mention(candidate: CandidateClaim, mention_id: str) -> EntityMention | None`。

**作用**：内部辅助步骤；将参数转换为本模块所需的中间对象或操作结果。

**输入与输出**：
- 输入：`candidate`（CandidateClaim；尚未成为正式 Claim 的候选）；`mention_id`（str）。
- 输出类型：`EntityMention | None`；具体返回路径见流程步骤。

**处理流程**：
1. 检查 `candidate.subject.id == mention_id`；按条件分流，else 分支不存在。
2. 检查 `isinstance(candidate.object, EntityMention) and candidate.object.id == mention_id`；按条件分流，else 分支不存在。
3. 返回 `None`。

**关键条件与保护**：
- [cases.py:32](../../../src/workflow/cases.py#L32)：`candidate.subject.id == mention_id`，不满足时跳过本分支。
- [cases.py:34](../../../src/workflow/cases.py#L34)：`isinstance(candidate.object, EntityMention) and candidate.object.id == mention_id`，不满足时跳过本分支。

**调用与被调用**：
- `isinstance`（[cases.py:34](../../../src/workflow/cases.py#L34)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- 静态可定位的调用方：[CaseService.project_review_event](cases.md)。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：未见 `raise`；下游异常可能继续上抛。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。
- 恢复/幂等性：仅在代码有检查点、事务、请求编号或显式去重时才成立；此函数不能单凭名称视为可安全重试。


---

# CaseService ⭐⭐⭐⭐

**位置与等级**：[cases.py:39](../../../src/workflow/cases.py#L39)；承担主要 Agent、应用服务或审核/执行入口，跨模块影响显著。

**职责**：跨步骤服务；组合依赖并暴露可复用业务入口。基类：无显式基类。

**字段与类级约束**：
- 类体未直接声明字段；实例状态请看 `__init__` 及方法中的赋值。

**内部成员**：`CaseService.__init__`、`CaseService.project_review_event`、`CaseService.replay`


---

# CaseService.__init__ ⭐⭐

**位置与等级**：[cases.py:40](../../../src/workflow/cases.py#L40)；局部辅助逻辑，需理解其调用条件与失败传播。

**签名**：`def __init__(self, repository: CaseRepository, evidence_store: Any) -> None`。

**作用**：初始化对象并保存依赖或配置；需检查是否创建持久化资源。

**输入与输出**：
- 输入：`repository`（CaseRepository）；`evidence_store`（Any；证据元数据和原始内容的存储接口）。
- 输出类型：`None`；具体返回路径见流程步骤。

**处理流程**：
1. 更新 `self.repository`，值来自 `repository`。
2. 更新 `self.evidence_store`，值来自 `evidence_store`。

**调用与被调用**：
- 无显式函数调用，或仅声明协议/常量。
- 静态扫描未定位直接调用方；可能通过路由注册、LangGraph 节点、协议方法或依赖注入动态调用，不据此判断为死代码。

**状态、副作用与异常**：
- 显式状态/容器赋值：`self.repository`、`self.evidence_store`。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：未见 `raise`；下游异常可能继续上抛。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。
- 恢复/幂等性：仅在代码有检查点、事务、请求编号或显式去重时才成立；此函数不能单凭名称视为可安全重试。


---

# CaseService.project_review_event ⭐⭐⭐⭐

**位置与等级**：[cases.py:44](../../../src/workflow/cases.py#L44)；承担主要 Agent、应用服务或审核/执行入口，跨模块影响显著。

**签名**：`async def project_review_event(self, event: ReviewEvent, state: WorkflowState) -> CaseRecord | None`。

**作用**：处理 `project_review_event` 对应步骤；下列步骤依据函数体的实际控制流和调用点整理。

**输入与输出**：
- 输入：`event`（ReviewEvent）；`state`（WorkflowState；跨节点 WorkflowState；调用方须保持证据与状态一致）。
- 输出类型：`CaseRecord | None`；具体返回路径见流程步骤。

**处理流程**：
1. 检查 `self.repository.projected(event.id)`；按条件分流，else 分支不存在。
2. 更新 `decision`，值来自 `event.action`。
3. 检查 `decision == 'commit_correction'`；按条件分流，else 分支不存在。
4. 检查 `decision == 'defer' or decision not in {'link', 'create', 'approve', 'reject'}`；按条件分流，else 分支不存在。
5. 更新 `reason`，值来自 `event.reason.strip()`。
6. 检查 `not event.reviewer.strip() or not reason or state.output_schema is None`；按条件分流，else 分支不存在。
7. 更新 `evidence_ids`，值来自 `声明`。
8. 更新 `input_summary`，值来自 `声明`。
9. 更新 `snapshot`，值来自 `声明`。
10. 检查 `event.kind == 'claim'`；按条件分流，else 分支存在。
11. 检查 `not evidence_ids`；按条件分流，else 分支不存在。
12. 遍历 `evidence_ids`，逐项处理 `evidence_id`。
13. 更新 `superseded`，值来自 `self.repository.by_source_event(event.supersedes_event_id) if event.supersedes_event_id else None`。
14. 更新 `record`，值来自 `CaseRecord(id=stable_id('case', event.id), run_id=event.run_id, case_type='bad' if decision == 'rej…`。
15. 调用 `self.repository.add`，结果未直接赋值。
16. 检查 `superseded and self.repository.is_active(superseded.id)`；按条件分流，else 分支不存在。
17. 调用 `self.repository.mark_projected`，结果未直接赋值。
18. 返回 `record`。

**关键条件与保护**：
- [cases.py:47](../../../src/workflow/cases.py#L47)：`self.repository.projected(event.id)`，不满足时跳过本分支。
- [cases.py:50](../../../src/workflow/cases.py#L50)：`decision == 'commit_correction'`，不满足时跳过本分支。
- [cases.py:52](../../../src/workflow/cases.py#L52)：`decision == 'defer' or decision not in {'link', 'create', 'approve', 'reject'}`，不满足时跳过本分支。
- [cases.py:61](../../../src/workflow/cases.py#L61)：`not event.reviewer.strip() or not reason or state.output_schema is None`，不满足时跳过本分支。
- [cases.py:67](../../../src/workflow/cases.py#L67)：`event.kind == 'claim'`，不满足时有 else 分支。
- [cases.py:70](../../../src/workflow/cases.py#L70)：`claim is None`，不满足时跳过本分支。
- [cases.py:93](../../../src/workflow/cases.py#L93)：`not located`，不满足时跳过本分支。
- [cases.py:104](../../../src/workflow/cases.py#L104)：`not evidence_ids`，不满足时跳过本分支。
- [cases.py:108](../../../src/workflow/cases.py#L108)：`not await self.evidence_store.exists(evidence_id) or not await self.evidence_store.verify(evidence_id)`，不满足时跳过本分支。
- [cases.py:135](../../../src/workflow/cases.py#L135)：`superseded and self.repository.is_active(superseded.id)`，不满足时跳过本分支。

**调用与被调用**：
- `self.repository.projected`（[cases.py:47](../../../src/workflow/cases.py#L47)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `self.repository.by_source_event`（[cases.py:48](../../../src/workflow/cases.py#L48)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `str`（[cases.py:51](../../../src/workflow/cases.py#L51)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `event.after.get`（[cases.py:51](../../../src/workflow/cases.py#L51)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `self.repository.mark_projected`（[cases.py:58](../../../src/workflow/cases.py#L58)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `event.reason.strip`（[cases.py:60](../../../src/workflow/cases.py#L60)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `event.reviewer.strip`（[cases.py:61](../../../src/workflow/cases.py#L61)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `event.before.get`（[cases.py:68](../../../src/workflow/cases.py#L68)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `next`（[cases.py:69](../../../src/workflow/cases.py#L69)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `list`（[cases.py:74](../../../src/workflow/cases.py#L74)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `<字符串常量>.join`（[cases.py:75](../../../src/workflow/cases.py#L75)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `claim.model_dump`（[cases.py:83](../../../src/workflow/cases.py#L83)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `item.model_dump`（[cases.py:84](../../../src/workflow/cases.py#L84)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `_mention`（调用点 [cases.py:91](../../../src/workflow/cases.py#L91)）→ [_mention](cases.md)，静态可定位。
- `dict.fromkeys`（[cases.py:97](../../../src/workflow/cases.py#L97)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `mention.model_dump`（[cases.py:100](../../../src/workflow/cases.py#L100)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `self.evidence_store.exists`（[cases.py:108](../../../src/workflow/cases.py#L108)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `self.evidence_store.verify`（[cases.py:110](../../../src/workflow/cases.py#L110)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `CaseRecord`（[cases.py:118](../../../src/workflow/cases.py#L118)）：来自 `src.domain.CaseRecord`；具体实现可能由依赖注入或运行时分派决定。
- `stable_id`（调用点 [cases.py:119](../../../src/workflow/cases.py#L119)）→ [stable_id](../core/ids.md)，静态可定位。
- `canonical_hash`（调用点 [cases.py:123](../../../src/workflow/cases.py#L123)）→ [canonical_hash](../core/ids.md)，静态可定位。
- `state.output_schema.model_dump`（[cases.py:123](../../../src/workflow/cases.py#L123)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `_language`（调用点 [cases.py:124](../../../src/workflow/cases.py#L124)）→ [_language](cases.md)，静态可定位。
- `self.repository.add`（[cases.py:134](../../../src/workflow/cases.py#L134)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `self.repository.is_active`（[cases.py:135](../../../src/workflow/cases.py#L135)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `self.repository.disable`（[cases.py:136](../../../src/workflow/cases.py#L136)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `CaseStatusEvent`（[cases.py:137](../../../src/workflow/cases.py#L137)）：来自 `src.domain.CaseStatusEvent`；具体实现可能由依赖注入或运行时分派决定。
- 静态可定位的调用方：[CaseService.replay](cases.md)。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：未见 `raise`；下游异常可能继续上抛。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。
- 恢复/幂等性：仅在代码有检查点、事务、请求编号或显式去重时才成立；此函数不能单凭名称视为可安全重试。


---

# CaseService.replay ⭐⭐

**位置与等级**：[cases.py:149](../../../src/workflow/cases.py#L149)；局部辅助逻辑，需理解其调用条件与失败传播。

**签名**：`async def replay(self, events: list[ReviewEvent], states: dict[str, WorkflowState]) -> int`。

**作用**：处理 `replay` 对应步骤；下列步骤依据函数体的实际控制流和调用点整理。

**输入与输出**：
- 输入：`events`（list[ReviewEvent]）；`states`（dict[str, WorkflowState]）。
- 输出类型：`int`；具体返回路径见流程步骤。

**处理流程**：
1. 更新 `count`，值来自 `0`。
2. 遍历 `events`，逐项处理 `event`。
3. 返回 `count`。

**关键条件与保护**：
- [cases.py:152](../../../src/workflow/cases.py#L152)：`self.repository.projected(event.id) or event.run_id not in states`，不满足时跳过本分支。

**调用与被调用**：
- `self.repository.projected`（[cases.py:152](../../../src/workflow/cases.py#L152)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `self.project_review_event`（调用点 [cases.py:154](../../../src/workflow/cases.py#L154)）→ [CaseService.project_review_event](cases.md)，静态可定位。
- 静态扫描未定位直接调用方；可能通过路由注册、LangGraph 节点、协议方法或依赖注入动态调用，不据此判断为死代码。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：未见 `raise`；下游异常可能继续上抛。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。
- 恢复/幂等性：仅在代码有检查点、事务、请求编号或显式去重时才成立；此函数不能单凭名称视为可安全重试。


---

# CaseRetriever ⭐⭐⭐⭐

**位置与等级**：[cases.py:159](../../../src/workflow/cases.py#L159)；承担主要 Agent、应用服务或审核/执行入口，跨模块影响显著。

**职责**：本模块的对象实现或数据契约；具体语义由字段、基类和方法共同决定。基类：无显式基类。

**字段与类级约束**：
- 类体未直接声明字段；实例状态请看 `__init__` 及方法中的赋值。

**内部成员**：`CaseRetriever.__init__`、`CaseRetriever._cosine`、`CaseRetriever._vectors`、`CaseRetriever.retrieve`、`CaseRetriever.rebuild`、`CaseRetriever.snapshot_fingerprint`、`CaseRetriever.snapshot_ids`、`CaseRetriever.fingerprint_for`


---

# CaseRetriever.__init__ ⭐⭐

**位置与等级**：[cases.py:160](../../../src/workflow/cases.py#L160)；局部辅助逻辑，需理解其调用条件与失败传播。

**签名**：`def __init__(self, repository: CaseRepository, embedding_provider: EmbeddingProvider) -> None`。

**作用**：初始化对象并保存依赖或配置；需检查是否创建持久化资源。

**输入与输出**：
- 输入：`repository`（CaseRepository）；`embedding_provider`（EmbeddingProvider）。
- 输出类型：`None`；具体返回路径见流程步骤。

**处理流程**：
1. 更新 `self.repository`，值来自 `repository`。
2. 更新 `self.embedding_provider`，值来自 `embedding_provider`。

**调用与被调用**：
- 无显式函数调用，或仅声明协议/常量。
- 静态扫描未定位直接调用方；可能通过路由注册、LangGraph 节点、协议方法或依赖注入动态调用，不据此判断为死代码。

**状态、副作用与异常**：
- 显式状态/容器赋值：`self.repository`、`self.embedding_provider`。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：未见 `raise`；下游异常可能继续上抛。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。
- 恢复/幂等性：仅在代码有检查点、事务、请求编号或显式去重时才成立；此函数不能单凭名称视为可安全重试。


---

# CaseRetriever._cosine ⭐⭐

**位置与等级**：[cases.py:165](../../../src/workflow/cases.py#L165)；局部辅助逻辑，需理解其调用条件与失败传播。

**签名**：`def _cosine(left: list[float], right: list[float]) -> float`。

**装饰器/路由**：`staticmethod`。

**作用**：内部辅助步骤；将参数转换为本模块所需的中间对象或操作结果。

**输入与输出**：
- 输入：`left`（list[float]）；`right`（list[float]）。
- 输出类型：`float`；具体返回路径见流程步骤。

**处理流程**：
1. 检查 `len(left) != len(right) or not left`；按条件分流，else 分支不存在。
2. 更新 `dot`，值来自 `sum((a * b for a, b in zip(left, right, strict=True)))`。
3. 更新 `norm`，值来自 `math.sqrt(sum((a * a for a in left)) * sum((b * b for b in right)))`。
4. 返回 `dot / norm if norm else -1.0`。

**关键条件与保护**：
- [cases.py:166](../../../src/workflow/cases.py#L166)：`len(left) != len(right) or not left`，不满足时跳过本分支。

**调用与被调用**：
- `len`（[cases.py:166](../../../src/workflow/cases.py#L166)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `sum`（[cases.py:168](../../../src/workflow/cases.py#L168)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `zip`（[cases.py:168](../../../src/workflow/cases.py#L168)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `math.sqrt`（[cases.py:169](../../../src/workflow/cases.py#L169)）：来自 `math`；具体实现可能由依赖注入或运行时分派决定。
- 静态可定位的调用方：[CaseRetriever.retrieve](cases.md)。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：未见 `raise`；下游异常可能继续上抛。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。
- 恢复/幂等性：仅在代码有检查点、事务、请求编号或显式去重时才成立；此函数不能单凭名称视为可安全重试。


---

# CaseRetriever._vectors ⭐⭐

**位置与等级**：[cases.py:172](../../../src/workflow/cases.py#L172)；局部辅助逻辑，需理解其调用条件与失败传播。

**签名**：`async def _vectors(self, records: list[CaseRecord]) -> dict[str, list[float]]`。

**作用**：内部辅助步骤；将参数转换为本模块所需的中间对象或操作结果。

**输入与输出**：
- 输入：`records`（list[CaseRecord]）。
- 输出类型：`dict[str, list[float]]`；具体返回路径见流程步骤。

**处理流程**：
1. 更新 `fingerprint`，值来自 `self.embedding_provider.fingerprint()`。
2. 更新 `vectors`，值来自 `{}`。
3. 更新 `missing`，值来自 `[]`。
4. 遍历 `records`，逐项处理 `record`。
5. 检查 `missing`；按条件分流，else 分支不存在。
6. 返回 `vectors`。

**关键条件与保护**：
- [cases.py:179](../../../src/workflow/cases.py#L179)：`cached and cached.model_fingerprint == fingerprint and (cached.text_hash == text_hash)`，不满足时有 else 分支。
- [cases.py:183](../../../src/workflow/cases.py#L183)：`missing`，不满足时跳过本分支。

**调用与被调用**：
- `self.embedding_provider.fingerprint`（[cases.py:173](../../../src/workflow/cases.py#L173)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `canonical_hash`（调用点 [cases.py:177](../../../src/workflow/cases.py#L177)）→ [canonical_hash](../core/ids.md)，静态可定位。
- `self.repository.embedding`（[cases.py:178](../../../src/workflow/cases.py#L178)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `missing.append`（[cases.py:182](../../../src/workflow/cases.py#L182)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `self.embedding_provider.encode`（[cases.py:184](../../../src/workflow/cases.py#L184)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `zip`（[cases.py:185](../../../src/workflow/cases.py#L185)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `CaseEmbedding`（[cases.py:186](../../../src/workflow/cases.py#L186)）：来自 `src.domain.CaseEmbedding`；具体实现可能由依赖注入或运行时分派决定。
- `len`（[cases.py:190](../../../src/workflow/cases.py#L190)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `self.repository.save_embedding`（[cases.py:193](../../../src/workflow/cases.py#L193)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- 静态可定位的调用方：[CaseRetriever.retrieve](cases.md)、[CaseRetriever.rebuild](cases.md)。

**状态、副作用与异常**：
- 显式状态/容器赋值：`vectors[record.id]`。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：未见 `raise`；下游异常可能继续上抛。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。
- 恢复/幂等性：仅在代码有检查点、事务、请求编号或显式去重时才成立；此函数不能单凭名称视为可安全重试。


---

# CaseRetriever.retrieve ⭐⭐

**位置与等级**：[cases.py:197](../../../src/workflow/cases.py#L197)；局部辅助逻辑，需理解其调用条件与失败传播。

**签名**：`async def retrieve(self, query: str, *, task_type: str, schema_fingerprint: str, language: str, case_types: set[str] | None=None, top_k: int=5, use_location: str='validation', allowed_case_ids: set[str] | None=None) -> list[RetrievedCase]`。

**作用**：处理 `retrieve` 对应步骤；下列步骤依据函数体的实际控制流和调用点整理。

**输入与输出**：
- 输入：`query`（str）；`task_type`（str）；`schema_fingerprint`（str）；`language`（str）；`case_types`（set[str] | None；默认 `None`）；`top_k`（int；默认 `5`；候选召回数量上限）；`use_location`（str；默认 `'validation'`）；`allowed_case_ids`（set[str] | None；默认 `None`）。
- 输出类型：`list[RetrievedCase]`；具体返回路径见流程步骤。

**处理流程**：
1. 更新 `records`，值来自 `self.repository.list(task_type=task_type, schema_fingerprint=schema_fingerprint, language=language,…`。
2. 检查 `allowed_case_ids is not None`；按条件分流，else 分支不存在。
3. 检查 `case_types is not None`；按条件分流，else 分支不存在。
4. 检查 `not records`；按条件分流，else 分支不存在。
5. 更新 `vectors`，值来自 `await self._vectors(records)`。
6. 更新 `query_vector`，值来自 `(await self.embedding_provider.encode([query]))[0]`。
7. 更新 `ranked`，值来自 `sorted(((self._cosine(query_vector, vectors[item.id]), item) for item in records), key=lambda item:…`。
8. 返回 `[RetrievedCase(case_id=record.id, case_type=record.case_type, task_type=record.task_type, score=score, d…`。

**关键条件与保护**：
- [cases.py:216](../../../src/workflow/cases.py#L216)：`allowed_case_ids is not None`，不满足时跳过本分支。
- [cases.py:218](../../../src/workflow/cases.py#L218)：`case_types is not None`，不满足时跳过本分支。
- [cases.py:220](../../../src/workflow/cases.py#L220)：`not records`，不满足时跳过本分支。

**调用与被调用**：
- `self.repository.list`（[cases.py:209](../../../src/workflow/cases.py#L209)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `self._vectors`（调用点 [cases.py:222](../../../src/workflow/cases.py#L222)）→ [CaseRetriever._vectors](cases.md)，静态可定位。
- `self.embedding_provider.encode`（[cases.py:223](../../../src/workflow/cases.py#L223)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `sorted`（[cases.py:224](../../../src/workflow/cases.py#L224)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `self._cosine`（调用点 [cases.py:225](../../../src/workflow/cases.py#L225)）→ [CaseRetriever._cosine](cases.md)，静态可定位。
- `max`（[cases.py:227](../../../src/workflow/cases.py#L227)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `min`（[cases.py:227](../../../src/workflow/cases.py#L227)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `RetrievedCase`（[cases.py:229](../../../src/workflow/cases.py#L229)）：来自 `src.domain.RetrievedCase`；具体实现可能由依赖注入或运行时分派决定。
- 静态扫描未定位直接调用方；可能通过路由注册、LangGraph 节点、协议方法或依赖注入动态调用，不据此判断为死代码。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：未见 `raise`；下游异常可能继续上抛。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。
- 恢复/幂等性：仅在代码有检查点、事务、请求编号或显式去重时才成立；此函数不能单凭名称视为可安全重试。


---

# CaseRetriever.rebuild ⭐⭐

**位置与等级**：[cases.py:243](../../../src/workflow/cases.py#L243)；局部辅助逻辑，需理解其调用条件与失败传播。

**签名**：`async def rebuild(self, *, dry_run: bool=False) -> dict[str, Any]`。

**作用**：处理 `rebuild` 对应步骤；下列步骤依据函数体的实际控制流和调用点整理。

**输入与输出**：
- 输入：`dry_run`（bool；默认 `False`）。
- 输出类型：`dict[str, Any]`；具体返回路径见流程步骤。

**处理流程**：
1. 更新 `records`，值来自 `self.repository.list(active_only=True, limit=10000)`。
2. 更新 `fingerprint`，值来自 `self.embedding_provider.fingerprint()`。
3. 更新 `stale`，值来自 `[record for record in records if (embedding := self.repository.embedding(record.id)) is None or emb…`。
4. 检查 `not dry_run`；按条件分流，else 分支不存在。
5. 返回 `{'active_cases': len(records), 'stale_cases': len(stale), 'model_fingerprint': fingerprint, 'dry_run': d…`。

**关键条件与保护**：
- [cases.py:255](../../../src/workflow/cases.py#L255)：`not dry_run`，不满足时跳过本分支。

**调用与被调用**：
- `self.repository.list`（[cases.py:244](../../../src/workflow/cases.py#L244)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `self.embedding_provider.fingerprint`（[cases.py:245](../../../src/workflow/cases.py#L245)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `self.repository.embedding`（[cases.py:250](../../../src/workflow/cases.py#L250)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `canonical_hash`（调用点 [cases.py:252](../../../src/workflow/cases.py#L252)）→ [canonical_hash](../core/ids.md)，静态可定位。
- `self._vectors`（调用点 [cases.py:256](../../../src/workflow/cases.py#L256)）→ [CaseRetriever._vectors](cases.md)，静态可定位。
- `len`（[cases.py:258](../../../src/workflow/cases.py#L258)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- 静态扫描未定位直接调用方；可能通过路由注册、LangGraph 节点、协议方法或依赖注入动态调用，不据此判断为死代码。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：未见 `raise`；下游异常可能继续上抛。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。
- 恢复/幂等性：仅在代码有检查点、事务、请求编号或显式去重时才成立；此函数不能单凭名称视为可安全重试。


---

# CaseRetriever.snapshot_fingerprint ⭐⭐

**位置与等级**：[cases.py:264](../../../src/workflow/cases.py#L264)；局部辅助逻辑，需理解其调用条件与失败传播。

**签名**：`def snapshot_fingerprint(self) -> str`。

**作用**：处理 `snapshot_fingerprint` 对应步骤；下列步骤依据函数体的实际控制流和调用点整理。

**输入与输出**：
- 输入：无业务参数（或仅隐式接收实例）。
- 输出类型：`str`；具体返回路径见流程步骤。

**处理流程**：
1. 返回 `self.fingerprint_for(self.snapshot_ids())`。

**调用与被调用**：
- `self.fingerprint_for`（调用点 [cases.py:265](../../../src/workflow/cases.py#L265)）→ [CaseRetriever.fingerprint_for](cases.md)，静态可定位。
- `self.snapshot_ids`（调用点 [cases.py:265](../../../src/workflow/cases.py#L265)）→ [CaseRetriever.snapshot_ids](cases.md)，静态可定位。
- 静态扫描未定位直接调用方；可能通过路由注册、LangGraph 节点、协议方法或依赖注入动态调用，不据此判断为死代码。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：未见 `raise`；下游异常可能继续上抛。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。
- 恢复/幂等性：仅在代码有检查点、事务、请求编号或显式去重时才成立；此函数不能单凭名称视为可安全重试。


---

# CaseRetriever.snapshot_ids ⭐⭐

**位置与等级**：[cases.py:267](../../../src/workflow/cases.py#L267)；局部辅助逻辑，需理解其调用条件与失败传播。

**签名**：`def snapshot_ids(self) -> list[str]`。

**作用**：处理 `snapshot_ids` 对应步骤；下列步骤依据函数体的实际控制流和调用点整理。

**输入与输出**：
- 输入：无业务参数（或仅隐式接收实例）。
- 输出类型：`list[str]`；具体返回路径见流程步骤。

**处理流程**：
1. 返回 `sorted((item.id for item in self.repository.list(active_only=True, limit=10000)))`。

**调用与被调用**：
- `sorted`（[cases.py:268](../../../src/workflow/cases.py#L268)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `self.repository.list`（[cases.py:268](../../../src/workflow/cases.py#L268)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- 静态可定位的调用方：[CaseRetriever.snapshot_fingerprint](cases.md)。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：未见 `raise`；下游异常可能继续上抛。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。
- 恢复/幂等性：仅在代码有检查点、事务、请求编号或显式去重时才成立；此函数不能单凭名称视为可安全重试。


---

# CaseRetriever.fingerprint_for ⭐⭐

**位置与等级**：[cases.py:270](../../../src/workflow/cases.py#L270)；局部辅助逻辑，需理解其调用条件与失败传播。

**签名**：`def fingerprint_for(self, case_ids: list[str]) -> str`。

**作用**：处理 `fingerprint_for` 对应步骤；下列步骤依据函数体的实际控制流和调用点整理。

**输入与输出**：
- 输入：`case_ids`（list[str]）。
- 输出类型：`str`；具体返回路径见流程步骤。

**处理流程**：
1. 返回 `canonical_hash({'policy': CASE_POLICY_VERSION, 'retrieval': CASE_RETRIEVAL_VERSION, 'embedding': self.em…`。

**调用与被调用**：
- `canonical_hash`（调用点 [cases.py:271](../../../src/workflow/cases.py#L271)）→ [canonical_hash](../core/ids.md)，静态可定位。
- `self.embedding_provider.fingerprint`（[cases.py:275](../../../src/workflow/cases.py#L275)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `sorted`（[cases.py:276](../../../src/workflow/cases.py#L276)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- 静态可定位的调用方：[CaseRetriever.snapshot_fingerprint](cases.md)。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：未见 `raise`；下游异常可能继续上抛。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。
- 恢复/幂等性：仅在代码有检查点、事务、请求编号或显式去重时才成立；此函数不能单凭名称视为可安全重试。


---
