源码：[runs.py:1](../../../src/persistence/runs.py#L1) | 基准：`dev/v0.10@f2f34d7` | 本文件符号数：11

**模块职责**：User-facing serialized workflow summaries.
**在系统中的位置**：图、证据、运行、审计、审核与案例的持久化；JSON/Neo4j 提供同一存储协议。
**直接依赖**：[src.domain](../domain/__init__.md)；外部/标准库：`__future__`、`filelock`、`orjson`、`os`、`pathlib`、`urllib`、`uuid`。
**主要调用方（静态导入）**：[persistence/__init__.py](__init__.md)、[workflow/graph.py](../workflow/graph.md)。
**阅读提示**：下列流程根据当前源码控制流整理；`self`/接口对象的实际类型可能在运行时注入，未能静态解析的调用会明确标注。链接指向源码行或对应讲解文件。

---

# RunRepository ⭐⭐⭐⭐

**位置与等级**：[runs.py:16](../../../src/persistence/runs.py#L16)；承担主要 Agent、应用服务或审核/执行入口，跨模块影响显著。

**职责**：存储接口或实现；方法决定数据读取、持久化与并发边界。基类：无显式基类。

**字段与类级约束**：
- 类体未直接声明字段；实例状态请看 `__init__` 及方法中的赋值。

**内部成员**：`RunRepository.__init__`、`RunRepository._target`、`RunRepository._legacy_target`、`RunRepository.exists`、`RunRepository.save`、`RunRepository.mutation_lock`、`RunRepository.creation_lock`、`RunRepository.load`、`RunRepository.list`、`RunRepository.find_review`


---

# RunRepository.__init__ ⭐⭐⭐⭐

**位置与等级**：[runs.py:17](../../../src/persistence/runs.py#L17)；承担主要 Agent、应用服务或审核/执行入口，跨模块影响显著。

**签名**：`def __init__(self, directory: Path) -> None`。

**作用**：初始化对象并保存依赖或配置；需检查是否创建持久化资源。

**输入与输出**：
- 输入：`directory`（Path）。
- 输出类型：`None`；具体返回路径见流程步骤。

**处理流程**：
1. 更新 `self.directory`，值来自 `directory`。
2. 调用 `self.directory.mkdir`，结果未直接赋值。

**调用与被调用**：
- `self.directory.mkdir`（[runs.py:19](../../../src/persistence/runs.py#L19)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- 静态扫描未定位直接调用方；可能通过路由注册、LangGraph 节点、协议方法或依赖注入动态调用，不据此判断为死代码。

**状态、副作用与异常**：
- 显式状态/容器赋值：`self.directory`。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：未见 `raise`；下游异常可能继续上抛。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。
- 恢复/幂等性：仅在代码有检查点、事务、请求编号或显式去重时才成立；此函数不能单凭名称视为可安全重试。


---

# RunRepository._target ⭐⭐

**位置与等级**：[runs.py:21](../../../src/persistence/runs.py#L21)；局部辅助逻辑，需理解其调用条件与失败传播。

**签名**：`def _target(self, run_id: str) -> Path`。

**作用**：内部辅助步骤；将参数转换为本模块所需的中间对象或操作结果。

**输入与输出**：
- 输入：`run_id`（str；目标运行的稳定标识）。
- 输出类型：`Path`；具体返回路径见流程步骤。

**处理流程**：
1. 返回 `self.directory / f<字符串常量><字符串常量>`。

**调用与被调用**：
- `quote`（[runs.py:22](../../../src/persistence/runs.py#L22)）：来自 `urllib.parse.quote`；具体实现可能由依赖注入或运行时分派决定。
- 静态可定位的调用方：[RunRepository.exists](runs.md)、[RunRepository.save](runs.md)、[RunRepository.mutation_lock](runs.md)、[RunRepository.creation_lock](runs.md)、[RunRepository.load](runs.md)。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：未见 `raise`；下游异常可能继续上抛。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。
- 恢复/幂等性：仅在代码有检查点、事务、请求编号或显式去重时才成立；此函数不能单凭名称视为可安全重试。


---

# RunRepository._legacy_target ⭐⭐

**位置与等级**：[runs.py:24](../../../src/persistence/runs.py#L24)；局部辅助逻辑，需理解其调用条件与失败传播。

**签名**：`def _legacy_target(self, run_id: str) -> Path`。

**作用**：内部辅助步骤；将参数转换为本模块所需的中间对象或操作结果。

**输入与输出**：
- 输入：`run_id`（str；目标运行的稳定标识）。
- 输出类型：`Path`；具体返回路径见流程步骤。

**处理流程**：
1. 返回 `self.directory / f<字符串常量>`。

**调用与被调用**：
- 无显式函数调用，或仅声明协议/常量。
- 静态可定位的调用方：[RunRepository.exists](runs.md)、[RunRepository.load](runs.md)。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：未见 `raise`；下游异常可能继续上抛。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。
- 恢复/幂等性：仅在代码有检查点、事务、请求编号或显式去重时才成立；此函数不能单凭名称视为可安全重试。


---

# RunRepository.exists ⭐⭐⭐⭐

**位置与等级**：[runs.py:27](../../../src/persistence/runs.py#L27)；承担主要 Agent、应用服务或审核/执行入口，跨模块影响显著。

**签名**：`def exists(self, run_id: str) -> bool`。

**作用**：处理 `exists` 对应步骤；下列步骤依据函数体的实际控制流和调用点整理。

**输入与输出**：
- 输入：`run_id`（str；目标运行的稳定标识）。
- 输出类型：`bool`；具体返回路径见流程步骤。

**处理流程**：
1. 返回 `self._target(run_id).is_file() or self._legacy_target(run_id).is_file()`。

**调用与被调用**：
- `self._target(run_id).is_file`（[runs.py:28](../../../src/persistence/runs.py#L28)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `self._target`（调用点 [runs.py:28](../../../src/persistence/runs.py#L28)）→ [RunRepository._target](runs.md)，静态可定位。
- `self._legacy_target(run_id).is_file`（[runs.py:28](../../../src/persistence/runs.py#L28)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `self._legacy_target`（调用点 [runs.py:28](../../../src/persistence/runs.py#L28)）→ [RunRepository._legacy_target](runs.md)，静态可定位。
- 静态扫描未定位直接调用方；可能通过路由注册、LangGraph 节点、协议方法或依赖注入动态调用，不据此判断为死代码。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：未见 `raise`；下游异常可能继续上抛。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。
- 恢复/幂等性：仅在代码有检查点、事务、请求编号或显式去重时才成立；此函数不能单凭名称视为可安全重试。


---

# RunRepository.save ⭐⭐⭐⭐

**位置与等级**：[runs.py:30](../../../src/persistence/runs.py#L30)；承担主要 Agent、应用服务或审核/执行入口，跨模块影响显著。

**签名**：`def save(self, state: WorkflowState) -> Path`。

**作用**：处理 `save` 对应步骤；下列步骤依据函数体的实际控制流和调用点整理。

**输入与输出**：
- 输入：`state`（WorkflowState；跨节点 WorkflowState；调用方须保持证据与状态一致）。
- 输出类型：`Path`；具体返回路径见流程步骤。

**处理流程**：
1. 更新 `target`，值来自 `self._target(state.run_id)`。
2. 更新 `temporary`，值来自 `target.with_name(f<字符串常量>)`。
3. 捕获 无显式捕获；另检查 finally/else 的清理和传播。
4. 返回 `target`。

**调用与被调用**：
- `self._target`（调用点 [runs.py:31](../../../src/persistence/runs.py#L31)）→ [RunRepository._target](runs.md)，静态可定位。
- `target.with_name`（[runs.py:32](../../../src/persistence/runs.py#L32)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `uuid4`（[runs.py:32](../../../src/persistence/runs.py#L32)）：来自 `uuid.uuid4`；具体实现可能由依赖注入或运行时分派决定。
- `temporary.open`（[runs.py:34](../../../src/persistence/runs.py#L34)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `stream.write`（[runs.py:35](../../../src/persistence/runs.py#L35)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `orjson.dumps`（[runs.py:36](../../../src/persistence/runs.py#L36)）：来自 `orjson`；具体实现可能由依赖注入或运行时分派决定。
- `state.model_dump`（[runs.py:36](../../../src/persistence/runs.py#L36)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `stream.flush`（[runs.py:38](../../../src/persistence/runs.py#L38)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `os.fsync`（[runs.py:39](../../../src/persistence/runs.py#L39)）：来自 `os`；具体实现可能由依赖注入或运行时分派决定。
- `stream.fileno`（[runs.py:39](../../../src/persistence/runs.py#L39)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `os.replace`（[runs.py:40](../../../src/persistence/runs.py#L40)）：来自 `os`；具体实现可能由依赖注入或运行时分派决定。
- `temporary.unlink`（[runs.py:42](../../../src/persistence/runs.py#L42)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- 静态扫描未定位直接调用方；可能通过路由注册、LangGraph 节点、协议方法或依赖注入动态调用，不据此判断为死代码。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：未见 `raise`；下游异常可能继续上抛。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。
- 恢复/幂等性：仅在代码有检查点、事务、请求编号或显式去重时才成立；此函数不能单凭名称视为可安全重试。


---

# RunRepository.mutation_lock ⭐⭐⭐⭐

**位置与等级**：[runs.py:45](../../../src/persistence/runs.py#L45)；承担主要 Agent、应用服务或审核/执行入口，跨模块影响显著。

**签名**：`def mutation_lock(self, run_id: str) -> FileLock`。

**作用**：处理 `mutation_lock` 对应步骤；下列步骤依据函数体的实际控制流和调用点整理。

**输入与输出**：
- 输入：`run_id`（str；目标运行的稳定标识）。
- 输出类型：`FileLock`；具体返回路径见流程步骤。

**处理流程**：
1. 返回 `FileLock(str(self._target(run_id).with_suffix('.lock')), timeout=0)`。

**调用与被调用**：
- `FileLock`（[runs.py:46](../../../src/persistence/runs.py#L46)）：来自 `filelock.FileLock`；具体实现可能由依赖注入或运行时分派决定。
- `str`（[runs.py:46](../../../src/persistence/runs.py#L46)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `self._target(run_id).with_suffix`（[runs.py:46](../../../src/persistence/runs.py#L46)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `self._target`（调用点 [runs.py:46](../../../src/persistence/runs.py#L46)）→ [RunRepository._target](runs.md)，静态可定位。
- 静态扫描未定位直接调用方；可能通过路由注册、LangGraph 节点、协议方法或依赖注入动态调用，不据此判断为死代码。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：未见 `raise`；下游异常可能继续上抛。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。
- 恢复/幂等性：仅在代码有检查点、事务、请求编号或显式去重时才成立；此函数不能单凭名称视为可安全重试。


---

# RunRepository.creation_lock ⭐⭐⭐⭐

**位置与等级**：[runs.py:48](../../../src/persistence/runs.py#L48)；承担主要 Agent、应用服务或审核/执行入口，跨模块影响显著。

**签名**：`def creation_lock(self, run_id: str) -> FileLock`。

**作用**：处理 `creation_lock` 对应步骤；下列步骤依据函数体的实际控制流和调用点整理。

**输入与输出**：
- 输入：`run_id`（str；目标运行的稳定标识）。
- 输出类型：`FileLock`；具体返回路径见流程步骤。

**处理流程**：
1. 返回 `FileLock(str(self._target(run_id).with_suffix('.creation.lock')), timeout=30)`。

**调用与被调用**：
- `FileLock`（[runs.py:49](../../../src/persistence/runs.py#L49)）：来自 `filelock.FileLock`；具体实现可能由依赖注入或运行时分派决定。
- `str`（[runs.py:49](../../../src/persistence/runs.py#L49)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `self._target(run_id).with_suffix`（[runs.py:49](../../../src/persistence/runs.py#L49)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `self._target`（调用点 [runs.py:49](../../../src/persistence/runs.py#L49)）→ [RunRepository._target](runs.md)，静态可定位。
- 静态扫描未定位直接调用方；可能通过路由注册、LangGraph 节点、协议方法或依赖注入动态调用，不据此判断为死代码。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：未见 `raise`；下游异常可能继续上抛。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。
- 恢复/幂等性：仅在代码有检查点、事务、请求编号或显式去重时才成立；此函数不能单凭名称视为可安全重试。


---

# RunRepository.load ⭐⭐⭐⭐

**位置与等级**：[runs.py:51](../../../src/persistence/runs.py#L51)；承担主要 Agent、应用服务或审核/执行入口，跨模块影响显著。

**签名**：`def load(self, run_id: str) -> WorkflowState`。

**作用**：处理 `load` 对应步骤；下列步骤依据函数体的实际控制流和调用点整理。

**输入与输出**：
- 输入：`run_id`（str；目标运行的稳定标识）。
- 输出类型：`WorkflowState`；具体返回路径见流程步骤。

**处理流程**：
1. 更新 `target`，值来自 `self._target(run_id)`。
2. 检查 `not target.is_file() and self._legacy_target(run_id).is_file()`；按条件分流，else 分支不存在。
3. 返回 `WorkflowState.model_validate(orjson.loads(target.read_bytes()))`。

**关键条件与保护**：
- [runs.py:53](../../../src/persistence/runs.py#L53)：`not target.is_file() and self._legacy_target(run_id).is_file()`，不满足时跳过本分支。

**调用与被调用**：
- `self._target`（调用点 [runs.py:52](../../../src/persistence/runs.py#L52)）→ [RunRepository._target](runs.md)，静态可定位。
- `target.is_file`（[runs.py:53](../../../src/persistence/runs.py#L53)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `self._legacy_target(run_id).is_file`（[runs.py:53](../../../src/persistence/runs.py#L53)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `self._legacy_target`（调用点 [runs.py:53](../../../src/persistence/runs.py#L53)）→ [RunRepository._legacy_target](runs.md)，静态可定位。
- `WorkflowState.model_validate`（[runs.py:55](../../../src/persistence/runs.py#L55)）：来自 `src.domain.WorkflowState`；具体实现可能由依赖注入或运行时分派决定。
- `orjson.loads`（[runs.py:55](../../../src/persistence/runs.py#L55)）：来自 `orjson`；具体实现可能由依赖注入或运行时分派决定。
- `target.read_bytes`（[runs.py:55](../../../src/persistence/runs.py#L55)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- 静态扫描未定位直接调用方；可能通过路由注册、LangGraph 节点、协议方法或依赖注入动态调用，不据此判断为死代码。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：未见 `raise`；下游异常可能继续上抛。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。
- 恢复/幂等性：仅在代码有检查点、事务、请求编号或显式去重时才成立；此函数不能单凭名称视为可安全重试。


---

# RunRepository.list ⭐⭐⭐⭐

**位置与等级**：[runs.py:57](../../../src/persistence/runs.py#L57)；承担主要 Agent、应用服务或审核/执行入口，跨模块影响显著。

**签名**：`def list(self, limit: int=100) -> list[WorkflowState]`。

**作用**：处理 `list` 对应步骤；下列步骤依据函数体的实际控制流和调用点整理。

**输入与输出**：
- 输入：`limit`（int；默认 `100`；查询或展示的最大条数）。
- 输出类型：`list[WorkflowState]`；具体返回路径见流程步骤。

**处理流程**：
1. 更新 `paths`，值来自 `sorted(self.directory.glob(<字符串常量>), key=lambda item: item.stat().st_mtime, reverse=True)`。
2. 更新 `states`，值来自 `[]`。
3. 遍历 `paths[:max(limit, 0)]`，逐项处理 `path`。
4. 返回 `states`。

**调用与被调用**：
- `sorted`（[runs.py:58](../../../src/persistence/runs.py#L58)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `self.directory.glob`（[runs.py:59](../../../src/persistence/runs.py#L59)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `max`（[runs.py:62](../../../src/persistence/runs.py#L62)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `states.append`（[runs.py:63](../../../src/persistence/runs.py#L63)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `WorkflowState.model_validate`（[runs.py:63](../../../src/persistence/runs.py#L63)）：来自 `src.domain.WorkflowState`；具体实现可能由依赖注入或运行时分派决定。
- `orjson.loads`（[runs.py:63](../../../src/persistence/runs.py#L63)）：来自 `orjson`；具体实现可能由依赖注入或运行时分派决定。
- `path.read_bytes`（[runs.py:63](../../../src/persistence/runs.py#L63)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- 静态可定位的调用方：[RunRepository.find_review](runs.md)。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：未见 `raise`；下游异常可能继续上抛。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。
- 恢复/幂等性：仅在代码有检查点、事务、请求编号或显式去重时才成立；此函数不能单凭名称视为可安全重试。


---

# RunRepository.find_review ⭐⭐⭐⭐

**位置与等级**：[runs.py:66](../../../src/persistence/runs.py#L66)；承担主要 Agent、应用服务或审核/执行入口，跨模块影响显著。

**签名**：`def find_review(self, task_id: str) -> tuple[WorkflowState, str]`。

**作用**：处理 `find_review` 对应步骤；下列步骤依据函数体的实际控制流和调用点整理。

**输入与输出**：
- 输入：`task_id`（str；待处理审核任务标识）。
- 输出类型：`tuple[WorkflowState, str]`；具体返回路径见流程步骤。

**处理流程**：
1. 遍历 `self.list()`，逐项处理 `state`。
2. 抛出 `KeyError(f<字符串常量>)`。

**关键条件与保护**：
- [runs.py:69](../../../src/persistence/runs.py#L69)：`task is not None`，不满足时跳过本分支。

**调用与被调用**：
- `self.list`（调用点 [runs.py:67](../../../src/persistence/runs.py#L67)）→ [RunRepository.list](runs.md)，静态可定位。
- `next`（[runs.py:68](../../../src/persistence/runs.py#L68)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `KeyError`（[runs.py:71](../../../src/persistence/runs.py#L71)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- 静态扫描未定位直接调用方；可能通过路由注册、LangGraph 节点、协议方法或依赖注入动态调用，不据此判断为死代码。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：`KeyError(f<字符串常量>)`。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。
- 恢复/幂等性：仅在代码有检查点、事务、请求编号或显式去重时才成立；此函数不能单凭名称视为可安全重试。


---
