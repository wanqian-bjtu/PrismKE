源码：[entity_governance.py:1](../../../src/persistence/entity_governance.py#L1) | 基准：`dev/v0.10@f2f34d7` | 本文件符号数：9

**模块职责**：Durable review queue for entity governance proposals.
**在系统中的位置**：图、证据、运行、审计、审核与案例的持久化；JSON/Neo4j 提供同一存储协议。
**直接依赖**：[src.domain](../domain/__init__.md)；外部/标准库：`__future__`、`filelock`、`orjson`、`os`、`pathlib`、`typing`、`uuid`。
**主要调用方（静态导入）**：[governance/entity_operations.py](../governance/entity_operations.md)、[persistence/__init__.py](__init__.md)。
**阅读提示**：下列流程根据当前源码控制流整理；`self`/接口对象的实际类型可能在运行时注入，未能静态解析的调用会明确标注。链接指向源码行或对应讲解文件。

---

# EntityGovernanceRepository ⭐⭐⭐⭐

**位置与等级**：[entity_governance.py:16](../../../src/persistence/entity_governance.py#L16)；承担主要 Agent、应用服务或审核/执行入口，跨模块影响显著。

**职责**：存储接口或实现；方法决定数据读取、持久化与并发边界。基类：无显式基类。

**字段与类级约束**：
- 类体未直接声明字段；实例状态请看 `__init__` 及方法中的赋值。

**内部成员**：`EntityGovernanceRepository.__init__`、`EntityGovernanceRepository._read`、`EntityGovernanceRepository._write`、`EntityGovernanceRepository.save`、`EntityGovernanceRepository.update`、`EntityGovernanceRepository.get_task`、`EntityGovernanceRepository.get_operation`、`EntityGovernanceRepository.list_tasks`


---

# EntityGovernanceRepository.__init__ ⭐⭐

**位置与等级**：[entity_governance.py:17](../../../src/persistence/entity_governance.py#L17)；局部辅助逻辑，需理解其调用条件与失败传播。

**签名**：`def __init__(self, path: Path) -> None`。

**作用**：初始化对象并保存依赖或配置；需检查是否创建持久化资源。

**输入与输出**：
- 输入：`path`（Path）。
- 输出类型：`None`；具体返回路径见流程步骤。

**处理流程**：
1. 更新 `self.path`，值来自 `path`。
2. 更新 `self.lock`，值来自 `FileLock(str(path.with_suffix(path.suffix + '.lock')))`。
3. 调用 `self.path.parent.mkdir`，结果未直接赋值。
4. 检查 `not self.path.exists()`；按条件分流，else 分支不存在。

**关键条件与保护**：
- [entity_governance.py:21](../../../src/persistence/entity_governance.py#L21)：`not self.path.exists()`，不满足时跳过本分支。

**调用与被调用**：
- `FileLock`（[entity_governance.py:19](../../../src/persistence/entity_governance.py#L19)）：来自 `filelock.FileLock`；具体实现可能由依赖注入或运行时分派决定。
- `str`（[entity_governance.py:19](../../../src/persistence/entity_governance.py#L19)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `path.with_suffix`（[entity_governance.py:19](../../../src/persistence/entity_governance.py#L19)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `self.path.parent.mkdir`（[entity_governance.py:20](../../../src/persistence/entity_governance.py#L20)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `self.path.exists`（[entity_governance.py:21](../../../src/persistence/entity_governance.py#L21)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `self._write`（调用点 [entity_governance.py:22](../../../src/persistence/entity_governance.py#L22)）→ [EntityGovernanceRepository._write](entity_governance.md)，静态可定位。
- 静态扫描未定位直接调用方；可能通过路由注册、LangGraph 节点、协议方法或依赖注入动态调用，不据此判断为死代码。

**状态、副作用与异常**：
- 显式状态/容器赋值：`self.path`、`self.lock`。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：未见 `raise`；下游异常可能继续上抛。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。
- 恢复/幂等性：仅在代码有检查点、事务、请求编号或显式去重时才成立；此函数不能单凭名称视为可安全重试。


---

# EntityGovernanceRepository._read ⭐⭐

**位置与等级**：[entity_governance.py:24](../../../src/persistence/entity_governance.py#L24)；局部辅助逻辑，需理解其调用条件与失败传播。

**签名**：`def _read(self) -> dict[str, Any]`。

**作用**：内部辅助步骤；将参数转换为本模块所需的中间对象或操作结果。

**输入与输出**：
- 输入：无业务参数（或仅隐式接收实例）。
- 输出类型：`dict[str, Any]`；具体返回路径见流程步骤。

**处理流程**：
1. 更新 `payload`，值来自 `cast(dict[str, Any], orjson.loads(self.path.read_bytes()))`。
2. 调用 `payload.setdefault`，结果未直接赋值。
3. 调用 `payload.setdefault`，结果未直接赋值。
4. 返回 `payload`。

**调用与被调用**：
- `cast`（[entity_governance.py:25](../../../src/persistence/entity_governance.py#L25)）：来自 `typing.cast`；具体实现可能由依赖注入或运行时分派决定。
- `orjson.loads`（[entity_governance.py:25](../../../src/persistence/entity_governance.py#L25)）：来自 `orjson`；具体实现可能由依赖注入或运行时分派决定。
- `self.path.read_bytes`（[entity_governance.py:25](../../../src/persistence/entity_governance.py#L25)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `payload.setdefault`（[entity_governance.py:26](../../../src/persistence/entity_governance.py#L26)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- 静态可定位的调用方：[EntityGovernanceRepository.save](entity_governance.md)、[EntityGovernanceRepository.get_task](entity_governance.md)、[EntityGovernanceRepository.get_operation](entity_governance.md)、[EntityGovernanceRepository.list_tasks](entity_governance.md)。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：未见 `raise`；下游异常可能继续上抛。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。
- 恢复/幂等性：仅在代码有检查点、事务、请求编号或显式去重时才成立；此函数不能单凭名称视为可安全重试。


---

# EntityGovernanceRepository._write ⭐⭐

**位置与等级**：[entity_governance.py:30](../../../src/persistence/entity_governance.py#L30)；局部辅助逻辑，需理解其调用条件与失败传播。

**签名**：`def _write(self, payload: dict[str, Any]) -> None`。

**作用**：内部辅助步骤；将参数转换为本模块所需的中间对象或操作结果。

**输入与输出**：
- 输入：`payload`（dict[str, Any]）。
- 输出类型：`None`；具体返回路径见流程步骤。

**处理流程**：
1. 更新 `temporary`，值来自 `self.path.with_name(f<字符串常量>)`。
2. 捕获 无显式捕获；另检查 finally/else 的清理和传播。

**调用与被调用**：
- `self.path.with_name`（[entity_governance.py:31](../../../src/persistence/entity_governance.py#L31)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `uuid4`（[entity_governance.py:31](../../../src/persistence/entity_governance.py#L31)）：来自 `uuid.uuid4`；具体实现可能由依赖注入或运行时分派决定。
- `temporary.open`（[entity_governance.py:33](../../../src/persistence/entity_governance.py#L33)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `stream.write`（[entity_governance.py:34](../../../src/persistence/entity_governance.py#L34)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `orjson.dumps`（[entity_governance.py:34](../../../src/persistence/entity_governance.py#L34)）：来自 `orjson`；具体实现可能由依赖注入或运行时分派决定。
- `stream.flush`（[entity_governance.py:35](../../../src/persistence/entity_governance.py#L35)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `os.fsync`（[entity_governance.py:36](../../../src/persistence/entity_governance.py#L36)）：来自 `os`；具体实现可能由依赖注入或运行时分派决定。
- `stream.fileno`（[entity_governance.py:36](../../../src/persistence/entity_governance.py#L36)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `os.replace`（[entity_governance.py:37](../../../src/persistence/entity_governance.py#L37)）：来自 `os`；具体实现可能由依赖注入或运行时分派决定。
- `temporary.unlink`（[entity_governance.py:39](../../../src/persistence/entity_governance.py#L39)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- 静态可定位的调用方：[EntityGovernanceRepository.__init__](entity_governance.md)、[EntityGovernanceRepository.save](entity_governance.md)。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：未见 `raise`；下游异常可能继续上抛。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。
- 恢复/幂等性：仅在代码有检查点、事务、请求编号或显式去重时才成立；此函数不能单凭名称视为可安全重试。


---

# EntityGovernanceRepository.save ⭐⭐

**位置与等级**：[entity_governance.py:41](../../../src/persistence/entity_governance.py#L41)；局部辅助逻辑，需理解其调用条件与失败传播。

**签名**：`def save(self, task: EntityReviewTask, operation: EntityOperation) -> None`。

**作用**：处理 `save` 对应步骤；下列步骤依据函数体的实际控制流和调用点整理。

**输入与输出**：
- 输入：`task`（EntityReviewTask）；`operation`（EntityOperation）。
- 输出类型：`None`；具体返回路径见流程步骤。

**处理流程**：
1. 进入上下文 `self.lock`，由上下文管理器控制资源释放或事务范围。

**调用与被调用**：
- `self._read`（调用点 [entity_governance.py:43](../../../src/persistence/entity_governance.py#L43)）→ [EntityGovernanceRepository._read](entity_governance.md)，静态可定位。
- `task.model_dump`（[entity_governance.py:44](../../../src/persistence/entity_governance.py#L44)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `operation.model_dump`（[entity_governance.py:45](../../../src/persistence/entity_governance.py#L45)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `self._write`（调用点 [entity_governance.py:46](../../../src/persistence/entity_governance.py#L46)）→ [EntityGovernanceRepository._write](entity_governance.md)，静态可定位。
- 静态可定位的调用方：[EntityGovernanceRepository.update](entity_governance.md)。

**状态、副作用与异常**：
- 显式状态/容器赋值：`data['tasks'][task.id]`、`data['operations'][operation.id]`。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：未见 `raise`；下游异常可能继续上抛。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。
- 恢复/幂等性：仅在代码有检查点、事务、请求编号或显式去重时才成立；此函数不能单凭名称视为可安全重试。


---

# EntityGovernanceRepository.update ⭐⭐

**位置与等级**：[entity_governance.py:48](../../../src/persistence/entity_governance.py#L48)；局部辅助逻辑，需理解其调用条件与失败传播。

**签名**：`def update(self, task: EntityReviewTask, operation: EntityOperation) -> None`。

**作用**：处理 `update` 对应步骤；下列步骤依据函数体的实际控制流和调用点整理。

**输入与输出**：
- 输入：`task`（EntityReviewTask）；`operation`（EntityOperation）。
- 输出类型：`None`；具体返回路径见流程步骤。

**处理流程**：
1. 调用 `self.save`，结果未直接赋值。

**调用与被调用**：
- `self.save`（调用点 [entity_governance.py:49](../../../src/persistence/entity_governance.py#L49)）→ [EntityGovernanceRepository.save](entity_governance.md)，静态可定位。
- 静态扫描未定位直接调用方；可能通过路由注册、LangGraph 节点、协议方法或依赖注入动态调用，不据此判断为死代码。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：未见 `raise`；下游异常可能继续上抛。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。
- 恢复/幂等性：仅在代码有检查点、事务、请求编号或显式去重时才成立；此函数不能单凭名称视为可安全重试。


---

# EntityGovernanceRepository.get_task ⭐⭐

**位置与等级**：[entity_governance.py:51](../../../src/persistence/entity_governance.py#L51)；局部辅助逻辑，需理解其调用条件与失败传播。

**签名**：`def get_task(self, task_id: str) -> EntityReviewTask | None`。

**作用**：读取或组装对应资源；是否纯只读及异常行为需结合下方显式调用与状态写入判断。

**输入与输出**：
- 输入：`task_id`（str；待处理审核任务标识）。
- 输出类型：`EntityReviewTask | None`；具体返回路径见流程步骤。

**处理流程**：
1. 进入上下文 `self.lock`，由上下文管理器控制资源释放或事务范围。
2. 返回 `EntityReviewTask.model_validate(payload) if payload is not None else None`。

**调用与被调用**：
- `self._read()['tasks'].get`（[entity_governance.py:53](../../../src/persistence/entity_governance.py#L53)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `self._read`（调用点 [entity_governance.py:53](../../../src/persistence/entity_governance.py#L53)）→ [EntityGovernanceRepository._read](entity_governance.md)，静态可定位。
- `EntityReviewTask.model_validate`（[entity_governance.py:54](../../../src/persistence/entity_governance.py#L54)）：来自 `src.domain.EntityReviewTask`；具体实现可能由依赖注入或运行时分派决定。
- 静态扫描未定位直接调用方；可能通过路由注册、LangGraph 节点、协议方法或依赖注入动态调用，不据此判断为死代码。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：未见 `raise`；下游异常可能继续上抛。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。
- 恢复/幂等性：仅在代码有检查点、事务、请求编号或显式去重时才成立；此函数不能单凭名称视为可安全重试。


---

# EntityGovernanceRepository.get_operation ⭐⭐

**位置与等级**：[entity_governance.py:56](../../../src/persistence/entity_governance.py#L56)；局部辅助逻辑，需理解其调用条件与失败传播。

**签名**：`def get_operation(self, operation_id: str) -> EntityOperation | None`。

**作用**：读取或组装对应资源；是否纯只读及异常行为需结合下方显式调用与状态写入判断。

**输入与输出**：
- 输入：`operation_id`（str）。
- 输出类型：`EntityOperation | None`；具体返回路径见流程步骤。

**处理流程**：
1. 进入上下文 `self.lock`，由上下文管理器控制资源释放或事务范围。
2. 返回 `EntityOperation.model_validate(payload) if payload is not None else None`。

**调用与被调用**：
- `self._read()['operations'].get`（[entity_governance.py:58](../../../src/persistence/entity_governance.py#L58)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `self._read`（调用点 [entity_governance.py:58](../../../src/persistence/entity_governance.py#L58)）→ [EntityGovernanceRepository._read](entity_governance.md)，静态可定位。
- `EntityOperation.model_validate`（[entity_governance.py:59](../../../src/persistence/entity_governance.py#L59)）：来自 `src.domain.EntityOperation`；具体实现可能由依赖注入或运行时分派决定。
- 静态扫描未定位直接调用方；可能通过路由注册、LangGraph 节点、协议方法或依赖注入动态调用，不据此判断为死代码。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：未见 `raise`；下游异常可能继续上抛。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。
- 恢复/幂等性：仅在代码有检查点、事务、请求编号或显式去重时才成立；此函数不能单凭名称视为可安全重试。


---

# EntityGovernanceRepository.list_tasks ⭐⭐

**位置与等级**：[entity_governance.py:61](../../../src/persistence/entity_governance.py#L61)；局部辅助逻辑，需理解其调用条件与失败传播。

**签名**：`def list_tasks(self, status: str | None=None) -> list[EntityReviewTask]`。

**作用**：读取或组装对应资源；是否纯只读及异常行为需结合下方显式调用与状态写入判断。

**输入与输出**：
- 输入：`status`（str | None；默认 `None`）。
- 输出类型：`list[EntityReviewTask]`；具体返回路径见流程步骤。

**处理流程**：
1. 进入上下文 `self.lock`，由上下文管理器控制资源释放或事务范围。
2. 更新 `tasks`，值来自 `[EntityReviewTask.model_validate(item) for item in payloads]`。
3. 检查 `status is not None`；按条件分流，else 分支不存在。
4. 返回 `sorted(tasks, key=lambda item: item.created_at, reverse=True)`。

**关键条件与保护**：
- [entity_governance.py:65](../../../src/persistence/entity_governance.py#L65)：`status is not None`，不满足时跳过本分支。

**调用与被调用**：
- `list`（[entity_governance.py:63](../../../src/persistence/entity_governance.py#L63)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `self._read()['tasks'].values`（[entity_governance.py:63](../../../src/persistence/entity_governance.py#L63)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `self._read`（调用点 [entity_governance.py:63](../../../src/persistence/entity_governance.py#L63)）→ [EntityGovernanceRepository._read](entity_governance.md)，静态可定位。
- `EntityReviewTask.model_validate`（[entity_governance.py:64](../../../src/persistence/entity_governance.py#L64)）：来自 `src.domain.EntityReviewTask`；具体实现可能由依赖注入或运行时分派决定。
- `sorted`（[entity_governance.py:67](../../../src/persistence/entity_governance.py#L67)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- 静态扫描未定位直接调用方；可能通过路由注册、LangGraph 节点、协议方法或依赖注入动态调用，不据此判断为死代码。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：未见 `raise`；下游异常可能继续上抛。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。
- 恢复/幂等性：仅在代码有检查点、事务、请求编号或显式去重时才成立；此函数不能单凭名称视为可安全重试。


---
