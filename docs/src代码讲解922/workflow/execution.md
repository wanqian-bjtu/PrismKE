源码：[execution.py:1](../../../src/workflow/execution.py#L1) | 基准：`dev/v0.10@f2f34d7` | 本文件符号数：43

**模块职责**：One durable worker per workspace, with conservative restart reconciliation.
**在系统中的位置**：应用服务、LangGraph 编排、执行状态、审核接续、图提交及纠正流程。
**直接依赖**：[src.core.errors](../core/errors.md)、[src.core.execution_control](../core/execution_control.md)、[src.core.ids](../core/ids.md)、[src.domain.execution](../domain/execution.md)、[src.persistence.execution](../persistence/execution.md)、[src.providers.base](../providers/base.md)；外部/标准库：`__future__`、`asyncio`、`contextlib`、`filelock`、`pathlib`、`typing`。
**主要调用方（静态导入）**：未见静态直接导入；可能由包入口、框架注册或动态加载。
**阅读提示**：下列流程根据当前源码控制流整理；`self`/接口对象的实际类型可能在运行时注入，未能静态解析的调用会明确标注。链接指向源码行或对应讲解文件。

## 核心路径解读

- `ExecutionManager` 为运行安排单工作器处理，记录排队、运行、取消、未知请求及完成等执行态；业务审核状态另行保留，不能混用。
- `RunControl` 在节点入口检查取消，在提交开始后禁止把已写图事务标作已取消；请求发送前后由执行账本记下逻辑 ID、结果与用量。
- 重启 `reconcile` 只自动接续检查点、Provider 指纹和账本均可证明安全的任务；未结算请求可能已计费，不能自动重发。

---

# RunControl ⭐⭐⭐⭐

**位置与等级**：[execution.py:31](../../../src/workflow/execution.py#L31)；承担主要 Agent、应用服务或审核/执行入口，跨模块影响显著。

**职责**：本模块的对象实现或数据契约；具体语义由字段、基类和方法共同决定。基类：无显式基类。

**字段与类级约束**：
- 类体未直接声明字段；实例状态请看 `__init__` 及方法中的赋值。

**内部成员**：`RunControl.__init__`、`RunControl.check`、`RunControl.node`、`RunControl.commit_started`、`RunControl.commit_finished`、`RunControl.begin_request`、`RunControl.finish_request`、`RunControl.result`、`RunControl.put_result`


---

# RunControl.__init__ ⭐⭐⭐⭐

**位置与等级**：[execution.py:32](../../../src/workflow/execution.py#L32)；承担主要 Agent、应用服务或审核/执行入口，跨模块影响显著。

**签名**：`def __init__(self, manager: ExecutionManager, run_id: str) -> None`。

**作用**：初始化对象并保存依赖或配置；需检查是否创建持久化资源。

**输入与输出**：
- 输入：`manager`（ExecutionManager）；`run_id`（str；目标运行的稳定标识）。
- 输出类型：`None`；具体返回路径见流程步骤。

**处理流程**：
1. 更新 `self.manager`，值来自 `manager`。
2. 更新 `self.run_id`，值来自 `run_id`。
3. 更新 `self.critical`，值来自 `False`。
4. 更新 `self.closed`，值来自 `False`。

**调用与被调用**：
- 无显式函数调用，或仅声明协议/常量。
- 静态扫描未定位直接调用方；可能通过路由注册、LangGraph 节点、协议方法或依赖注入动态调用，不据此判断为死代码。

**状态、副作用与异常**：
- 显式状态/容器赋值：`self.manager`、`self.run_id`、`self.critical`、`self.closed`。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：未见 `raise`；下游异常可能继续上抛。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。
- 恢复/幂等性：仅在代码有检查点、事务、请求编号或显式去重时才成立；此函数不能单凭名称视为可安全重试。


---

# RunControl.check ⭐⭐⭐⭐

**位置与等级**：[execution.py:38](../../../src/workflow/execution.py#L38)；承担主要 Agent、应用服务或审核/执行入口，跨模块影响显著。

**签名**：`def check(self) -> None`。

**作用**：处理 `check` 对应步骤；下列步骤依据函数体的实际控制流和调用点整理。

**输入与输出**：
- 输入：无业务参数（或仅隐式接收实例）。
- 输出类型：`None`；具体返回路径见流程步骤。

**处理流程**：
1. 检查 `self.critical`；按条件分流，else 分支不存在。
2. 检查 `self.closed or self.manager.stopping`；按条件分流，else 分支不存在。
3. 更新 `task`，值来自 `self.manager.repository.get(self.run_id)`。
4. 检查 `task and task.cancel_requested`；按条件分流，else 分支不存在。
5. 检查 `self.manager.repository.unknown(self.run_id, include_sent=False)`；按条件分流，else 分支不存在。

**关键条件与保护**：
- [execution.py:39](../../../src/workflow/execution.py#L39)：`self.critical`，不满足时跳过本分支。
- [execution.py:41](../../../src/workflow/execution.py#L41)：`self.closed or self.manager.stopping`，不满足时跳过本分支。
- [execution.py:44](../../../src/workflow/execution.py#L44)：`task and task.cancel_requested`，不满足时跳过本分支。
- [execution.py:46](../../../src/workflow/execution.py#L46)：`self.manager.repository.unknown(self.run_id, include_sent=False)`，不满足时跳过本分支。

**调用与被调用**：
- `ExecutionPaused`（调用点 [execution.py:42](../../../src/workflow/execution.py#L42)）→ [ExecutionPaused](../core/execution_control.md)，静态可定位。
- `self.manager.repository.get`（[execution.py:43](../../../src/workflow/execution.py#L43)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `self.manager.repository.unknown`（[execution.py:46](../../../src/workflow/execution.py#L46)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- 静态可定位的调用方：[RunControl.node](execution.md)、[RunControl.commit_started](execution.md)、[RunControl.begin_request](execution.md)。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：`ExecutionPaused('SERVER_SHUTDOWN')`、`ExecutionPaused('USER_CANCEL')`、`ExecutionPaused('UNKNOWN_PROVIDER_USAGE')`。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。
- 恢复/幂等性：仅在代码有检查点、事务、请求编号或显式去重时才成立；此函数不能单凭名称视为可安全重试。


---

# RunControl.node ⭐⭐⭐⭐

**位置与等级**：[execution.py:49](../../../src/workflow/execution.py#L49)；承担主要 Agent、应用服务或审核/执行入口，跨模块影响显著。

**签名**：`def node(self, name: str) -> None`。

**作用**：处理 `node` 对应步骤；下列步骤依据函数体的实际控制流和调用点整理。

**输入与输出**：
- 输入：`name`（str）。
- 输出类型：`None`；具体返回路径见流程步骤。

**处理流程**：
1. 调用 `self.check`，结果未直接赋值。
2. 调用 `self.manager.repository.change`，结果未直接赋值。

**调用与被调用**：
- `self.check`（调用点 [execution.py:50](../../../src/workflow/execution.py#L50)）→ [RunControl.check](execution.md)，静态可定位。
- `self.manager.repository.change`（[execution.py:51](../../../src/workflow/execution.py#L51)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- 静态扫描未定位直接调用方；可能通过路由注册、LangGraph 节点、协议方法或依赖注入动态调用，不据此判断为死代码。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：未见 `raise`；下游异常可能继续上抛。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。
- 恢复/幂等性：仅在代码有检查点、事务、请求编号或显式去重时才成立；此函数不能单凭名称视为可安全重试。


---

# RunControl.commit_started ⭐⭐⭐⭐

**位置与等级**：[execution.py:53](../../../src/workflow/execution.py#L53)；承担主要 Agent、应用服务或审核/执行入口，跨模块影响显著。

**签名**：`def commit_started(self, revision_id: str) -> None`。

**作用**：处理 `commit_started` 对应步骤；下列步骤依据函数体的实际控制流和调用点整理。

**输入与输出**：
- 输入：`revision_id`（str）。
- 输出类型：`None`；具体返回路径见流程步骤。

**处理流程**：
1. 调用 `self.check`，结果未直接赋值。
2. 调用 `self.manager.repository.change`，结果未直接赋值。
3. 更新 `self.critical`，值来自 `True`。

**调用与被调用**：
- `self.check`（调用点 [execution.py:54](../../../src/workflow/execution.py#L54)）→ [RunControl.check](execution.md)，静态可定位。
- `self.manager.repository.change`（[execution.py:55](../../../src/workflow/execution.py#L55)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- 静态扫描未定位直接调用方；可能通过路由注册、LangGraph 节点、协议方法或依赖注入动态调用，不据此判断为死代码。

**状态、副作用与异常**：
- 显式状态/容器赋值：`self.critical`。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：未见 `raise`；下游异常可能继续上抛。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。
- 恢复/幂等性：仅在代码有检查点、事务、请求编号或显式去重时才成立；此函数不能单凭名称视为可安全重试。


---

# RunControl.commit_finished ⭐⭐⭐⭐

**位置与等级**：[execution.py:60](../../../src/workflow/execution.py#L60)；承担主要 Agent、应用服务或审核/执行入口，跨模块影响显著。

**签名**：`def commit_finished(self) -> None`。

**作用**：处理 `commit_finished` 对应步骤；下列步骤依据函数体的实际控制流和调用点整理。

**输入与输出**：
- 输入：无业务参数（或仅隐式接收实例）。
- 输出类型：`None`；具体返回路径见流程步骤。

**处理流程**：
1. 调用 `self.manager.repository.change`，结果未直接赋值。

**调用与被调用**：
- `self.manager.repository.change`（[execution.py:61](../../../src/workflow/execution.py#L61)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- 静态扫描未定位直接调用方；可能通过路由注册、LangGraph 节点、协议方法或依赖注入动态调用，不据此判断为死代码。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：未见 `raise`；下游异常可能继续上抛。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。
- 恢复/幂等性：仅在代码有检查点、事务、请求编号或显式去重时才成立；此函数不能单凭名称视为可安全重试。


---

# RunControl.begin_request ⭐⭐⭐⭐

**位置与等级**：[execution.py:63](../../../src/workflow/execution.py#L63)；承担主要 Agent、应用服务或审核/执行入口，跨模块影响显著。

**签名**：`def begin_request(self, key: str, metadata: dict[str, Any]) -> dict[str, Any] | None`。

**作用**：处理 `begin_request` 对应步骤；下列步骤依据函数体的实际控制流和调用点整理。

**输入与输出**：
- 输入：`key`（str）；`metadata`（dict[str, Any]）。
- 输出类型：`dict[str, Any] | None`；具体返回路径见流程步骤。

**处理流程**：
1. 调用 `self.check`，结果未直接赋值。
2. 更新 `task`，值来自 `self.manager.repository.get(self.run_id)`。
3. 返回 `self.manager.repository.begin_request(self.run_id, key, {**metadata, 'attempt': task.attempt if task els…`。

**调用与被调用**：
- `self.check`（调用点 [execution.py:64](../../../src/workflow/execution.py#L64)）→ [RunControl.check](execution.md)，静态可定位。
- `self.manager.repository.get`（[execution.py:65](../../../src/workflow/execution.py#L65)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `self.manager.repository.begin_request`（[execution.py:66](../../../src/workflow/execution.py#L66)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- 静态扫描未定位直接调用方；可能通过路由注册、LangGraph 节点、协议方法或依赖注入动态调用，不据此判断为死代码。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：未见 `raise`；下游异常可能继续上抛。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。
- 恢复/幂等性：仅在代码有检查点、事务、请求编号或显式去重时才成立；此函数不能单凭名称视为可安全重试。


---

# RunControl.finish_request ⭐⭐⭐⭐

**位置与等级**：[execution.py:76](../../../src/workflow/execution.py#L76)；承担主要 Agent、应用服务或审核/执行入口，跨模块影响显著。

**签名**：`def finish_request(self, key: str, status: str, payload: dict[str, Any] | None, usage_known: bool) -> None`。

**作用**：处理 `finish_request` 对应步骤；下列步骤依据函数体的实际控制流和调用点整理。

**输入与输出**：
- 输入：`key`（str）；`status`（str）；`payload`（dict[str, Any] | None）；`usage_known`（bool）。
- 输出类型：`None`；具体返回路径见流程步骤。

**处理流程**：
1. 调用 `self.manager.repository.finish_request`，结果未直接赋值。

**调用与被调用**：
- `self.manager.repository.finish_request`（[execution.py:79](../../../src/workflow/execution.py#L79)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- 静态扫描未定位直接调用方；可能通过路由注册、LangGraph 节点、协议方法或依赖注入动态调用，不据此判断为死代码。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：未见 `raise`；下游异常可能继续上抛。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。
- 恢复/幂等性：仅在代码有检查点、事务、请求编号或显式去重时才成立；此函数不能单凭名称视为可安全重试。


---

# RunControl.result ⭐⭐⭐⭐

**位置与等级**：[execution.py:81](../../../src/workflow/execution.py#L81)；承担主要 Agent、应用服务或审核/执行入口，跨模块影响显著。

**签名**：`def result(self, key: str) -> dict[str, Any] | None`。

**作用**：处理 `result` 对应步骤；下列步骤依据函数体的实际控制流和调用点整理。

**输入与输出**：
- 输入：`key`（str）。
- 输出类型：`dict[str, Any] | None`；具体返回路径见流程步骤。

**处理流程**：
1. 返回 `self.manager.repository.result(self.run_id, key)`。

**调用与被调用**：
- `self.manager.repository.result`（[execution.py:82](../../../src/workflow/execution.py#L82)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- 静态扫描未定位直接调用方；可能通过路由注册、LangGraph 节点、协议方法或依赖注入动态调用，不据此判断为死代码。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：未见 `raise`；下游异常可能继续上抛。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。
- 恢复/幂等性：仅在代码有检查点、事务、请求编号或显式去重时才成立；此函数不能单凭名称视为可安全重试。


---

# RunControl.put_result ⭐⭐⭐⭐

**位置与等级**：[execution.py:84](../../../src/workflow/execution.py#L84)；承担主要 Agent、应用服务或审核/执行入口，跨模块影响显著。

**签名**：`def put_result(self, key: str, value: dict[str, Any]) -> None`。

**作用**：处理 `put_result` 对应步骤；下列步骤依据函数体的实际控制流和调用点整理。

**输入与输出**：
- 输入：`key`（str）；`value`（dict[str, Any]）。
- 输出类型：`None`；具体返回路径见流程步骤。

**处理流程**：
1. 调用 `self.manager.repository.put_result`，结果未直接赋值。

**调用与被调用**：
- `self.manager.repository.put_result`（[execution.py:85](../../../src/workflow/execution.py#L85)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- 静态扫描未定位直接调用方；可能通过路由注册、LangGraph 节点、协议方法或依赖注入动态调用，不据此判断为死代码。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：未见 `raise`；下游异常可能继续上抛。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。
- 恢复/幂等性：仅在代码有检查点、事务、请求编号或显式去重时才成立；此函数不能单凭名称视为可安全重试。


---

# ExecutionManager ⭐⭐⭐⭐

**位置与等级**：[execution.py:88](../../../src/workflow/execution.py#L88)；承担主要 Agent、应用服务或审核/执行入口，跨模块影响显著。

**职责**：跨步骤服务；组合依赖并暴露可复用业务入口。基类：无显式基类。

**字段与类级约束**：
- 类体未直接声明字段；实例状态请看 `__init__` 及方法中的赋值。

**内部成员**：`ExecutionManager.__init__`、`ExecutionManager.register`、`ExecutionManager.ensure_accepting`、`ExecutionManager.set_status`、`ExecutionManager.business_status`、`ExecutionManager.compatible`、`ExecutionManager.blockers`、`ExecutionManager.enqueue`、`ExecutionManager.cancel`、`ExecutionManager.view`、`ExecutionManager.branch_progress`、`ExecutionManager.reconcile_request`、`ExecutionManager.health`、`ExecutionManager.start`、`ExecutionManager._start`、`ExecutionManager.reconcile`、`ExecutionManager.settle_committed`、`ExecutionManager.preflight`、`ExecutionManager._work`、`ExecutionManager.wait`、`ExecutionManager.run_wait`、`ExecutionManager.stop`


---

# ExecutionManager.__init__ ⭐⭐

**位置与等级**：[execution.py:89](../../../src/workflow/execution.py#L89)；局部辅助逻辑，需理解其调用条件与失败传播。

**签名**：`def __init__(self, service: PrismKEService) -> None`。

**作用**：初始化对象并保存依赖或配置；需检查是否创建持久化资源。

**输入与输出**：
- 输入：`service`（PrismKEService）。
- 输出类型：`None`；具体返回路径见流程步骤。

**处理流程**：
1. 更新 `self.service`，值来自 `service`。
2. 更新 `self.repository`，值来自 `ExecutionRepository(service.settings.runtime_dir / 'executions.sqlite')`。
3. 更新 `self.owner`，值来自 `FileLock(str(service.settings.runtime_dir / 'execution-owner.lock'), timeout=0)`。
4. 更新 `self.worker`，值来自 `None`。
5. 更新 `self.stopping`，值来自 `False`。
6. 更新 `self.failures`，值来自 `{}`。
7. 更新 `self.lifecycle`，值来自 `asyncio.Lock()`。
8. 更新 `self.persistent`，值来自 `False`。
9. 更新 `self.waiters`，值来自 `0`。

**调用与被调用**：
- `ExecutionRepository`（调用点 [execution.py:91](../../../src/workflow/execution.py#L91)）→ [ExecutionRepository](../persistence/execution.md)，静态可定位。
- `FileLock`（[execution.py:92](../../../src/workflow/execution.py#L92)）：来自 `filelock.FileLock`；具体实现可能由依赖注入或运行时分派决定。
- `str`（[execution.py:92](../../../src/workflow/execution.py#L92)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `asyncio.Lock`（[execution.py:96](../../../src/workflow/execution.py#L96)）：来自 `asyncio`；具体实现可能由依赖注入或运行时分派决定。
- 静态扫描未定位直接调用方；可能通过路由注册、LangGraph 节点、协议方法或依赖注入动态调用，不据此判断为死代码。

**状态、副作用与异常**：
- 显式状态/容器赋值：`self.service`、`self.repository`、`self.owner`、`self.worker`、`self.stopping`、`self.failures`、`self.lifecycle`、`self.persistent`、`self.waiters`。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：未见 `raise`；下游异常可能继续上抛。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。
- 恢复/幂等性：仅在代码有检查点、事务、请求编号或显式去重时才成立；此函数不能单凭名称视为可安全重试。


---

# ExecutionManager.register ⭐⭐

**位置与等级**：[execution.py:100](../../../src/workflow/execution.py#L100)；局部辅助逻辑，需理解其调用条件与失败传播。

**签名**：`def register(self, state: WorkflowState) -> ExecutionTask`。

**作用**：处理 `register` 对应步骤；下列步骤依据函数体的实际控制流和调用点整理。

**输入与输出**：
- 输入：`state`（WorkflowState；跨节点 WorkflowState；调用方须保持证据与状态一致）。
- 输出类型：`ExecutionTask`；具体返回路径见流程步骤。

**处理流程**：
1. 更新 `task`，值来自 `self.repository.get(state.run_id)`。
2. 检查 `task`；按条件分流，else 分支不存在。
3. 返回 `self.repository.register(ExecutionTask(run_id=state.run_id, input_hash=file_sha256(Path(state.input_path…`。

**关键条件与保护**：
- [execution.py:102](../../../src/workflow/execution.py#L102)：`task`，不满足时跳过本分支。

**调用与被调用**：
- `self.repository.get`（[execution.py:101](../../../src/workflow/execution.py#L101)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `self.repository.register`（[execution.py:104](../../../src/workflow/execution.py#L104)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `ExecutionTask`（调用点 [execution.py:105](../../../src/workflow/execution.py#L105)）→ [ExecutionTask](../domain/execution.md)，静态可定位。
- `file_sha256`（调用点 [execution.py:107](../../../src/workflow/execution.py#L107)）→ [file_sha256](../core/ids.md)，静态可定位。
- `Path`（[execution.py:107](../../../src/workflow/execution.py#L107)）：来自 `pathlib.Path`；具体实现可能由依赖注入或运行时分派决定。
- `self.business_status`（调用点 [execution.py:110](../../../src/workflow/execution.py#L110)）→ [ExecutionManager.business_status](execution.md)，静态可定位。
- 静态可定位的调用方：[ExecutionManager.enqueue](execution.md)。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：未见 `raise`；下游异常可能继续上抛。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。
- 恢复/幂等性：仅在代码有检查点、事务、请求编号或显式去重时才成立；此函数不能单凭名称视为可安全重试。


---

# ExecutionManager.ensure_accepting ⭐⭐

**位置与等级**：[execution.py:114](../../../src/workflow/execution.py#L114)；局部辅助逻辑，需理解其调用条件与失败传播。

**签名**：`def ensure_accepting(self) -> None`。

**作用**：处理 `ensure_accepting` 对应步骤；下列步骤依据函数体的实际控制流和调用点整理。

**输入与输出**：
- 输入：无业务参数（或仅隐式接收实例）。
- 输出类型：`None`；具体返回路径见流程步骤。

**处理流程**：
1. 检查 `self.stopping and self.persistent`；按条件分流，else 分支不存在。

**关键条件与保护**：
- [execution.py:115](../../../src/workflow/execution.py#L115)：`self.stopping and self.persistent`，不满足时跳过本分支。

**调用与被调用**：
- `ExecutionConflict`（调用点 [execution.py:116](../../../src/workflow/execution.py#L116)）→ [ExecutionConflict](../persistence/execution.md)，静态可定位。
- 静态可定位的调用方：[ExecutionManager.enqueue](execution.md)。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：`ExecutionConflict('WORKER_SHUTTING_DOWN')`。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。
- 恢复/幂等性：仅在代码有检查点、事务、请求编号或显式去重时才成立；此函数不能单凭名称视为可安全重试。


---

# ExecutionManager.set_status ⭐⭐

**位置与等级**：[execution.py:118](../../../src/workflow/execution.py#L118)；局部辅助逻辑，需理解其调用条件与失败传播。

**签名**：`def set_status(self, run_id: str, status: ExecutionStatus) -> None`。

**作用**：处理 `set_status` 对应步骤；下列步骤依据函数体的实际控制流和调用点整理。

**输入与输出**：
- 输入：`run_id`（str；目标运行的稳定标识）；`status`（ExecutionStatus）。
- 输出类型：`None`；具体返回路径见流程步骤。

**处理流程**：
1. 调用 `self.repository.change`，结果未直接赋值。

**调用与被调用**：
- `self.repository.change`（[execution.py:119](../../../src/workflow/execution.py#L119)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- 静态可定位的调用方：[ExecutionManager.reconcile](execution.md)、[ExecutionManager._work](execution.md)。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：未见 `raise`；下游异常可能继续上抛。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。
- 恢复/幂等性：仅在代码有检查点、事务、请求编号或显式去重时才成立；此函数不能单凭名称视为可安全重试。


---

# ExecutionManager.business_status ⭐⭐

**位置与等级**：[execution.py:122](../../../src/workflow/execution.py#L122)；局部辅助逻辑，需理解其调用条件与失败传播。

**签名**：`def business_status(state: WorkflowState) -> Literal['awaiting_review', 'awaiting_commit', 'completed', 'failed', 'interrupted']`。

**装饰器/路由**：`staticmethod`。

**作用**：处理 `business_status` 对应步骤；下列步骤依据函数体的实际控制流和调用点整理。

**输入与输出**：
- 输入：`state`（WorkflowState；跨节点 WorkflowState；调用方须保持证据与状态一致）。
- 输出类型：`Literal['awaiting_review', 'awaiting_commit', 'completed', 'failed', 'interrupted']`；具体返回路径见流程步骤。

**处理流程**：
1. 检查 `state.status == 'completed'`；按条件分流，else 分支不存在。
2. 检查 `state.status == 'failed'`；按条件分流，else 分支不存在。
3. 检查 `state.status == 'awaiting_review'`；按条件分流，else 分支不存在。
4. 检查 `state.current_node == 'prepare_graph_commit'`；按条件分流，else 分支不存在。
5. 返回 `'interrupted'`。

**关键条件与保护**：
- [execution.py:125](../../../src/workflow/execution.py#L125)：`state.status == 'completed'`，不满足时跳过本分支。
- [execution.py:127](../../../src/workflow/execution.py#L127)：`state.status == 'failed'`，不满足时跳过本分支。
- [execution.py:129](../../../src/workflow/execution.py#L129)：`state.status == 'awaiting_review'`，不满足时跳过本分支。
- [execution.py:131](../../../src/workflow/execution.py#L131)：`state.current_node == 'prepare_graph_commit'`，不满足时跳过本分支。

**调用与被调用**：
- 无显式函数调用，或仅声明协议/常量。
- 静态可定位的调用方：[ExecutionManager.register](execution.md)、[ExecutionManager.view](execution.md)、[ExecutionManager.reconcile](execution.md)、[ExecutionManager._work.finish](execution.md)。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：未见 `raise`；下游异常可能继续上抛。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。
- 恢复/幂等性：仅在代码有检查点、事务、请求编号或显式去重时才成立；此函数不能单凭名称视为可安全重试。


---

# ExecutionManager.compatible ⭐⭐

**位置与等级**：[execution.py:135](../../../src/workflow/execution.py#L135)；局部辅助逻辑，需理解其调用条件与失败传播。

**签名**：`def compatible(self, state: WorkflowState) -> None`。

**作用**：处理 `compatible` 对应步骤；下列步骤依据函数体的实际控制流和调用点整理。

**输入与输出**：
- 输入：`state`（WorkflowState；跨节点 WorkflowState；调用方须保持证据与状态一致）。
- 输出类型：`None`；具体返回路径见流程步骤。

**处理流程**：
1. 检查 `state.pipeline_version != PIPELINE_VERSION`；按条件分流，else 分支不存在。

**关键条件与保护**：
- [execution.py:138](../../../src/workflow/execution.py#L138)：`state.pipeline_version != PIPELINE_VERSION`，不满足时跳过本分支。

**调用与被调用**：
- `LegacyCheckpointError`（调用点 [execution.py:139](../../../src/workflow/execution.py#L139)）→ [LegacyCheckpointError](../core/errors.md)，静态可定位。
- 静态可定位的调用方：[ExecutionManager.enqueue](execution.md)、[ExecutionManager.cancel](execution.md)、[ExecutionManager.reconcile_request](execution.md)、[ExecutionManager.reconcile](execution.md)、[ExecutionManager.preflight](execution.md)。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：`LegacyCheckpointError(<字符串常量>)`。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。
- 恢复/幂等性：仅在代码有检查点、事务、请求编号或显式去重时才成立；此函数不能单凭名称视为可安全重试。


---

# ExecutionManager.blockers ⭐⭐

**位置与等级**：[execution.py:143](../../../src/workflow/execution.py#L143)；局部辅助逻辑，需理解其调用条件与失败传播。

**签名**：`def blockers(self, state: WorkflowState, *, include_sent: bool=True) -> str | None`。

**作用**：处理 `blockers` 对应步骤；下列步骤依据函数体的实际控制流和调用点整理。

**输入与输出**：
- 输入：`state`（WorkflowState；跨节点 WorkflowState；调用方须保持证据与状态一致）；`include_sent`（bool；默认 `True`）。
- 输出类型：`str | None`；具体返回路径见流程步骤。

**处理流程**：
1. 检查 `self.service.reviews.repository.pending(state.run_id)`；按条件分流，else 分支不存在。
2. 检查 `self.repository.unknown(state.run_id, include_sent=include_sent)`；按条件分流，else 分支不存在。
3. 检查 `state.validation.blocking_count or any((t.status == 'pending' for t in state.entity_review_tasks)) or an…`；按条件分流，else 分支不存在。
4. 返回 `None`。

**关键条件与保护**：
- [execution.py:144](../../../src/workflow/execution.py#L144)：`self.service.reviews.repository.pending(state.run_id)`，不满足时跳过本分支。
- [execution.py:146](../../../src/workflow/execution.py#L146)：`self.repository.unknown(state.run_id, include_sent=include_sent)`，不满足时跳过本分支。
- [execution.py:148](../../../src/workflow/execution.py#L148)：`state.validation.blocking_count or any((t.status == 'pending' for t in state.entity_review_tasks)) or any((t.statu…`，不满足时跳过本分支。

**调用与被调用**：
- `self.service.reviews.repository.pending`（[execution.py:144](../../../src/workflow/execution.py#L144)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `self.repository.unknown`（[execution.py:146](../../../src/workflow/execution.py#L146)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `any`（[execution.py:150](../../../src/workflow/execution.py#L150)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- 静态可定位的调用方：[ExecutionManager.enqueue](execution.md)、[ExecutionManager.view](execution.md)、[ExecutionManager.reconcile](execution.md)。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：未见 `raise`；下游异常可能继续上抛。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。
- 恢复/幂等性：仅在代码有检查点、事务、请求编号或显式去重时才成立；此函数不能单凭名称视为可安全重试。


---

# ExecutionManager.enqueue ⭐⭐

**位置与等级**：[execution.py:156](../../../src/workflow/execution.py#L156)；局部辅助逻辑，需理解其调用条件与失败传播。

**签名**：`def enqueue(self, run_id: str, operation: Literal['execute', 'resume', 'confirm'], *, expected_version: int | None=None, reviewer: str | None=None) -> ExecutionTask`。

**作用**：处理 `enqueue` 对应步骤；下列步骤依据函数体的实际控制流和调用点整理。

**输入与输出**：
- 输入：`run_id`（str；目标运行的稳定标识）；`operation`（Literal['execute', 'resume', 'confirm']）；`expected_version`（int | None；默认 `None`；乐观并发版本；过期提交应拒绝）；`reviewer`（str | None；默认 `None`；审核操作者，形成审计归属）。
- 输出类型：`ExecutionTask`；具体返回路径见流程步骤。

**处理流程**：
1. 调用 `self.ensure_accepting`，结果未直接赋值。
2. 更新 `state`，值来自 `self.service.show_run(run_id)`。
3. 调用 `self.compatible`，结果未直接赋值。
4. 更新 `task`，值来自 `self.register(state)`。
5. 检查 `expected_version is not None and task.version != expected_version`；按条件分流，else 分支不存在。
6. 检查 `task.status in ACTIVE`；按条件分流，else 分支不存在。
7. 更新 `blocked`，值来自 `self.blockers(state)`。
8. 检查 `blocked`；按条件分流，else 分支不存在。
9. 更新 `progress`，值来自 `self.service.review_progress(run_id)`。
10. 检查 `operation == 'confirm'`；按条件分流，else 分支存在。
11. 返回 `self.repository.change(run_id, update, expected_version)`。

**关键条件与保护**：
- [execution.py:168](../../../src/workflow/execution.py#L168)：`expected_version is not None and task.version != expected_version`，不满足时跳过本分支。
- [execution.py:170](../../../src/workflow/execution.py#L170)：`task.status in ACTIVE`，不满足时跳过本分支。
- [execution.py:171](../../../src/workflow/execution.py#L171)：`task.operation != operation`，不满足时跳过本分支。
- [execution.py:175](../../../src/workflow/execution.py#L175)：`blocked`，不满足时跳过本分支。
- [execution.py:178](../../../src/workflow/execution.py#L178)：`operation == 'confirm'`，不满足时有 else 分支。
- [execution.py:179](../../../src/workflow/execution.py#L179)：`not reviewer or not reviewer.strip() or (not progress['can_commit'])`，不满足时跳过本分支。
- [execution.py:181](../../../src/workflow/execution.py#L181)：`operation == 'resume' and (not progress['can_resume'])`，不满足时有 else 分支。
- [execution.py:183](../../../src/workflow/execution.py#L183)：`operation == 'execute'`，不满足时跳过本分支。

**调用与被调用**：
- `self.ensure_accepting`（调用点 [execution.py:164](../../../src/workflow/execution.py#L164)）→ [ExecutionManager.ensure_accepting](execution.md)，静态可定位。
- `self.service.show_run`（[execution.py:165](../../../src/workflow/execution.py#L165)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `self.compatible`（调用点 [execution.py:166](../../../src/workflow/execution.py#L166)）→ [ExecutionManager.compatible](execution.md)，静态可定位。
- `self.register`（调用点 [execution.py:167](../../../src/workflow/execution.py#L167)）→ [ExecutionManager.register](execution.md)，静态可定位。
- `ExecutionConflict`（调用点 [execution.py:169](../../../src/workflow/execution.py#L169)）→ [ExecutionConflict](../persistence/execution.md)，静态可定位。
- `self.blockers`（调用点 [execution.py:174](../../../src/workflow/execution.py#L174)）→ [ExecutionManager.blockers](execution.md)，静态可定位。
- `self.service.review_progress`（[execution.py:177](../../../src/workflow/execution.py#L177)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `reviewer.strip`（[execution.py:179](../../../src/workflow/execution.py#L179)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `self.repository.change`（[execution.py:198](../../../src/workflow/execution.py#L198)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- 静态可定位的调用方：[ExecutionManager.run_wait](execution.md)。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：`ExecutionConflict('STALE_EXECUTION_VERSION')`、`ExecutionConflict('EXECUTION_BUSY')`、`ExecutionConflict(blocked)`、`ExecutionConflict('SUBMISSION_CONFIRMATION_REQUIRED')`、`ExecutionConflict('RUN_NOT_RESUMABLE')`、`ExecutionConflict('USE_RESUME_FOR_EXISTING_EXECUTION')`。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。
- 恢复/幂等性：仅在代码有检查点、事务、请求编号或显式去重时才成立；此函数不能单凭名称视为可安全重试。


---

# ExecutionManager.enqueue.update ⭐⭐

**位置与等级**：[execution.py:186](../../../src/workflow/execution.py#L186)；局部辅助逻辑，需理解其调用条件与失败传播。

**签名**：`def update(t: ExecutionTask) -> None`。

**作用**：处理 `update` 对应步骤；下列步骤依据函数体的实际控制流和调用点整理。

**输入与输出**：
- 输入：`t`（ExecutionTask）。
- 输出类型：`None`；具体返回路径见流程步骤。

**处理流程**：
1. 检查 `t.status in ACTIVE`；按条件分流，else 分支不存在。
2. 更新 `t.status`，值来自 `'queued'`。
3. 更新 `t.operation`，值来自 `operation`。
4. 更新 `t.reviewer`，值来自 `reviewer`。
5. 更新 `t.cancel_requested`，值来自 `False`。
6. 更新 `t.error_code`，值来自 `None`。
7. 更新 `t.reason`，值来自 `None`。
8. 更新 `t.commit_revision_id`，值来自 `None`。
9. 更新 `t.commit_applied`，值来自 `False`。

**关键条件与保护**：
- [execution.py:187](../../../src/workflow/execution.py#L187)：`t.status in ACTIVE`，不满足时跳过本分支。

**调用与被调用**：
- `ExecutionConflict`（调用点 [execution.py:188](../../../src/workflow/execution.py#L188)）→ [ExecutionConflict](../persistence/execution.md)，静态可定位。
- 静态扫描未定位直接调用方；可能通过路由注册、LangGraph 节点、协议方法或依赖注入动态调用，不据此判断为死代码。

**状态、副作用与异常**：
- 显式状态/容器赋值：`t.status`、`t.operation`、`t.reviewer`、`t.cancel_requested`、`t.error_code`、`t.reason`、`t.commit_revision_id`、`t.commit_applied`。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：`ExecutionConflict('EXECUTION_BUSY')`。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。
- 恢复/幂等性：仅在代码有检查点、事务、请求编号或显式去重时才成立；此函数不能单凭名称视为可安全重试。


---

# ExecutionManager.cancel ⭐⭐

**位置与等级**：[execution.py:200](../../../src/workflow/execution.py#L200)；局部辅助逻辑，需理解其调用条件与失败传播。

**签名**：`def cancel(self, run_id: str, operator: str, reason: str, request_id: str, expected_version: int) -> ExecutionTask`。

**作用**：处理 `cancel` 对应步骤；下列步骤依据函数体的实际控制流和调用点整理。

**输入与输出**：
- 输入：`run_id`（str；目标运行的稳定标识）；`operator`（str）；`reason`（str；人工操作或审核的理由）；`request_id`（str；幂等请求标识，避免重复动作）；`expected_version`（int；乐观并发版本；过期提交应拒绝）。
- 输出类型：`ExecutionTask`；具体返回路径见流程步骤。

**处理流程**：
1. 调用 `self.compatible`，结果未直接赋值。
2. 检查 `not all((s.strip() for s in [operator, reason, request_id]))`；按条件分流，else 分支不存在。
3. 返回 `self.repository.change(run_id, update, expected_version, (request_id, canonical_hash([operator.strip(), …`。

**关键条件与保护**：
- [execution.py:204](../../../src/workflow/execution.py#L204)：`not all((s.strip() for s in [operator, reason, request_id]))`，不满足时跳过本分支。

**调用与被调用**：
- `self.compatible`（调用点 [execution.py:203](../../../src/workflow/execution.py#L203)）→ [ExecutionManager.compatible](execution.md)，静态可定位。
- `self.service.show_run`（[execution.py:203](../../../src/workflow/execution.py#L203)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `all`（[execution.py:204](../../../src/workflow/execution.py#L204)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `s.strip`（[execution.py:204](../../../src/workflow/execution.py#L204)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `ExecutionConflict`（调用点 [execution.py:205](../../../src/workflow/execution.py#L205)）→ [ExecutionConflict](../persistence/execution.md)，静态可定位。
- `self.repository.change`（[execution.py:215](../../../src/workflow/execution.py#L215)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `canonical_hash`（调用点 [execution.py:221](../../../src/workflow/execution.py#L221)）→ [canonical_hash](../core/ids.md)，静态可定位。
- `operator.strip`（[execution.py:221](../../../src/workflow/execution.py#L221)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `reason.strip`（[execution.py:221](../../../src/workflow/execution.py#L221)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- 静态扫描未定位直接调用方；可能通过路由注册、LangGraph 节点、协议方法或依赖注入动态调用，不据此判断为死代码。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：`ExecutionConflict('CANCEL_OPERATOR_REASON_REQUIRED')`。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。
- 恢复/幂等性：仅在代码有检查点、事务、请求编号或显式去重时才成立；此函数不能单凭名称视为可安全重试。


---

# ExecutionManager.cancel.update ⭐⭐

**位置与等级**：[execution.py:207](../../../src/workflow/execution.py#L207)；局部辅助逻辑，需理解其调用条件与失败传播。

**签名**：`def update(t: ExecutionTask) -> None`。

**作用**：处理 `update` 对应步骤；下列步骤依据函数体的实际控制流和调用点整理。

**输入与输出**：
- 输入：`t`（ExecutionTask）。
- 输出类型：`None`；具体返回路径见流程步骤。

**处理流程**：
1. 检查 `t.status not in ACTIVE`；按条件分流，else 分支不存在。
2. 更新 `t.cancel_requested`，值来自 `True`。
3. 更新 `t.operator`，值来自 `operator.strip()`。
4. 更新 `t.reason`，值来自 `reason.strip()`。
5. 更新 `t.status`，值来自 `'cancelled' if t.status == 'queued' else 'cancelling'`。

**关键条件与保护**：
- [execution.py:208](../../../src/workflow/execution.py#L208)：`t.status not in ACTIVE`，不满足时跳过本分支。

**调用与被调用**：
- `ExecutionConflict`（调用点 [execution.py:209](../../../src/workflow/execution.py#L209)）→ [ExecutionConflict](../persistence/execution.md)，静态可定位。
- `operator.strip`（[execution.py:211](../../../src/workflow/execution.py#L211)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `reason.strip`（[execution.py:212](../../../src/workflow/execution.py#L212)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- 静态扫描未定位直接调用方；可能通过路由注册、LangGraph 节点、协议方法或依赖注入动态调用，不据此判断为死代码。

**状态、副作用与异常**：
- 显式状态/容器赋值：`t.cancel_requested`、`t.operator`、`t.reason`、`t.status`。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：`ExecutionConflict('EXECUTION_NOT_ACTIVE')`。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。
- 恢复/幂等性：仅在代码有检查点、事务、请求编号或显式去重时才成立；此函数不能单凭名称视为可安全重试。


---

# ExecutionManager.view ⭐⭐

**位置与等级**：[execution.py:225](../../../src/workflow/execution.py#L225)；局部辅助逻辑，需理解其调用条件与失败传播。

**签名**：`def view(self, run_id: str) -> dict[str, Any]`。

**作用**：处理 `view` 对应步骤；下列步骤依据函数体的实际控制流和调用点整理。

**输入与输出**：
- 输入：`run_id`（str；目标运行的稳定标识）。
- 输出类型：`dict[str, Any]`；具体返回路径见流程步骤。

**处理流程**：
1. 更新 `state`，值来自 `self.service.show_run(run_id)`。
2. 更新 `task`，值来自 `self.repository.get(run_id)`。
3. 更新 `legacy`，值来自 `state.pipeline_version != PIPELINE_VERSION`。
4. 更新 `status`，值来自 `task.status if task else self.business_status(state)`。
5. 更新 `active`，值来自 `task is not None and task.status in ACTIVE`。
6. 更新 `blocked`，值来自 `self.blockers(state, include_sent=not active)`。
7. 更新 `hard_blocks`，值来自 `{'PROJECTION_SYNC_PENDING', 'EXECUTION_INPUT_CHANGED', 'PROVIDER_CONFIGURATION_CHANGED', 'EXECUTION…`。
8. 检查 `task and task.error_code in hard_blocks`；按条件分流，else 分支不存在。
9. 检查 `task and (not active) and (task.status in {'awaiting_review', 'awaiting_commit', 'completed'})`；按条件分流，else 分支不存在。
10. 返回 `{'run_id': run_id, 'status': status, 'business_status': state.status, 'version': task.version if task el…`。

**关键条件与保护**：
- [execution.py:241](../../../src/workflow/execution.py#L241)：`task and task.error_code in hard_blocks`，不满足时跳过本分支。
- [execution.py:244](../../../src/workflow/execution.py#L244)：`task and (not active) and (task.status in {'awaiting_review', 'awaiting_commit', 'completed'})`，不满足时跳过本分支。

**调用与被调用**：
- `self.service.show_run`（[execution.py:226](../../../src/workflow/execution.py#L226)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `self.repository.get`（[execution.py:227](../../../src/workflow/execution.py#L227)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `self.business_status`（调用点 [execution.py:231](../../../src/workflow/execution.py#L231)）→ [ExecutionManager.business_status](execution.md)，静态可定位。
- `self.blockers`（调用点 [execution.py:233](../../../src/workflow/execution.py#L233)）→ [ExecutionManager.blockers](execution.md)，静态可定位。
- `task.updated_at.isoformat`（[execution.py:259](../../../src/workflow/execution.py#L259)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `self.repository.unknown`（[execution.py:264](../../../src/workflow/execution.py#L264)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `bool`（[execution.py:266](../../../src/workflow/execution.py#L266)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- 静态可定位的调用方：[ExecutionManager.reconcile_request](execution.md)。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：未见 `raise`；下游异常可能继续上抛。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。
- 恢复/幂等性：仅在代码有检查点、事务、请求编号或显式去重时才成立；此函数不能单凭名称视为可安全重试。


---

# ExecutionManager.branch_progress ⭐⭐

**位置与等级**：[execution.py:270](../../../src/workflow/execution.py#L270)；局部辅助逻辑，需理解其调用条件与失败传播。

**签名**：`def branch_progress(self, run_id: str) -> list[BranchProgress]`。

**作用**：处理 `branch_progress` 对应步骤；下列步骤依据函数体的实际控制流和调用点整理。

**输入与输出**：
- 输入：`run_id`（str；目标运行的稳定标识）。
- 输出类型：`list[BranchProgress]`；具体返回路径见流程步骤。

**处理流程**：
1. 更新 `state`，值来自 `self.service.show_run(run_id)`。
2. 更新 `task`，值来自 `self.repository.get(run_id)`。
3. 更新 `updated`，值来自 `task.updated_at if task else state.revision.created_at if state.revision else None`。
4. 检查 `updated is None`；按条件分流，else 分支不存在。
5. 更新 `node`，值来自 `task.node if task else state.current_node`。
6. 更新 `active`，值来自 `bool(task and task.status in ACTIVE)`。
7. 更新 `failed`，值来自 `bool(task and task.status == 'failed')`。
8. 更新 `calls`，值来自 `state.provider_calls`。
9. 更新 `document`，值来自 `state.document`。
10. 更新 `text_total`，值来自 `1 if document and document.text_blocks else 0`。
11. 更新 `text_done`，值来自 `min(text_total, sum((c.provider == 'llm' and c.status == 'succeeded' for c in calls)))`。
12. 更新 `visual_total`，值来自 `len(document.media_assets) if document else 0`。
13. 更新 `visual_done`，值来自 `min(visual_total, sum((c.provider == 'vlm' and c.status == 'succeeded' for c in calls)))`。
14. 更新 `ocr_total`，值来自 `sum((asset.requires_ocr for asset in document.media_assets)) if document else 0`。
15. 更新 `node_order`，值来自 `['ingest', 'parse_document', 'materialize_visual_assets', 'run_ocr', 'persist_evidence', 'load_sche…`。
16. 更新 `position`，值来自 `node_order.index(node) if node in node_order else -1`。
17. 更新 `ocr_done`，值来自 `ocr_total if position > node_order.index('run_ocr') else 0`。
18. 更新 `commit_done`，值来自 `int(state.revision is not None or bool(task and task.commit_applied))`。
19. 返回 `[BranchProgress(branch='text', status=status(text_done, text_total, 'extract_text_claims', 'extract_text…`。

**关键条件与保护**：
- [execution.py:274](../../../src/workflow/execution.py#L274)：`updated is None`，不满足时跳过本分支。

**调用与被调用**：
- `self.service.show_run`（[execution.py:271](../../../src/workflow/execution.py#L271)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `self.repository.get`（[execution.py:272](../../../src/workflow/execution.py#L272)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `datetime.now`（[execution.py:277](../../../src/workflow/execution.py#L277)）：来自 `datetime.datetime`；具体实现可能由依赖注入或运行时分派决定。
- `bool`（[execution.py:279](../../../src/workflow/execution.py#L279)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `min`（[execution.py:284](../../../src/workflow/execution.py#L284)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `sum`（[execution.py:286](../../../src/workflow/execution.py#L286)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `len`（[execution.py:288](../../../src/workflow/execution.py#L288)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `node_order.index`（[execution.py:313](../../../src/workflow/execution.py#L313)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `int`（[execution.py:327](../../../src/workflow/execution.py#L327)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `BranchProgress`（调用点 [execution.py:329](../../../src/workflow/execution.py#L329)）→ [BranchProgress](../domain/execution.md)，静态可定位。
- `status`（[execution.py:331](../../../src/workflow/execution.py#L331)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- 静态扫描未定位直接调用方；可能通过路由注册、LangGraph 节点、协议方法或依赖注入动态调用，不据此判断为死代码。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：未见 `raise`；下游异常可能继续上抛。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。
- 恢复/幂等性：仅在代码有检查点、事务、请求编号或显式去重时才成立；此函数不能单凭名称视为可安全重试。


---

# ExecutionManager.branch_progress.status ⭐⭐

**位置与等级**：[execution.py:315](../../../src/workflow/execution.py#L315)；局部辅助逻辑，需理解其调用条件与失败传播。

**签名**：`def status(completed: int, total: int, start: str, done: str) -> str`。

**作用**：处理 `status` 对应步骤；下列步骤依据函数体的实际控制流和调用点整理。

**输入与输出**：
- 输入：`completed`（int）；`total`（int）；`start`（str）；`done`（str）。
- 输出类型：`str`；具体返回路径见流程步骤。

**处理流程**：
1. 检查 `total == 0`；按条件分流，else 分支不存在。
2. 检查 `completed >= total or (done in node_order and position > node_order.index(done))`；按条件分流，else 分支不存在。
3. 检查 `failed and node == start`；按条件分流，else 分支不存在。
4. 检查 `active and node == start`；按条件分流，else 分支不存在。
5. 返回 `'pending'`。

**关键条件与保护**：
- [execution.py:316](../../../src/workflow/execution.py#L316)：`total == 0`，不满足时跳过本分支。
- [execution.py:318](../../../src/workflow/execution.py#L318)：`completed >= total or (done in node_order and position > node_order.index(done))`，不满足时跳过本分支。
- [execution.py:320](../../../src/workflow/execution.py#L320)：`failed and node == start`，不满足时跳过本分支。
- [execution.py:322](../../../src/workflow/execution.py#L322)：`active and node == start`，不满足时跳过本分支。

**调用与被调用**：
- `node_order.index`（[execution.py:318](../../../src/workflow/execution.py#L318)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- 静态扫描未定位直接调用方；可能通过路由注册、LangGraph 节点、协议方法或依赖注入动态调用，不据此判断为死代码。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：未见 `raise`；下游异常可能继续上抛。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。
- 恢复/幂等性：仅在代码有检查点、事务、请求编号或显式去重时才成立；此函数不能单凭名称视为可安全重试。


---

# ExecutionManager.reconcile_request ⭐⭐⭐⭐

**位置与等级**：[execution.py:365](../../../src/workflow/execution.py#L365)；承担主要 Agent、应用服务或审核/执行入口，跨模块影响显著。

**签名**：`def reconcile_request(self, run_id: str, decision: RequestReconciliation) -> dict[str, Any]`。

**作用**：处理 `reconcile_request` 对应步骤；下列步骤依据函数体的实际控制流和调用点整理。

**输入与输出**：
- 输入：`run_id`（str；目标运行的稳定标识）；`decision`（RequestReconciliation）。
- 输出类型：`dict[str, Any]`；具体返回路径见流程步骤。

**处理流程**：
1. 调用 `self.compatible`，结果未直接赋值。
2. 更新 `event`，值来自 `self.repository.reconcile_request(run_id, decision)`。
3. 返回 `{'event': event.model_dump(mode='json'), 'execution': self.view(run_id), 'requests': self.repository.req…`。

**调用与被调用**：
- `self.compatible`（调用点 [execution.py:368](../../../src/workflow/execution.py#L368)）→ [ExecutionManager.compatible](execution.md)，静态可定位。
- `self.service.show_run`（[execution.py:368](../../../src/workflow/execution.py#L368)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `self.repository.reconcile_request`（[execution.py:369](../../../src/workflow/execution.py#L369)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `event.model_dump`（[execution.py:371](../../../src/workflow/execution.py#L371)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `self.view`（调用点 [execution.py:372](../../../src/workflow/execution.py#L372)）→ [ExecutionManager.view](execution.md)，静态可定位。
- `self.repository.requests`（[execution.py:373](../../../src/workflow/execution.py#L373)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- 静态扫描未定位直接调用方；可能通过路由注册、LangGraph 节点、协议方法或依赖注入动态调用，不据此判断为死代码。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：未见 `raise`；下游异常可能继续上抛。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。
- 恢复/幂等性：仅在代码有检查点、事务、请求编号或显式去重时才成立；此函数不能单凭名称视为可安全重试。


---

# ExecutionManager.health ⭐⭐

**位置与等级**：[execution.py:376](../../../src/workflow/execution.py#L376)；局部辅助逻辑，需理解其调用条件与失败传播。

**签名**：`def health(self) -> dict[str, Any]`。

**作用**：处理 `health` 对应步骤；下列步骤依据函数体的实际控制流和调用点整理。

**输入与输出**：
- 输入：无业务参数（或仅隐式接收实例）。
- 输出类型：`dict[str, Any]`；具体返回路径见流程步骤。

**处理流程**：
1. 更新 `tasks`，值来自 `self.repository.list_tasks()`。
2. 返回 `{'worker': 'stopping' if self.stopping else 'running' if self.worker and (not self.worker.done()) else '…`。

**调用与被调用**：
- `self.repository.list_tasks`（[execution.py:377](../../../src/workflow/execution.py#L377)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `self.worker.done`（[execution.py:382](../../../src/workflow/execution.py#L382)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `sum`（[execution.py:384](../../../src/workflow/execution.py#L384)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `bool`（[execution.py:386](../../../src/workflow/execution.py#L386)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- 静态扫描未定位直接调用方；可能通过路由注册、LangGraph 节点、协议方法或依赖注入动态调用，不据此判断为死代码。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：未见 `raise`；下游异常可能继续上抛。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。
- 恢复/幂等性：仅在代码有检查点、事务、请求编号或显式去重时才成立；此函数不能单凭名称视为可安全重试。


---

# ExecutionManager.start ⭐⭐

**位置与等级**：[execution.py:390](../../../src/workflow/execution.py#L390)；局部辅助逻辑，需理解其调用条件与失败传播。

**签名**：`async def start(self, *, persistent: bool=True) -> None`。

**作用**：处理 `start` 对应步骤；下列步骤依据函数体的实际控制流和调用点整理。

**输入与输出**：
- 输入：`persistent`（bool；默认 `True`）。
- 输出类型：`None`；具体返回路径见流程步骤。

**处理流程**：
1. 进入上下文 `self.lifecycle`，由上下文管理器控制资源释放或事务范围。

**调用与被调用**：
- `self._start`（调用点 [execution.py:392](../../../src/workflow/execution.py#L392)）→ [ExecutionManager._start](execution.md)，静态可定位。
- 静态可定位的调用方：[ExecutionManager.run_wait](execution.md)。

**状态、副作用与异常**：
- 显式状态/容器赋值：`self.persistent`。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：未见 `raise`；下游异常可能继续上抛。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。
- 恢复/幂等性：仅在代码有检查点、事务、请求编号或显式去重时才成立；此函数不能单凭名称视为可安全重试。


---

# ExecutionManager._start ⭐⭐

**位置与等级**：[execution.py:395](../../../src/workflow/execution.py#L395)；局部辅助逻辑，需理解其调用条件与失败传播。

**签名**：`async def _start(self) -> None`。

**作用**：内部辅助步骤；将参数转换为本模块所需的中间对象或操作结果。

**输入与输出**：
- 输入：无业务参数（或仅隐式接收实例）。
- 输出类型：`None`；具体返回路径见流程步骤。

**处理流程**：
1. 检查 `self.worker and (not self.worker.done())`；按条件分流，else 分支不存在。
2. 检查 `self.owner.is_locked`；按条件分流，else 分支不存在。
3. 捕获 Timeout；另检查 finally/else 的清理和传播。
4. 更新 `self.stopping`，值来自 `False`。
5. 捕获 BaseException；另检查 finally/else 的清理和传播。

**关键条件与保护**：
- [execution.py:396](../../../src/workflow/execution.py#L396)：`self.worker and (not self.worker.done())`，不满足时跳过本分支。
- [execution.py:398](../../../src/workflow/execution.py#L398)：`self.owner.is_locked`，不满足时跳过本分支。

**调用与被调用**：
- `self.worker.done`（[execution.py:396](../../../src/workflow/execution.py#L396)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `self.owner.release`（[execution.py:399](../../../src/workflow/execution.py#L399)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `self.owner.acquire`（[execution.py:401](../../../src/workflow/execution.py#L401)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `ExecutionConflict`（调用点 [execution.py:403](../../../src/workflow/execution.py#L403)）→ [ExecutionConflict](../persistence/execution.md)，静态可定位。
- `self.reconcile`（调用点 [execution.py:408](../../../src/workflow/execution.py#L408)）→ [ExecutionManager.reconcile](execution.md)，静态可定位。
- `asyncio.create_task`（[execution.py:409](../../../src/workflow/execution.py#L409)）：来自 `asyncio`；具体实现可能由依赖注入或运行时分派决定。
- `self._work`（调用点 [execution.py:409](../../../src/workflow/execution.py#L409)）→ [ExecutionManager._work](execution.md)，静态可定位。
- 静态可定位的调用方：[ExecutionManager.start](execution.md)。

**状态、副作用与异常**：
- 显式状态/容器赋值：`self.stopping`、`self.worker`。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：`ExecutionConflict(<字符串常量>)`、`重新抛出`。
- 本地捕获：`Timeout`、`BaseException`。
- 恢复/幂等性：仅在代码有检查点、事务、请求编号或显式去重时才成立；此函数不能单凭名称视为可安全重试。


---

# ExecutionManager.reconcile ⭐⭐⭐⭐

**位置与等级**：[execution.py:414](../../../src/workflow/execution.py#L414)；承担主要 Agent、应用服务或审核/执行入口，跨模块影响显著。

**签名**：`async def reconcile(self) -> None`。

**作用**：处理 `reconcile` 对应步骤；下列步骤依据函数体的实际控制流和调用点整理。

**输入与输出**：
- 输入：无业务参数（或仅隐式接收实例）。
- 输出类型：`None`；具体返回路径见流程步骤。

**处理流程**：
1. 遍历 `self.repository.list_tasks()`，逐项处理 `task`。

**关键条件与保护**：
- [execution.py:416](../../../src/workflow/execution.py#L416)：`task.status not in ACTIVE | {'interrupted'}`，不满足时跳过本分支。
- [execution.py:424](../../../src/workflow/execution.py#L424)：`task.commit_revision_id`，不满足时跳过本分支。
- [execution.py:426](../../../src/workflow/execution.py#L426)：`task.commit_revision_id in {r.id for r in revisions}`，不满足时跳过本分支。
- [execution.py:427](../../../src/workflow/execution.py#L427)：`state.graph_commit and state.graph_commit.revision.id == task.commit_revision_id`，不满足时跳过本分支。
- [execution.py:439](../../../src/workflow/execution.py#L439)：`task.cancel_requested`，不满足时跳过本分支。
- [execution.py:442](../../../src/workflow/execution.py#L442)：`state.status == 'awaiting_review' and (not self.service.reviews.repository.pending(task.run_id))`，不满足时跳过本分支。
- [execution.py:448](../../../src/workflow/execution.py#L448)：`task.operation == 'confirm'`，不满足时跳过本分支。
- [execution.py:452](../../../src/workflow/execution.py#L452)：`blocked`，不满足时跳过本分支。
- [execution.py:455](../../../src/workflow/execution.py#L455)：`state.current_node == 'prepare_graph_commit' and (state.review_workspace or state.pending_correction_id)`，不满足时跳过本分支。
- [execution.py:460](../../../src/workflow/execution.py#L460)：`state.status in {'completed', 'awaiting_review', 'failed'} and task.status == 'queued'`，不满足时跳过本分支。
- [execution.py:468](../../../src/workflow/execution.py#L468)：`snapshot['exists'] and (not snapshot['next'])`，不满足时跳过本分支。
- [execution.py:471](../../../src/workflow/execution.py#L471)：`not snapshot['exists'] and task.attempt and state.document`，不满足时跳过本分支。

**调用与被调用**：
- `self.repository.list_tasks`（[execution.py:415](../../../src/workflow/execution.py#L415)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `self.service.show_run`（[execution.py:419](../../../src/workflow/execution.py#L419)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `self.compatible`（调用点 [execution.py:420](../../../src/workflow/execution.py#L420)）→ [ExecutionManager.compatible](execution.md)，静态可定位。
- `self.service.runs.mutation_lock`（[execution.py:421](../../../src/workflow/execution.py#L421)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `self.service.reviews.recover`（[execution.py:422](../../../src/workflow/execution.py#L422)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `self.service.graph_store.list_revisions`（[execution.py:425](../../../src/workflow/execution.py#L425)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `self.service.runs.save`（[execution.py:433](../../../src/workflow/execution.py#L433)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `self.repository.change`（[execution.py:434](../../../src/workflow/execution.py#L434)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `ExecutionConflict`（调用点 [execution.py:438](../../../src/workflow/execution.py#L438)）→ [ExecutionConflict](../persistence/execution.md)，静态可定位。
- `self.service.reviews.repository.pending`（[execution.py:444](../../../src/workflow/execution.py#L444)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `self.set_status`（调用点 [execution.py:446](../../../src/workflow/execution.py#L446)）→ [ExecutionManager.set_status](execution.md)，静态可定位。
- `self.blockers`（调用点 [execution.py:451](../../../src/workflow/execution.py#L451)）→ [ExecutionManager.blockers](execution.md)，静态可定位。
- `self.preflight`（调用点 [execution.py:454](../../../src/workflow/execution.py#L454)）→ [ExecutionManager.preflight](execution.md)，静态可定位。
- `self.business_status`（调用点 [execution.py:464](../../../src/workflow/execution.py#L464)）→ [ExecutionManager.business_status](execution.md)，静态可定位。
- `self.service.review_workflow`（[execution.py:466](../../../src/workflow/execution.py#L466)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `workflow.execution_snapshot`（[execution.py:467](../../../src/workflow/execution.py#L467)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `isinstance`（[execution.py:482](../../../src/workflow/execution.py#L482)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `str`（[execution.py:482](../../../src/workflow/execution.py#L482)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `type`（[execution.py:482](../../../src/workflow/execution.py#L482)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- 静态可定位的调用方：[ExecutionManager._start](execution.md)。

**状态、副作用与异常**：
- 显式状态/容器赋值：`state.status`、`state.revision`。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：`ExecutionConflict('SUBMISSION_CONFIRMATION_REQUIRED')`、`ExecutionConflict(blocked)`、`ExecutionConflict('CHECKPOINT_MISSING')`。
- 本地捕获：`Exception`。
- 恢复/幂等性：仅在代码有检查点、事务、请求编号或显式去重时才成立；此函数不能单凭名称视为可安全重试。


---

# ExecutionManager.reconcile.requeue ⭐⭐⭐⭐

**位置与等级**：[execution.py:474](../../../src/workflow/execution.py#L474)；承担主要 Agent、应用服务或审核/执行入口，跨模块影响显著。

**签名**：`def requeue(t: ExecutionTask, checkpoint: dict[str, Any]=snapshot) -> None`。

**作用**：处理 `requeue` 对应步骤；下列步骤依据函数体的实际控制流和调用点整理。

**输入与输出**：
- 输入：`t`（ExecutionTask）；`checkpoint`（dict[str, Any]；默认 `snapshot`）。
- 输出类型：`None`；具体返回路径见流程步骤。

**处理流程**：
1. 更新 `t.status`，值来自 `'queued'`。
2. 更新 `t.operation`，值来自 `'resume' if checkpoint['exists'] else 'execute'`。
3. 更新 `t.error_code`，值来自 `None`。
4. 更新 `t.reason`，值来自 `'SAFE_RESTART_RECOVERY' if t.attempt else None`。

**调用与被调用**：
- 无显式函数调用，或仅声明协议/常量。
- 静态扫描未定位直接调用方；可能通过路由注册、LangGraph 节点、协议方法或依赖注入动态调用，不据此判断为死代码。

**状态、副作用与异常**：
- 显式状态/容器赋值：`t.status`、`t.operation`、`t.error_code`、`t.reason`。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：未见 `raise`；下游异常可能继续上抛。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。
- 恢复/幂等性：仅在代码有检查点、事务、请求编号或显式去重时才成立；此函数不能单凭名称视为可安全重试。


---

# ExecutionManager.reconcile.block ⭐⭐⭐⭐

**位置与等级**：[execution.py:484](../../../src/workflow/execution.py#L484)；承担主要 Agent、应用服务或审核/执行入口，跨模块影响显著。

**签名**：`def block(t: ExecutionTask, error: str=code) -> None`。

**作用**：处理 `block` 对应步骤；下列步骤依据函数体的实际控制流和调用点整理。

**输入与输出**：
- 输入：`t`（ExecutionTask）；`error`（str；默认 `code`）。
- 输出类型：`None`；具体返回路径见流程步骤。

**处理流程**：
1. 更新 `t.status`，值来自 `'interrupted'`。
2. 更新 `t.error_code`，值来自 `error`。

**调用与被调用**：
- 无显式函数调用，或仅声明协议/常量。
- 静态扫描未定位直接调用方；可能通过路由注册、LangGraph 节点、协议方法或依赖注入动态调用，不据此判断为死代码。

**状态、副作用与异常**：
- 显式状态/容器赋值：`t.status`、`t.error_code`。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：未见 `raise`；下游异常可能继续上抛。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。
- 恢复/幂等性：仅在代码有检查点、事务、请求编号或显式去重时才成立；此函数不能单凭名称视为可安全重试。


---

# ExecutionManager.settle_committed ⭐⭐

**位置与等级**：[execution.py:490](../../../src/workflow/execution.py#L490)；局部辅助逻辑，需理解其调用条件与失败传播。

**签名**：`async def settle_committed(self, run_id: str) -> bool`。

**作用**：处理 `settle_committed` 对应步骤；下列步骤依据函数体的实际控制流和调用点整理。

**输入与输出**：
- 输入：`run_id`（str；目标运行的稳定标识）。
- 输出类型：`bool`；具体返回路径见流程步骤。

**处理流程**：
1. 更新 `task`，值来自 `self.repository.get(run_id)`。
2. 检查 `not task or not task.commit_revision_id`；按条件分流，else 分支不存在。
3. 更新 `revisions`，值来自 `await self.service.graph_store.list_revisions(limit=1000)`。
4. 检查 `not any((r.id == task.commit_revision_id for r in revisions))`；按条件分流，else 分支不存在。
5. 更新 `state`，值来自 `self.service.show_run(run_id)`。
6. 更新 `state.status`，值来自 `'completed'`。
7. 更新 `state.current_node`，值来自 `'commit_graph'`。
8. 调用 `self.service.runs.save`，结果未直接赋值。
9. 调用 `self.repository.change`，结果未直接赋值。
10. 返回 `True`。

**关键条件与保护**：
- [execution.py:492](../../../src/workflow/execution.py#L492)：`not task or not task.commit_revision_id`，不满足时跳过本分支。
- [execution.py:495](../../../src/workflow/execution.py#L495)：`not any((r.id == task.commit_revision_id for r in revisions))`，不满足时跳过本分支。

**调用与被调用**：
- `self.repository.get`（[execution.py:491](../../../src/workflow/execution.py#L491)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `self.service.graph_store.list_revisions`（[execution.py:494](../../../src/workflow/execution.py#L494)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `any`（[execution.py:495](../../../src/workflow/execution.py#L495)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `self.service.show_run`（[execution.py:497](../../../src/workflow/execution.py#L497)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `self.service.runs.save`（[execution.py:500](../../../src/workflow/execution.py#L500)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `self.repository.change`（[execution.py:509](../../../src/workflow/execution.py#L509)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- 静态可定位的调用方：[ExecutionManager._work](execution.md)。

**状态、副作用与异常**：
- 显式状态/容器赋值：`state.status`、`state.current_node`。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：未见 `raise`；下游异常可能继续上抛。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。
- 恢复/幂等性：仅在代码有检查点、事务、请求编号或显式去重时才成立；此函数不能单凭名称视为可安全重试。


---

# ExecutionManager.settle_committed.settle ⭐⭐

**位置与等级**：[execution.py:502](../../../src/workflow/execution.py#L502)；局部辅助逻辑，需理解其调用条件与失败传播。

**签名**：`def settle(t: ExecutionTask) -> None`。

**作用**：处理 `settle` 对应步骤；下列步骤依据函数体的实际控制流和调用点整理。

**输入与输出**：
- 输入：`t`（ExecutionTask）。
- 输出类型：`None`；具体返回路径见流程步骤。

**处理流程**：
1. 更新 `t.status`，值来自 `'completed'`。
2. 更新 `t.commit_applied`，值来自 `True`。
3. 更新 `t.error_code`，值来自 `None`。
4. 检查 `t.cancel_requested`；按条件分流，else 分支不存在。

**关键条件与保护**：
- [execution.py:506](../../../src/workflow/execution.py#L506)：`t.cancel_requested`，不满足时跳过本分支。

**调用与被调用**：
- 无显式函数调用，或仅声明协议/常量。
- 静态扫描未定位直接调用方；可能通过路由注册、LangGraph 节点、协议方法或依赖注入动态调用，不据此判断为死代码。

**状态、副作用与异常**：
- 显式状态/容器赋值：`t.status`、`t.commit_applied`、`t.error_code`、`t.reason`。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：未见 `raise`；下游异常可能继续上抛。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。
- 恢复/幂等性：仅在代码有检查点、事务、请求编号或显式去重时才成立；此函数不能单凭名称视为可安全重试。


---

# ExecutionManager.preflight ⭐⭐

**位置与等级**：[execution.py:512](../../../src/workflow/execution.py#L512)；局部辅助逻辑，需理解其调用条件与失败传播。

**签名**：`async def preflight(self, state: WorkflowState, task: ExecutionTask) -> None`。

**作用**：处理 `preflight` 对应步骤；下列步骤依据函数体的实际控制流和调用点整理。

**输入与输出**：
- 输入：`state`（WorkflowState；跨节点 WorkflowState；调用方须保持证据与状态一致）；`task`（ExecutionTask）。
- 输出类型：`None`；具体返回路径见流程步骤。

**处理流程**：
1. 调用 `self.compatible`，结果未直接赋值。
2. 检查 `file_sha256(Path(state.input_path)) != task.input_hash or file_sha256(Path(state.schema_path)) != task.s…`；按条件分流，else 分支不存在。
3. 调用 `self.service._validate_entity_policy`，结果未直接赋值。
4. 更新 `tail_nodes`，值来自 `{'resolve_entities', 'normalize_claims', 'detect_conflicts', 'route_by_risk', 'prepare_graph_commit…`。
5. 检查 `not (state.review_workspace or state.correction_tail_only or state.current_node in tail_nodes)`；按条件分流，else 分支不存在。
6. 检查 `state.document and state.current_node not in {'ingest', 'parse_document', 'materialize_visual_assets', '…`；按条件分流，else 分支不存在。

**关键条件与保护**：
- [execution.py:514](../../../src/workflow/execution.py#L514)：`file_sha256(Path(state.input_path)) != task.input_hash or file_sha256(Path(state.schema_path)) != task.schema_hash`，不满足时跳过本分支。
- [execution.py:528](../../../src/workflow/execution.py#L528)：`not (state.review_workspace or state.correction_tail_only or state.current_node in tail_nodes)`，不满足时跳过本分支。
- [execution.py:543](../../../src/workflow/execution.py#L543)：`any((p.fingerprint() != expected for p, expected in pairs))`，不满足时跳过本分支。
- [execution.py:545](../../../src/workflow/execution.py#L545)：`state.document and state.current_node not in {'ingest', 'parse_document', 'materialize_visual_assets', 'run_ocr'}`，不满足时跳过本分支。
- [execution.py:552](../../../src/workflow/execution.py#L552)：`not await self.service.evidence_store.verify(evidence.id)`，不满足时跳过本分支。

**调用与被调用**：
- `self.compatible`（调用点 [execution.py:513](../../../src/workflow/execution.py#L513)）→ [ExecutionManager.compatible](execution.md)，静态可定位。
- `file_sha256`（调用点 [execution.py:515](../../../src/workflow/execution.py#L515)）→ [file_sha256](../core/ids.md)，静态可定位。
- `Path`（[execution.py:515](../../../src/workflow/execution.py#L515)）：来自 `pathlib.Path`；具体实现可能由依赖注入或运行时分派决定。
- `ExecutionConflict`（调用点 [execution.py:518](../../../src/workflow/execution.py#L518)）→ [ExecutionConflict](../persistence/execution.md)，静态可定位。
- `self.service._validate_entity_policy`（[execution.py:519](../../../src/workflow/execution.py#L519)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `self.service.provider`（[execution.py:532](../../../src/workflow/execution.py#L532)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `self.service.ocr_provider`（[execution.py:534](../../../src/workflow/execution.py#L534)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `self.service.vlm_provider`（[execution.py:538](../../../src/workflow/execution.py#L538)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `self.service.embedding_provider`（[execution.py:541](../../../src/workflow/execution.py#L541)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `any`（[execution.py:543](../../../src/workflow/execution.py#L543)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `p.fingerprint`（[execution.py:543](../../../src/workflow/execution.py#L543)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `self.service.evidence_store.verify`（[execution.py:552](../../../src/workflow/execution.py#L552)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- 静态可定位的调用方：[ExecutionManager.reconcile](execution.md)、[ExecutionManager._work](execution.md)。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：`ExecutionConflict('EXECUTION_INPUT_CHANGED')`、`ExecutionConflict('PROVIDER_CONFIGURATION_CHANGED')`、`ExecutionConflict('EXECUTION_EVIDENCE_INVALID')`。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。
- 恢复/幂等性：仅在代码有检查点、事务、请求编号或显式去重时才成立；此函数不能单凭名称视为可安全重试。


---

# ExecutionManager._work ⭐⭐

**位置与等级**：[execution.py:555](../../../src/workflow/execution.py#L555)；局部辅助逻辑，需理解其调用条件与失败传播。

**签名**：`async def _work(self) -> None`。

**作用**：内部辅助步骤；将参数转换为本模块所需的中间对象或操作结果。

**输入与输出**：
- 输入：无业务参数（或仅隐式接收实例）。
- 输出类型：`None`；具体返回路径见流程步骤。

**处理流程**：
1. 在 `not self.stopping` 成立期间迭代，需关注退出和预算条件。

**关键条件与保护**：
- [execution.py:558](../../../src/workflow/execution.py#L558)：`task is None`，不满足时跳过本分支。
- [execution.py:574](../../../src/workflow/execution.py#L574)：`task.operation == 'execute'`，不满足时有 else 分支。
- [execution.py:576](../../../src/workflow/execution.py#L576)：`task.operation == 'resume'`，不满足时有 else 分支。
- [execution.py:578](../../../src/workflow/execution.py#L578)：`task.attempt == 0 and (not initial.document) and (initial.current_node == 'ingest')`，不满足时有 else 分支。
- [execution.py:607](../../../src/workflow/execution.py#L607)：`not await self.settle_committed(task.run_id)`，不满足时跳过本分支。
- [execution.py:612](../../../src/workflow/execution.py#L612)：`await self.settle_committed(task.run_id)`，不满足时跳过本分支。

**调用与被调用**：
- `next`（[execution.py:557](../../../src/workflow/execution.py#L557)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `self.repository.list_tasks`（[execution.py:557](../../../src/workflow/execution.py#L557)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `asyncio.sleep`（[execution.py:559](../../../src/workflow/execution.py#L559)）：来自 `asyncio`；具体实现可能由依赖注入或运行时分派决定。
- `RunControl`（调用点 [execution.py:561](../../../src/workflow/execution.py#L561)）→ [RunControl](execution.md)，静态可定位。
- `current_execution.set`（[execution.py:562](../../../src/workflow/execution.py#L562)）：来自 `src.core.execution_control.current_execution`；具体实现可能由依赖注入或运行时分派决定。
- `self.service.runs.mutation_lock`（[execution.py:564](../../../src/workflow/execution.py#L564)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `self.preflight`（调用点 [execution.py:565](../../../src/workflow/execution.py#L565)）→ [ExecutionManager.preflight](execution.md)，静态可定位。
- `self.service.show_run`（[execution.py:565](../../../src/workflow/execution.py#L565)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `self.repository.change`（[execution.py:573](../../../src/workflow/execution.py#L573)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `self.service._execute_run`（[execution.py:575](../../../src/workflow/execution.py#L575)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `self.service._resume`（[execution.py:585](../../../src/workflow/execution.py#L585)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `self.service._confirm_review_commit`（[execution.py:587](../../../src/workflow/execution.py#L587)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `str`（[execution.py:599](../../../src/workflow/execution.py#L599)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `self.settle_committed`（调用点 [execution.py:607](../../../src/workflow/execution.py#L607)）→ [ExecutionManager.settle_committed](execution.md)，静态可定位。
- `self.set_status`（调用点 [execution.py:608](../../../src/workflow/execution.py#L608)）→ [ExecutionManager.set_status](execution.md)，静态可定位。
- `type`（[execution.py:621](../../../src/workflow/execution.py#L621)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `current_execution.reset`（[execution.py:630](../../../src/workflow/execution.py#L630)）：来自 `src.core.execution_control.current_execution`；具体实现可能由依赖注入或运行时分派决定。
- 静态可定位的调用方：[ExecutionManager._start](execution.md)。

**状态、副作用与异常**：
- 显式状态/容器赋值：`self.failures[task.run_id]`、`control.closed`。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：`重新抛出`。
- 本地捕获：`ExecutionPaused`、`asyncio.CancelledError`、`Exception`。
- 恢复/幂等性：仅在代码有检查点、事务、请求编号或显式去重时才成立；此函数不能单凭名称视为可安全重试。


---

# ExecutionManager._work.claim ⭐⭐

**位置与等级**：[execution.py:567](../../../src/workflow/execution.py#L567)；局部辅助逻辑，需理解其调用条件与失败传播。

**签名**：`def claim(t: ExecutionTask) -> None`。

**作用**：处理 `claim` 对应步骤；下列步骤依据函数体的实际控制流和调用点整理。

**输入与输出**：
- 输入：`t`（ExecutionTask）。
- 输出类型：`None`；具体返回路径见流程步骤。

**处理流程**：
1. 检查 `t.status != 'queued'`；按条件分流，else 分支不存在。
2. 更新 `t.status`，值来自 `'running'`。
3. 更新 `t.attempt`，值来自 `1`。

**关键条件与保护**：
- [execution.py:568](../../../src/workflow/execution.py#L568)：`t.status != 'queued'`，不满足时跳过本分支。

**调用与被调用**：
- `ExecutionPaused`（调用点 [execution.py:569](../../../src/workflow/execution.py#L569)）→ [ExecutionPaused](../core/execution_control.md)，静态可定位。
- 静态扫描未定位直接调用方；可能通过路由注册、LangGraph 节点、协议方法或依赖注入动态调用，不据此判断为死代码。

**状态、副作用与异常**：
- 显式状态/容器赋值：`t.status`、`t.attempt`。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：`ExecutionPaused('USER_CANCEL')`。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。
- 恢复/幂等性：仅在代码有检查点、事务、请求编号或显式去重时才成立；此函数不能单凭名称视为可安全重试。


---

# ExecutionManager._work.finish ⭐⭐

**位置与等级**：[execution.py:591](../../../src/workflow/execution.py#L591)；局部辅助逻辑，需理解其调用条件与失败传播。

**签名**：`def finish(t: ExecutionTask, result: WorkflowState=state) -> None`。

**作用**：处理 `finish` 对应步骤；下列步骤依据函数体的实际控制流和调用点整理。

**输入与输出**：
- 输入：`t`（ExecutionTask）；`result`（WorkflowState；默认 `state`）。
- 输出类型：`None`；具体返回路径见流程步骤。

**处理流程**：
1. 更新 `t.status`，值来自 `self.business_status(result)`。
2. 更新 `t.node`，值来自 `result.current_node`。
3. 检查 `t.cancel_requested and result.status == 'completed'`；按条件分流，else 分支不存在。

**关键条件与保护**：
- [execution.py:594](../../../src/workflow/execution.py#L594)：`t.cancel_requested and result.status == 'completed'`，不满足时跳过本分支。

**调用与被调用**：
- `self.business_status`（调用点 [execution.py:592](../../../src/workflow/execution.py#L592)）→ [ExecutionManager.business_status](execution.md)，静态可定位。
- 静态扫描未定位直接调用方；可能通过路由注册、LangGraph 节点、协议方法或依赖注入动态调用，不据此判断为死代码。

**状态、副作用与异常**：
- 显式状态/容器赋值：`t.status`、`t.node`、`t.reason`。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：未见 `raise`；下游异常可能继续上抛。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。
- 恢复/幂等性：仅在代码有检查点、事务、请求编号或显式去重时才成立；此函数不能单凭名称视为可安全重试。


---

# ExecutionManager._work.pause ⭐⭐

**位置与等级**：[execution.py:601](../../../src/workflow/execution.py#L601)；局部辅助逻辑，需理解其调用条件与失败传播。

**签名**：`def pause(t: ExecutionTask, code: str=reason) -> None`。

**作用**：处理 `pause` 对应步骤；下列步骤依据函数体的实际控制流和调用点整理。

**输入与输出**：
- 输入：`t`（ExecutionTask）；`code`（str；默认 `reason`）。
- 输出类型：`None`；具体返回路径见流程步骤。

**处理流程**：
1. 更新 `t.status`，值来自 `'cancelled' if code == 'USER_CANCEL' else 'interrupted'`。
2. 更新 `t.error_code`，值来自 `code`。

**调用与被调用**：
- 无显式函数调用，或仅声明协议/常量。
- 静态扫描未定位直接调用方；可能通过路由注册、LangGraph 节点、协议方法或依赖注入动态调用，不据此判断为死代码。

**状态、副作用与异常**：
- 显式状态/容器赋值：`t.status`、`t.error_code`。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：未见 `raise`；下游异常可能继续上抛。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。
- 恢复/幂等性：仅在代码有检查点、事务、请求编号或显式去重时才成立；此函数不能单凭名称视为可安全重试。


---

# ExecutionManager._work.fail ⭐⭐

**位置与等级**：[execution.py:623](../../../src/workflow/execution.py#L623)；局部辅助逻辑，需理解其调用条件与失败传播。

**签名**：`def fail(t: ExecutionTask, code: str=error) -> None`。

**作用**：处理 `fail` 对应步骤；下列步骤依据函数体的实际控制流和调用点整理。

**输入与输出**：
- 输入：`t`（ExecutionTask）；`code`（str；默认 `error`）。
- 输出类型：`None`；具体返回路径见流程步骤。

**处理流程**：
1. 更新 `t.status`，值来自 `'failed'`。
2. 更新 `t.error_code`，值来自 `code`。

**调用与被调用**：
- 无显式函数调用，或仅声明协议/常量。
- 静态扫描未定位直接调用方；可能通过路由注册、LangGraph 节点、协议方法或依赖注入动态调用，不据此判断为死代码。

**状态、副作用与异常**：
- 显式状态/容器赋值：`t.status`、`t.error_code`。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：未见 `raise`；下游异常可能继续上抛。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。
- 恢复/幂等性：仅在代码有检查点、事务、请求编号或显式去重时才成立；此函数不能单凭名称视为可安全重试。


---

# ExecutionManager.wait ⭐⭐

**位置与等级**：[execution.py:632](../../../src/workflow/execution.py#L632)；局部辅助逻辑，需理解其调用条件与失败传播。

**签名**：`async def wait(self, run_id: str) -> WorkflowState`。

**作用**：处理 `wait` 对应步骤；下列步骤依据函数体的实际控制流和调用点整理。

**输入与输出**：
- 输入：`run_id`（str；目标运行的稳定标识）。
- 输出类型：`WorkflowState`；具体返回路径见流程步骤。

**处理流程**：
1. 在 `True` 成立期间迭代，需关注退出和预算条件。

**关键条件与保护**：
- [execution.py:635](../../../src/workflow/execution.py#L635)：`task and task.status not in ACTIVE`，不满足时跳过本分支。
- [execution.py:636](../../../src/workflow/execution.py#L636)：`task.status == 'failed'`，不满足时跳过本分支。
- [execution.py:641](../../../src/workflow/execution.py#L641)：`not self.worker or self.worker.done()`，不满足时跳过本分支。

**调用与被调用**：
- `self.repository.get`（[execution.py:634](../../../src/workflow/execution.py#L634)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `self.failures.get`（[execution.py:637](../../../src/workflow/execution.py#L637)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `ExecutionConflict`（调用点 [execution.py:638](../../../src/workflow/execution.py#L638)）→ [ExecutionConflict](../persistence/execution.md)，静态可定位。
- `self.service.show_run`（[execution.py:640](../../../src/workflow/execution.py#L640)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `self.worker.done`（[execution.py:641](../../../src/workflow/execution.py#L641)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `asyncio.sleep`（[execution.py:643](../../../src/workflow/execution.py#L643)）：来自 `asyncio`；具体实现可能由依赖注入或运行时分派决定。
- 静态可定位的调用方：[ExecutionManager.run_wait](execution.md)。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：`self.failures.get(run_id, ExecutionConflict(task.error_code or 'EXECUTION_FAILED'))`、`ExecutionConflict('WORKER_NOT_RUNNING')`。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。
- 恢复/幂等性：仅在代码有检查点、事务、请求编号或显式去重时才成立；此函数不能单凭名称视为可安全重试。


---

# ExecutionManager.run_wait ⭐⭐⭐⭐

**位置与等级**：[execution.py:645](../../../src/workflow/execution.py#L645)；承担主要 Agent、应用服务或审核/执行入口，跨模块影响显著。

**签名**：`async def run_wait(self, run_id: str, operation: Literal['execute', 'resume', 'confirm'], reviewer: str | None=None) -> WorkflowState`。

**作用**：处理 `run_wait` 对应步骤；下列步骤依据函数体的实际控制流和调用点整理。

**输入与输出**：
- 输入：`run_id`（str；目标运行的稳定标识）；`operation`（Literal['execute', 'resume', 'confirm']）；`reviewer`（str | None；默认 `None`；审核操作者，形成审计归属）。
- 输出类型：`WorkflowState`；具体返回路径见流程步骤。

**处理流程**：
1. 更新 `self.waiters`，值来自 `1`。
2. 捕获 无显式捕获；另检查 finally/else 的清理和传播。

**关键条件与保护**：
- [execution.py:655](../../../src/workflow/execution.py#L655)：`not existing or existing.status not in ACTIVE`，不满足时跳过本分支。
- [execution.py:662](../../../src/workflow/execution.py#L662)：`not self.persistent and (not self.waiters) and self.owner.is_locked`，不满足时跳过本分支。

**调用与被调用**：
- `self.start`（调用点 [execution.py:653](../../../src/workflow/execution.py#L653)）→ [ExecutionManager.start](execution.md)，静态可定位。
- `self.repository.get`（[execution.py:654](../../../src/workflow/execution.py#L654)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `self.service.runs.mutation_lock`（[execution.py:656](../../../src/workflow/execution.py#L656)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `self.service.reviews.recover`（[execution.py:657](../../../src/workflow/execution.py#L657)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `self.enqueue`（调用点 [execution.py:658](../../../src/workflow/execution.py#L658)）→ [ExecutionManager.enqueue](execution.md)，静态可定位。
- `self.wait`（调用点 [execution.py:659](../../../src/workflow/execution.py#L659)）→ [ExecutionManager.wait](execution.md)，静态可定位。
- `self.stop`（调用点 [execution.py:663](../../../src/workflow/execution.py#L663)）→ [ExecutionManager.stop](execution.md)，静态可定位。
- 静态扫描未定位直接调用方；可能通过路由注册、LangGraph 节点、协议方法或依赖注入动态调用，不据此判断为死代码。

**状态、副作用与异常**：
- 显式状态/容器赋值：`self.waiters`。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：未见 `raise`；下游异常可能继续上抛。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。
- 恢复/幂等性：仅在代码有检查点、事务、请求编号或显式去重时才成立；此函数不能单凭名称视为可安全重试。


---

# ExecutionManager.stop ⭐⭐

**位置与等级**：[execution.py:665](../../../src/workflow/execution.py#L665)；局部辅助逻辑，需理解其调用条件与失败传播。

**签名**：`async def stop(self) -> None`。

**作用**：处理 `stop` 对应步骤；下列步骤依据函数体的实际控制流和调用点整理。

**输入与输出**：
- 输入：无业务参数（或仅隐式接收实例）。
- 输出类型：`None`；具体返回路径见流程步骤。

**处理流程**：
1. 更新 `self.stopping`，值来自 `True`。
2. 捕获 无显式捕获；另检查 finally/else 的清理和传播。

**关键条件与保护**：
- [execution.py:668](../../../src/workflow/execution.py#L668)：`self.worker and (not self.worker.done())`，不满足时跳过本分支。

**调用与被调用**：
- `self.worker.done`（[execution.py:668](../../../src/workflow/execution.py#L668)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `asyncio.wait_for`（[execution.py:670](../../../src/workflow/execution.py#L670)）：来自 `asyncio`；具体实现可能由依赖注入或运行时分派决定。
- `asyncio.shield`（[execution.py:670](../../../src/workflow/execution.py#L670)）：来自 `asyncio`；具体实现可能由依赖注入或运行时分派决定。
- `self.worker.cancel`（[execution.py:672](../../../src/workflow/execution.py#L672)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `suppress`（[execution.py:673](../../../src/workflow/execution.py#L673)）：来自 `contextlib.suppress`；具体实现可能由依赖注入或运行时分派决定。
- `self.owner.release`（[execution.py:676](../../../src/workflow/execution.py#L676)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- 静态可定位的调用方：[ExecutionManager.run_wait](execution.md)。

**状态、副作用与异常**：
- 显式状态/容器赋值：`self.stopping`、`self.persistent`。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：未见 `raise`；下游异常可能继续上抛。
- 本地捕获：`TimeoutError`。
- 恢复/幂等性：仅在代码有检查点、事务、请求编号或显式去重时才成立；此函数不能单凭名称视为可安全重试。


---
