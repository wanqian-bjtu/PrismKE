源码：[execution.py:1](../../../src/persistence/execution.py#L1) | 基准：`dev/v0.10@f2f34d7` | 本文件符号数：18

**模块职责**：Durable execution state, immutable transitions and private response journal.
**在系统中的位置**：图、证据、运行、审计、审核与案例的持久化；JSON/Neo4j 提供同一存储协议。
**直接依赖**：[src.domain.execution](../domain/execution.md)；外部/标准库：`collections`、`contextlib`、`datetime`、`orjson`、`pathlib`、`sqlite3`、`typing`。
**主要调用方（静态导入）**：[api/app.py](../api/app.md)、[workflow/execution.py](../workflow/execution.md)。
**阅读提示**：下列流程根据当前源码控制流整理；`self`/接口对象的实际类型可能在运行时注入，未能静态解析的调用会明确标注。链接指向源码行或对应讲解文件。

---

# ExecutionConflict ⭐⭐⭐⭐

**位置与等级**：[execution.py:20](../../../src/persistence/execution.py#L20)；承担主要 Agent、应用服务或审核/执行入口，跨模块影响显著。

**职责**：失败类型；调用方可据此区分可恢复、阻断和一般错误。基类：`ValueError`。

**字段与类级约束**：
- 类体未直接声明字段；实例状态请看 `__init__` 及方法中的赋值。

**内部成员**：此类未直接定义方法；字段/继承行为见源码。


---

# ExecutionRepository ⭐⭐⭐⭐

**位置与等级**：[execution.py:24](../../../src/persistence/execution.py#L24)；承担主要 Agent、应用服务或审核/执行入口，跨模块影响显著。

**职责**：存储接口或实现；方法决定数据读取、持久化与并发边界。基类：无显式基类。

**字段与类级约束**：
- 类体未直接声明字段；实例状态请看 `__init__` 及方法中的赋值。

**内部成员**：`ExecutionRepository.__init__`、`ExecutionRepository.connect`、`ExecutionRepository.get`、`ExecutionRepository.list_tasks`、`ExecutionRepository._write`、`ExecutionRepository.register`、`ExecutionRepository.change`、`ExecutionRepository.events`、`ExecutionRepository.begin_request`、`ExecutionRepository.finish_request`、`ExecutionRepository.unknown`、`ExecutionRepository.requests`、`ExecutionRepository.reconcile_request`、`ExecutionRepository.reconciliations`、`ExecutionRepository.result`、`ExecutionRepository.put_result`


---

# ExecutionRepository.__init__ ⭐⭐

**位置与等级**：[execution.py:25](../../../src/persistence/execution.py#L25)；局部辅助逻辑，需理解其调用条件与失败传播。

**签名**：`def __init__(self, path: Path) -> None`。

**作用**：初始化对象并保存依赖或配置；需检查是否创建持久化资源。

**输入与输出**：
- 输入：`path`（Path）。
- 输出类型：`None`；具体返回路径见流程步骤。

**处理流程**：
1. 更新 `self.path`，值来自 `path`。
2. 调用 `path.parent.mkdir`，结果未直接赋值。
3. 进入上下文 `self.connect()`，由上下文管理器控制资源释放或事务范围。

**调用与被调用**：
- `path.parent.mkdir`（[execution.py:27](../../../src/persistence/execution.py#L27)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `self.connect`（调用点 [execution.py:28](../../../src/persistence/execution.py#L28)）→ [ExecutionRepository.connect](execution.md)，静态可定位。
- `db.executescript`（[execution.py:29](../../../src/persistence/execution.py#L29)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- 静态扫描未定位直接调用方；可能通过路由注册、LangGraph 节点、协议方法或依赖注入动态调用，不据此判断为死代码。

**状态、副作用与异常**：
- 显式状态/容器赋值：`self.path`。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：未见 `raise`；下游异常可能继续上抛。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。
- 恢复/幂等性：仅在代码有检查点、事务、请求编号或显式去重时才成立；此函数不能单凭名称视为可安全重试。


---

# ExecutionRepository.connect ⭐⭐

**位置与等级**：[execution.py:62](../../../src/persistence/execution.py#L62)；局部辅助逻辑，需理解其调用条件与失败传播。

**签名**：`def connect(self) -> Iterator[sqlite3.Connection]`。

**装饰器/路由**：`contextmanager`。

**作用**：处理 `connect` 对应步骤；下列步骤依据函数体的实际控制流和调用点整理。

**输入与输出**：
- 输入：无业务参数（或仅隐式接收实例）。
- 输出类型：`Iterator[sqlite3.Connection]`；具体返回路径见流程步骤。

**处理流程**：
1. 更新 `db`，值来自 `sqlite3.connect(self.path, timeout=30)`。
2. 调用 `db.execute`，结果未直接赋值。
3. 捕获 无显式捕获；另检查 finally/else 的清理和传播。

**调用与被调用**：
- `sqlite3.connect`（[execution.py:63](../../../src/persistence/execution.py#L63)）：来自 `sqlite3`；具体实现可能由依赖注入或运行时分派决定。
- `db.execute`（[execution.py:64](../../../src/persistence/execution.py#L64)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `db.close`（[execution.py:69](../../../src/persistence/execution.py#L69)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- 静态可定位的调用方：[ExecutionRepository.__init__](execution.md)、[ExecutionRepository.get](execution.md)、[ExecutionRepository.list_tasks](execution.md)、[ExecutionRepository.register](execution.md)、[ExecutionRepository.change](execution.md)、[ExecutionRepository.events](execution.md)、[ExecutionRepository.begin_request](execution.md)、[ExecutionRepository.finish_request](execution.md)、[ExecutionRepository.unknown](execution.md)、[ExecutionRepository.requests](execution.md)。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：未见 `raise`；下游异常可能继续上抛。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。
- 恢复/幂等性：仅在代码有检查点、事务、请求编号或显式去重时才成立；此函数不能单凭名称视为可安全重试。


---

# ExecutionRepository.get ⭐⭐

**位置与等级**：[execution.py:71](../../../src/persistence/execution.py#L71)；局部辅助逻辑，需理解其调用条件与失败传播。

**签名**：`def get(self, run_id: str) -> ExecutionTask | None`。

**作用**：处理 `get` 对应步骤；下列步骤依据函数体的实际控制流和调用点整理。

**输入与输出**：
- 输入：`run_id`（str；目标运行的稳定标识）。
- 输出类型：`ExecutionTask | None`；具体返回路径见流程步骤。

**处理流程**：
1. 进入上下文 `self.connect()`，由上下文管理器控制资源释放或事务范围。
2. 返回 `ExecutionTask.model_validate(orjson.loads(row[0])) if row else None`。

**调用与被调用**：
- `self.connect`（调用点 [execution.py:72](../../../src/persistence/execution.py#L72)）→ [ExecutionRepository.connect](execution.md)，静态可定位。
- `db.execute(<字符串常量>, (run_id,)).fetchone`（[execution.py:73](../../../src/persistence/execution.py#L73)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `db.execute`（[execution.py:73](../../../src/persistence/execution.py#L73)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `ExecutionTask.model_validate`（[execution.py:74](../../../src/persistence/execution.py#L74)）：来自 `src.domain.execution.ExecutionTask`；具体实现可能由依赖注入或运行时分派决定。
- `orjson.loads`（[execution.py:74](../../../src/persistence/execution.py#L74)）：来自 `orjson`；具体实现可能由依赖注入或运行时分派决定。
- 静态扫描未定位直接调用方；可能通过路由注册、LangGraph 节点、协议方法或依赖注入动态调用，不据此判断为死代码。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：未见 `raise`；下游异常可能继续上抛。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。
- 恢复/幂等性：仅在代码有检查点、事务、请求编号或显式去重时才成立；此函数不能单凭名称视为可安全重试。


---

# ExecutionRepository.list_tasks ⭐⭐

**位置与等级**：[execution.py:76](../../../src/persistence/execution.py#L76)；局部辅助逻辑，需理解其调用条件与失败传播。

**签名**：`def list_tasks(self) -> list[ExecutionTask]`。

**作用**：读取或组装对应资源；是否纯只读及异常行为需结合下方显式调用与状态写入判断。

**输入与输出**：
- 输入：无业务参数（或仅隐式接收实例）。
- 输出类型：`list[ExecutionTask]`；具体返回路径见流程步骤。

**处理流程**：
1. 进入上下文 `self.connect()`，由上下文管理器控制资源释放或事务范围。
2. 返回 `[ExecutionTask.model_validate(orjson.loads(r[0])) for r in rows]`。

**调用与被调用**：
- `self.connect`（调用点 [execution.py:77](../../../src/persistence/execution.py#L77)）→ [ExecutionRepository.connect](execution.md)，静态可定位。
- `db.execute(<字符串常量>).fetchall`（[execution.py:78](../../../src/persistence/execution.py#L78)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `db.execute`（[execution.py:78](../../../src/persistence/execution.py#L78)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `ExecutionTask.model_validate`（[execution.py:79](../../../src/persistence/execution.py#L79)）：来自 `src.domain.execution.ExecutionTask`；具体实现可能由依赖注入或运行时分派决定。
- `orjson.loads`（[execution.py:79](../../../src/persistence/execution.py#L79)）：来自 `orjson`；具体实现可能由依赖注入或运行时分派决定。
- 静态扫描未定位直接调用方；可能通过路由注册、LangGraph 节点、协议方法或依赖注入动态调用，不据此判断为死代码。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：未见 `raise`；下游异常可能继续上抛。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。
- 恢复/幂等性：仅在代码有检查点、事务、请求编号或显式去重时才成立；此函数不能单凭名称视为可安全重试。


---

# ExecutionRepository._write ⭐⭐

**位置与等级**：[execution.py:82](../../../src/persistence/execution.py#L82)；局部辅助逻辑，需理解其调用条件与失败传播。

**签名**：`def _write(db: sqlite3.Connection, task: ExecutionTask) -> None`。

**装饰器/路由**：`staticmethod`。

**作用**：内部辅助步骤；将参数转换为本模块所需的中间对象或操作结果。

**输入与输出**：
- 输入：`db`（sqlite3.Connection）；`task`（ExecutionTask）。
- 输出类型：`None`；具体返回路径见流程步骤。

**处理流程**：
1. 更新 `task.updated_at`，值来自 `datetime.now(UTC)`。
2. 更新 `payload`，值来自 `orjson.dumps(task.model_dump(mode='json'))`。
3. 调用 `db.execute`，结果未直接赋值。
4. 调用 `db.execute`，结果未直接赋值。

**调用与被调用**：
- `datetime.now`（[execution.py:83](../../../src/persistence/execution.py#L83)）：来自 `datetime.datetime`；具体实现可能由依赖注入或运行时分派决定。
- `orjson.dumps`（[execution.py:84](../../../src/persistence/execution.py#L84)）：来自 `orjson`；具体实现可能由依赖注入或运行时分派决定。
- `task.model_dump`（[execution.py:84](../../../src/persistence/execution.py#L84)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `db.execute`（[execution.py:85](../../../src/persistence/execution.py#L85)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- 静态可定位的调用方：[ExecutionRepository.register](execution.md)、[ExecutionRepository.change](execution.md)、[ExecutionRepository.reconcile_request](execution.md)。

**状态、副作用与异常**：
- 显式状态/容器赋值：`task.updated_at`。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：未见 `raise`；下游异常可能继续上抛。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。
- 恢复/幂等性：仅在代码有检查点、事务、请求编号或显式去重时才成立；此函数不能单凭名称视为可安全重试。


---

# ExecutionRepository.register ⭐⭐

**位置与等级**：[execution.py:88](../../../src/persistence/execution.py#L88)；局部辅助逻辑，需理解其调用条件与失败传播。

**签名**：`def register(self, task: ExecutionTask) -> ExecutionTask`。

**作用**：处理 `register` 对应步骤；下列步骤依据函数体的实际控制流和调用点整理。

**输入与输出**：
- 输入：`task`（ExecutionTask）。
- 输出类型：`ExecutionTask`；具体返回路径见流程步骤。

**处理流程**：
1. 进入上下文 `self.connect()`，由上下文管理器控制资源释放或事务范围。
2. 返回 `task`。

**关键条件与保护**：
- [execution.py:92](../../../src/persistence/execution.py#L92)：`row`，不满足时跳过本分支。

**调用与被调用**：
- `self.connect`（调用点 [execution.py:89](../../../src/persistence/execution.py#L89)）→ [ExecutionRepository.connect](execution.md)，静态可定位。
- `db.execute`（[execution.py:90](../../../src/persistence/execution.py#L90)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `db.execute(<字符串常量>, (task.run_id,)).fetchone`（[execution.py:91](../../../src/persistence/execution.py#L91)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `ExecutionTask.model_validate`（[execution.py:93](../../../src/persistence/execution.py#L93)）：来自 `src.domain.execution.ExecutionTask`；具体实现可能由依赖注入或运行时分派决定。
- `orjson.loads`（[execution.py:93](../../../src/persistence/execution.py#L93)）：来自 `orjson`；具体实现可能由依赖注入或运行时分派决定。
- `self._write`（调用点 [execution.py:94](../../../src/persistence/execution.py#L94)）→ [ExecutionRepository._write](execution.md)，静态可定位。
- 静态扫描未定位直接调用方；可能通过路由注册、LangGraph 节点、协议方法或依赖注入动态调用，不据此判断为死代码。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：未见 `raise`；下游异常可能继续上抛。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。
- 恢复/幂等性：仅在代码有检查点、事务、请求编号或显式去重时才成立；此函数不能单凭名称视为可安全重试。


---

# ExecutionRepository.change ⭐⭐

**位置与等级**：[execution.py:97](../../../src/persistence/execution.py#L97)；局部辅助逻辑，需理解其调用条件与失败传播。

**签名**：`def change(self, run_id: str, action: Callable[[ExecutionTask], None], expected_version: int | None=None, command: tuple[str, str] | None=None) -> ExecutionTask`。

**作用**：处理 `change` 对应步骤；下列步骤依据函数体的实际控制流和调用点整理。

**输入与输出**：
- 输入：`run_id`（str；目标运行的稳定标识）；`action`（Callable[[ExecutionTask], None]）；`expected_version`（int | None；默认 `None`；乐观并发版本；过期提交应拒绝）；`command`（tuple[str, str] | None；默认 `None`）。
- 输出类型：`ExecutionTask`；具体返回路径见流程步骤。

**处理流程**：
1. 进入上下文 `self.connect()`，由上下文管理器控制资源释放或事务范围。
2. 返回 `task`。

**关键条件与保护**：
- [execution.py:106](../../../src/persistence/execution.py#L106)：`command`，不满足时跳过本分支。
- [execution.py:111](../../../src/persistence/execution.py#L111)：`old`，不满足时跳过本分支。
- [execution.py:112](../../../src/persistence/execution.py#L112)：`old[0] != command[1]`，不满足时跳过本分支。
- [execution.py:116](../../../src/persistence/execution.py#L116)：`not row`，不满足时跳过本分支。
- [execution.py:119](../../../src/persistence/execution.py#L119)：`expected_version is not None and task.version != expected_version`，不满足时跳过本分支。
- [execution.py:124](../../../src/persistence/execution.py#L124)：`command`，不满足时跳过本分支。

**调用与被调用**：
- `self.connect`（调用点 [execution.py:104](../../../src/persistence/execution.py#L104)）→ [ExecutionRepository.connect](execution.md)，静态可定位。
- `db.execute`（[execution.py:105](../../../src/persistence/execution.py#L105)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `db.execute(<字符串常量>, (run_id, command[0])).fetchone`（[execution.py:107](../../../src/persistence/execution.py#L107)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `ExecutionConflict`（调用点 [execution.py:113](../../../src/persistence/execution.py#L113)）→ [ExecutionConflict](execution.md)，静态可定位。
- `ExecutionTask.model_validate`（[execution.py:114](../../../src/persistence/execution.py#L114)）：来自 `src.domain.execution.ExecutionTask`；具体实现可能由依赖注入或运行时分派决定。
- `orjson.loads`（[execution.py:114](../../../src/persistence/execution.py#L114)）：来自 `orjson`；具体实现可能由依赖注入或运行时分派决定。
- `db.execute(<字符串常量>, (run_id,)).fetchone`（[execution.py:115](../../../src/persistence/execution.py#L115)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `action`（[execution.py:121](../../../src/persistence/execution.py#L121)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `self._write`（调用点 [execution.py:123](../../../src/persistence/execution.py#L123)）→ [ExecutionRepository._write](execution.md)，静态可定位。
- `orjson.dumps`（[execution.py:130](../../../src/persistence/execution.py#L130)）：来自 `orjson`；具体实现可能由依赖注入或运行时分派决定。
- `task.model_dump`（[execution.py:130](../../../src/persistence/execution.py#L130)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- 静态扫描未定位直接调用方；可能通过路由注册、LangGraph 节点、协议方法或依赖注入动态调用，不据此判断为死代码。

**状态、副作用与异常**：
- 显式状态/容器赋值：`task.version`。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：`ExecutionConflict('REQUEST_ID_REUSED')`、`ExecutionConflict('EXECUTION_NOT_REGISTERED')`、`ExecutionConflict('STALE_EXECUTION_VERSION')`。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。
- 恢复/幂等性：仅在代码有检查点、事务、请求编号或显式去重时才成立；此函数不能单凭名称视为可安全重试。


---

# ExecutionRepository.events ⭐⭐

**位置与等级**：[execution.py:135](../../../src/persistence/execution.py#L135)；局部辅助逻辑，需理解其调用条件与失败传播。

**签名**：`def events(self, run_id: str) -> list[ExecutionEvent]`。

**作用**：处理 `events` 对应步骤；下列步骤依据函数体的实际控制流和调用点整理。

**输入与输出**：
- 输入：`run_id`（str；目标运行的稳定标识）。
- 输出类型：`list[ExecutionEvent]`；具体返回路径见流程步骤。

**处理流程**：
1. 进入上下文 `self.connect()`，由上下文管理器控制资源释放或事务范围。
2. 返回 `[ExecutionEvent(sequence=seq, **{k: v for k, v in orjson.loads(payload).items() if k in {'run_id', 'vers…`。

**调用与被调用**：
- `self.connect`（调用点 [execution.py:136](../../../src/persistence/execution.py#L136)）→ [ExecutionRepository.connect](execution.md)，静态可定位。
- `db.execute(<字符串常量>, (run_id,)).fetchall`（[execution.py:137](../../../src/persistence/execution.py#L137)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `db.execute`（[execution.py:137](../../../src/persistence/execution.py#L137)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `ExecutionEvent`（调用点 [execution.py:141](../../../src/persistence/execution.py#L141)）→ [ExecutionEvent](../domain/execution.md)，静态可定位。
- `orjson.loads(payload).items`（[execution.py:145](../../../src/persistence/execution.py#L145)）：来自 `orjson`；具体实现可能由依赖注入或运行时分派决定。
- `orjson.loads`（[execution.py:145](../../../src/persistence/execution.py#L145)）：来自 `orjson`；具体实现可能由依赖注入或运行时分派决定。
- 静态扫描未定位直接调用方；可能通过路由注册、LangGraph 节点、协议方法或依赖注入动态调用，不据此判断为死代码。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：未见 `raise`；下游异常可能继续上抛。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。
- 恢复/幂等性：仅在代码有检查点、事务、请求编号或显式去重时才成立；此函数不能单凭名称视为可安全重试。


---

# ExecutionRepository.begin_request ⭐⭐

**位置与等级**：[execution.py:153](../../../src/persistence/execution.py#L153)；局部辅助逻辑，需理解其调用条件与失败传播。

**签名**：`def begin_request(self, run_id: str, key: str, metadata: dict[str, Any]) -> dict[str, Any] | None`。

**作用**：处理 `begin_request` 对应步骤；下列步骤依据函数体的实际控制流和调用点整理。

**输入与输出**：
- 输入：`run_id`（str；目标运行的稳定标识）；`key`（str）；`metadata`（dict[str, Any]）。
- 输出类型：`dict[str, Any] | None`；具体返回路径见流程步骤。

**处理流程**：
1. 进入上下文 `self.connect()`，由上下文管理器控制资源释放或事务范围。
2. 返回 `None`。

**关键条件与保护**：
- [execution.py:161](../../../src/persistence/execution.py#L161)：`old and old[0] == 'completed'`，不满足时跳过本分支。
- [execution.py:163](../../../src/persistence/execution.py#L163)：`old and old[0] in {'sent', 'unknown'}`，不满足时跳过本分支。

**调用与被调用**：
- `self.connect`（调用点 [execution.py:156](../../../src/persistence/execution.py#L156)）→ [ExecutionRepository.connect](execution.md)，静态可定位。
- `db.execute`（[execution.py:157](../../../src/persistence/execution.py#L157)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `db.execute(<字符串常量>, (run_id, key)).fetchone`（[execution.py:158](../../../src/persistence/execution.py#L158)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `dict`（[execution.py:162](../../../src/persistence/execution.py#L162)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `orjson.loads`（[execution.py:162](../../../src/persistence/execution.py#L162)）：来自 `orjson`；具体实现可能由依赖注入或运行时分派决定。
- `ExecutionConflict`（调用点 [execution.py:164](../../../src/persistence/execution.py#L164)）→ [ExecutionConflict](execution.md)，静态可定位。
- `orjson.dumps`（[execution.py:171](../../../src/persistence/execution.py#L171)）：来自 `orjson`；具体实现可能由依赖注入或运行时分派决定。
- `datetime.now(UTC).isoformat`（[execution.py:174](../../../src/persistence/execution.py#L174)）：来自 `datetime.datetime`；具体实现可能由依赖注入或运行时分派决定。
- `datetime.now`（[execution.py:174](../../../src/persistence/execution.py#L174)）：来自 `datetime.datetime`；具体实现可能由依赖注入或运行时分派决定。
- 静态扫描未定位直接调用方；可能通过路由注册、LangGraph 节点、协议方法或依赖注入动态调用，不据此判断为死代码。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：`ExecutionConflict('UNKNOWN_PROVIDER_REQUEST')`。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。
- 恢复/幂等性：仅在代码有检查点、事务、请求编号或显式去重时才成立；此函数不能单凭名称视为可安全重试。


---

# ExecutionRepository.finish_request ⭐⭐

**位置与等级**：[execution.py:181](../../../src/persistence/execution.py#L181)；局部辅助逻辑，需理解其调用条件与失败传播。

**签名**：`def finish_request(self, run_id: str, key: str, status: str, response: dict[str, Any] | None=None, usage_known: bool=False) -> None`。

**作用**：处理 `finish_request` 对应步骤；下列步骤依据函数体的实际控制流和调用点整理。

**输入与输出**：
- 输入：`run_id`（str；目标运行的稳定标识）；`key`（str）；`status`（str）；`response`（dict[str, Any] | None；默认 `None`）；`usage_known`（bool；默认 `False`）。
- 输出类型：`None`；具体返回路径见流程步骤。

**处理流程**：
1. 进入上下文 `self.connect()`，由上下文管理器控制资源释放或事务范围。

**关键条件与保护**：
- [execution.py:194](../../../src/persistence/execution.py#L194)：`row is None`，不满足时跳过本分支。
- [execution.py:199](../../../src/persistence/execution.py#L199)：`metadata.get('dispatched_at')`，不满足时跳过本分支。
- [execution.py:217](../../../src/persistence/execution.py#L217)：`changed != 1`，不满足时跳过本分支。

**调用与被调用**：
- `self.connect`（调用点 [execution.py:189](../../../src/persistence/execution.py#L189)）→ [ExecutionRepository.connect](execution.md)，静态可定位。
- `db.execute`（[execution.py:190](../../../src/persistence/execution.py#L190)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `db.execute(<字符串常量>, (run_id, key)).fetchone`（[execution.py:191](../../../src/persistence/execution.py#L191)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `ExecutionConflict`（调用点 [execution.py:195](../../../src/persistence/execution.py#L195)）→ [ExecutionConflict](execution.md)，静态可定位。
- `dict`（[execution.py:196](../../../src/persistence/execution.py#L196)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `orjson.loads`（[execution.py:196](../../../src/persistence/execution.py#L196)）：来自 `orjson`；具体实现可能由依赖注入或运行时分派决定。
- `datetime.now`（[execution.py:197](../../../src/persistence/execution.py#L197)）：来自 `datetime.datetime`；具体实现可能由依赖注入或运行时分派决定。
- `settled.isoformat`（[execution.py:198](../../../src/persistence/execution.py#L198)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `metadata.get`（[execution.py:199](../../../src/persistence/execution.py#L199)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `round`（[execution.py:200](../../../src/persistence/execution.py#L200)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `(settled - datetime.fromisoformat(metadata['dispatched_at'])).total_seconds`（[execution.py:201](../../../src/persistence/execution.py#L201)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `datetime.fromisoformat`（[execution.py:201](../../../src/persistence/execution.py#L201)）：来自 `datetime.datetime`；具体实现可能由依赖注入或运行时分派决定。
- `orjson.dumps`（[execution.py:210](../../../src/persistence/execution.py#L210)）：来自 `orjson`；具体实现可能由依赖注入或运行时分派决定。
- `int`（[execution.py:211](../../../src/persistence/execution.py#L211)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- 静态扫描未定位直接调用方；可能通过路由注册、LangGraph 节点、协议方法或依赖注入动态调用，不据此判断为死代码。

**状态、副作用与异常**：
- 显式状态/容器赋值：`metadata['settled_at']`、`metadata['latency_ms']`。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：`ExecutionConflict('REQUEST_JOURNAL_MISSING')`。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。
- 恢复/幂等性：仅在代码有检查点、事务、请求编号或显式去重时才成立；此函数不能单凭名称视为可安全重试。


---

# ExecutionRepository.unknown ⭐⭐

**位置与等级**：[execution.py:220](../../../src/persistence/execution.py#L220)；局部辅助逻辑，需理解其调用条件与失败传播。

**签名**：`def unknown(self, run_id: str, *, include_sent: bool=True) -> int`。

**作用**：处理 `unknown` 对应步骤；下列步骤依据函数体的实际控制流和调用点整理。

**输入与输出**：
- 输入：`run_id`（str；目标运行的稳定标识）；`include_sent`（bool；默认 `True`）。
- 输出类型：`int`；具体返回路径见流程步骤。

**处理流程**：
1. 进入上下文 `self.connect()`，由上下文管理器控制资源释放或事务范围。

**调用与被调用**：
- `self.connect`（调用点 [execution.py:221](../../../src/persistence/execution.py#L221)）→ [ExecutionRepository.connect](execution.md)，静态可定位。
- `int`（[execution.py:222](../../../src/persistence/execution.py#L222)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `db.execute(<字符串常量>, (run_id, int(include_sent))).fetchone`（[execution.py:223](../../../src/persistence/execution.py#L223)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `db.execute`（[execution.py:223](../../../src/persistence/execution.py#L223)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- 静态扫描未定位直接调用方；可能通过路由注册、LangGraph 节点、协议方法或依赖注入动态调用，不据此判断为死代码。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：未见 `raise`；下游异常可能继续上抛。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。
- 恢复/幂等性：仅在代码有检查点、事务、请求编号或显式去重时才成立；此函数不能单凭名称视为可安全重试。


---

# ExecutionRepository.requests ⭐⭐

**位置与等级**：[execution.py:231](../../../src/persistence/execution.py#L231)；局部辅助逻辑，需理解其调用条件与失败传播。

**签名**：`def requests(self, run_id: str) -> list[dict[str, Any]]`。

**作用**：处理 `requests` 对应步骤；下列步骤依据函数体的实际控制流和调用点整理。

**输入与输出**：
- 输入：`run_id`（str；目标运行的稳定标识）。
- 输出类型：`list[dict[str, Any]]`；具体返回路径见流程步骤。

**处理流程**：
1. 进入上下文 `self.connect()`，由上下文管理器控制资源释放或事务范围。
2. 返回 `[{'request_id': key, 'status': status, 'metadata': dict(orjson.loads(metadata)), 'usage_known': bool(usa…`。

**调用与被调用**：
- `self.connect`（调用点 [execution.py:232](../../../src/persistence/execution.py#L232)）→ [ExecutionRepository.connect](execution.md)，静态可定位。
- `db.execute(<字符串常量>, (run_id,)).fetchall`（[execution.py:233](../../../src/persistence/execution.py#L233)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `db.execute`（[execution.py:233](../../../src/persistence/execution.py#L233)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `dict`（[execution.py:242](../../../src/persistence/execution.py#L242)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `orjson.loads`（[execution.py:242](../../../src/persistence/execution.py#L242)）：来自 `orjson`；具体实现可能由依赖注入或运行时分派决定。
- `bool`（[execution.py:243](../../../src/persistence/execution.py#L243)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- 静态扫描未定位直接调用方；可能通过路由注册、LangGraph 节点、协议方法或依赖注入动态调用，不据此判断为死代码。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：未见 `raise`；下游异常可能继续上抛。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。
- 恢复/幂等性：仅在代码有检查点、事务、请求编号或显式去重时才成立；此函数不能单凭名称视为可安全重试。


---

# ExecutionRepository.reconcile_request ⭐⭐⭐⭐

**位置与等级**：[execution.py:248](../../../src/persistence/execution.py#L248)；承担主要 Agent、应用服务或审核/执行入口，跨模块影响显著。

**签名**：`def reconcile_request(self, run_id: str, decision: RequestReconciliation) -> RequestReconciliationEvent`。

**作用**：处理 `reconcile_request` 对应步骤；下列步骤依据函数体的实际控制流和调用点整理。

**输入与输出**：
- 输入：`run_id`（str；目标运行的稳定标识）；`decision`（RequestReconciliation）。
- 输出类型：`RequestReconciliationEvent`；具体返回路径见流程步骤。

**处理流程**：
1. 更新 `now`，值来自 `datetime.now(UTC)`。
2. 进入上下文 `self.connect()`，由上下文管理器控制资源释放或事务范围。
3. 返回 `RequestReconciliationEvent(sequence=sequence, **payload)`。

**关键条件与保护**：
- [execution.py:257](../../../src/persistence/execution.py#L257)：`task_row is None`，不满足时跳过本分支。
- [execution.py:260](../../../src/persistence/execution.py#L260)：`task.version != decision.expected_execution_version`，不满足时跳过本分支。
- [execution.py:262](../../../src/persistence/execution.py#L262)：`task.status in {'queued', 'running', 'cancelling'}`，不满足时跳过本分支。
- [execution.py:268](../../../src/persistence/execution.py#L268)：`request_row is None`，不满足时跳过本分支。
- [execution.py:271](../../../src/persistence/execution.py#L271)：`status not in {'sent', 'unknown'} and (not (status == 'completed' and (not usage_known)))`，不满足时跳过本分支。
- [execution.py:296](../../../src/persistence/execution.py#L296)：`cursor.lastrowid is None`，不满足时跳过本分支。

**调用与被调用**：
- `datetime.now`（[execution.py:251](../../../src/persistence/execution.py#L251)）：来自 `datetime.datetime`；具体实现可能由依赖注入或运行时分派决定。
- `self.connect`（调用点 [execution.py:252](../../../src/persistence/execution.py#L252)）→ [ExecutionRepository.connect](execution.md)，静态可定位。
- `db.execute`（[execution.py:253](../../../src/persistence/execution.py#L253)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `db.execute(<字符串常量>, (run_id,)).fetchone`（[execution.py:254](../../../src/persistence/execution.py#L254)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `ExecutionConflict`（调用点 [execution.py:258](../../../src/persistence/execution.py#L258)）→ [ExecutionConflict](execution.md)，静态可定位。
- `ExecutionTask.model_validate`（[execution.py:259](../../../src/persistence/execution.py#L259)）：来自 `src.domain.execution.ExecutionTask`；具体实现可能由依赖注入或运行时分派决定。
- `orjson.loads`（[execution.py:259](../../../src/persistence/execution.py#L259)）：来自 `orjson`；具体实现可能由依赖注入或运行时分派决定。
- `db.execute(<字符串常量>, (run_id, decision.request_id)).fetchone`（[execution.py:264](../../../src/persistence/execution.py#L264)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `int`（[execution.py:282](../../../src/persistence/execution.py#L282)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `decision.model_dump`（[execution.py:285](../../../src/persistence/execution.py#L285)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `now.isoformat`（[execution.py:287](../../../src/persistence/execution.py#L287)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `orjson.dumps`（[execution.py:291](../../../src/persistence/execution.py#L291)）：来自 `orjson`；具体实现可能由依赖注入或运行时分派决定。
- `self._write`（调用点 [execution.py:295](../../../src/persistence/execution.py#L295)）→ [ExecutionRepository._write](execution.md)，静态可定位。
- `RequestReconciliationEvent`（调用点 [execution.py:299](../../../src/persistence/execution.py#L299)）→ [RequestReconciliationEvent](../domain/execution.md)，静态可定位。
- 静态扫描未定位直接调用方；可能通过路由注册、LangGraph 节点、协议方法或依赖注入动态调用，不据此判断为死代码。

**状态、副作用与异常**：
- 显式状态/容器赋值：`task.version`、`task.reason`。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：`ExecutionConflict('EXECUTION_NOT_REGISTERED')`、`ExecutionConflict('STALE_EXECUTION_VERSION')`、`ExecutionConflict('EXECUTION_BUSY')`、`ExecutionConflict('REQUEST_JOURNAL_MISSING')`、`ExecutionConflict('REQUEST_ALREADY_SETTLED')`、`ExecutionConflict('RECONCILIATION_EVENT_NOT_SAVED')`。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。
- 恢复/幂等性：仅在代码有检查点、事务、请求编号或显式去重时才成立；此函数不能单凭名称视为可安全重试。


---

# ExecutionRepository.reconciliations ⭐⭐

**位置与等级**：[execution.py:301](../../../src/persistence/execution.py#L301)；局部辅助逻辑，需理解其调用条件与失败传播。

**签名**：`def reconciliations(self, run_id: str) -> list[RequestReconciliationEvent]`。

**作用**：处理 `reconciliations` 对应步骤；下列步骤依据函数体的实际控制流和调用点整理。

**输入与输出**：
- 输入：`run_id`（str；目标运行的稳定标识）。
- 输出类型：`list[RequestReconciliationEvent]`；具体返回路径见流程步骤。

**处理流程**：
1. 进入上下文 `self.connect()`，由上下文管理器控制资源释放或事务范围。
2. 返回 `[RequestReconciliationEvent(sequence=sequence, **orjson.loads(payload)) for sequence, payload in rows]`。

**调用与被调用**：
- `self.connect`（调用点 [execution.py:302](../../../src/persistence/execution.py#L302)）→ [ExecutionRepository.connect](execution.md)，静态可定位。
- `db.execute(<字符串常量>, (run_id,)).fetchall`（[execution.py:303](../../../src/persistence/execution.py#L303)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `db.execute`（[execution.py:303](../../../src/persistence/execution.py#L303)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `RequestReconciliationEvent`（调用点 [execution.py:309](../../../src/persistence/execution.py#L309)）→ [RequestReconciliationEvent](../domain/execution.md)，静态可定位。
- `orjson.loads`（[execution.py:309](../../../src/persistence/execution.py#L309)）：来自 `orjson`；具体实现可能由依赖注入或运行时分派决定。
- 静态扫描未定位直接调用方；可能通过路由注册、LangGraph 节点、协议方法或依赖注入动态调用，不据此判断为死代码。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：未见 `raise`；下游异常可能继续上抛。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。
- 恢复/幂等性：仅在代码有检查点、事务、请求编号或显式去重时才成立；此函数不能单凭名称视为可安全重试。


---

# ExecutionRepository.result ⭐⭐

**位置与等级**：[execution.py:313](../../../src/persistence/execution.py#L313)；局部辅助逻辑，需理解其调用条件与失败传播。

**签名**：`def result(self, run_id: str, key: str) -> dict[str, Any] | None`。

**作用**：处理 `result` 对应步骤；下列步骤依据函数体的实际控制流和调用点整理。

**输入与输出**：
- 输入：`run_id`（str；目标运行的稳定标识）；`key`（str）。
- 输出类型：`dict[str, Any] | None`；具体返回路径见流程步骤。

**处理流程**：
1. 进入上下文 `self.connect()`，由上下文管理器控制资源释放或事务范围。
2. 返回 `dict(orjson.loads(row[0])) if row else None`。

**调用与被调用**：
- `self.connect`（调用点 [execution.py:314](../../../src/persistence/execution.py#L314)）→ [ExecutionRepository.connect](execution.md)，静态可定位。
- `db.execute(<字符串常量>, (run_id, key)).fetchone`（[execution.py:315](../../../src/persistence/execution.py#L315)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `db.execute`（[execution.py:315](../../../src/persistence/execution.py#L315)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `dict`（[execution.py:318](../../../src/persistence/execution.py#L318)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `orjson.loads`（[execution.py:318](../../../src/persistence/execution.py#L318)）：来自 `orjson`；具体实现可能由依赖注入或运行时分派决定。
- 静态扫描未定位直接调用方；可能通过路由注册、LangGraph 节点、协议方法或依赖注入动态调用，不据此判断为死代码。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：未见 `raise`；下游异常可能继续上抛。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。
- 恢复/幂等性：仅在代码有检查点、事务、请求编号或显式去重时才成立；此函数不能单凭名称视为可安全重试。


---

# ExecutionRepository.put_result ⭐⭐

**位置与等级**：[execution.py:320](../../../src/persistence/execution.py#L320)；局部辅助逻辑，需理解其调用条件与失败传播。

**签名**：`def put_result(self, run_id: str, key: str, payload: dict[str, Any]) -> None`。

**作用**：处理 `put_result` 对应步骤；下列步骤依据函数体的实际控制流和调用点整理。

**输入与输出**：
- 输入：`run_id`（str；目标运行的稳定标识）；`key`（str）；`payload`（dict[str, Any]）。
- 输出类型：`None`；具体返回路径见流程步骤。

**处理流程**：
1. 进入上下文 `self.connect()`，由上下文管理器控制资源释放或事务范围。

**调用与被调用**：
- `self.connect`（调用点 [execution.py:321](../../../src/persistence/execution.py#L321)）→ [ExecutionRepository.connect](execution.md)，静态可定位。
- `db.execute`（[execution.py:322](../../../src/persistence/execution.py#L322)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `orjson.dumps`（[execution.py:323](../../../src/persistence/execution.py#L323)）：来自 `orjson`；具体实现可能由依赖注入或运行时分派决定。
- 静态扫描未定位直接调用方；可能通过路由注册、LangGraph 节点、协议方法或依赖注入动态调用，不据此判断为死代码。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：未见 `raise`；下游异常可能继续上抛。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。
- 恢复/幂等性：仅在代码有检查点、事务、请求编号或显式去重时才成立；此函数不能单凭名称视为可安全重试。


---
