源码：[json_graph.py:1](../../../src/persistence/json_graph.py#L1) | 基准：`dev/v0.10@f2f34d7` | 本文件符号数：25

**模块职责**：Atomic local graph persistence with revisions and compensating rollback.
**在系统中的位置**：图、证据、运行、审计、审核与案例的持久化；JSON/Neo4j 提供同一存储协议。
**阅读重点**：JSONGraphStore 以锁和原子文件替换实现一次 GraphCommit。读取/预览与写入分离，最终提交仍需重新校验父版本、引用和证据。
**直接依赖**：[src.core.errors](../core/errors.md)、[src.core.ids](../core/ids.md)、[src.domain](../domain/__init__.md)、[src.governance.review_guards](../governance/review_guards.md)、[src.governance.validation](../governance/validation/__init__.md)、[src.governance.validation.context](../governance/validation/context.md)、[src.persistence.base](base.md)；外部/标准库：`__future__`、`copy`、`datetime`、`filelock`、`math`、`orjson`、`os`、`pathlib`、`typing`、`uuid`。
**主要调用方（静态导入）**：[evaluation/document_validation.py](../evaluation/document_validation.md)、[evaluation/entity_linking.py](../evaluation/entity_linking.md)、[persistence/__init__.py](__init__.md)。
**阅读提示**：下列流程根据当前源码控制流整理；`self`/接口对象的实际类型可能在运行时注入，未能静态解析的调用会明确标注。链接指向源码行或对应讲解文件。

## 核心路径解读

- `_apply` 先识别相同 Revision 的幂等重放，再核对最新父版本，按文档、证据、实体、Embedding、Claim、冲突和 Revision 建立候选图状态；任何引用不完整都应拒绝。
- `commit` 在文件锁内复制当前图状态，复核纠正防护、最终 Claim 状态和 ValidationService 硬约束，最后通过原子文件替换持久化；预览或旧快照不能替代锁内检查。
- `rollback_revision` 生成补偿变化，不物理删除旧 Claim 和历史 Revision；若后续版本改变了相关资源，应拒绝过期回滚。

---

# JSONGraphStore ⭐⭐⭐⭐

**位置与等级**：[json_graph.py:40](../../../src/persistence/json_graph.py#L40)；承担主要 Agent、应用服务或审核/执行入口，跨模块影响显著。

**职责**：存储接口或实现；方法决定数据读取、持久化与并发边界。基类：无显式基类。

**字段与类级约束**：
- 类体未直接声明字段；实例状态请看 `__init__` 及方法中的赋值。

**内部成员**：`JSONGraphStore.__init__`、`JSONGraphStore._empty_graph`、`JSONGraphStore._upgrade`、`JSONGraphStore._read`、`JSONGraphStore.snapshot`、`JSONGraphStore._write_atomic`、`JSONGraphStore.healthcheck`、`JSONGraphStore.list_entities`、`JSONGraphStore.get_entity`、`JSONGraphStore.search_entities`、`JSONGraphStore.list_entity_embeddings`、`JSONGraphStore.upsert_entity_embeddings`、`JSONGraphStore.list_claims`、`JSONGraphStore.latest_revision`、`JSONGraphStore.list_revisions`、`JSONGraphStore.get_claim`、`JSONGraphStore.get_evidence`、`JSONGraphStore.get_neighborhood`、`JSONGraphStore._merge_claim`、`JSONGraphStore._apply`、`JSONGraphStore.commit`、`JSONGraphStore.diff_revisions`、`JSONGraphStore.rollback_revision`、`JSONGraphStore.close`


---

# JSONGraphStore.__init__ ⭐⭐

**位置与等级**：[json_graph.py:41](../../../src/persistence/json_graph.py#L41)；局部辅助逻辑，需理解其调用条件与失败传播。

**签名**：`def __init__(self, directory: Path, *, evidence_store: EvidenceStore | None=None) -> None`。

**作用**：初始化对象并保存依赖或配置；需检查是否创建持久化资源。

**输入与输出**：
- 输入：`directory`（Path）；`evidence_store`（EvidenceStore | None；默认 `None`；证据元数据和原始内容的存储接口）。
- 输出类型：`None`；具体返回路径见流程步骤。

**处理流程**：
1. 更新 `self.evidence_store`，值来自 `evidence_store`。
2. 更新 `self.directory`，值来自 `directory`。
3. 更新 `self.path`，值来自 `directory / 'graph.json'`。
4. 更新 `self.lock`，值来自 `FileLock(str(directory / 'graph.lock'))`。
5. 调用 `self.directory.mkdir`，结果未直接赋值。
6. 检查 `not self.path.exists()`；按条件分流，else 分支不存在。

**关键条件与保护**：
- [json_graph.py:47](../../../src/persistence/json_graph.py#L47)：`not self.path.exists()`，不满足时跳过本分支。

**调用与被调用**：
- `FileLock`（[json_graph.py:45](../../../src/persistence/json_graph.py#L45)）：来自 `filelock.FileLock`；具体实现可能由依赖注入或运行时分派决定。
- `str`（[json_graph.py:45](../../../src/persistence/json_graph.py#L45)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `self.directory.mkdir`（[json_graph.py:46](../../../src/persistence/json_graph.py#L46)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `self.path.exists`（[json_graph.py:47](../../../src/persistence/json_graph.py#L47)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `self._write_atomic`（调用点 [json_graph.py:48](../../../src/persistence/json_graph.py#L48)）→ [JSONGraphStore._write_atomic](json_graph.md)，静态可定位。
- `self._empty_graph`（调用点 [json_graph.py:48](../../../src/persistence/json_graph.py#L48)）→ [JSONGraphStore._empty_graph](json_graph.md)，静态可定位。
- 静态扫描未定位直接调用方；可能通过路由注册、LangGraph 节点、协议方法或依赖注入动态调用，不据此判断为死代码。

**状态、副作用与异常**：
- 显式状态/容器赋值：`self.evidence_store`、`self.directory`、`self.path`、`self.lock`。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：未见 `raise`；下游异常可能继续上抛。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。
- 恢复/幂等性：仅在代码有检查点、事务、请求编号或显式去重时才成立；此函数不能单凭名称视为可安全重试。


---

# JSONGraphStore._empty_graph ⭐⭐

**位置与等级**：[json_graph.py:51](../../../src/persistence/json_graph.py#L51)；局部辅助逻辑，需理解其调用条件与失败传播。

**签名**：`def _empty_graph() -> dict[str, Any]`。

**装饰器/路由**：`staticmethod`。

**作用**：内部辅助步骤；将参数转换为本模块所需的中间对象或操作结果。

**输入与输出**：
- 输入：无业务参数（或仅隐式接收实例）。
- 输出类型：`dict[str, Any]`；具体返回路径见流程步骤。

**处理流程**：
1. 返回 `{'documents': {}, 'evidence': {}, 'entities': {}, 'entity_embeddings': {}, 'entity_operations': {}, 'cla…`。

**调用与被调用**：
- 无显式函数调用，或仅声明协议/常量。
- 静态可定位的调用方：[JSONGraphStore.__init__](json_graph.md)。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：未见 `raise`；下游异常可能继续上抛。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。
- 恢复/幂等性：仅在代码有检查点、事务、请求编号或显式去重时才成立；此函数不能单凭名称视为可安全重试。


---

# JSONGraphStore._upgrade ⭐⭐

**位置与等级**：[json_graph.py:64](../../../src/persistence/json_graph.py#L64)；局部辅助逻辑，需理解其调用条件与失败传播。

**签名**：`def _upgrade(data: dict[str, Any]) -> dict[str, Any]`。

**装饰器/路由**：`staticmethod`。

**作用**：内部辅助步骤；将参数转换为本模块所需的中间对象或操作结果。

**输入与输出**：
- 输入：`data`（dict[str, Any]）。
- 输出类型：`dict[str, Any]`；具体返回路径见流程步骤。

**处理流程**：
1. 遍历 `JSONGraphStore._empty_graph().items()`，逐项处理 `(key, default)`。
2. 返回 `data`。

**调用与被调用**：
- `JSONGraphStore._empty_graph().items`（[json_graph.py:65](../../../src/persistence/json_graph.py#L65)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `JSONGraphStore._empty_graph`（[json_graph.py:65](../../../src/persistence/json_graph.py#L65)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `data.setdefault`（[json_graph.py:66](../../../src/persistence/json_graph.py#L66)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `deepcopy`（[json_graph.py:66](../../../src/persistence/json_graph.py#L66)）：来自 `copy.deepcopy`；具体实现可能由依赖注入或运行时分派决定。
- 静态可定位的调用方：[JSONGraphStore._read](json_graph.md)。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：未见 `raise`；下游异常可能继续上抛。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。
- 恢复/幂等性：仅在代码有检查点、事务、请求编号或显式去重时才成立；此函数不能单凭名称视为可安全重试。


---

# JSONGraphStore._read ⭐⭐

**位置与等级**：[json_graph.py:69](../../../src/persistence/json_graph.py#L69)；局部辅助逻辑，需理解其调用条件与失败传播。

**签名**：`def _read(self) -> dict[str, Any]`。

**作用**：内部辅助步骤；将参数转换为本模块所需的中间对象或操作结果。

**输入与输出**：
- 输入：无业务参数（或仅隐式接收实例）。
- 输出类型：`dict[str, Any]`；具体返回路径见流程步骤。

**处理流程**：
1. 返回 `self._upgrade(cast(dict[str, Any], orjson.loads(self.path.read_bytes())))`。

**调用与被调用**：
- `self._upgrade`（调用点 [json_graph.py:70](../../../src/persistence/json_graph.py#L70)）→ [JSONGraphStore._upgrade](json_graph.md)，静态可定位。
- `cast`（[json_graph.py:70](../../../src/persistence/json_graph.py#L70)）：来自 `typing.cast`；具体实现可能由依赖注入或运行时分派决定。
- `orjson.loads`（[json_graph.py:70](../../../src/persistence/json_graph.py#L70)）：来自 `orjson`；具体实现可能由依赖注入或运行时分派决定。
- `self.path.read_bytes`（[json_graph.py:70](../../../src/persistence/json_graph.py#L70)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- 静态可定位的调用方：[JSONGraphStore.snapshot](json_graph.md)、[JSONGraphStore.healthcheck](json_graph.md)、[JSONGraphStore.list_entities](json_graph.md)、[JSONGraphStore.get_entity](json_graph.md)、[JSONGraphStore.search_entities](json_graph.md)、[JSONGraphStore.list_entity_embeddings](json_graph.md)、[JSONGraphStore.upsert_entity_embeddings](json_graph.md)、[JSONGraphStore.list_claims](json_graph.md)、[JSONGraphStore.latest_revision](json_graph.md)、[JSONGraphStore.list_revisions](json_graph.md)。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：未见 `raise`；下游异常可能继续上抛。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。
- 恢复/幂等性：仅在代码有检查点、事务、请求编号或显式去重时才成立；此函数不能单凭名称视为可安全重试。


---

# JSONGraphStore.snapshot ⭐⭐

**位置与等级**：[json_graph.py:72](../../../src/persistence/json_graph.py#L72)；局部辅助逻辑，需理解其调用条件与失败传播。

**签名**：`def snapshot(self) -> dict[str, Any]`。

**作用**：Return a detached snapshot for migration and diagnostics.

**输入与输出**：
- 输入：无业务参数（或仅隐式接收实例）。
- 输出类型：`dict[str, Any]`；具体返回路径见流程步骤。

**处理流程**：
1. 进入上下文 `self.lock`，由上下文管理器控制资源释放或事务范围。

**调用与被调用**：
- `deepcopy`（[json_graph.py:75](../../../src/persistence/json_graph.py#L75)）：来自 `copy.deepcopy`；具体实现可能由依赖注入或运行时分派决定。
- `self._read`（调用点 [json_graph.py:75](../../../src/persistence/json_graph.py#L75)）→ [JSONGraphStore._read](json_graph.md)，静态可定位。
- 静态扫描未定位直接调用方；可能通过路由注册、LangGraph 节点、协议方法或依赖注入动态调用，不据此判断为死代码。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：未见 `raise`；下游异常可能继续上抛。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。
- 恢复/幂等性：仅在代码有检查点、事务、请求编号或显式去重时才成立；此函数不能单凭名称视为可安全重试。


---

# JSONGraphStore._write_atomic ⭐⭐

**位置与等级**：[json_graph.py:77](../../../src/persistence/json_graph.py#L77)；局部辅助逻辑，需理解其调用条件与失败传播。

**签名**：`def _write_atomic(self, payload: dict[str, Any]) -> None`。

**作用**：内部辅助步骤；将参数转换为本模块所需的中间对象或操作结果。

**输入与输出**：
- 输入：`payload`（dict[str, Any]）。
- 输出类型：`None`；具体返回路径见流程步骤。

**处理流程**：
1. 更新 `temporary`，值来自 `self.path.with_name(f<字符串常量>)`。
2. 捕获 无显式捕获；另检查 finally/else 的清理和传播。

**调用与被调用**：
- `self.path.with_name`（[json_graph.py:78](../../../src/persistence/json_graph.py#L78)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `uuid4`（[json_graph.py:78](../../../src/persistence/json_graph.py#L78)）：来自 `uuid.uuid4`；具体实现可能由依赖注入或运行时分派决定。
- `temporary.open`（[json_graph.py:80](../../../src/persistence/json_graph.py#L80)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `stream.write`（[json_graph.py:81](../../../src/persistence/json_graph.py#L81)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `orjson.dumps`（[json_graph.py:81](../../../src/persistence/json_graph.py#L81)）：来自 `orjson`；具体实现可能由依赖注入或运行时分派决定。
- `stream.flush`（[json_graph.py:82](../../../src/persistence/json_graph.py#L82)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `os.fsync`（[json_graph.py:83](../../../src/persistence/json_graph.py#L83)）：来自 `os`；具体实现可能由依赖注入或运行时分派决定。
- `stream.fileno`（[json_graph.py:83](../../../src/persistence/json_graph.py#L83)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `os.replace`（[json_graph.py:84](../../../src/persistence/json_graph.py#L84)）：来自 `os`；具体实现可能由依赖注入或运行时分派决定。
- `temporary.unlink`（[json_graph.py:86](../../../src/persistence/json_graph.py#L86)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- 静态可定位的调用方：[JSONGraphStore.__init__](json_graph.md)、[JSONGraphStore.upsert_entity_embeddings](json_graph.md)、[JSONGraphStore.commit](json_graph.md)、[JSONGraphStore.rollback_revision](json_graph.md)。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：未见 `raise`；下游异常可能继续上抛。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。
- 恢复/幂等性：仅在代码有检查点、事务、请求编号或显式去重时才成立；此函数不能单凭名称视为可安全重试。


---

# JSONGraphStore.healthcheck ⭐⭐

**位置与等级**：[json_graph.py:88](../../../src/persistence/json_graph.py#L88)；局部辅助逻辑，需理解其调用条件与失败传播。

**签名**：`async def healthcheck(self) -> GraphHealth`。

**作用**：查询当前后端是否可用并构造健康状态。

**输入与输出**：
- 输入：无业务参数（或仅隐式接收实例）。
- 输出类型：`GraphHealth`；具体返回路径见流程步骤。

**处理流程**：
1. 捕获 (OSError, orjson.JSONDecodeError, TypeError, ValueErro…；另检查 finally/else 的清理和传播。
2. 返回 `GraphHealth(backend='json', healthy=True)`。

**调用与被调用**：
- `self._read`（调用点 [json_graph.py:91](../../../src/persistence/json_graph.py#L91)）→ [JSONGraphStore._read](json_graph.md)，静态可定位。
- `GraphHealth`（[json_graph.py:93](../../../src/persistence/json_graph.py#L93)）：来自 `src.domain.GraphHealth`；具体实现可能由依赖注入或运行时分派决定。
- `str`（[json_graph.py:93](../../../src/persistence/json_graph.py#L93)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- 静态扫描未定位直接调用方；可能通过路由注册、LangGraph 节点、协议方法或依赖注入动态调用，不据此判断为死代码。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：未见 `raise`；下游异常可能继续上抛。
- 本地捕获：`(OSError, orjson.JSONDecodeError, TypeError, ValueError)`。
- 恢复/幂等性：仅在代码有检查点、事务、请求编号或显式去重时才成立；此函数不能单凭名称视为可安全重试。


---

# JSONGraphStore.list_entities ⭐⭐

**位置与等级**：[json_graph.py:96](../../../src/persistence/json_graph.py#L96)；局部辅助逻辑，需理解其调用条件与失败传播。

**签名**：`async def list_entities(self) -> list[CanonicalEntity]`。

**作用**：读取或组装对应资源；是否纯只读及异常行为需结合下方显式调用与状态写入判断。

**输入与输出**：
- 输入：无业务参数（或仅隐式接收实例）。
- 输出类型：`list[CanonicalEntity]`；具体返回路径见流程步骤。

**处理流程**：
1. 进入上下文 `self.lock`，由上下文管理器控制资源释放或事务范围。
2. 返回 `[CanonicalEntity.model_validate(item) for item in data['entities'].values()]`。

**调用与被调用**：
- `self._read`（调用点 [json_graph.py:98](../../../src/persistence/json_graph.py#L98)）→ [JSONGraphStore._read](json_graph.md)，静态可定位。
- `CanonicalEntity.model_validate`（[json_graph.py:99](../../../src/persistence/json_graph.py#L99)）：来自 `src.domain.CanonicalEntity`；具体实现可能由依赖注入或运行时分派决定。
- `data['entities'].values`（[json_graph.py:99](../../../src/persistence/json_graph.py#L99)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- 静态扫描未定位直接调用方；可能通过路由注册、LangGraph 节点、协议方法或依赖注入动态调用，不据此判断为死代码。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：未见 `raise`；下游异常可能继续上抛。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。
- 恢复/幂等性：仅在代码有检查点、事务、请求编号或显式去重时才成立；此函数不能单凭名称视为可安全重试。


---

# JSONGraphStore.get_entity ⭐⭐

**位置与等级**：[json_graph.py:101](../../../src/persistence/json_graph.py#L101)；局部辅助逻辑，需理解其调用条件与失败传播。

**签名**：`async def get_entity(self, entity_id: str) -> CanonicalEntity | None`。

**作用**：读取或组装对应资源；是否纯只读及异常行为需结合下方显式调用与状态写入判断。

**输入与输出**：
- 输入：`entity_id`（str）。
- 输出类型：`CanonicalEntity | None`；具体返回路径见流程步骤。

**处理流程**：
1. 进入上下文 `self.lock`，由上下文管理器控制资源释放或事务范围。
2. 返回 `CanonicalEntity.model_validate(payload) if payload is not None else None`。

**调用与被调用**：
- `self._read()['entities'].get`（[json_graph.py:103](../../../src/persistence/json_graph.py#L103)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `self._read`（调用点 [json_graph.py:103](../../../src/persistence/json_graph.py#L103)）→ [JSONGraphStore._read](json_graph.md)，静态可定位。
- `CanonicalEntity.model_validate`（[json_graph.py:104](../../../src/persistence/json_graph.py#L104)）：来自 `src.domain.CanonicalEntity`；具体实现可能由依赖注入或运行时分派决定。
- 静态扫描未定位直接调用方；可能通过路由注册、LangGraph 节点、协议方法或依赖注入动态调用，不据此判断为死代码。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：未见 `raise`；下游异常可能继续上抛。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。
- 恢复/幂等性：仅在代码有检查点、事务、请求编号或显式去重时才成立；此函数不能单凭名称视为可安全重试。


---

# JSONGraphStore.search_entities ⭐⭐

**位置与等级**：[json_graph.py:106](../../../src/persistence/json_graph.py#L106)；局部辅助逻辑，需理解其调用条件与失败传播。

**签名**：`async def search_entities(self, vector: list[float], entity_type: str, top_k: int, model_fingerprint: str | None=None) -> list[tuple[CanonicalEntity, float]]`。

**作用**：处理 `search_entities` 对应步骤；下列步骤依据函数体的实际控制流和调用点整理。

**输入与输出**：
- 输入：`vector`（list[float]）；`entity_type`（str）；`top_k`（int；候选召回数量上限）；`model_fingerprint`（str | None；默认 `None`）。
- 输出类型：`list[tuple[CanonicalEntity, float]]`；具体返回路径见流程步骤。

**处理流程**：
1. 检查 `not vector or top_k < 1`；按条件分流，else 分支不存在。
2. 进入上下文 `self.lock`，由上下文管理器控制资源释放或事务范围。
3. 更新 `query_norm`，值来自 `math.sqrt(sum((value * value for value in vector))) or 1.0`。
4. 更新 `matches`，值来自 `[]`。
5. 遍历 `data['entities'].items()`，逐项处理 `(entity_id, payload)`。
6. 返回 `sorted(matches, key=lambda item: (-round(item[1], 12), item[0].id))[:top_k]`。

**关键条件与保护**：
- [json_graph.py:113](../../../src/persistence/json_graph.py#L113)：`not vector or top_k < 1`，不满足时跳过本分支。
- [json_graph.py:122](../../../src/persistence/json_graph.py#L122)：`not entity.active or entity.entity_type != entity_type or embedding_payload is None`，不满足时跳过本分支。
- [json_graph.py:125](../../../src/persistence/json_graph.py#L125)：`len(embedding.vector) != len(vector) or (model_fingerprint is not None and embedding.model_fingerprint != model_fi…`，不满足时跳过本分支。

**调用与被调用**：
- `self._read`（调用点 [json_graph.py:116](../../../src/persistence/json_graph.py#L116)）→ [JSONGraphStore._read](json_graph.md)，静态可定位。
- `math.sqrt`（[json_graph.py:117](../../../src/persistence/json_graph.py#L117)）：来自 `math`；具体实现可能由依赖注入或运行时分派决定。
- `sum`（[json_graph.py:117](../../../src/persistence/json_graph.py#L117)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `data['entities'].items`（[json_graph.py:119](../../../src/persistence/json_graph.py#L119)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `CanonicalEntity.model_validate`（[json_graph.py:120](../../../src/persistence/json_graph.py#L120)）：来自 `src.domain.CanonicalEntity`；具体实现可能由依赖注入或运行时分派决定。
- `data['entity_embeddings'].get`（[json_graph.py:121](../../../src/persistence/json_graph.py#L121)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `EntityEmbedding.model_validate`（[json_graph.py:124](../../../src/persistence/json_graph.py#L124)）：来自 `src.domain.EntityEmbedding`；具体实现可能由依赖注入或运行时分派决定。
- `len`（[json_graph.py:126](../../../src/persistence/json_graph.py#L126)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `zip`（[json_graph.py:133](../../../src/persistence/json_graph.py#L133)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `matches.append`（[json_graph.py:135](../../../src/persistence/json_graph.py#L135)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `max`（[json_graph.py:135](../../../src/persistence/json_graph.py#L135)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `min`（[json_graph.py:135](../../../src/persistence/json_graph.py#L135)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `sorted`（[json_graph.py:136](../../../src/persistence/json_graph.py#L136)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- 静态扫描未定位直接调用方；可能通过路由注册、LangGraph 节点、协议方法或依赖注入动态调用，不据此判断为死代码。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：未见 `raise`；下游异常可能继续上抛。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。
- 恢复/幂等性：仅在代码有检查点、事务、请求编号或显式去重时才成立；此函数不能单凭名称视为可安全重试。


---

# JSONGraphStore.list_entity_embeddings ⭐⭐

**位置与等级**：[json_graph.py:138](../../../src/persistence/json_graph.py#L138)；局部辅助逻辑，需理解其调用条件与失败传播。

**签名**：`async def list_entity_embeddings(self) -> list[EntityEmbedding]`。

**作用**：读取或组装对应资源；是否纯只读及异常行为需结合下方显式调用与状态写入判断。

**输入与输出**：
- 输入：无业务参数（或仅隐式接收实例）。
- 输出类型：`list[EntityEmbedding]`；具体返回路径见流程步骤。

**处理流程**：
1. 进入上下文 `self.lock`，由上下文管理器控制资源释放或事务范围。

**调用与被调用**：
- `self._read()['entity_embeddings'].values`（[json_graph.py:140](../../../src/persistence/json_graph.py#L140)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `self._read`（调用点 [json_graph.py:140](../../../src/persistence/json_graph.py#L140)）→ [JSONGraphStore._read](json_graph.md)，静态可定位。
- `EntityEmbedding.model_validate`（[json_graph.py:141](../../../src/persistence/json_graph.py#L141)）：来自 `src.domain.EntityEmbedding`；具体实现可能由依赖注入或运行时分派决定。
- 静态扫描未定位直接调用方；可能通过路由注册、LangGraph 节点、协议方法或依赖注入动态调用，不据此判断为死代码。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：未见 `raise`；下游异常可能继续上抛。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。
- 恢复/幂等性：仅在代码有检查点、事务、请求编号或显式去重时才成立；此函数不能单凭名称视为可安全重试。


---

# JSONGraphStore.upsert_entity_embeddings ⭐⭐

**位置与等级**：[json_graph.py:143](../../../src/persistence/json_graph.py#L143)；局部辅助逻辑，需理解其调用条件与失败传播。

**签名**：`async def upsert_entity_embeddings(self, embeddings: list[EntityEmbedding]) -> None`。

**作用**：创建、更新或记录相应资源；写入/审计边界以实际调用和状态赋值为准。

**输入与输出**：
- 输入：`embeddings`（list[EntityEmbedding]）。
- 输出类型：`None`；具体返回路径见流程步骤。

**处理流程**：
1. 进入上下文 `self.lock`，由上下文管理器控制资源释放或事务范围。

**关键条件与保护**：
- [json_graph.py:147](../../../src/persistence/json_graph.py#L147)：`unknown`，不满足时跳过本分支。

**调用与被调用**：
- `self._read`（调用点 [json_graph.py:145](../../../src/persistence/json_graph.py#L145)）→ [JSONGraphStore._read](json_graph.md)，静态可定位。
- `set`（[json_graph.py:146](../../../src/persistence/json_graph.py#L146)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `GraphIntegrityError`（调用点 [json_graph.py:148](../../../src/persistence/json_graph.py#L148)）→ [GraphIntegrityError](../core/errors.md)，静态可定位。
- `embedding.model_dump`（[json_graph.py:150](../../../src/persistence/json_graph.py#L150)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `self._write_atomic`（调用点 [json_graph.py:151](../../../src/persistence/json_graph.py#L151)）→ [JSONGraphStore._write_atomic](json_graph.md)，静态可定位。
- 静态扫描未定位直接调用方；可能通过路由注册、LangGraph 节点、协议方法或依赖注入动态调用，不据此判断为死代码。

**状态、副作用与异常**：
- 显式状态/容器赋值：`data['entity_embeddings'][embedding.entity_id]`。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：`GraphIntegrityError(f<字符串常量>)`。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。
- 恢复/幂等性：仅在代码有检查点、事务、请求编号或显式去重时才成立；此函数不能单凭名称视为可安全重试。


---

# JSONGraphStore.list_claims ⭐⭐

**位置与等级**：[json_graph.py:153](../../../src/persistence/json_graph.py#L153)；局部辅助逻辑，需理解其调用条件与失败传播。

**签名**：`async def list_claims(self) -> list[Claim]`。

**作用**：读取或组装对应资源；是否纯只读及异常行为需结合下方显式调用与状态写入判断。

**输入与输出**：
- 输入：无业务参数（或仅隐式接收实例）。
- 输出类型：`list[Claim]`；具体返回路径见流程步骤。

**处理流程**：
1. 进入上下文 `self.lock`，由上下文管理器控制资源释放或事务范围。
2. 返回 `[Claim.model_validate(item) for item in data['claims'].values()]`。

**调用与被调用**：
- `self._read`（调用点 [json_graph.py:155](../../../src/persistence/json_graph.py#L155)）→ [JSONGraphStore._read](json_graph.md)，静态可定位。
- `Claim.model_validate`（[json_graph.py:156](../../../src/persistence/json_graph.py#L156)）：来自 `src.domain.Claim`；具体实现可能由依赖注入或运行时分派决定。
- `data['claims'].values`（[json_graph.py:156](../../../src/persistence/json_graph.py#L156)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- 静态扫描未定位直接调用方；可能通过路由注册、LangGraph 节点、协议方法或依赖注入动态调用，不据此判断为死代码。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：未见 `raise`；下游异常可能继续上抛。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。
- 恢复/幂等性：仅在代码有检查点、事务、请求编号或显式去重时才成立；此函数不能单凭名称视为可安全重试。


---

# JSONGraphStore.latest_revision ⭐⭐

**位置与等级**：[json_graph.py:158](../../../src/persistence/json_graph.py#L158)；局部辅助逻辑，需理解其调用条件与失败传播。

**签名**：`async def latest_revision(self) -> GraphRevision | None`。

**作用**：处理 `latest_revision` 对应步骤；下列步骤依据函数体的实际控制流和调用点整理。

**输入与输出**：
- 输入：无业务参数（或仅隐式接收实例）。
- 输出类型：`GraphRevision | None`；具体返回路径见流程步骤。

**处理流程**：
1. 进入上下文 `self.lock`，由上下文管理器控制资源释放或事务范围。
2. 返回 `GraphRevision.model_validate(revisions[-1]) if revisions else None`。

**调用与被调用**：
- `self._read`（调用点 [json_graph.py:160](../../../src/persistence/json_graph.py#L160)）→ [JSONGraphStore._read](json_graph.md)，静态可定位。
- `GraphRevision.model_validate`（[json_graph.py:161](../../../src/persistence/json_graph.py#L161)）：来自 `src.domain.GraphRevision`；具体实现可能由依赖注入或运行时分派决定。
- 静态扫描未定位直接调用方；可能通过路由注册、LangGraph 节点、协议方法或依赖注入动态调用，不据此判断为死代码。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：未见 `raise`；下游异常可能继续上抛。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。
- 恢复/幂等性：仅在代码有检查点、事务、请求编号或显式去重时才成立；此函数不能单凭名称视为可安全重试。


---

# JSONGraphStore.list_revisions ⭐⭐

**位置与等级**：[json_graph.py:163](../../../src/persistence/json_graph.py#L163)；局部辅助逻辑，需理解其调用条件与失败传播。

**签名**：`async def list_revisions(self, limit: int=50) -> list[GraphRevision]`。

**作用**：读取或组装对应资源；是否纯只读及异常行为需结合下方显式调用与状态写入判断。

**输入与输出**：
- 输入：`limit`（int；默认 `50`；查询或展示的最大条数）。
- 输出类型：`list[GraphRevision]`；具体返回路径见流程步骤。

**处理流程**：
1. 检查 `limit < 1`；按条件分流，else 分支不存在。
2. 进入上下文 `self.lock`，由上下文管理器控制资源释放或事务范围。
3. 返回 `[GraphRevision.model_validate(item) for item in reversed(revisions)]`。

**关键条件与保护**：
- [json_graph.py:164](../../../src/persistence/json_graph.py#L164)：`limit < 1`，不满足时跳过本分支。

**调用与被调用**：
- `self._read`（调用点 [json_graph.py:167](../../../src/persistence/json_graph.py#L167)）→ [JSONGraphStore._read](json_graph.md)，静态可定位。
- `GraphRevision.model_validate`（[json_graph.py:168](../../../src/persistence/json_graph.py#L168)）：来自 `src.domain.GraphRevision`；具体实现可能由依赖注入或运行时分派决定。
- `reversed`（[json_graph.py:168](../../../src/persistence/json_graph.py#L168)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- 静态扫描未定位直接调用方；可能通过路由注册、LangGraph 节点、协议方法或依赖注入动态调用，不据此判断为死代码。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：未见 `raise`；下游异常可能继续上抛。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。
- 恢复/幂等性：仅在代码有检查点、事务、请求编号或显式去重时才成立；此函数不能单凭名称视为可安全重试。


---

# JSONGraphStore.get_claim ⭐⭐

**位置与等级**：[json_graph.py:170](../../../src/persistence/json_graph.py#L170)；局部辅助逻辑，需理解其调用条件与失败传播。

**签名**：`async def get_claim(self, claim_id: str) -> Claim | None`。

**作用**：读取或组装对应资源；是否纯只读及异常行为需结合下方显式调用与状态写入判断。

**输入与输出**：
- 输入：`claim_id`（str）。
- 输出类型：`Claim | None`；具体返回路径见流程步骤。

**处理流程**：
1. 进入上下文 `self.lock`，由上下文管理器控制资源释放或事务范围。
2. 返回 `Claim.model_validate(payload) if payload is not None else None`。

**调用与被调用**：
- `self._read()['claims'].get`（[json_graph.py:172](../../../src/persistence/json_graph.py#L172)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `self._read`（调用点 [json_graph.py:172](../../../src/persistence/json_graph.py#L172)）→ [JSONGraphStore._read](json_graph.md)，静态可定位。
- `Claim.model_validate`（[json_graph.py:173](../../../src/persistence/json_graph.py#L173)）：来自 `src.domain.Claim`；具体实现可能由依赖注入或运行时分派决定。
- 静态扫描未定位直接调用方；可能通过路由注册、LangGraph 节点、协议方法或依赖注入动态调用，不据此判断为死代码。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：未见 `raise`；下游异常可能继续上抛。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。
- 恢复/幂等性：仅在代码有检查点、事务、请求编号或显式去重时才成立；此函数不能单凭名称视为可安全重试。


---

# JSONGraphStore.get_evidence ⭐⭐

**位置与等级**：[json_graph.py:175](../../../src/persistence/json_graph.py#L175)；局部辅助逻辑，需理解其调用条件与失败传播。

**签名**：`async def get_evidence(self, evidence_id: str) -> EvidenceRef | None`。

**作用**：读取或组装对应资源；是否纯只读及异常行为需结合下方显式调用与状态写入判断。

**输入与输出**：
- 输入：`evidence_id`（str）。
- 输出类型：`EvidenceRef | None`；具体返回路径见流程步骤。

**处理流程**：
1. 进入上下文 `self.lock`，由上下文管理器控制资源释放或事务范围。
2. 返回 `EvidenceRef.model_validate(payload) if payload is not None else None`。

**调用与被调用**：
- `self._read()['evidence'].get`（[json_graph.py:177](../../../src/persistence/json_graph.py#L177)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `self._read`（调用点 [json_graph.py:177](../../../src/persistence/json_graph.py#L177)）→ [JSONGraphStore._read](json_graph.md)，静态可定位。
- `EvidenceRef.model_validate`（[json_graph.py:178](../../../src/persistence/json_graph.py#L178)）：来自 `src.domain.EvidenceRef`；具体实现可能由依赖注入或运行时分派决定。
- 静态扫描未定位直接调用方；可能通过路由注册、LangGraph 节点、协议方法或依赖注入动态调用，不据此判断为死代码。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：未见 `raise`；下游异常可能继续上抛。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。
- 恢复/幂等性：仅在代码有检查点、事务、请求编号或显式去重时才成立；此函数不能单凭名称视为可安全重试。


---

# JSONGraphStore.get_neighborhood ⭐⭐

**位置与等级**：[json_graph.py:180](../../../src/persistence/json_graph.py#L180)；局部辅助逻辑，需理解其调用条件与失败传播。

**签名**：`async def get_neighborhood(self, entity_id: str, depth: int=1) -> GraphNeighborhood`。

**作用**：读取或组装对应资源；是否纯只读及异常行为需结合下方显式调用与状态写入判断。

**输入与输出**：
- 输入：`entity_id`（str）；`depth`（int；默认 `1`）。
- 输出类型：`GraphNeighborhood`；具体返回路径见流程步骤。

**处理流程**：
1. 检查 `depth < 1 or depth > 3`；按条件分流，else 分支不存在。
2. 进入上下文 `self.lock`，由上下文管理器控制资源释放或事务范围。
3. 检查 `entity_id not in data['entities']`；按条件分流，else 分支不存在。
4. 更新 `seen`，值来自 `{entity_id}`。
5. 更新 `frontier`，值来自 `{entity_id}`。
6. 更新 `selected_claims`，值来自 `{}`。
7. 遍历 `range(depth)`，逐项处理 `_`。
8. 更新 `entities`，值来自 `[CanonicalEntity.model_validate(data['entities'][item]) for item in sorted(seen)]`。
9. 返回 `GraphNeighborhood(center_entity_id=entity_id, depth=depth, entities=entities, claims=list(selected_claim…`。

**关键条件与保护**：
- [json_graph.py:181](../../../src/persistence/json_graph.py#L181)：`depth < 1 or depth > 3`，不满足时跳过本分支。
- [json_graph.py:185](../../../src/persistence/json_graph.py#L185)：`entity_id not in data['entities']`，不满足时跳过本分支。
- [json_graph.py:194](../../../src/persistence/json_graph.py#L194)：`claim.tx_to is not None`，不满足时跳过本分支。
- [json_graph.py:197](../../../src/persistence/json_graph.py#L197)：`claim.object_entity_id`，不满足时跳过本分支。
- [json_graph.py:199](../../../src/persistence/json_graph.py#L199)：`endpoints & frontier`，不满足时跳过本分支。
- [json_graph.py:204](../../../src/persistence/json_graph.py#L204)：`not frontier`，不满足时跳过本分支。

**调用与被调用**：
- `ValueError`（[json_graph.py:182](../../../src/persistence/json_graph.py#L182)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `self._read`（调用点 [json_graph.py:184](../../../src/persistence/json_graph.py#L184)）→ [JSONGraphStore._read](json_graph.md)，静态可定位。
- `KeyError`（[json_graph.py:186](../../../src/persistence/json_graph.py#L186)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `range`（[json_graph.py:190](../../../src/persistence/json_graph.py#L190)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `set`（[json_graph.py:191](../../../src/persistence/json_graph.py#L191)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `data['claims'].values`（[json_graph.py:192](../../../src/persistence/json_graph.py#L192)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `Claim.model_validate`（[json_graph.py:193](../../../src/persistence/json_graph.py#L193)）：来自 `src.domain.Claim`；具体实现可能由依赖注入或运行时分派决定。
- `endpoints.add`（[json_graph.py:198](../../../src/persistence/json_graph.py#L198)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `next_frontier.update`（[json_graph.py:201](../../../src/persistence/json_graph.py#L201)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `seen.update`（[json_graph.py:202](../../../src/persistence/json_graph.py#L202)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `CanonicalEntity.model_validate`（[json_graph.py:206](../../../src/persistence/json_graph.py#L206)）：来自 `src.domain.CanonicalEntity`；具体实现可能由依赖注入或运行时分派决定。
- `sorted`（[json_graph.py:206](../../../src/persistence/json_graph.py#L206)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `GraphNeighborhood`（[json_graph.py:207](../../../src/persistence/json_graph.py#L207)）：来自 `src.domain.GraphNeighborhood`；具体实现可能由依赖注入或运行时分派决定。
- `list`（[json_graph.py:211](../../../src/persistence/json_graph.py#L211)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `selected_claims.values`（[json_graph.py:211](../../../src/persistence/json_graph.py#L211)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- 静态扫描未定位直接调用方；可能通过路由注册、LangGraph 节点、协议方法或依赖注入动态调用，不据此判断为死代码。

**状态、副作用与异常**：
- 显式状态/容器赋值：`selected_claims[claim.id]`。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：`ValueError(<字符串常量>)`、`KeyError(f<字符串常量>)`。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。
- 恢复/幂等性：仅在代码有检查点、事务、请求编号或显式去重时才成立；此函数不能单凭名称视为可安全重试。


---

# JSONGraphStore._merge_claim ⭐⭐

**位置与等级**：[json_graph.py:215](../../../src/persistence/json_graph.py#L215)；局部辅助逻辑，需理解其调用条件与失败传播。

**签名**：`def _merge_claim(current: dict[str, Any], incoming: Claim) -> Claim`。

**装饰器/路由**：`staticmethod`。

**作用**：内部辅助步骤；将参数转换为本模块所需的中间对象或操作结果。

**输入与输出**：
- 输入：`current`（dict[str, Any]）；`incoming`（Claim）。
- 输出类型：`Claim`；具体返回路径见流程步骤。

**处理流程**：
1. 更新 `previous`，值来自 `Claim.model_validate(current)`。
2. 更新 `merged`，值来自 `incoming.model_copy(deep=True)`。
3. 更新 `merged.evidence_ids`，值来自 `sorted(set(previous.evidence_ids + incoming.evidence_ids))`。
4. 更新 `merged.source_candidate_ids`，值来自 `sorted(set(previous.source_candidate_ids + incoming.source_candidate_ids))`。
5. 更新 `merged.confidence`，值来自 `max(previous.confidence, incoming.confidence)`。
6. 更新 `merged.source_run_ids`，值来自 `sorted(set(previous.source_run_ids + incoming.source_run_ids))`。
7. 返回 `merged`。

**调用与被调用**：
- `Claim.model_validate`（[json_graph.py:216](../../../src/persistence/json_graph.py#L216)）：来自 `src.domain.Claim`；具体实现可能由依赖注入或运行时分派决定。
- `incoming.model_copy`（[json_graph.py:217](../../../src/persistence/json_graph.py#L217)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `sorted`（[json_graph.py:218](../../../src/persistence/json_graph.py#L218)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `set`（[json_graph.py:218](../../../src/persistence/json_graph.py#L218)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `max`（[json_graph.py:222](../../../src/persistence/json_graph.py#L222)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- 静态可定位的调用方：[JSONGraphStore._apply](json_graph.md)。

**状态、副作用与异常**：
- 显式状态/容器赋值：`merged.evidence_ids`、`merged.source_candidate_ids`、`merged.confidence`、`merged.source_run_ids`。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：未见 `raise`；下游异常可能继续上抛。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。
- 恢复/幂等性：仅在代码有检查点、事务、请求编号或显式去重时才成立；此函数不能单凭名称视为可安全重试。


---

# JSONGraphStore._apply ⭐⭐⭐⭐⭐

**位置与等级**：[json_graph.py:226](../../../src/persistence/json_graph.py#L226)；位于工作流推进、硬校验或原子事务的关键边界；错误可能影响审核停顿或图状态。

**签名**：`def _apply(self, data: dict[str, Any], transaction: GraphCommit) -> tuple[dict[str, Any], bool]`。

**作用**：内部辅助步骤；将参数转换为本模块所需的中间对象或操作结果。

**输入与输出**：
- 输入：`data`（dict[str, Any]）；`transaction`（GraphCommit；待提交 GraphCommit；必须在最终写入边界重新校验）。
- 输出类型：`tuple[dict[str, Any], bool]`；具体返回路径见流程步骤。

**处理流程**：
1. 更新 `revisions`，值来自 `data['revisions']`。
2. 更新 `existing_revision`，值来自 `next((item for item in revisions if item['id'] == transaction.revision.id), None)`。
3. 更新 `revision_payload`，值来自 `transaction.revision.model_dump(mode='json')`。
4. 检查 `existing_revision is not None`；按条件分流，else 分支不存在。
5. 更新 `latest_id`，值来自 `revisions[-1]['id'] if revisions else None`。
6. 检查 `transaction.revision.parent_id != latest_id`；按条件分流，else 分支不存在。
7. 遍历 `transaction.documents`，逐项处理 `document`。
8. 遍历 `transaction.evidence`，逐项处理 `evidence`。
9. 遍历 `transaction.entities`，逐项处理 `entity`。
10. 遍历 `transaction.entity_operations`，逐项处理 `operation`。
11. 遍历 `transaction.entity_embeddings`，逐项处理 `embedding`。
12. 遍历 `transaction.claims`，逐项处理 `claim`。
13. 遍历 `transaction.conflicts`，逐项处理 `conflict`。
14. 更新 `known_entities`，值来自 `set(data['entities'])`。
15. 更新 `known_claims`，值来自 `set(data['claims'])`。
16. 更新 `known_conflicts`，值来自 `set(data['conflicts'])`。
17. 更新 `known_evidence`，值来自 `set(data['evidence'])`。
18. 检查 `not {item.entity_id for item in transaction.entity_embeddings} <= known_entities`；按条件分流，else 分支不存在。
19. 遍历 `transaction.entity_operations`，逐项处理 `operation`。
20. 遍历 `transaction.claims`，逐项处理 `claim`。
21. 检查 `not set(transaction.revision.entity_ids) <= known_entities`；按条件分流，else 分支不存在。
22. 检查 `not set(transaction.revision.claim_ids) <= known_claims`；按条件分流，else 分支不存在。
23. 检查 `not set(transaction.revision.conflict_ids) <= known_conflicts`；按条件分流，else 分支不存在。
24. 遍历 `transaction.conflicts`，逐项处理 `conflict`。
后续还有 2 个语句级步骤，见源码对应行；这里优先保留主要控制流。

**关键条件与保护**：
- [json_graph.py:232](../../../src/persistence/json_graph.py#L232)：`existing_revision is not None`，不满足时跳过本分支。
- [json_graph.py:233](../../../src/persistence/json_graph.py#L233)：`GraphRevision.model_validate(existing_revision) != transaction.revision`，不满足时跳过本分支。
- [json_graph.py:240](../../../src/persistence/json_graph.py#L240)：`transaction.revision.parent_id != latest_id`，不满足时跳过本分支。
- [json_graph.py:249](../../../src/persistence/json_graph.py#L249)：`evidence.document_id not in data['documents']`，不满足时跳过本分支。
- [json_graph.py:256](../../../src/persistence/json_graph.py#L256)：`previous is not None and CanonicalEntity.model_validate(previous).embedding_source() != entity.embedding_source()`，不满足时跳过本分支。
- [json_graph.py:267](../../../src/persistence/json_graph.py#L267)：`not claim.evidence_ids`，不满足时跳过本分支。
- [json_graph.py:270](../../../src/persistence/json_graph.py#L270)：`current and transaction.correction_guard is None`，不满足时跳过本分支。
- [json_graph.py:280](../../../src/persistence/json_graph.py#L280)：`not {item.entity_id for item in transaction.entity_embeddings} <= known_entities`，不满足时跳过本分支。
- [json_graph.py:283](../../../src/persistence/json_graph.py#L283)：`not set(operation.source_entity_ids + operation.target_entity_ids) <= known_entities`，不满足时跳过本分支。
- [json_graph.py:289](../../../src/persistence/json_graph.py#L289)：`claim.object_entity_id`，不满足时跳过本分支。
- [json_graph.py:291](../../../src/persistence/json_graph.py#L291)：`not entity_refs <= known_entities`，不满足时跳过本分支。
- [json_graph.py:293](../../../src/persistence/json_graph.py#L293)：`transaction.evidence and (not set(claim.evidence_ids) <= known_evidence)`，不满足时跳过本分支。
- 另有 4 个条件判断，参见源码；不要将本列表当作全部分支。

**调用与被调用**：
- `next`（[json_graph.py:228](../../../src/persistence/json_graph.py#L228)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `transaction.revision.model_dump`（[json_graph.py:231](../../../src/persistence/json_graph.py#L231)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `GraphRevision.model_validate`（[json_graph.py:233](../../../src/persistence/json_graph.py#L233)）：来自 `src.domain.GraphRevision`；具体实现可能由依赖注入或运行时分派决定。
- `GraphIntegrityError`（调用点 [json_graph.py:234](../../../src/persistence/json_graph.py#L234)）→ [GraphIntegrityError](../core/errors.md)，静态可定位。
- `document.model_dump`（[json_graph.py:247](../../../src/persistence/json_graph.py#L247)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `evidence.model_dump`（[json_graph.py:253](../../../src/persistence/json_graph.py#L253)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `data['entities'].get`（[json_graph.py:255](../../../src/persistence/json_graph.py#L255)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `CanonicalEntity.model_validate(previous).embedding_source`（[json_graph.py:257](../../../src/persistence/json_graph.py#L257)）：来自 `src.domain.CanonicalEntity`；具体实现可能由依赖注入或运行时分派决定。
- `CanonicalEntity.model_validate`（[json_graph.py:257](../../../src/persistence/json_graph.py#L257)）：来自 `src.domain.CanonicalEntity`；具体实现可能由依赖注入或运行时分派决定。
- `entity.embedding_source`（[json_graph.py:258](../../../src/persistence/json_graph.py#L258)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `data['entity_embeddings'].pop`（[json_graph.py:260](../../../src/persistence/json_graph.py#L260)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `entity.model_dump`（[json_graph.py:261](../../../src/persistence/json_graph.py#L261)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `operation.model_dump`（[json_graph.py:263](../../../src/persistence/json_graph.py#L263)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `embedding.model_dump`（[json_graph.py:265](../../../src/persistence/json_graph.py#L265)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `EvidenceRequiredError`（调用点 [json_graph.py:268](../../../src/persistence/json_graph.py#L268)）→ [EvidenceRequiredError](../core/errors.md)，静态可定位。
- `data['claims'].get`（[json_graph.py:269](../../../src/persistence/json_graph.py#L269)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `self._merge_claim`（调用点 [json_graph.py:271](../../../src/persistence/json_graph.py#L271)）→ [JSONGraphStore._merge_claim](json_graph.md)，静态可定位。
- `claim.model_dump`（[json_graph.py:272](../../../src/persistence/json_graph.py#L272)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `conflict.model_dump`（[json_graph.py:274](../../../src/persistence/json_graph.py#L274)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `set`（[json_graph.py:276](../../../src/persistence/json_graph.py#L276)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `entity_refs.add`（[json_graph.py:290](../../../src/persistence/json_graph.py#L290)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `revisions.append`（[json_graph.py:307](../../../src/persistence/json_graph.py#L307)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- 静态可定位的调用方：[JSONGraphStore.commit](json_graph.md)。

**状态、副作用与异常**：
- 显式状态/容器赋值：`data['documents'][document.id]`、`data['evidence'][evidence.id]`、`data['entities'][entity.id]`、`data['entity_operations'][operation.id]`、`data['entity_embeddings'][embedding.entity_id]`、`data['claims'][claim.id]`、`data['conflicts'][conflict.id]`。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：`GraphIntegrityError(f<字符串常量>)`、`EvidenceRequiredError(f<字符串常量>)`、`GraphIntegrityError(<字符串常量>)`。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。
- 恢复/幂等性：仅在代码有检查点、事务、请求编号或显式去重时才成立；此函数不能单凭名称视为可安全重试。


---

# JSONGraphStore.commit ⭐⭐⭐⭐⭐

**位置与等级**：[json_graph.py:310](../../../src/persistence/json_graph.py#L310)；位于工作流推进、硬校验或原子事务的关键边界；错误可能影响审核停顿或图状态。

**签名**：`async def commit(self, transaction: GraphCommit) -> None`。

**作用**：执行图谱提交；这是写入边界，需核对父版本、引用完整性和原子性。

**输入与输出**：
- 输入：`transaction`（GraphCommit；待提交 GraphCommit；必须在最终写入边界重新校验）。
- 输出类型：`None`；具体返回路径见流程步骤。

**处理流程**：
1. 调用 `bind_commit_provenance`，结果未直接赋值。
2. 更新 `transaction`，值来自 `transaction.model_copy(deep=True)`。
3. 进入上下文 `self.lock`，由上下文管理器控制资源释放或事务范围。

**关键条件与保护**：
- [json_graph.py:315](../../../src/persistence/json_graph.py#L315)：`transaction.revision.id not in {r['id'] for r in data['revisions']}`，不满足时跳过本分支。
- [json_graph.py:324](../../../src/persistence/json_graph.py#L324)：`is_noop`，不满足时跳过本分支。

**调用与被调用**：
- `bind_commit_provenance`（调用点 [json_graph.py:311](../../../src/persistence/json_graph.py#L311)）→ [bind_commit_provenance](../governance/validation/context.md)，静态可定位。
- `transaction.model_copy`（[json_graph.py:312](../../../src/persistence/json_graph.py#L312)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `self._read`（调用点 [json_graph.py:314](../../../src/persistence/json_graph.py#L314)）→ [JSONGraphStore._read](json_graph.md)，静态可定位。
- `verify_correction`（调用点 [json_graph.py:316](../../../src/persistence/json_graph.py#L316)）→ [verify_correction](../governance/review_guards.md)，静态可定位。
- `data['entities'].items`（[json_graph.py:319](../../../src/persistence/json_graph.py#L319)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `data['claims'].items`（[json_graph.py:320](../../../src/persistence/json_graph.py#L320)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `self._apply`（调用点 [json_graph.py:323](../../../src/persistence/json_graph.py#L323)）→ [JSONGraphStore._apply](json_graph.md)，静态可定位。
- `deepcopy`（[json_graph.py:323](../../../src/persistence/json_graph.py#L323)）：来自 `copy.deepcopy`；具体实现可能由依赖注入或运行时分派决定。
- `final_state_commit`（调用点 [json_graph.py:326](../../../src/persistence/json_graph.py#L326)）→ [final_state_commit](../governance/validation/context.md)，静态可定位。
- `Claim.model_validate`（[json_graph.py:328](../../../src/persistence/json_graph.py#L328)）：来自 `src.domain.Claim`；具体实现可能由依赖注入或运行时分派决定。
- `updated['claims'].items`（[json_graph.py:328](../../../src/persistence/json_graph.py#L328)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `CanonicalEntity.model_validate`（[json_graph.py:329](../../../src/persistence/json_graph.py#L329)）：来自 `src.domain.CanonicalEntity`；具体实现可能由依赖注入或运行时分派决定。
- `GraphRevision.model_validate`（[json_graph.py:330](../../../src/persistence/json_graph.py#L330)）：来自 `src.domain.GraphRevision`；具体实现可能由依赖注入或运行时分派决定。
- `reversed`（[json_graph.py:330](../../../src/persistence/json_graph.py#L330)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `ValidationService().commit`（[json_graph.py:332](../../../src/persistence/json_graph.py#L332)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `ValidationService`（[json_graph.py:332](../../../src/persistence/json_graph.py#L332)）：来自 `src.governance.validation.ValidationService`；具体实现可能由依赖注入或运行时分派决定。
- `updated['entities'].items`（[json_graph.py:334](../../../src/persistence/json_graph.py#L334)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `EvidenceRef.model_validate`（[json_graph.py:335](../../../src/persistence/json_graph.py#L335)）：来自 `src.domain.EvidenceRef`；具体实现可能由依赖注入或运行时分派决定。
- `updated['evidence'].items`（[json_graph.py:335](../../../src/persistence/json_graph.py#L335)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `set`（[json_graph.py:336](../../../src/persistence/json_graph.py#L336)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `self._write_atomic`（调用点 [json_graph.py:339](../../../src/persistence/json_graph.py#L339)）→ [JSONGraphStore._write_atomic](json_graph.md)，静态可定位。
- 静态扫描未定位直接调用方；可能通过路由注册、LangGraph 节点、协议方法或依赖注入动态调用，不据此判断为死代码。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：未见 `raise`；下游异常可能继续上抛。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。
- 恢复/幂等性：仅在代码有检查点、事务、请求编号或显式去重时才成立；此函数不能单凭名称视为可安全重试。


---

# JSONGraphStore.diff_revisions ⭐⭐

**位置与等级**：[json_graph.py:341](../../../src/persistence/json_graph.py#L341)；局部辅助逻辑，需理解其调用条件与失败传播。

**签名**：`async def diff_revisions(self, from_id: str, to_id: str) -> RevisionDiff`。

**作用**：比较两个版本间的资源变化，不修改图谱。

**输入与输出**：
- 输入：`from_id`（str）；`to_id`（str）。
- 输出类型：`RevisionDiff`；具体返回路径见流程步骤。

**处理流程**：
1. 进入上下文 `self.lock`，由上下文管理器控制资源释放或事务范围。
2. 更新 `positions`，值来自 `{revision.id: index for index, revision in enumerate(revisions)}`。
3. 检查 `from_id not in positions or to_id not in positions`；按条件分流，else 分支不存在。
4. 检查 `positions[from_id] > positions[to_id]`；按条件分流，else 分支不存在。
5. 更新 `selected`，值来自 `revisions[positions[from_id] + 1:positions[to_id] + 1]`。
6. 返回 `RevisionDiff(from_revision_id=from_id, to_revision_id=to_id, changes=[change for revision in selected fo…`。

**关键条件与保护**：
- [json_graph.py:345](../../../src/persistence/json_graph.py#L345)：`from_id not in positions or to_id not in positions`，不满足时跳过本分支。
- [json_graph.py:347](../../../src/persistence/json_graph.py#L347)：`positions[from_id] > positions[to_id]`，不满足时跳过本分支。

**调用与被调用**：
- `GraphRevision.model_validate`（[json_graph.py:343](../../../src/persistence/json_graph.py#L343)）：来自 `src.domain.GraphRevision`；具体实现可能由依赖注入或运行时分派决定。
- `self._read`（调用点 [json_graph.py:343](../../../src/persistence/json_graph.py#L343)）→ [JSONGraphStore._read](json_graph.md)，静态可定位。
- `enumerate`（[json_graph.py:344](../../../src/persistence/json_graph.py#L344)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `KeyError`（[json_graph.py:346](../../../src/persistence/json_graph.py#L346)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `ValueError`（[json_graph.py:348](../../../src/persistence/json_graph.py#L348)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `RevisionDiff`（[json_graph.py:350](../../../src/persistence/json_graph.py#L350)）：来自 `src.domain.RevisionDiff`；具体实现可能由依赖注入或运行时分派决定。
- `any`（[json_graph.py:354](../../../src/persistence/json_graph.py#L354)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `sorted`（[json_graph.py:355](../../../src/persistence/json_graph.py#L355)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- 静态扫描未定位直接调用方；可能通过路由注册、LangGraph 节点、协议方法或依赖注入动态调用，不据此判断为死代码。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：`KeyError(<字符串常量>)`、`ValueError(<字符串常量>)`。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。
- 恢复/幂等性：仅在代码有检查点、事务、请求编号或显式去重时才成立；此函数不能单凭名称视为可安全重试。


---

# JSONGraphStore.rollback_revision ⭐⭐⭐⭐⭐

**位置与等级**：[json_graph.py:360](../../../src/persistence/json_graph.py#L360)；位于工作流推进、硬校验或原子事务的关键边界；错误可能影响审核停顿或图状态。

**签名**：`async def rollback_revision(self, revision_id: str) -> GraphRevision`。

**作用**：构造补偿版本恢复目标状态，保留历史记录而不是删除 Revision。

**输入与输出**：
- 输入：`revision_id`（str）。
- 输出类型：`GraphRevision`；具体返回路径见流程步骤。

**处理流程**：
1. 进入上下文 `self.lock`，由上下文管理器控制资源释放或事务范围。

**关键条件与保护**：
- [json_graph.py:369](../../../src/persistence/json_graph.py#L369)：`target_payload is None`，不满足时跳过本分支。
- [json_graph.py:372](../../../src/persistence/json_graph.py#L372)：`not target.changes`，不满足时跳过本分支。
- [json_graph.py:377](../../../src/persistence/json_graph.py#L377)：`latest.run_id == f<字符串常量>`，不满足时跳过本分支。
- [json_graph.py:386](../../../src/persistence/json_graph.py#L386)：`data[buckets[change.resource_type]].get(change.resource_id) != change.after`，不满足时跳过本分支。
- [json_graph.py:409](../../../src/persistence/json_graph.py#L409)：`change.action == 'create'`，不满足时有 else 分支。
- [json_graph.py:410](../../../src/persistence/json_graph.py#L410)：`change.resource_type == 'claim' and current is not None`，不满足时有 else 分支。
- [json_graph.py:412](../../../src/persistence/json_graph.py#L412)：`change.resource_type == 'entity' and current is not None`，不满足时有 else 分支。
- [json_graph.py:420](../../../src/persistence/json_graph.py#L420)：`active_claims`，不满足时跳过本分支。
- [json_graph.py:425](../../../src/persistence/json_graph.py#L425)：`change.resource_type == 'conflict' and current is not None`，不满足时有 else 分支。
- [json_graph.py:427](../../../src/persistence/json_graph.py#L427)：`change.resource_type == 'entity_operation' and current is not None`，不满足时跳过本分支。
- [json_graph.py:438](../../../src/persistence/json_graph.py#L438)：`change.before is not None`，不满足时跳过本分支。
- [json_graph.py:468](../../../src/persistence/json_graph.py#L468)：`existing is not None`，不满足时跳过本分支。

**调用与被调用**：
- `self._read`（调用点 [json_graph.py:362](../../../src/persistence/json_graph.py#L362)）→ [JSONGraphStore._read](json_graph.md)，静态可定位。
- `CanonicalEntity.model_validate`（[json_graph.py:364](../../../src/persistence/json_graph.py#L364)）：来自 `src.domain.CanonicalEntity`；具体实现可能由依赖注入或运行时分派决定。
- `data['entities'].items`（[json_graph.py:364](../../../src/persistence/json_graph.py#L364)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `next`（[json_graph.py:366](../../../src/persistence/json_graph.py#L366)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `KeyError`（[json_graph.py:370](../../../src/persistence/json_graph.py#L370)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `GraphRevision.model_validate`（[json_graph.py:371](../../../src/persistence/json_graph.py#L371)）：来自 `src.domain.GraphRevision`；具体实现可能由依赖注入或运行时分派决定。
- `GraphIntegrityError`（调用点 [json_graph.py:373](../../../src/persistence/json_graph.py#L373)）→ [GraphIntegrityError](../core/errors.md)，静态可定位。
- `data[buckets[change.resource_type]].get`（[json_graph.py:386](../../../src/persistence/json_graph.py#L386)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `datetime.now`（[json_graph.py:388](../../../src/persistence/json_graph.py#L388)）：来自 `datetime.datetime`；具体实现可能由依赖注入或运行时分派决定。
- `sorted`（[json_graph.py:396](../../../src/persistence/json_graph.py#L396)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `reversed`（[json_graph.py:397](../../../src/persistence/json_graph.py#L397)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `bucket.get`（[json_graph.py:408](../../../src/persistence/json_graph.py#L408)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `timestamp.isoformat().replace`（[json_graph.py:411](../../../src/persistence/json_graph.py#L411)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `timestamp.isoformat`（[json_graph.py:411](../../../src/persistence/json_graph.py#L411)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `data['claims'].values`（[json_graph.py:415](../../../src/persistence/json_graph.py#L415)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `claim.get`（[json_graph.py:416](../../../src/persistence/json_graph.py#L416)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `inverse.append`（[json_graph.py:429](../../../src/persistence/json_graph.py#L429)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `GraphChange`（[json_graph.py:430](../../../src/persistence/json_graph.py#L430)）：来自 `src.domain.GraphChange`；具体实现可能由依赖注入或运行时分派决定。
- `deepcopy`（[json_graph.py:434](../../../src/persistence/json_graph.py#L434)）：来自 `copy.deepcopy`；具体实现可能由依赖注入或运行时分派决定。
- `GraphRevision`（[json_graph.py:449](../../../src/persistence/json_graph.py#L449)）：来自 `src.domain.GraphRevision`；具体实现可能由依赖注入或运行时分派决定。
- `stable_id`（调用点 [json_graph.py:450](../../../src/persistence/json_graph.py#L450)）→ [stable_id](../core/ids.md)，静态可定位。
- `Claim.model_validate`（[json_graph.py:471](../../../src/persistence/json_graph.py#L471)）：来自 `src.domain.Claim`；具体实现可能由依赖注入或运行时分派决定。
- `context_for_claims`（调用点 [json_graph.py:475](../../../src/persistence/json_graph.py#L475)）→ [context_for_claims](../governance/validation/context.md)，静态可定位。
- `GraphCommit`（[json_graph.py:480](../../../src/persistence/json_graph.py#L480)）：来自 `src.domain.GraphCommit`；具体实现可能由依赖注入或运行时分派决定。
- `final_state_commit`（调用点 [json_graph.py:489](../../../src/persistence/json_graph.py#L489)）→ [final_state_commit](../governance/validation/context.md)，静态可定位。
- `data['claims'].items`（[json_graph.py:491](../../../src/persistence/json_graph.py#L491)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `bind_commit_provenance`（调用点 [json_graph.py:495](../../../src/persistence/json_graph.py#L495)）→ [bind_commit_provenance](../governance/validation/context.md)，静态可定位。
- `ValidationService().commit`（[json_graph.py:496](../../../src/persistence/json_graph.py#L496)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `ValidationService`（[json_graph.py:496](../../../src/persistence/json_graph.py#L496)）：来自 `src.governance.validation.ValidationService`；具体实现可能由依赖注入或运行时分派决定。
- `EvidenceRef.model_validate`（[json_graph.py:499](../../../src/persistence/json_graph.py#L499)）：来自 `src.domain.EvidenceRef`；具体实现可能由依赖注入或运行时分派决定。
- 此处列出前 30 个不同调用表达式，另有 5 个，需按源码继续追踪。
- 静态扫描未定位直接调用方；可能通过路由注册、LangGraph 节点、协议方法或依赖注入动态调用，不据此判断为死代码。

**状态、副作用与异常**：
- 显式状态/容器赋值：`current['tx_to']`、`current['active']`、`current['status']`、`bucket[change.resource_id]`、`compensation.validation_context`。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：`KeyError(f<字符串常量>)`、`GraphIntegrityError(<字符串常量>)`、`GraphIntegrityError(f<字符串常量>)`。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。
- 恢复/幂等性：仅在代码有检查点、事务、请求编号或显式去重时才成立；此函数不能单凭名称视为可安全重试。


---

# JSONGraphStore.close ⭐⭐

**位置与等级**：[json_graph.py:507](../../../src/persistence/json_graph.py#L507)；局部辅助逻辑，需理解其调用条件与失败传播。

**签名**：`async def close(self) -> None`。

**作用**：释放该对象管理的外部资源；重复调用是否安全取决于实现。

**输入与输出**：
- 输入：无业务参数（或仅隐式接收实例）。
- 输出类型：`None`；具体返回路径见流程步骤。

**处理流程**：
1. 返回 `None`。

**调用与被调用**：
- 无显式函数调用，或仅声明协议/常量。
- 静态扫描未定位直接调用方；可能通过路由注册、LangGraph 节点、协议方法或依赖注入动态调用，不据此判断为死代码。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：未见 `raise`；下游异常可能继续上抛。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。
- 恢复/幂等性：仅在代码有检查点、事务、请求编号或显式去重时才成立；此函数不能单凭名称视为可安全重试。


---
