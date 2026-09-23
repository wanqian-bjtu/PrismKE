源码：[cases.py:1](../../../src/persistence/cases.py#L1) | 基准：`dev/v0.10@f2f34d7` | 本文件符号数：15

**模块职责**：Immutable review-case store and rebuildable dense embeddings.
**在系统中的位置**：图、证据、运行、审计、审核与案例的持久化；JSON/Neo4j 提供同一存储协议。
**直接依赖**：[src.core.ids](../core/ids.md)、[src.domain](../domain/__init__.md)；外部/标准库：`__future__`、`builtins`、`contextlib`、`pathlib`、`sqlite3`。
**主要调用方（静态导入）**：[persistence/__init__.py](__init__.md)。
**阅读提示**：下列流程根据当前源码控制流整理；`self`/接口对象的实际类型可能在运行时注入，未能静态解析的调用会明确标注。链接指向源码行或对应讲解文件。

---

# CaseRepository ⭐⭐⭐⭐

**位置与等级**：[cases.py:14](../../../src/persistence/cases.py#L14)；承担主要 Agent、应用服务或审核/执行入口，跨模块影响显著。

**职责**：存储接口或实现；方法决定数据读取、持久化与并发边界。基类：无显式基类。

**字段与类级约束**：
- 类体未直接声明字段；实例状态请看 `__init__` 及方法中的赋值。

**内部成员**：`CaseRepository.__init__`、`CaseRepository.connect`、`CaseRepository.add`、`CaseRepository.get`、`CaseRepository.by_source_event`、`CaseRepository.list`、`CaseRepository.status_events`、`CaseRepository.disable`、`CaseRepository.is_active`、`CaseRepository.projected`、`CaseRepository.mark_projected`、`CaseRepository.embedding`、`CaseRepository.save_embedding`、`CaseRepository.index_status`


---

# CaseRepository.__init__ ⭐⭐

**位置与等级**：[cases.py:15](../../../src/persistence/cases.py#L15)；局部辅助逻辑，需理解其调用条件与失败传播。

**签名**：`def __init__(self, path: Path) -> None`。

**作用**：初始化对象并保存依赖或配置；需检查是否创建持久化资源。

**输入与输出**：
- 输入：`path`（Path）。
- 输出类型：`None`；具体返回路径见流程步骤。

**处理流程**：
1. 更新 `self.path`，值来自 `path`。
2. 调用 `path.parent.mkdir`，结果未直接赋值。
3. 进入上下文 `closing(self.connect()), connection`，由上下文管理器控制资源释放或事务范围。

**调用与被调用**：
- `path.parent.mkdir`（[cases.py:17](../../../src/persistence/cases.py#L17)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `closing`（[cases.py:18](../../../src/persistence/cases.py#L18)）：来自 `contextlib.closing`；具体实现可能由依赖注入或运行时分派决定。
- `self.connect`（调用点 [cases.py:18](../../../src/persistence/cases.py#L18)）→ [CaseRepository.connect](cases.md)，静态可定位。
- `connection.executescript`（[cases.py:19](../../../src/persistence/cases.py#L19)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- 静态扫描未定位直接调用方；可能通过路由注册、LangGraph 节点、协议方法或依赖注入动态调用，不据此判断为死代码。

**状态、副作用与异常**：
- 显式状态/容器赋值：`self.path`。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：未见 `raise`；下游异常可能继续上抛。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。
- 恢复/幂等性：仅在代码有检查点、事务、请求编号或显式去重时才成立；此函数不能单凭名称视为可安全重试。


---

# CaseRepository.connect ⭐⭐

**位置与等级**：[cases.py:56](../../../src/persistence/cases.py#L56)；局部辅助逻辑，需理解其调用条件与失败传播。

**签名**：`def connect(self) -> sqlite3.Connection`。

**作用**：处理 `connect` 对应步骤；下列步骤依据函数体的实际控制流和调用点整理。

**输入与输出**：
- 输入：无业务参数（或仅隐式接收实例）。
- 输出类型：`sqlite3.Connection`；具体返回路径见流程步骤。

**处理流程**：
1. 更新 `connection`，值来自 `sqlite3.connect(self.path, timeout=10)`。
2. 调用 `connection.execute`，结果未直接赋值。
3. 调用 `connection.execute`，结果未直接赋值。
4. 返回 `connection`。

**调用与被调用**：
- `sqlite3.connect`（[cases.py:57](../../../src/persistence/cases.py#L57)）：来自 `sqlite3`；具体实现可能由依赖注入或运行时分派决定。
- `connection.execute`（[cases.py:58](../../../src/persistence/cases.py#L58)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- 静态可定位的调用方：[CaseRepository.__init__](cases.md)、[CaseRepository.add](cases.md)、[CaseRepository.get](cases.md)、[CaseRepository.by_source_event](cases.md)、[CaseRepository.list](cases.md)、[CaseRepository.status_events](cases.md)、[CaseRepository.disable](cases.md)、[CaseRepository.is_active](cases.md)、[CaseRepository.projected](cases.md)、[CaseRepository.mark_projected](cases.md)。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：未见 `raise`；下游异常可能继续上抛。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。
- 恢复/幂等性：仅在代码有检查点、事务、请求编号或显式去重时才成立；此函数不能单凭名称视为可安全重试。


---

# CaseRepository.add ⭐⭐

**位置与等级**：[cases.py:62](../../../src/persistence/cases.py#L62)；局部辅助逻辑，需理解其调用条件与失败传播。

**签名**：`def add(self, record: CaseRecord) -> CaseRecord`。

**作用**：处理 `add` 对应步骤；下列步骤依据函数体的实际控制流和调用点整理。

**输入与输出**：
- 输入：`record`（CaseRecord）。
- 输出类型：`CaseRecord`；具体返回路径见流程步骤。

**处理流程**：
1. 更新 `payload`，值来自 `record.model_dump_json()`。
2. 进入上下文 `closing(self.connect()), connection`，由上下文管理器控制资源释放或事务范围。
3. 返回 `record`。

**关键条件与保护**：
- [cases.py:68](../../../src/persistence/cases.py#L68)：`row is not None`，不满足时跳过本分支。
- [cases.py:70](../../../src/persistence/cases.py#L70)：`canonical_hash(existing.model_dump(mode='json')) != canonical_hash(record.model_dump(mode='json'))`，不满足时跳过本分支。

**调用与被调用**：
- `record.model_dump_json`（[cases.py:63](../../../src/persistence/cases.py#L63)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `closing`（[cases.py:64](../../../src/persistence/cases.py#L64)）：来自 `contextlib.closing`；具体实现可能由依赖注入或运行时分派决定。
- `self.connect`（调用点 [cases.py:64](../../../src/persistence/cases.py#L64)）→ [CaseRepository.connect](cases.md)，静态可定位。
- `connection.execute(<字符串常量>, (record.id,)).fetchone`（[cases.py:65](../../../src/persistence/cases.py#L65)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `connection.execute`（[cases.py:65](../../../src/persistence/cases.py#L65)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `CaseRecord.model_validate_json`（[cases.py:69](../../../src/persistence/cases.py#L69)）：来自 `src.domain.CaseRecord`；具体实现可能由依赖注入或运行时分派决定。
- `canonical_hash`（调用点 [cases.py:70](../../../src/persistence/cases.py#L70)）→ [canonical_hash](../core/ids.md)，静态可定位。
- `existing.model_dump`（[cases.py:70](../../../src/persistence/cases.py#L70)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `record.model_dump`（[cases.py:71](../../../src/persistence/cases.py#L71)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `ValueError`（[cases.py:73](../../../src/persistence/cases.py#L73)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- 静态扫描未定位直接调用方；可能通过路由注册、LangGraph 节点、协议方法或依赖注入动态调用，不据此判断为死代码。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：`ValueError(<字符串常量>)`。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。
- 恢复/幂等性：仅在代码有检查点、事务、请求编号或显式去重时才成立；此函数不能单凭名称视为可安全重试。


---

# CaseRepository.get ⭐⭐

**位置与等级**：[cases.py:81](../../../src/persistence/cases.py#L81)；局部辅助逻辑，需理解其调用条件与失败传播。

**签名**：`def get(self, case_id: str) -> CaseRecord`。

**作用**：处理 `get` 对应步骤；下列步骤依据函数体的实际控制流和调用点整理。

**输入与输出**：
- 输入：`case_id`（str）。
- 输出类型：`CaseRecord`；具体返回路径见流程步骤。

**处理流程**：
1. 进入上下文 `closing(self.connect())`，由上下文管理器控制资源释放或事务范围。
2. 检查 `row is None`；按条件分流，else 分支不存在。
3. 返回 `CaseRecord.model_validate_json(row[0])`。

**关键条件与保护**：
- [cases.py:84](../../../src/persistence/cases.py#L84)：`row is None`，不满足时跳过本分支。

**调用与被调用**：
- `closing`（[cases.py:82](../../../src/persistence/cases.py#L82)）：来自 `contextlib.closing`；具体实现可能由依赖注入或运行时分派决定。
- `self.connect`（调用点 [cases.py:82](../../../src/persistence/cases.py#L82)）→ [CaseRepository.connect](cases.md)，静态可定位。
- `connection.execute(<字符串常量>, (case_id,)).fetchone`（[cases.py:83](../../../src/persistence/cases.py#L83)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `connection.execute`（[cases.py:83](../../../src/persistence/cases.py#L83)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `KeyError`（[cases.py:85](../../../src/persistence/cases.py#L85)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `CaseRecord.model_validate_json`（[cases.py:86](../../../src/persistence/cases.py#L86)）：来自 `src.domain.CaseRecord`；具体实现可能由依赖注入或运行时分派决定。
- 静态可定位的调用方：[CaseRepository.disable](cases.md)、[CaseRepository.is_active](cases.md)。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：`KeyError(<字符串常量>)`。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。
- 恢复/幂等性：仅在代码有检查点、事务、请求编号或显式去重时才成立；此函数不能单凭名称视为可安全重试。


---

# CaseRepository.by_source_event ⭐⭐

**位置与等级**：[cases.py:88](../../../src/persistence/cases.py#L88)；局部辅助逻辑，需理解其调用条件与失败传播。

**签名**：`def by_source_event(self, event_id: str) -> CaseRecord | None`。

**作用**：处理 `by_source_event` 对应步骤；下列步骤依据函数体的实际控制流和调用点整理。

**输入与输出**：
- 输入：`event_id`（str）。
- 输出类型：`CaseRecord | None`；具体返回路径见流程步骤。

**处理流程**：
1. 进入上下文 `closing(self.connect())`，由上下文管理器控制资源释放或事务范围。
2. 返回 `CaseRecord.model_validate_json(row[0]) if row else None`。

**调用与被调用**：
- `closing`（[cases.py:89](../../../src/persistence/cases.py#L89)）：来自 `contextlib.closing`；具体实现可能由依赖注入或运行时分派决定。
- `self.connect`（调用点 [cases.py:89](../../../src/persistence/cases.py#L89)）→ [CaseRepository.connect](cases.md)，静态可定位。
- `connection.execute(<字符串常量>, (event_id,)).fetchone`（[cases.py:90](../../../src/persistence/cases.py#L90)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `connection.execute`（[cases.py:90](../../../src/persistence/cases.py#L90)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `CaseRecord.model_validate_json`（[cases.py:93](../../../src/persistence/cases.py#L93)）：来自 `src.domain.CaseRecord`；具体实现可能由依赖注入或运行时分派决定。
- 静态扫描未定位直接调用方；可能通过路由注册、LangGraph 节点、协议方法或依赖注入动态调用，不据此判断为死代码。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：未见 `raise`；下游异常可能继续上抛。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。
- 恢复/幂等性：仅在代码有检查点、事务、请求编号或显式去重时才成立；此函数不能单凭名称视为可安全重试。


---

# CaseRepository.list ⭐⭐

**位置与等级**：[cases.py:95](../../../src/persistence/cases.py#L95)；局部辅助逻辑，需理解其调用条件与失败传播。

**签名**：`def list(self, *, case_type: str | None=None, task_type: str | None=None, schema_fingerprint: str | None=None, language: str | None=None, active_only: bool=False, limit: int=100) -> builtins.list[CaseRecord]`。

**作用**：处理 `list` 对应步骤；下列步骤依据函数体的实际控制流和调用点整理。

**输入与输出**：
- 输入：`case_type`（str | None；默认 `None`）；`task_type`（str | None；默认 `None`）；`schema_fingerprint`（str | None；默认 `None`）；`language`（str | None；默认 `None`）；`active_only`（bool；默认 `False`）；`limit`（int；默认 `100`；查询或展示的最大条数）。
- 输出类型：`builtins.list[CaseRecord]`；具体返回路径见流程步骤。

**处理流程**：
1. 更新 `clauses`，值来自 `[]`。
2. 更新 `values`，值来自 `[]`。
3. 遍历 `((<字符串常量>, case_type), (<字符串常量>, task_type), (<字符串常量>, schema_fingerprint), (<字符串常量>…`，逐项处理 `(expression, value)`。
4. 检查 `active_only`；按条件分流，else 分支不存在。
5. 更新 `sql`，值来自 `<字符串常量>`。
6. 检查 `clauses`；按条件分流，else 分支不存在。
7. 更新 `sql`，值来自 `<字符串常量>`。
8. 调用 `values.append`，结果未直接赋值。
9. 进入上下文 `closing(self.connect())`，由上下文管理器控制资源释放或事务范围。
10. 返回 `[CaseRecord.model_validate_json(row[0]) for row in rows]`。

**关键条件与保护**：
- [cases.py:113](../../../src/persistence/cases.py#L113)：`value is not None`，不满足时跳过本分支。
- [cases.py:116](../../../src/persistence/cases.py#L116)：`active_only`，不满足时跳过本分支。
- [cases.py:122](../../../src/persistence/cases.py#L122)：`clauses`，不满足时跳过本分支。

**调用与被调用**：
- `clauses.append`（[cases.py:114](../../../src/persistence/cases.py#L114)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `values.append`（[cases.py:115](../../../src/persistence/cases.py#L115)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `<字符串常量>.join`（[cases.py:123](../../../src/persistence/cases.py#L123)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `max`（[cases.py:125](../../../src/persistence/cases.py#L125)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `min`（[cases.py:125](../../../src/persistence/cases.py#L125)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `closing`（[cases.py:126](../../../src/persistence/cases.py#L126)）：来自 `contextlib.closing`；具体实现可能由依赖注入或运行时分派决定。
- `self.connect`（调用点 [cases.py:126](../../../src/persistence/cases.py#L126)）→ [CaseRepository.connect](cases.md)，静态可定位。
- `connection.execute(sql, values).fetchall`（[cases.py:127](../../../src/persistence/cases.py#L127)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `connection.execute`（[cases.py:127](../../../src/persistence/cases.py#L127)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `CaseRecord.model_validate_json`（[cases.py:128](../../../src/persistence/cases.py#L128)）：来自 `src.domain.CaseRecord`；具体实现可能由依赖注入或运行时分派决定。
- 静态可定位的调用方：[CaseRepository.index_status](cases.md)。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：未见 `raise`；下游异常可能继续上抛。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。
- 恢复/幂等性：仅在代码有检查点、事务、请求编号或显式去重时才成立；此函数不能单凭名称视为可安全重试。


---

# CaseRepository.status_events ⭐⭐

**位置与等级**：[cases.py:130](../../../src/persistence/cases.py#L130)；局部辅助逻辑，需理解其调用条件与失败传播。

**签名**：`def status_events(self, case_id: str) -> builtins.list[CaseStatusEvent]`。

**作用**：处理 `status_events` 对应步骤；下列步骤依据函数体的实际控制流和调用点整理。

**输入与输出**：
- 输入：`case_id`（str）。
- 输出类型：`builtins.list[CaseStatusEvent]`；具体返回路径见流程步骤。

**处理流程**：
1. 进入上下文 `closing(self.connect())`，由上下文管理器控制资源释放或事务范围。
2. 返回 `[CaseStatusEvent.model_validate_json(row[0]) for row in rows]`。

**调用与被调用**：
- `closing`（[cases.py:131](../../../src/persistence/cases.py#L131)）：来自 `contextlib.closing`；具体实现可能由依赖注入或运行时分派决定。
- `self.connect`（调用点 [cases.py:131](../../../src/persistence/cases.py#L131)）→ [CaseRepository.connect](cases.md)，静态可定位。
- `connection.execute(<字符串常量>, (case_id,)).fetchall`（[cases.py:132](../../../src/persistence/cases.py#L132)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `connection.execute`（[cases.py:132](../../../src/persistence/cases.py#L132)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `CaseStatusEvent.model_validate_json`（[cases.py:135](../../../src/persistence/cases.py#L135)）：来自 `src.domain.CaseStatusEvent`；具体实现可能由依赖注入或运行时分派决定。
- 静态扫描未定位直接调用方；可能通过路由注册、LangGraph 节点、协议方法或依赖注入动态调用，不据此判断为死代码。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：未见 `raise`；下游异常可能继续上抛。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。
- 恢复/幂等性：仅在代码有检查点、事务、请求编号或显式去重时才成立；此函数不能单凭名称视为可安全重试。


---

# CaseRepository.disable ⭐⭐

**位置与等级**：[cases.py:137](../../../src/persistence/cases.py#L137)；局部辅助逻辑，需理解其调用条件与失败传播。

**签名**：`def disable(self, event: CaseStatusEvent) -> CaseStatusEvent`。

**作用**：处理 `disable` 对应步骤；下列步骤依据函数体的实际控制流和调用点整理。

**输入与输出**：
- 输入：`event`（CaseStatusEvent）。
- 输出类型：`CaseStatusEvent`；具体返回路径见流程步骤。

**处理流程**：
1. 调用 `self.get`，结果未直接赋值。
2. 进入上下文 `closing(self.connect()), connection`，由上下文管理器控制资源释放或事务范围。
3. 返回 `event`。

**关键条件与保护**：
- [cases.py:143](../../../src/persistence/cases.py#L143)：`row is not None`，不满足时跳过本分支。
- [cases.py:145](../../../src/persistence/cases.py#L145)：`existing != event`，不满足时跳过本分支。

**调用与被调用**：
- `self.get`（调用点 [cases.py:138](../../../src/persistence/cases.py#L138)）→ [CaseRepository.get](cases.md)，静态可定位。
- `closing`（[cases.py:139](../../../src/persistence/cases.py#L139)）：来自 `contextlib.closing`；具体实现可能由依赖注入或运行时分派决定。
- `self.connect`（调用点 [cases.py:139](../../../src/persistence/cases.py#L139)）→ [CaseRepository.connect](cases.md)，静态可定位。
- `connection.execute(<字符串常量>, (event.id,)).fetchone`（[cases.py:140](../../../src/persistence/cases.py#L140)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `connection.execute`（[cases.py:140](../../../src/persistence/cases.py#L140)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `CaseStatusEvent.model_validate_json`（[cases.py:144](../../../src/persistence/cases.py#L144)）：来自 `src.domain.CaseStatusEvent`；具体实现可能由依赖注入或运行时分派决定。
- `ValueError`（[cases.py:146](../../../src/persistence/cases.py#L146)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `event.model_dump_json`（[cases.py:150](../../../src/persistence/cases.py#L150)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- 静态扫描未定位直接调用方；可能通过路由注册、LangGraph 节点、协议方法或依赖注入动态调用，不据此判断为死代码。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：`ValueError(<字符串常量>)`。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。
- 恢复/幂等性：仅在代码有检查点、事务、请求编号或显式去重时才成立；此函数不能单凭名称视为可安全重试。


---

# CaseRepository.is_active ⭐⭐

**位置与等级**：[cases.py:154](../../../src/persistence/cases.py#L154)；局部辅助逻辑，需理解其调用条件与失败传播。

**签名**：`def is_active(self, case_id: str) -> bool`。

**作用**：处理 `is_active` 对应步骤；下列步骤依据函数体的实际控制流和调用点整理。

**输入与输出**：
- 输入：`case_id`（str）。
- 输出类型：`bool`；具体返回路径见流程步骤。

**处理流程**：
1. 调用 `self.get`，结果未直接赋值。
2. 进入上下文 `closing(self.connect())`，由上下文管理器控制资源释放或事务范围。
3. 返回 `row is None`。

**调用与被调用**：
- `self.get`（调用点 [cases.py:155](../../../src/persistence/cases.py#L155)）→ [CaseRepository.get](cases.md)，静态可定位。
- `closing`（[cases.py:156](../../../src/persistence/cases.py#L156)）：来自 `contextlib.closing`；具体实现可能由依赖注入或运行时分派决定。
- `self.connect`（调用点 [cases.py:156](../../../src/persistence/cases.py#L156)）→ [CaseRepository.connect](cases.md)，静态可定位。
- `connection.execute(<字符串常量>, (case_id,)).fetchone`（[cases.py:157](../../../src/persistence/cases.py#L157)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `connection.execute`（[cases.py:157](../../../src/persistence/cases.py#L157)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- 静态扫描未定位直接调用方；可能通过路由注册、LangGraph 节点、协议方法或依赖注入动态调用，不据此判断为死代码。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：未见 `raise`；下游异常可能继续上抛。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。
- 恢复/幂等性：仅在代码有检查点、事务、请求编号或显式去重时才成立；此函数不能单凭名称视为可安全重试。


---

# CaseRepository.projected ⭐⭐

**位置与等级**：[cases.py:164](../../../src/persistence/cases.py#L164)；局部辅助逻辑，需理解其调用条件与失败传播。

**签名**：`def projected(self, event_id: str) -> bool`。

**作用**：处理 `projected` 对应步骤；下列步骤依据函数体的实际控制流和调用点整理。

**输入与输出**：
- 输入：`event_id`（str）。
- 输出类型：`bool`；具体返回路径见流程步骤。

**处理流程**：
1. 进入上下文 `closing(self.connect())`，由上下文管理器控制资源释放或事务范围。

**调用与被调用**：
- `closing`（[cases.py:165](../../../src/persistence/cases.py#L165)）：来自 `contextlib.closing`；具体实现可能由依赖注入或运行时分派决定。
- `self.connect`（调用点 [cases.py:165](../../../src/persistence/cases.py#L165)）→ [CaseRepository.connect](cases.md)，静态可定位。
- `connection.execute(<字符串常量>, (event_id,)).fetchone`（[cases.py:167](../../../src/persistence/cases.py#L167)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `connection.execute`（[cases.py:167](../../../src/persistence/cases.py#L167)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- 静态扫描未定位直接调用方；可能通过路由注册、LangGraph 节点、协议方法或依赖注入动态调用，不据此判断为死代码。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：未见 `raise`；下游异常可能继续上抛。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。
- 恢复/幂等性：仅在代码有检查点、事务、请求编号或显式去重时才成立；此函数不能单凭名称视为可安全重试。


---

# CaseRepository.mark_projected ⭐⭐

**位置与等级**：[cases.py:173](../../../src/persistence/cases.py#L173)；局部辅助逻辑，需理解其调用条件与失败传播。

**签名**：`def mark_projected(self, event_id: str, case_id: str | None) -> None`。

**作用**：处理 `mark_projected` 对应步骤；下列步骤依据函数体的实际控制流和调用点整理。

**输入与输出**：
- 输入：`event_id`（str）；`case_id`（str | None）。
- 输出类型：`None`；具体返回路径见流程步骤。

**处理流程**：
1. 进入上下文 `closing(self.connect()), connection`，由上下文管理器控制资源释放或事务范围。

**调用与被调用**：
- `closing`（[cases.py:174](../../../src/persistence/cases.py#L174)）：来自 `contextlib.closing`；具体实现可能由依赖注入或运行时分派决定。
- `self.connect`（调用点 [cases.py:174](../../../src/persistence/cases.py#L174)）→ [CaseRepository.connect](cases.md)，静态可定位。
- `connection.execute`（[cases.py:175](../../../src/persistence/cases.py#L175)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- 静态扫描未定位直接调用方；可能通过路由注册、LangGraph 节点、协议方法或依赖注入动态调用，不据此判断为死代码。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：未见 `raise`；下游异常可能继续上抛。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。
- 恢复/幂等性：仅在代码有检查点、事务、请求编号或显式去重时才成立；此函数不能单凭名称视为可安全重试。


---

# CaseRepository.embedding ⭐⭐

**位置与等级**：[cases.py:180](../../../src/persistence/cases.py#L180)；局部辅助逻辑，需理解其调用条件与失败传播。

**签名**：`def embedding(self, case_id: str) -> CaseEmbedding | None`。

**作用**：处理 `embedding` 对应步骤；下列步骤依据函数体的实际控制流和调用点整理。

**输入与输出**：
- 输入：`case_id`（str）。
- 输出类型：`CaseEmbedding | None`；具体返回路径见流程步骤。

**处理流程**：
1. 进入上下文 `closing(self.connect())`，由上下文管理器控制资源释放或事务范围。
2. 返回 `CaseEmbedding.model_validate_json(row[0]) if row else None`。

**调用与被调用**：
- `closing`（[cases.py:181](../../../src/persistence/cases.py#L181)）：来自 `contextlib.closing`；具体实现可能由依赖注入或运行时分派决定。
- `self.connect`（调用点 [cases.py:181](../../../src/persistence/cases.py#L181)）→ [CaseRepository.connect](cases.md)，静态可定位。
- `connection.execute(<字符串常量>, (case_id,)).fetchone`（[cases.py:182](../../../src/persistence/cases.py#L182)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `connection.execute`（[cases.py:182](../../../src/persistence/cases.py#L182)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `CaseEmbedding.model_validate_json`（[cases.py:185](../../../src/persistence/cases.py#L185)）：来自 `src.domain.CaseEmbedding`；具体实现可能由依赖注入或运行时分派决定。
- 静态可定位的调用方：[CaseRepository.index_status](cases.md)。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：未见 `raise`；下游异常可能继续上抛。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。
- 恢复/幂等性：仅在代码有检查点、事务、请求编号或显式去重时才成立；此函数不能单凭名称视为可安全重试。


---

# CaseRepository.save_embedding ⭐⭐

**位置与等级**：[cases.py:187](../../../src/persistence/cases.py#L187)；局部辅助逻辑，需理解其调用条件与失败传播。

**签名**：`def save_embedding(self, embedding: CaseEmbedding) -> None`。

**作用**：创建、更新或记录相应资源；写入/审计边界以实际调用和状态赋值为准。

**输入与输出**：
- 输入：`embedding`（CaseEmbedding）。
- 输出类型：`None`；具体返回路径见流程步骤。

**处理流程**：
1. 进入上下文 `closing(self.connect()), connection`，由上下文管理器控制资源释放或事务范围。

**调用与被调用**：
- `closing`（[cases.py:188](../../../src/persistence/cases.py#L188)）：来自 `contextlib.closing`；具体实现可能由依赖注入或运行时分派决定。
- `self.connect`（调用点 [cases.py:188](../../../src/persistence/cases.py#L188)）→ [CaseRepository.connect](cases.md)，静态可定位。
- `connection.execute`（[cases.py:189](../../../src/persistence/cases.py#L189)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `embedding.model_dump_json`（[cases.py:198](../../../src/persistence/cases.py#L198)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- 静态扫描未定位直接调用方；可能通过路由注册、LangGraph 节点、协议方法或依赖注入动态调用，不据此判断为死代码。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：未见 `raise`；下游异常可能继续上抛。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。
- 恢复/幂等性：仅在代码有检查点、事务、请求编号或显式去重时才成立；此函数不能单凭名称视为可安全重试。


---

# CaseRepository.index_status ⭐⭐

**位置与等级**：[cases.py:202](../../../src/persistence/cases.py#L202)；局部辅助逻辑，需理解其调用条件与失败传播。

**签名**：`def index_status(self, model_fingerprint: str) -> dict[str, int]`。

**作用**：处理 `index_status` 对应步骤；下列步骤依据函数体的实际控制流和调用点整理。

**输入与输出**：
- 输入：`model_fingerprint`（str）。
- 输出类型：`dict[str, int]`；具体返回路径见流程步骤。

**处理流程**：
1. 更新 `active`，值来自 `self.list(active_only=True, limit=10000)`。
2. 更新 `current`，值来自 `0`。
3. 遍历 `active`，逐项处理 `record`。
4. 返回 `{'active_cases': len(active), 'indexed_cases': current, 'stale_cases': len(active) - current}`。

**关键条件与保护**：
- [cases.py:207](../../../src/persistence/cases.py#L207)：`embedding and embedding.model_fingerprint == model_fingerprint`，不满足时跳过本分支。

**调用与被调用**：
- `self.list`（调用点 [cases.py:203](../../../src/persistence/cases.py#L203)）→ [CaseRepository.list](cases.md)，静态可定位。
- `self.embedding`（调用点 [cases.py:206](../../../src/persistence/cases.py#L206)）→ [CaseRepository.embedding](cases.md)，静态可定位。
- `len`（[cases.py:210](../../../src/persistence/cases.py#L210)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- 静态扫描未定位直接调用方；可能通过路由注册、LangGraph 节点、协议方法或依赖注入动态调用，不据此判断为死代码。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：未见 `raise`；下游异常可能继续上抛。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。
- 恢复/幂等性：仅在代码有检查点、事务、请求编号或显式去重时才成立；此函数不能单凭名称视为可安全重试。


---
