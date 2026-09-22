源码：[request_budget.py:1](../../../src/evaluation/request_budget.py#L1) | 基准：`dev/v0.10@f2f34d7` | 本文件符号数：13

**模块职责**：Shared, sanitized request accounting for bounded live evaluation only.
**在系统中的位置**：离线评测、预算账本、标注导出及报告；不等于生产工作流。
**直接依赖**：无显式项目内模块导入；外部/标准库：`__future__`、`asyncio`、`dataclasses`、`httpx`、`json`、`os`、`pathlib`、`tempfile`、`time`、`typing`。
**主要调用方（静态导入）**：[evaluation/document_validation.py](document_validation.md)、[evaluation/reflection.py](reflection.md)。
**阅读提示**：下列流程根据当前源码控制流整理；`self`/接口对象的实际类型可能在运行时注入，未能静态解析的调用会明确标注。链接指向源码行或对应讲解文件。

---

# EvaluationBudgetStop ⭐⭐⭐

**位置与等级**：[request_budget.py:17](../../../src/evaluation/request_budget.py#L17)；关键支撑逻辑，影响候选、证据或接口的正确传递。

**职责**：本模块的对象实现或数据契约；具体语义由字段、基类和方法共同决定。基类：`RuntimeError`。
**源码说明**：Stop further live calls when budget or reliable accounting is unavailable.

**字段与类级约束**：
- 类体未直接声明字段；实例状态请看 `__init__` 及方法中的赋值。

**内部成员**：此类未直接定义方法；字段/继承行为见源码。


---

# RequestBudget ⭐⭐⭐

**位置与等级**：[request_budget.py:22](../../../src/evaluation/request_budget.py#L22)；关键支撑逻辑，影响候选、证据或接口的正确传递。

**职责**：本模块的对象实现或数据契约；具体语义由字段、基类和方法共同决定。基类：无显式基类。
**约束/装饰器**：`dataclass`。

**字段与类级约束**：
- `limit`：`int`；默认 `100000`。
- `stop_at`：`int`；默认 `90000`。
- `max_output_tokens`：`int`；默认 `4096`。
- `total_tokens`：`int`；默认 `0`。
- `reserved_tokens`：`int`；默认 `0`。
- `stopped_reason`：`str | None`；默认 `None`。
- `calls`：`list[dict[str, Any]]`；默认 `field(default_factory=list)`。
- `lock`：`asyncio.Lock`；默认 `field(default_factory=asyncio.Lock)`。
- `request_gate`：`asyncio.Lock`；默认 `field(default_factory=asyncio.Lock)`。
- `active_tasks`：`list[asyncio.Task[httpx.Response]]`；默认 `field(default_factory=list)`。
- `accounting_complete`：`bool`；默认 `True`。
- `ledger_path`：`Path | None`；默认 `None`。
- `case_id`：`str | None`；默认 `None`。
- `resume_ledger`：`bool`；默认 `False`。
- `extend_budget`：`bool`；默认 `False`。
- `budget_amendments`：`list[dict[str, Any]]`；默认 `field(default_factory=list)`。

**内部成员**：`RequestBudget.__post_init__`、`RequestBudget._persist`、`RequestBudget.settle`、`RequestBudget.estimate`、`RequestBudget.reserve`、`RequestBudget.record`


---

# RequestBudget.__post_init__ ⭐⭐

**位置与等级**：[request_budget.py:40](../../../src/evaluation/request_budget.py#L40)；局部辅助逻辑，需理解其调用条件与失败传播。

**签名**：`def __post_init__(self) -> None`。

**作用**：内部辅助步骤；将参数转换为本模块所需的中间对象或操作结果。

**输入与输出**：
- 输入：无业务参数（或仅隐式接收实例）。
- 输出类型：`None`；具体返回路径见流程步骤。

**处理流程**：
1. 检查 `not 0 < self.stop_at < self.limit`；按条件分流，else 分支不存在。
2. 检查 `self.ledger_path is not None and self.ledger_path.exists()`；按条件分流，else 分支不存在。

**关键条件与保护**：
- [request_budget.py:41](../../../src/evaluation/request_budget.py#L41)：`not 0 < self.stop_at < self.limit`，不满足时跳过本分支。
- [request_budget.py:43](../../../src/evaluation/request_budget.py#L43)：`self.ledger_path is not None and self.ledger_path.exists()`，不满足时跳过本分支。
- [request_budget.py:48](../../../src/evaluation/request_budget.py#L48)：`pending`，不满足时跳过本分支。
- [request_budget.py:50](../../../src/evaluation/request_budget.py#L50)：`self.resume_ledger`，不满足时跳过本分支。
- [request_budget.py:56](../../../src/evaluation/request_budget.py#L56)：`changed and (not (self.extend_budget and increasing))`，不满足时跳过本分支。
- [request_budget.py:62](../../../src/evaluation/request_budget.py#L62)：`not saved.get('accounting_complete') or not settled_stop`，不满足时跳过本分支。
- [request_budget.py:68](../../../src/evaluation/request_budget.py#L68)：`self.total_tokens != sum((row.get(<字符串常量>, 0) for row in self.calls))`，不满足时跳过本分支。
- [request_budget.py:71](../../../src/evaluation/request_budget.py#L71)：`changed`，不满足时跳过本分支。

**调用与被调用**：
- `ValueError`（[request_budget.py:42](../../../src/evaluation/request_budget.py#L42)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `self.ledger_path.exists`（[request_budget.py:43](../../../src/evaluation/request_budget.py#L43)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `json.loads`（[request_budget.py:44](../../../src/evaluation/request_budget.py#L44)）：来自 `json`；具体实现可能由依赖注入或运行时分派决定。
- `self.ledger_path.read_text`（[request_budget.py:44](../../../src/evaluation/request_budget.py#L44)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `row.get`（[request_budget.py:46](../../../src/evaluation/request_budget.py#L46)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `EvaluationBudgetStop`（调用点 [request_budget.py:49](../../../src/evaluation/request_budget.py#L49)）→ [EvaluationBudgetStop](request_budget.md)，静态可定位。
- `saved.get`（[request_budget.py:51](../../../src/evaluation/request_budget.py#L51)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `sum`（[request_budget.py:68](../../../src/evaluation/request_budget.py#L68)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `self.budget_amendments.append`（[request_budget.py:72](../../../src/evaluation/request_budget.py#L72)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `time.time`（[request_budget.py:74](../../../src/evaluation/request_budget.py#L74)）：来自 `time`；具体实现可能由依赖注入或运行时分派决定。
- `self._persist`（调用点 [request_budget.py:83](../../../src/evaluation/request_budget.py#L83)）→ [RequestBudget._persist](request_budget.md)，静态可定位。
- 静态扫描未定位直接调用方；可能通过路由注册、LangGraph 节点、协议方法或依赖注入动态调用，不据此判断为死代码。

**状态、副作用与异常**：
- 显式状态/容器赋值：`self.calls`、`self.total_tokens`、`self.budget_amendments`。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：`ValueError(<字符串常量>)`、`EvaluationBudgetStop(f<字符串常量>)`、`EvaluationBudgetStop(<字符串常量>)`。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。


---

# RequestBudget._persist ⭐⭐

**位置与等级**：[request_budget.py:87](../../../src/evaluation/request_budget.py#L87)；局部辅助逻辑，需理解其调用条件与失败传播。

**签名**：`def _persist(self) -> None`。

**作用**：内部辅助步骤；将参数转换为本模块所需的中间对象或操作结果。

**输入与输出**：
- 输入：无业务参数（或仅隐式接收实例）。
- 输出类型：`None`；具体返回路径见流程步骤。

**处理流程**：
1. 检查 `self.ledger_path is None`；按条件分流，else 分支不存在。
2. 更新 `temporary`，值来自 `None`。
3. 捕获 OSError；另检查 finally/else 的清理和传播。

**关键条件与保护**：
- [request_budget.py:88](../../../src/evaluation/request_budget.py#L88)：`self.ledger_path is None`，不满足时跳过本分支。
- [request_budget.py:117](../../../src/evaluation/request_budget.py#L117)：`temporary is not None`，不满足时跳过本分支。

**调用与被调用**：
- `self.ledger_path.parent.mkdir`（[request_budget.py:92](../../../src/evaluation/request_budget.py#L92)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `tempfile.NamedTemporaryFile`（[request_budget.py:93](../../../src/evaluation/request_budget.py#L93)）：来自 `tempfile`；具体实现可能由依赖注入或运行时分派决定。
- `Path`（[request_budget.py:96](../../../src/evaluation/request_budget.py#L96)）：来自 `pathlib.Path`；具体实现可能由依赖注入或运行时分派决定。
- `json.dump`（[request_budget.py:97](../../../src/evaluation/request_budget.py#L97)）：来自 `json`；具体实现可能由依赖注入或运行时分派决定。
- `stream.flush`（[request_budget.py:110](../../../src/evaluation/request_budget.py#L110)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `os.fsync`（[request_budget.py:111](../../../src/evaluation/request_budget.py#L111)）：来自 `os`；具体实现可能由依赖注入或运行时分派决定。
- `stream.fileno`（[request_budget.py:111](../../../src/evaluation/request_budget.py#L111)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `os.replace`（[request_budget.py:112](../../../src/evaluation/request_budget.py#L112)）：来自 `os`；具体实现可能由依赖注入或运行时分派决定。
- `EvaluationBudgetStop`（调用点 [request_budget.py:115](../../../src/evaluation/request_budget.py#L115)）→ [EvaluationBudgetStop](request_budget.md)，静态可定位。
- `temporary.unlink`（[request_budget.py:118](../../../src/evaluation/request_budget.py#L118)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- 静态可定位的调用方：[RequestBudget.__post_init__](request_budget.md)、[RequestBudget.reserve](request_budget.md)、[RequestBudget.record](request_budget.md)。

**状态、副作用与异常**：
- 显式状态/容器赋值：`self.stopped_reason`。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：`EvaluationBudgetStop(self.stopped_reason)`。
- 本地捕获：`OSError`。


---

# RequestBudget.settle ⭐⭐

**位置与等级**：[request_budget.py:120](../../../src/evaluation/request_budget.py#L120)；局部辅助逻辑，需理解其调用条件与失败传播。

**签名**：`async def settle(self) -> None`。

**作用**：Account already dispatched requests before closing a validation run.

**输入与输出**：
- 输入：无业务参数（或仅隐式接收实例）。
- 输出类型：`None`；具体返回路径见流程步骤。

**处理流程**：
1. 检查 `self.active_tasks`；按条件分流，else 分支不存在。
2. 检查 `any((row.get('status') == 'pending' for row in self.calls))`；按条件分流，else 分支不存在。

**关键条件与保护**：
- [request_budget.py:122](../../../src/evaluation/request_budget.py#L122)：`self.active_tasks`，不满足时跳过本分支。
- [request_budget.py:125](../../../src/evaluation/request_budget.py#L125)：`any((row.get('status') == 'pending' for row in self.calls))`，不满足时跳过本分支。

**调用与被调用**：
- `asyncio.gather`（[request_budget.py:123](../../../src/evaluation/request_budget.py#L123)）：来自 `asyncio`；具体实现可能由依赖注入或运行时分派决定。
- `self.active_tasks.clear`（[request_budget.py:124](../../../src/evaluation/request_budget.py#L124)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `any`（[request_budget.py:125](../../../src/evaluation/request_budget.py#L125)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `row.get`（[request_budget.py:125](../../../src/evaluation/request_budget.py#L125)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- 静态扫描未定位直接调用方；可能通过路由注册、LangGraph 节点、协议方法或依赖注入动态调用，不据此判断为死代码。

**状态、副作用与异常**：
- 显式状态/容器赋值：`self.accounting_complete`、`self.stopped_reason`。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：未见 `raise`；下游异常可能继续上抛。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。


---

# RequestBudget.estimate ⭐⭐

**位置与等级**：[request_budget.py:129](../../../src/evaluation/request_budget.py#L129)；局部辅助逻辑，需理解其调用条件与失败传播。

**签名**：`def estimate(self, body: dict[str, Any]) -> int`。

**作用**：处理 `estimate` 对应步骤；下列步骤依据函数体的实际控制流和调用点整理。

**输入与输出**：
- 输入：`body`（dict[str, Any]）。
- 输出类型：`int`；具体返回路径见流程步骤。

**处理流程**：
1. 更新 `text_bytes, images`，值来自 `0`。
2. 遍历 `body.get('messages', [])`，逐项处理 `message`。
3. 返回 `text_bytes + images * 8192 + int(body.get(<字符串常量>, self.max_output_tokens)) + 1024`。

**关键条件与保护**：
- [request_budget.py:133](../../../src/evaluation/request_budget.py#L133)：`isinstance(content, str)`，不满足时有 else 分支。
- [request_budget.py:135](../../../src/evaluation/request_budget.py#L135)：`isinstance(content, list)`，不满足时跳过本分支。
- [request_budget.py:137](../../../src/evaluation/request_budget.py#L137)：`part.get('type') == 'image_url'`，不满足时有 else 分支。

**调用与被调用**：
- `body.get`（[request_budget.py:131](../../../src/evaluation/request_budget.py#L131)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `message.get`（[request_budget.py:132](../../../src/evaluation/request_budget.py#L132)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `isinstance`（[request_budget.py:133](../../../src/evaluation/request_budget.py#L133)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `len`（[request_budget.py:134](../../../src/evaluation/request_budget.py#L134)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `content.encode`（[request_budget.py:134](../../../src/evaluation/request_budget.py#L134)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `part.get`（[request_budget.py:137](../../../src/evaluation/request_budget.py#L137)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `str(part.get('text', '')).encode`（[request_budget.py:140](../../../src/evaluation/request_budget.py#L140)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `str`（[request_budget.py:140](../../../src/evaluation/request_budget.py#L140)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `int`（[request_budget.py:142](../../../src/evaluation/request_budget.py#L142)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- 静态扫描未定位直接调用方；可能通过路由注册、LangGraph 节点、协议方法或依赖注入动态调用，不据此判断为死代码。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：未见 `raise`；下游异常可能继续上抛。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。


---

# RequestBudget.reserve ⭐⭐

**位置与等级**：[request_budget.py:145](../../../src/evaluation/request_budget.py#L145)；局部辅助逻辑，需理解其调用条件与失败传播。

**签名**：`async def reserve(self, estimate: int, requested_model: str | None=None) -> int`。

**作用**：处理 `reserve` 对应步骤；下列步骤依据函数体的实际控制流和调用点整理。

**输入与输出**：
- 输入：`estimate`（int）；`requested_model`（str | None；默认 `None`）。
- 输出类型：`int`；具体返回路径见流程步骤。

**处理流程**：
1. 进入上下文 `self.lock`，由上下文管理器控制资源释放或事务范围。

**关键条件与保护**：
- [request_budget.py:147](../../../src/evaluation/request_budget.py#L147)：`self.stopped_reason or self.total_tokens >= self.stop_at`，不满足时跳过本分支。
- [request_budget.py:149](../../../src/evaluation/request_budget.py#L149)：`self.total_tokens + self.reserved_tokens + estimate > self.limit`，不满足时跳过本分支。

**调用与被调用**：
- `EvaluationBudgetStop`（调用点 [request_budget.py:148](../../../src/evaluation/request_budget.py#L148)）→ [EvaluationBudgetStop](request_budget.md)，静态可定位。
- `len`（[request_budget.py:153](../../../src/evaluation/request_budget.py#L153)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `self.calls.append`（[request_budget.py:154](../../../src/evaluation/request_budget.py#L154)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `time.time`（[request_budget.py:160](../../../src/evaluation/request_budget.py#L160)）：来自 `time`；具体实现可能由依赖注入或运行时分派决定。
- `self._persist`（调用点 [request_budget.py:164](../../../src/evaluation/request_budget.py#L164)）→ [RequestBudget._persist](request_budget.md)，静态可定位。
- 静态扫描未定位直接调用方；可能通过路由注册、LangGraph 节点、协议方法或依赖注入动态调用，不据此判断为死代码。

**状态、副作用与异常**：
- 显式状态/容器赋值：`self.stopped_reason`、`self.reserved_tokens`。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：`EvaluationBudgetStop(self.stopped_reason or <字符串常量>)`、`EvaluationBudgetStop(self.stopped_reason)`。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。


---

# RequestBudget.record ⭐⭐

**位置与等级**：[request_budget.py:167](../../../src/evaluation/request_budget.py#L167)；局部辅助逻辑，需理解其调用条件与失败传播。

**签名**：`async def record(self, estimate: int, response: httpx.Response, number: int) -> None`。

**作用**：处理 `record` 对应步骤；下列步骤依据函数体的实际控制流和调用点整理。

**输入与输出**：
- 输入：`estimate`（int）；`response`（httpx.Response）；`number`（int）。
- 输出类型：`None`；具体返回路径见流程步骤。

**处理流程**：
1. 进入上下文 `self.lock`，由上下文管理器控制资源释放或事务范围。

**关键条件与保护**：
- [request_budget.py:178](../../../src/evaluation/request_budget.py#L178)：`response.is_success`，不满足时有 else 分支。
- [request_budget.py:183](../../../src/evaluation/request_budget.py#L183)：`tokens <= 0`，不满足时跳过本分支。
- [request_budget.py:202](../../../src/evaluation/request_budget.py#L202)：`response.status_code in {401, 403, 404}`，不满足时有 else 分支。
- [request_budget.py:211](../../../src/evaluation/request_budget.py#L211)：`self.total_tokens > self.limit`，不满足时跳过本分支。
- [request_budget.py:214](../../../src/evaluation/request_budget.py#L214)：`self.stopped_reason`，不满足时跳过本分支。

**调用与被调用**：
- `row.update`（[request_budget.py:171](../../../src/evaluation/request_budget.py#L171)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `time.time`（[request_budget.py:175](../../../src/evaluation/request_budget.py#L175)）：来自 `time`；具体实现可能由依赖注入或运行时分派决定。
- `response.json`（[request_budget.py:180](../../../src/evaluation/request_budget.py#L180)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `int`（[request_budget.py:182](../../../src/evaluation/request_budget.py#L182)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `ValueError`（[request_budget.py:184](../../../src/evaluation/request_budget.py#L184)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `payload.get`（[request_budget.py:187](../../../src/evaluation/request_budget.py#L187)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `usage.get`（[request_budget.py:189](../../../src/evaluation/request_budget.py#L189)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `(payload.get('choices') or [{}])[0].get`（[request_budget.py:193](../../../src/evaluation/request_budget.py#L193)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `self._persist`（调用点 [request_budget.py:213](../../../src/evaluation/request_budget.py#L213)）→ [RequestBudget._persist](request_budget.md)，静态可定位。
- `EvaluationBudgetStop`（调用点 [request_budget.py:215](../../../src/evaluation/request_budget.py#L215)）→ [EvaluationBudgetStop](request_budget.md)，静态可定位。
- 静态扫描未定位直接调用方；可能通过路由注册、LangGraph 节点、协议方法或依赖注入动态调用，不据此判断为死代码。

**状态、副作用与异常**：
- 显式状态/容器赋值：`self.reserved_tokens`、`self.total_tokens`、`self.accounting_complete`、`self.stopped_reason`。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：`ValueError(<字符串常量>)`、`EvaluationBudgetStop(self.stopped_reason)`。
- 本地捕获：`(ValueError, KeyError, TypeError)`。


---

# BudgetedTransport ⭐⭐⭐

**位置与等级**：[request_budget.py:218](../../../src/evaluation/request_budget.py#L218)；关键支撑逻辑，影响候选、证据或接口的正确传递。

**职责**：本模块的对象实现或数据契约；具体语义由字段、基类和方法共同决定。基类：`httpx.AsyncBaseTransport`。

**字段与类级约束**：
- 类体未直接声明字段；实例状态请看 `__init__` 及方法中的赋值。

**内部成员**：`BudgetedTransport.__init__`、`BudgetedTransport.handle_async_request`、`BudgetedTransport._send`、`BudgetedTransport._send_serial`


---

# BudgetedTransport.__init__ ⭐⭐

**位置与等级**：[request_budget.py:219](../../../src/evaluation/request_budget.py#L219)；局部辅助逻辑，需理解其调用条件与失败传播。

**签名**：`def __init__(self, budget: RequestBudget, inner: httpx.AsyncBaseTransport | None=None) -> None`。

**作用**：初始化对象并保存依赖或配置；需检查是否创建持久化资源。

**输入与输出**：
- 输入：`budget`（RequestBudget）；`inner`（httpx.AsyncBaseTransport | None；默认 `None`）。
- 输出类型：`None`；具体返回路径见流程步骤。

**处理流程**：
1. 更新 `self.budget`，值来自 `budget`。
2. 更新 `self.inner`，值来自 `inner`。

**调用与被调用**：
- 无显式函数调用，或仅声明协议/常量。
- 静态扫描未定位直接调用方；可能通过路由注册、LangGraph 节点、协议方法或依赖注入动态调用，不据此判断为死代码。

**状态、副作用与异常**：
- 显式状态/容器赋值：`self.budget`、`self.inner`。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：未见 `raise`；下游异常可能继续上抛。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。


---

# BudgetedTransport.handle_async_request ⭐⭐

**位置与等级**：[request_budget.py:225](../../../src/evaluation/request_budget.py#L225)；局部辅助逻辑，需理解其调用条件与失败传播。

**签名**：`async def handle_async_request(self, request: httpx.Request) -> httpx.Response`。

**作用**：处理 `handle_async_request` 对应步骤；下列步骤依据函数体的实际控制流和调用点整理。

**输入与输出**：
- 输入：`request`（httpx.Request）。
- 输出类型：`httpx.Response`；具体返回路径见流程步骤。

**处理流程**：
1. 更新 `body`，值来自 `json.loads(await request.aread())`。
2. 调用 `body.setdefault`，结果未直接赋值。
3. 检查 `'aliyuncs.com' in request.url.host and str(body.get('model', '')).startswith('qwen')`；按条件分流，else 分支不存在。
4. 更新 `task`，值来自 `asyncio.create_task(self._send(request, body))`。
5. 调用 `self.budget.active_tasks.append`，结果未直接赋值。
6. 捕获 asyncio.CancelledError；另检查 finally/else 的清理和传播。

**关键条件与保护**：
- [request_budget.py:229](../../../src/evaluation/request_budget.py#L229)：`'aliyuncs.com' in request.url.host and str(body.get('model', '')).startswith('qwen')`，不满足时跳过本分支。

**调用与被调用**：
- `json.loads`（[request_budget.py:226](../../../src/evaluation/request_budget.py#L226)）：来自 `json`；具体实现可能由依赖注入或运行时分派决定。
- `request.aread`（[request_budget.py:226](../../../src/evaluation/request_budget.py#L226)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `body.setdefault`（[request_budget.py:227](../../../src/evaluation/request_budget.py#L227)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `str(body.get('model', '')).startswith`（[request_budget.py:229](../../../src/evaluation/request_budget.py#L229)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `str`（[request_budget.py:229](../../../src/evaluation/request_budget.py#L229)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `body.get`（[request_budget.py:229](../../../src/evaluation/request_budget.py#L229)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `asyncio.create_task`（[request_budget.py:231](../../../src/evaluation/request_budget.py#L231)）：来自 `asyncio`；具体实现可能由依赖注入或运行时分派决定。
- `self._send`（调用点 [request_budget.py:231](../../../src/evaluation/request_budget.py#L231)）→ [BudgetedTransport._send](request_budget.md)，静态可定位。
- `self.budget.active_tasks.append`（[request_budget.py:232](../../../src/evaluation/request_budget.py#L232)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `asyncio.shield`（[request_budget.py:234](../../../src/evaluation/request_budget.py#L234)）：来自 `asyncio`；具体实现可能由依赖注入或运行时分派决定。
- 静态扫描未定位直接调用方；可能通过路由注册、LangGraph 节点、协议方法或依赖注入动态调用，不据此判断为死代码。

**状态、副作用与异常**：
- 显式状态/容器赋值：`body['enable_thinking']`、`self.budget.stopped_reason`。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：`重新抛出`。
- 本地捕获：`asyncio.CancelledError`。


---

# BudgetedTransport._send ⭐⭐

**位置与等级**：[request_budget.py:239](../../../src/evaluation/request_budget.py#L239)；局部辅助逻辑，需理解其调用条件与失败传播。

**签名**：`async def _send(self, request: httpx.Request, body: dict[str, Any]) -> httpx.Response`。

**作用**：内部辅助步骤；将参数转换为本模块所需的中间对象或操作结果。

**输入与输出**：
- 输入：`request`（httpx.Request）；`body`（dict[str, Any]）。
- 输出类型：`httpx.Response`；具体返回路径见流程步骤。

**处理流程**：
1. 进入上下文 `self.budget.request_gate`，由上下文管理器控制资源释放或事务范围。

**调用与被调用**：
- `self._send_serial`（调用点 [request_budget.py:241](../../../src/evaluation/request_budget.py#L241)）→ [BudgetedTransport._send_serial](request_budget.md)，静态可定位。
- 静态可定位的调用方：[BudgetedTransport.handle_async_request](request_budget.md)。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：未见 `raise`；下游异常可能继续上抛。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。


---

# BudgetedTransport._send_serial ⭐⭐

**位置与等级**：[request_budget.py:243](../../../src/evaluation/request_budget.py#L243)；局部辅助逻辑，需理解其调用条件与失败传播。

**签名**：`async def _send_serial(self, request: httpx.Request, body: dict[str, Any]) -> httpx.Response`。

**作用**：内部辅助步骤；将参数转换为本模块所需的中间对象或操作结果。

**输入与输出**：
- 输入：`request`（httpx.Request）；`body`（dict[str, Any]）。
- 输出类型：`httpx.Response`；具体返回路径见流程步骤。

**处理流程**：
1. 更新 `estimate`，值来自 `self.budget.estimate(body)`。
2. 更新 `number`，值来自 `await self.budget.reserve(estimate, str(body.get('model', '')))`。
3. 更新 `forwarded`，值来自 `httpx.Request(request.method, request.url, headers={key: value for key, value in request.headers.it…`。
4. 更新 `inner`，值来自 `self.inner or httpx.AsyncHTTPTransport()`。
5. 捕获 Exception；另检查 finally/else 的清理和传播。
6. 等待 `self.budget.record(estimate, response, number)` 完成。
7. 返回 `response`。

**关键条件与保护**：
- [request_budget.py:272](../../../src/evaluation/request_budget.py#L272)：`self.inner is None`，不满足时跳过本分支。

**调用与被调用**：
- `self.budget.estimate`（[request_budget.py:244](../../../src/evaluation/request_budget.py#L244)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `self.budget.reserve`（[request_budget.py:245](../../../src/evaluation/request_budget.py#L245)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `str`（[request_budget.py:245](../../../src/evaluation/request_budget.py#L245)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `body.get`（[request_budget.py:245](../../../src/evaluation/request_budget.py#L245)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `httpx.Request`（[request_budget.py:246](../../../src/evaluation/request_budget.py#L246)）：来自 `httpx`；具体实现可能由依赖注入或运行时分派决定。
- `request.headers.items`（[request_budget.py:251](../../../src/evaluation/request_budget.py#L251)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `key.lower`（[request_budget.py:252](../../../src/evaluation/request_budget.py#L252)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `httpx.AsyncHTTPTransport`（[request_budget.py:257](../../../src/evaluation/request_budget.py#L257)）：来自 `httpx`；具体实现可能由依赖注入或运行时分派决定。
- `inner.handle_async_request`（[request_budget.py:259](../../../src/evaluation/request_budget.py#L259)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `response.aread`（[request_budget.py:260](../../../src/evaluation/request_budget.py#L260)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `self.budget.calls[number - 1].update`（[request_budget.py:266](../../../src/evaluation/request_budget.py#L266)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `self.budget._persist`（[request_budget.py:269](../../../src/evaluation/request_budget.py#L269)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `EvaluationBudgetStop`（调用点 [request_budget.py:270](../../../src/evaluation/request_budget.py#L270)）→ [EvaluationBudgetStop](request_budget.md)，静态可定位。
- `inner.aclose`（[request_budget.py:273](../../../src/evaluation/request_budget.py#L273)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `self.budget.record`（[request_budget.py:274](../../../src/evaluation/request_budget.py#L274)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- 静态可定位的调用方：[BudgetedTransport._send](request_budget.md)。

**状态、副作用与异常**：
- 显式状态/容器赋值：`self.budget.reserved_tokens`、`self.budget.stopped_reason`、`self.budget.accounting_complete`。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：`EvaluationBudgetStop(self.budget.stopped_reason)`。
- 本地捕获：`Exception`。


---
