源码：[reviews.py:1](../../../src/persistence/reviews.py#L1) | 基准：`dev/v0.10@f2f34d7` | 本文件符号数：14

**模块职责**：Authoritative review events and transactional projection outbox.
**在系统中的位置**：图、证据、运行、审计、审核与案例的持久化；JSON/Neo4j 提供同一存储协议。
**直接依赖**：[src.core.ids](../core/ids.md)、[src.domain.reviews](../domain/reviews.md)；外部/标准库：`contextlib`、`orjson`、`pathlib`、`sqlite3`、`typing`。
**主要调用方（静态导入）**：[agents/fusion_review_agent.py](../agents/fusion_review_agent.md)、[workflow/corrections.py](../workflow/corrections.md)、[workflow/graph.py](../workflow/graph.md)、[workflow/nodes.py](../workflow/nodes.md)、[workflow/reviews.py](../workflow/reviews.md)。
**阅读提示**：下列流程根据当前源码控制流整理；`self`/接口对象的实际类型可能在运行时注入，未能静态解析的调用会明确标注。链接指向源码行或对应讲解文件。

---

# ReviewRepository ⭐⭐⭐⭐

**位置与等级**：[reviews.py:14](../../../src/persistence/reviews.py#L14)；承担主要 Agent、应用服务或审核/执行入口，跨模块影响显著。

**职责**：存储接口或实现；方法决定数据读取、持久化与并发边界。基类：无显式基类。

**字段与类级约束**：
- 类体未直接声明字段；实例状态请看 `__init__` 及方法中的赋值。

**内部成员**：`ReviewRepository.__init__`、`ReviewRepository.connect`、`ReviewRepository.archive`、`ReviewRepository.original`、`ReviewRepository.events`、`ReviewRepository.request`、`ReviewRepository.event_state`、`ReviewRepository.version`、`ReviewRepository.append`、`ReviewRepository.pending`、`ReviewRepository.delivered`、`ReviewRepository.propose`、`ReviewRepository.correction`


---

# ReviewRepository.__init__ ⭐⭐⭐⭐

**位置与等级**：[reviews.py:15](../../../src/persistence/reviews.py#L15)；承担主要 Agent、应用服务或审核/执行入口，跨模块影响显著。

**签名**：`def __init__(self, path: Path) -> None`。

**作用**：初始化对象并保存依赖或配置；需检查是否创建持久化资源。

**输入与输出**：
- 输入：`path`（Path）。
- 输出类型：`None`；具体返回路径见流程步骤。

**处理流程**：
1. 更新 `self.path`，值来自 `path`。
2. 调用 `path.parent.mkdir`，结果未直接赋值。
3. 进入上下文 `closing(self.connect()), c`，由上下文管理器控制资源释放或事务范围。

**调用与被调用**：
- `path.parent.mkdir`（[reviews.py:17](../../../src/persistence/reviews.py#L17)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `closing`（[reviews.py:18](../../../src/persistence/reviews.py#L18)）：来自 `contextlib.closing`；具体实现可能由依赖注入或运行时分派决定。
- `self.connect`（调用点 [reviews.py:18](../../../src/persistence/reviews.py#L18)）→ [ReviewRepository.connect](reviews.md)，静态可定位。
- `c.executescript`（[reviews.py:19](../../../src/persistence/reviews.py#L19)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- 静态扫描未定位直接调用方；可能通过路由注册、LangGraph 节点、协议方法或依赖注入动态调用，不据此判断为死代码。

**状态、副作用与异常**：
- 显式状态/容器赋值：`self.path`。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：未见 `raise`；下游异常可能继续上抛。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。
- 恢复/幂等性：仅在代码有检查点、事务、请求编号或显式去重时才成立；此函数不能单凭名称视为可安全重试。


---

# ReviewRepository.connect ⭐⭐⭐⭐

**位置与等级**：[reviews.py:47](../../../src/persistence/reviews.py#L47)；承担主要 Agent、应用服务或审核/执行入口，跨模块影响显著。

**签名**：`def connect(self) -> sqlite3.Connection`。

**作用**：处理 `connect` 对应步骤；下列步骤依据函数体的实际控制流和调用点整理。

**输入与输出**：
- 输入：无业务参数（或仅隐式接收实例）。
- 输出类型：`sqlite3.Connection`；具体返回路径见流程步骤。

**处理流程**：
1. 更新 `c`，值来自 `sqlite3.connect(self.path, timeout=10)`。
2. 调用 `c.execute`，结果未直接赋值。
3. 返回 `c`。

**调用与被调用**：
- `sqlite3.connect`（[reviews.py:48](../../../src/persistence/reviews.py#L48)）：来自 `sqlite3`；具体实现可能由依赖注入或运行时分派决定。
- `c.execute`（[reviews.py:49](../../../src/persistence/reviews.py#L49)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- 静态可定位的调用方：[ReviewRepository.__init__](reviews.md)、[ReviewRepository.archive](reviews.md)、[ReviewRepository.original](reviews.md)、[ReviewRepository.events](reviews.md)、[ReviewRepository.request](reviews.md)、[ReviewRepository.event_state](reviews.md)、[ReviewRepository.version](reviews.md)、[ReviewRepository.append](reviews.md)、[ReviewRepository.pending](reviews.md)、[ReviewRepository.delivered](reviews.md)。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：未见 `raise`；下游异常可能继续上抛。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。
- 恢复/幂等性：仅在代码有检查点、事务、请求编号或显式去重时才成立；此函数不能单凭名称视为可安全重试。


---

# ReviewRepository.archive ⭐⭐⭐⭐

**位置与等级**：[reviews.py:52](../../../src/persistence/reviews.py#L52)；承担主要 Agent、应用服务或审核/执行入口，跨模块影响显著。

**签名**：`def archive(self, run_id: str, candidates: list[dict[str, Any]]) -> None`。

**作用**：处理 `archive` 对应步骤；下列步骤依据函数体的实际控制流和调用点整理。

**输入与输出**：
- 输入：`run_id`（str；目标运行的稳定标识）；`candidates`（list[dict[str, Any]]；待逐项检查/治理的候选集合）。
- 输出类型：`None`；具体返回路径见流程步骤。

**处理流程**：
1. 更新 `payload`，值来自 `orjson.dumps(candidates, option=orjson.OPT_SORT_KEYS)`。
2. 进入上下文 `closing(self.connect()), c`，由上下文管理器控制资源释放或事务范围。

**关键条件与保护**：
- [reviews.py:56](../../../src/persistence/reviews.py#L56)：`row and row[0] != payload`，不满足时跳过本分支。

**调用与被调用**：
- `orjson.dumps`（[reviews.py:53](../../../src/persistence/reviews.py#L53)）：来自 `orjson`；具体实现可能由依赖注入或运行时分派决定。
- `closing`（[reviews.py:54](../../../src/persistence/reviews.py#L54)）：来自 `contextlib.closing`；具体实现可能由依赖注入或运行时分派决定。
- `self.connect`（调用点 [reviews.py:54](../../../src/persistence/reviews.py#L54)）→ [ReviewRepository.connect](reviews.md)，静态可定位。
- `c.execute(<字符串常量>, (run_id,)).fetchone`（[reviews.py:55](../../../src/persistence/reviews.py#L55)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `c.execute`（[reviews.py:55](../../../src/persistence/reviews.py#L55)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `ValueError`（[reviews.py:57](../../../src/persistence/reviews.py#L57)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- 静态扫描未定位直接调用方；可能通过路由注册、LangGraph 节点、协议方法或依赖注入动态调用，不据此判断为死代码。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：`ValueError(<字符串常量>)`。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。
- 恢复/幂等性：仅在代码有检查点、事务、请求编号或显式去重时才成立；此函数不能单凭名称视为可安全重试。


---

# ReviewRepository.original ⭐⭐⭐⭐

**位置与等级**：[reviews.py:60](../../../src/persistence/reviews.py#L60)；承担主要 Agent、应用服务或审核/执行入口，跨模块影响显著。

**签名**：`def original(self, run_id: str) -> list[dict[str, Any]]`。

**作用**：处理 `original` 对应步骤；下列步骤依据函数体的实际控制流和调用点整理。

**输入与输出**：
- 输入：`run_id`（str；目标运行的稳定标识）。
- 输出类型：`list[dict[str, Any]]`；具体返回路径见流程步骤。

**处理流程**：
1. 进入上下文 `closing(self.connect())`，由上下文管理器控制资源释放或事务范围。
2. 检查 `not row`；按条件分流，else 分支不存在。
3. 返回 `orjson.loads(row[0])`。

**关键条件与保护**：
- [reviews.py:63](../../../src/persistence/reviews.py#L63)：`not row`，不满足时跳过本分支。

**调用与被调用**：
- `closing`（[reviews.py:61](../../../src/persistence/reviews.py#L61)）：来自 `contextlib.closing`；具体实现可能由依赖注入或运行时分派决定。
- `self.connect`（调用点 [reviews.py:61](../../../src/persistence/reviews.py#L61)）→ [ReviewRepository.connect](reviews.md)，静态可定位。
- `c.execute(<字符串常量>, (run_id,)).fetchone`（[reviews.py:62](../../../src/persistence/reviews.py#L62)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `c.execute`（[reviews.py:62](../../../src/persistence/reviews.py#L62)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `ValueError`（[reviews.py:64](../../../src/persistence/reviews.py#L64)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `orjson.loads`（[reviews.py:67](../../../src/persistence/reviews.py#L67)）：来自 `orjson`；具体实现可能由依赖注入或运行时分派决定。
- 静态扫描未定位直接调用方；可能通过路由注册、LangGraph 节点、协议方法或依赖注入动态调用，不据此判断为死代码。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：`ValueError(<字符串常量>)`。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。
- 恢复/幂等性：仅在代码有检查点、事务、请求编号或显式去重时才成立；此函数不能单凭名称视为可安全重试。


---

# ReviewRepository.events ⭐⭐⭐⭐

**位置与等级**：[reviews.py:69](../../../src/persistence/reviews.py#L69)；承担主要 Agent、应用服务或审核/执行入口，跨模块影响显著。

**签名**：`def events(self, run_id: str) -> list[ReviewEvent]`。

**作用**：处理 `events` 对应步骤；下列步骤依据函数体的实际控制流和调用点整理。

**输入与输出**：
- 输入：`run_id`（str；目标运行的稳定标识）。
- 输出类型：`list[ReviewEvent]`；具体返回路径见流程步骤。

**处理流程**：
1. 进入上下文 `closing(self.connect())`，由上下文管理器控制资源释放或事务范围。

**调用与被调用**：
- `closing`（[reviews.py:70](../../../src/persistence/reviews.py#L70)）：来自 `contextlib.closing`；具体实现可能由依赖注入或运行时分派决定。
- `self.connect`（调用点 [reviews.py:70](../../../src/persistence/reviews.py#L70)）→ [ReviewRepository.connect](reviews.md)，静态可定位。
- `c.execute`（[reviews.py:71](../../../src/persistence/reviews.py#L71)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `ReviewEvent.model_validate_json`（[reviews.py:72](../../../src/persistence/reviews.py#L72)）：来自 `src.domain.reviews.ReviewEvent`；具体实现可能由依赖注入或运行时分派决定。
- 静态扫描未定位直接调用方；可能通过路由注册、LangGraph 节点、协议方法或依赖注入动态调用，不据此判断为死代码。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：未见 `raise`；下游异常可能继续上抛。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。
- 恢复/幂等性：仅在代码有检查点、事务、请求编号或显式去重时才成立；此函数不能单凭名称视为可安全重试。


---

# ReviewRepository.request ⭐⭐⭐⭐

**位置与等级**：[reviews.py:74](../../../src/persistence/reviews.py#L74)；承担主要 Agent、应用服务或审核/执行入口，跨模块影响显著。

**签名**：`def request(self, run_id: str, request_id: str) -> ReviewEvent | None`。

**作用**：处理 `request` 对应步骤；下列步骤依据函数体的实际控制流和调用点整理。

**输入与输出**：
- 输入：`run_id`（str；目标运行的稳定标识）；`request_id`（str；幂等请求标识，避免重复动作）。
- 输出类型：`ReviewEvent | None`；具体返回路径见流程步骤。

**处理流程**：
1. 进入上下文 `closing(self.connect())`，由上下文管理器控制资源释放或事务范围。
2. 返回 `ReviewEvent.model_validate_json(row[0]) if row else None`。

**调用与被调用**：
- `closing`（[reviews.py:75](../../../src/persistence/reviews.py#L75)）：来自 `contextlib.closing`；具体实现可能由依赖注入或运行时分派决定。
- `self.connect`（调用点 [reviews.py:75](../../../src/persistence/reviews.py#L75)）→ [ReviewRepository.connect](reviews.md)，静态可定位。
- `c.execute(<字符串常量>, (run_id, request_id)).fetchone`（[reviews.py:76](../../../src/persistence/reviews.py#L76)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `c.execute`（[reviews.py:76](../../../src/persistence/reviews.py#L76)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `ReviewEvent.model_validate_json`（[reviews.py:79](../../../src/persistence/reviews.py#L79)）：来自 `src.domain.reviews.ReviewEvent`；具体实现可能由依赖注入或运行时分派决定。
- 静态扫描未定位直接调用方；可能通过路由注册、LangGraph 节点、协议方法或依赖注入动态调用，不据此判断为死代码。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：未见 `raise`；下游异常可能继续上抛。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。
- 恢复/幂等性：仅在代码有检查点、事务、请求编号或显式去重时才成立；此函数不能单凭名称视为可安全重试。


---

# ReviewRepository.event_state ⭐⭐⭐⭐

**位置与等级**：[reviews.py:81](../../../src/persistence/reviews.py#L81)；承担主要 Agent、应用服务或审核/执行入口，跨模块影响显著。

**签名**：`def event_state(self, event_id: str) -> dict[str, Any]`。

**作用**：处理 `event_state` 对应步骤；下列步骤依据函数体的实际控制流和调用点整理。

**输入与输出**：
- 输入：`event_id`（str）。
- 输出类型：`dict[str, Any]`；具体返回路径见流程步骤。

**处理流程**：
1. 进入上下文 `closing(self.connect())`，由上下文管理器控制资源释放或事务范围。
2. 检查 `row is None`；按条件分流，else 分支不存在。
3. 返回 `orjson.loads(row[0])`。

**关键条件与保护**：
- [reviews.py:84](../../../src/persistence/reviews.py#L84)：`row is None`，不满足时跳过本分支。

**调用与被调用**：
- `closing`（[reviews.py:82](../../../src/persistence/reviews.py#L82)）：来自 `contextlib.closing`；具体实现可能由依赖注入或运行时分派决定。
- `self.connect`（调用点 [reviews.py:82](../../../src/persistence/reviews.py#L82)）→ [ReviewRepository.connect](reviews.md)，静态可定位。
- `c.execute(<字符串常量>, (event_id,)).fetchone`（[reviews.py:83](../../../src/persistence/reviews.py#L83)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `c.execute`（[reviews.py:83](../../../src/persistence/reviews.py#L83)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `KeyError`（[reviews.py:85](../../../src/persistence/reviews.py#L85)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `orjson.loads`（[reviews.py:86](../../../src/persistence/reviews.py#L86)）：来自 `orjson`；具体实现可能由依赖注入或运行时分派决定。
- 静态扫描未定位直接调用方；可能通过路由注册、LangGraph 节点、协议方法或依赖注入动态调用，不据此判断为死代码。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：`KeyError(<字符串常量>)`。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。
- 恢复/幂等性：仅在代码有检查点、事务、请求编号或显式去重时才成立；此函数不能单凭名称视为可安全重试。


---

# ReviewRepository.version ⭐⭐⭐⭐

**位置与等级**：[reviews.py:88](../../../src/persistence/reviews.py#L88)；承担主要 Agent、应用服务或审核/执行入口，跨模块影响显著。

**签名**：`def version(self, run_id: str, task_id: str) -> int`。

**作用**：处理 `version` 对应步骤；下列步骤依据函数体的实际控制流和调用点整理。

**输入与输出**：
- 输入：`run_id`（str；目标运行的稳定标识）；`task_id`（str；待处理审核任务标识）。
- 输出类型：`int`；具体返回路径见流程步骤。

**处理流程**：
1. 进入上下文 `closing(self.connect())`，由上下文管理器控制资源释放或事务范围。
2. 返回 `row[0] if row else 0`。

**调用与被调用**：
- `closing`（[reviews.py:89](../../../src/persistence/reviews.py#L89)）：来自 `contextlib.closing`；具体实现可能由依赖注入或运行时分派决定。
- `self.connect`（调用点 [reviews.py:89](../../../src/persistence/reviews.py#L89)）→ [ReviewRepository.connect](reviews.md)，静态可定位。
- `c.execute(<字符串常量>, (run_id, task_id)).fetchone`（[reviews.py:90](../../../src/persistence/reviews.py#L90)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `c.execute`（[reviews.py:90](../../../src/persistence/reviews.py#L90)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- 静态扫描未定位直接调用方；可能通过路由注册、LangGraph 节点、协议方法或依赖注入动态调用，不据此判断为死代码。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：未见 `raise`；下游异常可能继续上抛。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。
- 恢复/幂等性：仅在代码有检查点、事务、请求编号或显式去重时才成立；此函数不能单凭名称视为可安全重试。


---

# ReviewRepository.append ⭐⭐⭐⭐

**位置与等级**：[reviews.py:95](../../../src/persistence/reviews.py#L95)；承担主要 Agent、应用服务或审核/执行入口，跨模块影响显著。

**签名**：`def append(self, event: ReviewEvent, state: dict[str, Any], expected_version: int) -> None`。

**作用**：处理 `append` 对应步骤；下列步骤依据函数体的实际控制流和调用点整理。

**输入与输出**：
- 输入：`event`（ReviewEvent）；`state`（dict[str, Any]；跨节点 WorkflowState；调用方须保持证据与状态一致）；`expected_version`（int；乐观并发版本；过期提交应拒绝）。
- 输出类型：`None`；具体返回路径见流程步骤。

**处理流程**：
1. 进入上下文 `closing(self.connect()), c`，由上下文管理器控制资源释放或事务范围。

**关键条件与保护**：
- [reviews.py:98](../../../src/persistence/reviews.py#L98)：`c.execute(<字符串常量>, (event.run_id,)).fetchone()`，不满足时跳过本分支。
- [reviews.py:109](../../../src/persistence/reviews.py#L109)：`actual != expected_version or event.version != expected_version + 1`，不满足时跳过本分支。

**调用与被调用**：
- `closing`（[reviews.py:96](../../../src/persistence/reviews.py#L96)）：来自 `contextlib.closing`；具体实现可能由依赖注入或运行时分派决定。
- `self.connect`（调用点 [reviews.py:96](../../../src/persistence/reviews.py#L96)）→ [ReviewRepository.connect](reviews.md)，静态可定位。
- `c.execute`（[reviews.py:97](../../../src/persistence/reviews.py#L97)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `c.execute(<字符串常量>, (event.run_id,)).fetchone`（[reviews.py:98](../../../src/persistence/reviews.py#L98)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `ValueError`（[reviews.py:103](../../../src/persistence/reviews.py#L103)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `c.execute(<字符串常量>, (event.run_id, event.task_id)).fetchone`（[reviews.py:104](../../../src/persistence/reviews.py#L104)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `event.model_dump_json`（[reviews.py:118](../../../src/persistence/reviews.py#L118)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `orjson.dumps`（[reviews.py:119](../../../src/persistence/reviews.py#L119)）：来自 `orjson`；具体实现可能由依赖注入或运行时分派决定。
- 静态扫描未定位直接调用方；可能通过路由注册、LangGraph 节点、协议方法或依赖注入动态调用，不据此判断为死代码。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：`ValueError(<字符串常量>)`。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。
- 恢复/幂等性：仅在代码有检查点、事务、请求编号或显式去重时才成立；此函数不能单凭名称视为可安全重试。


---

# ReviewRepository.pending ⭐⭐⭐⭐

**位置与等级**：[reviews.py:128](../../../src/persistence/reviews.py#L128)；承担主要 Agent、应用服务或审核/执行入口，跨模块影响显著。

**签名**：`def pending(self, run_id: str | None=None) -> list[tuple[ReviewEvent, dict[str, Any]]]`。

**作用**：处理 `pending` 对应步骤；下列步骤依据函数体的实际控制流和调用点整理。

**输入与输出**：
- 输入：`run_id`（str | None；默认 `None`；目标运行的稳定标识）。
- 输出类型：`list[tuple[ReviewEvent, dict[str, Any]]]`；具体返回路径见流程步骤。

**处理流程**：
1. 进入上下文 `closing(self.connect())`，由上下文管理器控制资源释放或事务范围。

**调用与被调用**：
- `closing`（[reviews.py:129](../../../src/persistence/reviews.py#L129)）：来自 `contextlib.closing`；具体实现可能由依赖注入或运行时分派决定。
- `self.connect`（调用点 [reviews.py:129](../../../src/persistence/reviews.py#L129)）→ [ReviewRepository.connect](reviews.md)，静态可定位。
- `c.execute`（[reviews.py:134](../../../src/persistence/reviews.py#L134)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `ReviewEvent.model_validate_json`（[reviews.py:135](../../../src/persistence/reviews.py#L135)）：来自 `src.domain.reviews.ReviewEvent`；具体实现可能由依赖注入或运行时分派决定。
- `orjson.loads`（[reviews.py:135](../../../src/persistence/reviews.py#L135)）：来自 `orjson`；具体实现可能由依赖注入或运行时分派决定。
- 静态扫描未定位直接调用方；可能通过路由注册、LangGraph 节点、协议方法或依赖注入动态调用，不据此判断为死代码。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：未见 `raise`；下游异常可能继续上抛。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。
- 恢复/幂等性：仅在代码有检查点、事务、请求编号或显式去重时才成立；此函数不能单凭名称视为可安全重试。


---

# ReviewRepository.delivered ⭐⭐⭐⭐

**位置与等级**：[reviews.py:137](../../../src/persistence/reviews.py#L137)；承担主要 Agent、应用服务或审核/执行入口，跨模块影响显著。

**签名**：`def delivered(self, event_id: str) -> None`。

**作用**：处理 `delivered` 对应步骤；下列步骤依据函数体的实际控制流和调用点整理。

**输入与输出**：
- 输入：`event_id`（str）。
- 输出类型：`None`；具体返回路径见流程步骤。

**处理流程**：
1. 进入上下文 `closing(self.connect()), c`，由上下文管理器控制资源释放或事务范围。

**调用与被调用**：
- `closing`（[reviews.py:138](../../../src/persistence/reviews.py#L138)）：来自 `contextlib.closing`；具体实现可能由依赖注入或运行时分派决定。
- `self.connect`（调用点 [reviews.py:138](../../../src/persistence/reviews.py#L138)）→ [ReviewRepository.connect](reviews.md)，静态可定位。
- `c.execute`（[reviews.py:139](../../../src/persistence/reviews.py#L139)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- 静态扫描未定位直接调用方；可能通过路由注册、LangGraph 节点、协议方法或依赖注入动态调用，不据此判断为死代码。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：未见 `raise`；下游异常可能继续上抛。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。
- 恢复/幂等性：仅在代码有检查点、事务、请求编号或显式去重时才成立；此函数不能单凭名称视为可安全重试。


---

# ReviewRepository.propose ⭐⭐⭐⭐

**位置与等级**：[reviews.py:141](../../../src/persistence/reviews.py#L141)；承担主要 Agent、应用服务或审核/执行入口，跨模块影响显著。

**签名**：`def propose(self, proposal: ReviewCorrection) -> None`。

**作用**：处理 `propose` 对应步骤；下列步骤依据函数体的实际控制流和调用点整理。

**输入与输出**：
- 输入：`proposal`（ReviewCorrection）。
- 输出类型：`None`；具体返回路径见流程步骤。

**处理流程**：
1. 进入上下文 `closing(self.connect()), c`，由上下文管理器控制资源释放或事务范围。

**关键条件与保护**：
- [reviews.py:144](../../../src/persistence/reviews.py#L144)：`row and canonical_hash(orjson.loads(row[0])) != canonical_hash(proposal.model_dump(mode='json'))`，不满足时跳过本分支。

**调用与被调用**：
- `closing`（[reviews.py:142](../../../src/persistence/reviews.py#L142)）：来自 `contextlib.closing`；具体实现可能由依赖注入或运行时分派决定。
- `self.connect`（调用点 [reviews.py:142](../../../src/persistence/reviews.py#L142)）→ [ReviewRepository.connect](reviews.md)，静态可定位。
- `c.execute(<字符串常量>, (proposal.id,)).fetchone`（[reviews.py:143](../../../src/persistence/reviews.py#L143)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `c.execute`（[reviews.py:143](../../../src/persistence/reviews.py#L143)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `canonical_hash`（调用点 [reviews.py:144](../../../src/persistence/reviews.py#L144)）→ [canonical_hash](../core/ids.md)，静态可定位。
- `orjson.loads`（[reviews.py:144](../../../src/persistence/reviews.py#L144)）：来自 `orjson`；具体实现可能由依赖注入或运行时分派决定。
- `proposal.model_dump`（[reviews.py:145](../../../src/persistence/reviews.py#L145)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `ValueError`（[reviews.py:147](../../../src/persistence/reviews.py#L147)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `proposal.model_dump_json`（[reviews.py:150](../../../src/persistence/reviews.py#L150)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- 静态扫描未定位直接调用方；可能通过路由注册、LangGraph 节点、协议方法或依赖注入动态调用，不据此判断为死代码。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：`ValueError(<字符串常量>)`。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。
- 恢复/幂等性：仅在代码有检查点、事务、请求编号或显式去重时才成立；此函数不能单凭名称视为可安全重试。


---

# ReviewRepository.correction ⭐⭐⭐⭐

**位置与等级**：[reviews.py:153](../../../src/persistence/reviews.py#L153)；承担主要 Agent、应用服务或审核/执行入口，跨模块影响显著。

**签名**：`def correction(self, correction_id: str) -> ReviewCorrection`。

**作用**：处理 `correction` 对应步骤；下列步骤依据函数体的实际控制流和调用点整理。

**输入与输出**：
- 输入：`correction_id`（str）。
- 输出类型：`ReviewCorrection`；具体返回路径见流程步骤。

**处理流程**：
1. 进入上下文 `closing(self.connect())`，由上下文管理器控制资源释放或事务范围。
2. 检查 `row is None`；按条件分流，else 分支不存在。
3. 返回 `ReviewCorrection.model_validate_json(row[0])`。

**关键条件与保护**：
- [reviews.py:158](../../../src/persistence/reviews.py#L158)：`row is None`，不满足时跳过本分支。

**调用与被调用**：
- `closing`（[reviews.py:154](../../../src/persistence/reviews.py#L154)）：来自 `contextlib.closing`；具体实现可能由依赖注入或运行时分派决定。
- `self.connect`（调用点 [reviews.py:154](../../../src/persistence/reviews.py#L154)）→ [ReviewRepository.connect](reviews.md)，静态可定位。
- `c.execute(<字符串常量>, (correction_id,)).fetchone`（[reviews.py:155](../../../src/persistence/reviews.py#L155)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `c.execute`（[reviews.py:155](../../../src/persistence/reviews.py#L155)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `KeyError`（[reviews.py:159](../../../src/persistence/reviews.py#L159)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `ReviewCorrection.model_validate_json`（[reviews.py:160](../../../src/persistence/reviews.py#L160)）：来自 `src.domain.reviews.ReviewCorrection`；具体实现可能由依赖注入或运行时分派决定。
- 静态扫描未定位直接调用方；可能通过路由注册、LangGraph 节点、协议方法或依赖注入动态调用，不据此判断为死代码。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：`KeyError(<字符串常量>)`。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。
- 恢复/幂等性：仅在代码有检查点、事务、请求编号或显式去重时才成立；此函数不能单凭名称视为可安全重试。


---
