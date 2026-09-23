源码：[file_evidence.py:1](../../../src/persistence/file_evidence.py#L1) | 基准：`dev/v0.10@f2f34d7` | 本文件符号数：18

**模块职责**：Immutable content-addressed evidence storage.
**在系统中的位置**：图、证据、运行、审计、审核与案例的持久化；JSON/Neo4j 提供同一存储协议。
**直接依赖**：[src.core.errors](../core/errors.md)、[src.core.ids](../core/ids.md)、[src.domain](../domain/__init__.md)；外部/标准库：`PIL`、`__future__`、`hashlib`、`io`、`orjson`、`os`、`pathlib`、`pymupdf`、`shutil`、`typing`、`uuid`。
**主要调用方（静态导入）**：[persistence/__init__.py](__init__.md)、[persistence/legacy_evidence.py](legacy_evidence.md)。
**阅读提示**：下列流程根据当前源码控制流整理；`self`/接口对象的实际类型可能在运行时注入，未能静态解析的调用会明确标注。链接指向源码行或对应讲解文件。

---

# FileEvidenceStore ⭐⭐⭐⭐

**位置与等级**：[file_evidence.py:22](../../../src/persistence/file_evidence.py#L22)；承担主要 Agent、应用服务或审核/执行入口，跨模块影响显著。

**职责**：存储接口或实现；方法决定数据读取、持久化与并发边界。基类：无显式基类。

**字段与类级约束**：
- 类体未直接声明字段；实例状态请看 `__init__` 及方法中的赋值。

**内部成员**：`FileEvidenceStore.__init__`、`FileEvidenceStore._blob_path`、`FileEvidenceStore._ref_path`、`FileEvidenceStore._atomic_write`、`FileEvidenceStore._store_blob`、`FileEvidenceStore._store_blob_bytes`、`FileEvidenceStore._serialize_ref`、`FileEvidenceStore._load_ref`、`FileEvidenceStore.put_document`、`FileEvidenceStore.put_blob`、`FileEvidenceStore.put_ref`、`FileEvidenceStore.get_blob`、`FileEvidenceStore.crop`、`FileEvidenceStore.get`、`FileEvidenceStore.exists`、`FileEvidenceStore._require_available`、`FileEvidenceStore.verify`


---

# FileEvidenceStore.__init__ ⭐⭐

**位置与等级**：[file_evidence.py:23](../../../src/persistence/file_evidence.py#L23)；局部辅助逻辑，需理解其调用条件与失败传播。

**签名**：`def __init__(self, directory: Path) -> None`。

**作用**：初始化对象并保存依赖或配置；需检查是否创建持久化资源。

**输入与输出**：
- 输入：`directory`（Path）。
- 输出类型：`None`；具体返回路径见流程步骤。

**处理流程**：
1. 更新 `self.directory`，值来自 `directory`。
2. 更新 `self.blobs_dir`，值来自 `directory / 'blobs'`。
3. 更新 `self.refs_dir`，值来自 `directory / 'refs'`。
4. 调用 `self.blobs_dir.mkdir`，结果未直接赋值。
5. 调用 `self.refs_dir.mkdir`，结果未直接赋值。

**调用与被调用**：
- `self.blobs_dir.mkdir`（[file_evidence.py:27](../../../src/persistence/file_evidence.py#L27)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `self.refs_dir.mkdir`（[file_evidence.py:28](../../../src/persistence/file_evidence.py#L28)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- 静态扫描未定位直接调用方；可能通过路由注册、LangGraph 节点、协议方法或依赖注入动态调用，不据此判断为死代码。

**状态、副作用与异常**：
- 显式状态/容器赋值：`self.directory`、`self.blobs_dir`、`self.refs_dir`。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：未见 `raise`；下游异常可能继续上抛。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。
- 恢复/幂等性：仅在代码有检查点、事务、请求编号或显式去重时才成立；此函数不能单凭名称视为可安全重试。


---

# FileEvidenceStore._blob_path ⭐⭐

**位置与等级**：[file_evidence.py:30](../../../src/persistence/file_evidence.py#L30)；局部辅助逻辑，需理解其调用条件与失败传播。

**签名**：`def _blob_path(self, source_hash: str) -> Path`。

**作用**：内部辅助步骤；将参数转换为本模块所需的中间对象或操作结果。

**输入与输出**：
- 输入：`source_hash`（str）。
- 输出类型：`Path`；具体返回路径见流程步骤。

**处理流程**：
1. 返回 `self.blobs_dir / source_hash[:2] / source_hash`。

**调用与被调用**：
- 无显式函数调用，或仅声明协议/常量。
- 静态可定位的调用方：[FileEvidenceStore._store_blob](file_evidence.md)、[FileEvidenceStore._store_blob_bytes](file_evidence.md)、[FileEvidenceStore._load_ref](file_evidence.md)、[FileEvidenceStore.put_ref](file_evidence.md)、[FileEvidenceStore.get_blob](file_evidence.md)。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：未见 `raise`；下游异常可能继续上抛。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。
- 恢复/幂等性：仅在代码有检查点、事务、请求编号或显式去重时才成立；此函数不能单凭名称视为可安全重试。


---

# FileEvidenceStore._ref_path ⭐⭐

**位置与等级**：[file_evidence.py:33](../../../src/persistence/file_evidence.py#L33)；局部辅助逻辑，需理解其调用条件与失败传播。

**签名**：`def _ref_path(self, evidence_id: str) -> Path`。

**作用**：内部辅助步骤；将参数转换为本模块所需的中间对象或操作结果。

**输入与输出**：
- 输入：`evidence_id`（str）。
- 输出类型：`Path`；具体返回路径见流程步骤。

**处理流程**：
1. 更新 `safe_name`，值来自 `sha256(evidence_id.encode('utf-8')).hexdigest()`。
2. 返回 `self.refs_dir / f<字符串常量>`。

**调用与被调用**：
- `sha256(evidence_id.encode('utf-8')).hexdigest`（[file_evidence.py:34](../../../src/persistence/file_evidence.py#L34)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `sha256`（[file_evidence.py:34](../../../src/persistence/file_evidence.py#L34)）：来自 `hashlib.sha256`；具体实现可能由依赖注入或运行时分派决定。
- `evidence_id.encode`（[file_evidence.py:34](../../../src/persistence/file_evidence.py#L34)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- 静态可定位的调用方：[FileEvidenceStore._load_ref](file_evidence.md)、[FileEvidenceStore.put_ref](file_evidence.md)、[FileEvidenceStore.exists](file_evidence.md)。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：未见 `raise`；下游异常可能继续上抛。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。
- 恢复/幂等性：仅在代码有检查点、事务、请求编号或显式去重时才成立；此函数不能单凭名称视为可安全重试。


---

# FileEvidenceStore._atomic_write ⭐⭐

**位置与等级**：[file_evidence.py:37](../../../src/persistence/file_evidence.py#L37)；局部辅助逻辑，需理解其调用条件与失败传播。

**签名**：`def _atomic_write(self, path: Path, payload: bytes) -> None`。

**作用**：内部辅助步骤；将参数转换为本模块所需的中间对象或操作结果。

**输入与输出**：
- 输入：`path`（Path）；`payload`（bytes）。
- 输出类型：`None`；具体返回路径见流程步骤。

**处理流程**：
1. 调用 `path.parent.mkdir`，结果未直接赋值。
2. 更新 `temporary`，值来自 `path.with_name(f<字符串常量>)`。
3. 捕获 无显式捕获；另检查 finally/else 的清理和传播。

**调用与被调用**：
- `path.parent.mkdir`（[file_evidence.py:38](../../../src/persistence/file_evidence.py#L38)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `path.with_name`（[file_evidence.py:39](../../../src/persistence/file_evidence.py#L39)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `uuid4`（[file_evidence.py:39](../../../src/persistence/file_evidence.py#L39)）：来自 `uuid.uuid4`；具体实现可能由依赖注入或运行时分派决定。
- `temporary.open`（[file_evidence.py:41](../../../src/persistence/file_evidence.py#L41)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `stream.write`（[file_evidence.py:42](../../../src/persistence/file_evidence.py#L42)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `stream.flush`（[file_evidence.py:43](../../../src/persistence/file_evidence.py#L43)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `os.fsync`（[file_evidence.py:44](../../../src/persistence/file_evidence.py#L44)）：来自 `os`；具体实现可能由依赖注入或运行时分派决定。
- `stream.fileno`（[file_evidence.py:44](../../../src/persistence/file_evidence.py#L44)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `os.replace`（[file_evidence.py:45](../../../src/persistence/file_evidence.py#L45)）：来自 `os`；具体实现可能由依赖注入或运行时分派决定。
- `temporary.unlink`（[file_evidence.py:47](../../../src/persistence/file_evidence.py#L47)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- 静态可定位的调用方：[FileEvidenceStore._store_blob_bytes](file_evidence.md)、[FileEvidenceStore.put_ref](file_evidence.md)。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：未见 `raise`；下游异常可能继续上抛。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。
- 恢复/幂等性：仅在代码有检查点、事务、请求编号或显式去重时才成立；此函数不能单凭名称视为可安全重试。


---

# FileEvidenceStore._store_blob ⭐⭐

**位置与等级**：[file_evidence.py:49](../../../src/persistence/file_evidence.py#L49)；局部辅助逻辑，需理解其调用条件与失败传播。

**签名**：`def _store_blob(self, source: Path, source_hash: str) -> None`。

**作用**：内部辅助步骤；将参数转换为本模块所需的中间对象或操作结果。

**输入与输出**：
- 输入：`source`（Path）；`source_hash`（str）。
- 输出类型：`None`；具体返回路径见流程步骤。

**处理流程**：
1. 检查 `file_sha256(source) != source_hash`；按条件分流，else 分支不存在。
2. 更新 `target`，值来自 `self._blob_path(source_hash)`。
3. 检查 `target.exists()`；按条件分流，else 分支不存在。
4. 调用 `target.parent.mkdir`，结果未直接赋值。
5. 更新 `temporary`，值来自 `target.with_name(f<字符串常量>)`。
6. 捕获 无显式捕获；另检查 finally/else 的清理和传播。

**关键条件与保护**：
- [file_evidence.py:50](../../../src/persistence/file_evidence.py#L50)：`file_sha256(source) != source_hash`，不满足时跳过本分支。
- [file_evidence.py:53](../../../src/persistence/file_evidence.py#L53)：`target.exists()`，不满足时跳过本分支。
- [file_evidence.py:54](../../../src/persistence/file_evidence.py#L54)：`file_sha256(target) != source_hash`，不满足时跳过本分支。
- [file_evidence.py:61](../../../src/persistence/file_evidence.py#L61)：`file_sha256(temporary) != source_hash`，不满足时跳过本分支。

**调用与被调用**：
- `file_sha256`（调用点 [file_evidence.py:50](../../../src/persistence/file_evidence.py#L50)）→ [file_sha256](../core/ids.md)，静态可定位。
- `EvidenceIntegrityError`（调用点 [file_evidence.py:51](../../../src/persistence/file_evidence.py#L51)）→ [EvidenceIntegrityError](../core/errors.md)，静态可定位。
- `self._blob_path`（调用点 [file_evidence.py:52](../../../src/persistence/file_evidence.py#L52)）→ [FileEvidenceStore._blob_path](file_evidence.md)，静态可定位。
- `target.exists`（[file_evidence.py:53](../../../src/persistence/file_evidence.py#L53)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `target.parent.mkdir`（[file_evidence.py:57](../../../src/persistence/file_evidence.py#L57)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `target.with_name`（[file_evidence.py:58](../../../src/persistence/file_evidence.py#L58)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `uuid4`（[file_evidence.py:58](../../../src/persistence/file_evidence.py#L58)）：来自 `uuid.uuid4`；具体实现可能由依赖注入或运行时分派决定。
- `shutil.copyfile`（[file_evidence.py:60](../../../src/persistence/file_evidence.py#L60)）：来自 `shutil`；具体实现可能由依赖注入或运行时分派决定。
- `os.replace`（[file_evidence.py:63](../../../src/persistence/file_evidence.py#L63)）：来自 `os`；具体实现可能由依赖注入或运行时分派决定。
- `temporary.unlink`（[file_evidence.py:65](../../../src/persistence/file_evidence.py#L65)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- 静态可定位的调用方：[FileEvidenceStore.put_document](file_evidence.md)。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：`EvidenceIntegrityError(<字符串常量>)`、`EvidenceIntegrityError(f<字符串常量>)`。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。
- 恢复/幂等性：仅在代码有检查点、事务、请求编号或显式去重时才成立；此函数不能单凭名称视为可安全重试。


---

# FileEvidenceStore._store_blob_bytes ⭐⭐

**位置与等级**：[file_evidence.py:67](../../../src/persistence/file_evidence.py#L67)；局部辅助逻辑，需理解其调用条件与失败传播。

**签名**：`def _store_blob_bytes(self, content: bytes) -> str`。

**作用**：内部辅助步骤；将参数转换为本模块所需的中间对象或操作结果。

**输入与输出**：
- 输入：`content`（bytes）。
- 输出类型：`str`；具体返回路径见流程步骤。

**处理流程**：
1. 更新 `digest`，值来自 `sha256(content).hexdigest()`。
2. 更新 `target`，值来自 `self._blob_path(digest)`。
3. 检查 `target.exists()`；按条件分流，else 分支不存在。
4. 调用 `self._atomic_write`，结果未直接赋值。
5. 返回 `digest`。

**关键条件与保护**：
- [file_evidence.py:70](../../../src/persistence/file_evidence.py#L70)：`target.exists()`，不满足时跳过本分支。
- [file_evidence.py:71](../../../src/persistence/file_evidence.py#L71)：`file_sha256(target) != digest`，不满足时跳过本分支。

**调用与被调用**：
- `sha256(content).hexdigest`（[file_evidence.py:68](../../../src/persistence/file_evidence.py#L68)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `sha256`（[file_evidence.py:68](../../../src/persistence/file_evidence.py#L68)）：来自 `hashlib.sha256`；具体实现可能由依赖注入或运行时分派决定。
- `self._blob_path`（调用点 [file_evidence.py:69](../../../src/persistence/file_evidence.py#L69)）→ [FileEvidenceStore._blob_path](file_evidence.md)，静态可定位。
- `target.exists`（[file_evidence.py:70](../../../src/persistence/file_evidence.py#L70)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `file_sha256`（调用点 [file_evidence.py:71](../../../src/persistence/file_evidence.py#L71)）→ [file_sha256](../core/ids.md)，静态可定位。
- `EvidenceIntegrityError`（调用点 [file_evidence.py:72](../../../src/persistence/file_evidence.py#L72)）→ [EvidenceIntegrityError](../core/errors.md)，静态可定位。
- `self._atomic_write`（调用点 [file_evidence.py:74](../../../src/persistence/file_evidence.py#L74)）→ [FileEvidenceStore._atomic_write](file_evidence.md)，静态可定位。
- 静态可定位的调用方：[FileEvidenceStore.put_blob](file_evidence.md)。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：`EvidenceIntegrityError(f<字符串常量>)`。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。
- 恢复/幂等性：仅在代码有检查点、事务、请求编号或显式去重时才成立；此函数不能单凭名称视为可安全重试。


---

# FileEvidenceStore._serialize_ref ⭐⭐

**位置与等级**：[file_evidence.py:77](../../../src/persistence/file_evidence.py#L77)；局部辅助逻辑，需理解其调用条件与失败传播。

**签名**：`def _serialize_ref(self, evidence: EvidenceRef) -> bytes`。

**作用**：内部辅助步骤；将参数转换为本模块所需的中间对象或操作结果。

**输入与输出**：
- 输入：`evidence`（EvidenceRef）。
- 输出类型：`bytes`；具体返回路径见流程步骤。

**处理流程**：
1. 更新 `record`，值来自 `evidence.model_dump(mode='json')`。
2. 更新 `wrapper`，值来自 `{'checksum': canonical_hash(record), 'record': record}`。
3. 返回 `orjson.dumps(wrapper, option=orjson.OPT_SORT_KEYS | orjson.OPT_INDENT_2)`。

**调用与被调用**：
- `evidence.model_dump`（[file_evidence.py:78](../../../src/persistence/file_evidence.py#L78)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `canonical_hash`（调用点 [file_evidence.py:79](../../../src/persistence/file_evidence.py#L79)）→ [canonical_hash](../core/ids.md)，静态可定位。
- `orjson.dumps`（[file_evidence.py:80](../../../src/persistence/file_evidence.py#L80)）：来自 `orjson`；具体实现可能由依赖注入或运行时分派决定。
- 静态可定位的调用方：[FileEvidenceStore.put_ref](file_evidence.md)。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：未见 `raise`；下游异常可能继续上抛。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。
- 恢复/幂等性：仅在代码有检查点、事务、请求编号或显式去重时才成立；此函数不能单凭名称视为可安全重试。


---

# FileEvidenceStore._load_ref ⭐⭐

**位置与等级**：[file_evidence.py:82](../../../src/persistence/file_evidence.py#L82)；局部辅助逻辑，需理解其调用条件与失败传播。

**签名**：`def _load_ref(self, evidence_id: str) -> EvidenceRef`。

**作用**：内部辅助步骤；将参数转换为本模块所需的中间对象或操作结果。

**输入与输出**：
- 输入：`evidence_id`（str）。
- 输出类型：`EvidenceRef`；具体返回路径见流程步骤。

**处理流程**：
1. 更新 `path`，值来自 `self._ref_path(evidence_id)`。
2. 检查 `not path.exists()`；按条件分流，else 分支不存在。
3. 捕获 (KeyError, TypeError, ValueError, orjson.JSONDecodeErr…；另检查 finally/else 的清理和传播。
4. 检查 `evidence.id != evidence_id`；按条件分流，else 分支不存在。
5. 检查 `file_sha256(self._blob_path(evidence.source_hash)) != evidence.source_hash`；按条件分流，else 分支不存在。
6. 返回 `evidence`。

**关键条件与保护**：
- [file_evidence.py:84](../../../src/persistence/file_evidence.py#L84)：`not path.exists()`，不满足时跳过本分支。
- [file_evidence.py:89](../../../src/persistence/file_evidence.py#L89)：`wrapper['checksum'] != canonical_hash(record)`，不满足时跳过本分支。
- [file_evidence.py:93](../../../src/persistence/file_evidence.py#L93)：`isinstance(exc, EvidenceIntegrityError)`，不满足时跳过本分支。
- [file_evidence.py:96](../../../src/persistence/file_evidence.py#L96)：`evidence.id != evidence_id`，不满足时跳过本分支。
- [file_evidence.py:98](../../../src/persistence/file_evidence.py#L98)：`file_sha256(self._blob_path(evidence.source_hash)) != evidence.source_hash`，不满足时跳过本分支。

**调用与被调用**：
- `self._ref_path`（调用点 [file_evidence.py:83](../../../src/persistence/file_evidence.py#L83)）→ [FileEvidenceStore._ref_path](file_evidence.md)，静态可定位。
- `path.exists`（[file_evidence.py:84](../../../src/persistence/file_evidence.py#L84)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `EvidenceIntegrityError`（调用点 [file_evidence.py:85](../../../src/persistence/file_evidence.py#L85)）→ [EvidenceIntegrityError](../core/errors.md)，静态可定位。
- `cast`（[file_evidence.py:87](../../../src/persistence/file_evidence.py#L87)）：来自 `typing.cast`；具体实现可能由依赖注入或运行时分派决定。
- `orjson.loads`（[file_evidence.py:87](../../../src/persistence/file_evidence.py#L87)）：来自 `orjson`；具体实现可能由依赖注入或运行时分派决定。
- `path.read_bytes`（[file_evidence.py:87](../../../src/persistence/file_evidence.py#L87)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `canonical_hash`（调用点 [file_evidence.py:89](../../../src/persistence/file_evidence.py#L89)）→ [canonical_hash](../core/ids.md)，静态可定位。
- `EvidenceRef.model_validate`（[file_evidence.py:91](../../../src/persistence/file_evidence.py#L91)）：来自 `src.domain.EvidenceRef`；具体实现可能由依赖注入或运行时分派决定。
- `isinstance`（[file_evidence.py:93](../../../src/persistence/file_evidence.py#L93)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `file_sha256`（调用点 [file_evidence.py:98](../../../src/persistence/file_evidence.py#L98)）→ [file_sha256](../core/ids.md)，静态可定位。
- `self._blob_path`（调用点 [file_evidence.py:98](../../../src/persistence/file_evidence.py#L98)）→ [FileEvidenceStore._blob_path](file_evidence.md)，静态可定位。
- 静态可定位的调用方：[FileEvidenceStore.crop](file_evidence.md)、[FileEvidenceStore.get](file_evidence.md)、[FileEvidenceStore.verify](file_evidence.md)。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：`EvidenceIntegrityError(f<字符串常量>)`、`重新抛出`。
- 本地捕获：`(KeyError, TypeError, ValueError, orjson.JSONDecodeError)`。
- 恢复/幂等性：仅在代码有检查点、事务、请求编号或显式去重时才成立；此函数不能单凭名称视为可安全重试。


---

# FileEvidenceStore.put_document ⭐⭐

**位置与等级**：[file_evidence.py:102](../../../src/persistence/file_evidence.py#L102)；局部辅助逻辑，需理解其调用条件与失败传播。

**签名**：`async def put_document(self, document: DocumentIR) -> None`。

**作用**：处理 `put_document` 对应步骤；下列步骤依据函数体的实际控制流和调用点整理。

**输入与输出**：
- 输入：`document`（DocumentIR；解析后的文档及其文本、媒体、证据定位）。
- 输出类型：`None`；具体返回路径见流程步骤。

**处理流程**：
1. 更新 `source`，值来自 `Path(document.source_path)`。
2. 检查 `not source.is_file()`；按条件分流，else 分支不存在。
3. 调用 `self._store_blob`，结果未直接赋值。
4. 遍历 `document.media_assets`，逐项处理 `asset`。
5. 遍历 `document.evidence`，逐项处理 `evidence`。

**关键条件与保护**：
- [file_evidence.py:104](../../../src/persistence/file_evidence.py#L104)：`not source.is_file()`，不满足时跳过本分支。
- [file_evidence.py:109](../../../src/persistence/file_evidence.py#L109)：`not asset_path.is_file()`，不满足时跳过本分支。
- [file_evidence.py:112](../../../src/persistence/file_evidence.py#L112)：`asset.blob_hash and digest != asset.blob_hash`，不满足时跳过本分支。
- [file_evidence.py:116](../../../src/persistence/file_evidence.py#L116)：`evidence.document_id != document.id`，不满足时跳过本分支。

**调用与被调用**：
- `Path`（[file_evidence.py:103](../../../src/persistence/file_evidence.py#L103)）：来自 `pathlib.Path`；具体实现可能由依赖注入或运行时分派决定。
- `source.is_file`（[file_evidence.py:104](../../../src/persistence/file_evidence.py#L104)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `EvidenceIntegrityError`（调用点 [file_evidence.py:105](../../../src/persistence/file_evidence.py#L105)）→ [EvidenceIntegrityError](../core/errors.md)，静态可定位。
- `self._store_blob`（调用点 [file_evidence.py:106](../../../src/persistence/file_evidence.py#L106)）→ [FileEvidenceStore._store_blob](file_evidence.md)，静态可定位。
- `asset_path.is_file`（[file_evidence.py:109](../../../src/persistence/file_evidence.py#L109)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `file_sha256`（调用点 [file_evidence.py:111](../../../src/persistence/file_evidence.py#L111)）→ [file_sha256](../core/ids.md)，静态可定位。
- `self.put_ref`（调用点 [file_evidence.py:120](../../../src/persistence/file_evidence.py#L120)）→ [FileEvidenceStore.put_ref](file_evidence.md)，静态可定位。
- 静态扫描未定位直接调用方；可能通过路由注册、LangGraph 节点、协议方法或依赖注入动态调用，不据此判断为死代码。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：`EvidenceIntegrityError(f<字符串常量>)`。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。
- 恢复/幂等性：仅在代码有检查点、事务、请求编号或显式去重时才成立；此函数不能单凭名称视为可安全重试。


---

# FileEvidenceStore.put_blob ⭐⭐

**位置与等级**：[file_evidence.py:122](../../../src/persistence/file_evidence.py#L122)；局部辅助逻辑，需理解其调用条件与失败传播。

**签名**：`async def put_blob(self, content: bytes, media_type: str) -> str`。

**作用**：处理 `put_blob` 对应步骤；下列步骤依据函数体的实际控制流和调用点整理。

**输入与输出**：
- 输入：`content`（bytes）；`media_type`（str）。
- 输出类型：`str`；具体返回路径见流程步骤。

**处理流程**：
1. 返回 `self._store_blob_bytes(content)`。

**调用与被调用**：
- `self._store_blob_bytes`（调用点 [file_evidence.py:124](../../../src/persistence/file_evidence.py#L124)）→ [FileEvidenceStore._store_blob_bytes](file_evidence.md)，静态可定位。
- 静态扫描未定位直接调用方；可能通过路由注册、LangGraph 节点、协议方法或依赖注入动态调用，不据此判断为死代码。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：未见 `raise`；下游异常可能继续上抛。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。
- 恢复/幂等性：仅在代码有检查点、事务、请求编号或显式去重时才成立；此函数不能单凭名称视为可安全重试。


---

# FileEvidenceStore.put_ref ⭐⭐

**位置与等级**：[file_evidence.py:126](../../../src/persistence/file_evidence.py#L126)；局部辅助逻辑，需理解其调用条件与失败传播。

**签名**：`async def put_ref(self, evidence: EvidenceRef) -> None`。

**作用**：处理 `put_ref` 对应步骤；下列步骤依据函数体的实际控制流和调用点整理。

**输入与输出**：
- 输入：`evidence`（EvidenceRef）。
- 输出类型：`None`；具体返回路径见流程步骤。

**处理流程**：
1. 检查 `not self._blob_path(evidence.source_hash).is_file()`；按条件分流，else 分支不存在。
2. 更新 `path`，值来自 `self._ref_path(evidence.id)`。
3. 更新 `payload`，值来自 `self._serialize_ref(evidence)`。
4. 检查 `path.exists()`；按条件分流，else 分支不存在。
5. 调用 `self._atomic_write`，结果未直接赋值。

**关键条件与保护**：
- [file_evidence.py:127](../../../src/persistence/file_evidence.py#L127)：`not self._blob_path(evidence.source_hash).is_file()`，不满足时跳过本分支。
- [file_evidence.py:131](../../../src/persistence/file_evidence.py#L131)：`path.exists()`，不满足时跳过本分支。
- [file_evidence.py:132](../../../src/persistence/file_evidence.py#L132)：`path.read_bytes() != payload`，不满足时跳过本分支。

**调用与被调用**：
- `self._blob_path(evidence.source_hash).is_file`（[file_evidence.py:127](../../../src/persistence/file_evidence.py#L127)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `self._blob_path`（调用点 [file_evidence.py:127](../../../src/persistence/file_evidence.py#L127)）→ [FileEvidenceStore._blob_path](file_evidence.md)，静态可定位。
- `EvidenceIntegrityError`（调用点 [file_evidence.py:128](../../../src/persistence/file_evidence.py#L128)）→ [EvidenceIntegrityError](../core/errors.md)，静态可定位。
- `self._ref_path`（调用点 [file_evidence.py:129](../../../src/persistence/file_evidence.py#L129)）→ [FileEvidenceStore._ref_path](file_evidence.md)，静态可定位。
- `self._serialize_ref`（调用点 [file_evidence.py:130](../../../src/persistence/file_evidence.py#L130)）→ [FileEvidenceStore._serialize_ref](file_evidence.md)，静态可定位。
- `path.exists`（[file_evidence.py:131](../../../src/persistence/file_evidence.py#L131)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `path.read_bytes`（[file_evidence.py:132](../../../src/persistence/file_evidence.py#L132)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `self._atomic_write`（调用点 [file_evidence.py:137](../../../src/persistence/file_evidence.py#L137)）→ [FileEvidenceStore._atomic_write](file_evidence.md)，静态可定位。
- 静态可定位的调用方：[FileEvidenceStore.put_document](file_evidence.md)。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：`EvidenceIntegrityError(f<字符串常量>)`。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。
- 恢复/幂等性：仅在代码有检查点、事务、请求编号或显式去重时才成立；此函数不能单凭名称视为可安全重试。


---

# FileEvidenceStore.get_blob ⭐⭐

**位置与等级**：[file_evidence.py:139](../../../src/persistence/file_evidence.py#L139)；局部辅助逻辑，需理解其调用条件与失败传播。

**签名**：`async def get_blob(self, blob_hash: str) -> bytes`。

**作用**：读取或组装对应资源；是否纯只读及异常行为需结合下方显式调用与状态写入判断。

**输入与输出**：
- 输入：`blob_hash`（str）。
- 输出类型：`bytes`；具体返回路径见流程步骤。

**处理流程**：
1. 更新 `path`，值来自 `self._blob_path(blob_hash)`。
2. 检查 `not path.is_file() or file_sha256(path) != blob_hash`；按条件分流，else 分支不存在。
3. 返回 `path.read_bytes()`。

**关键条件与保护**：
- [file_evidence.py:141](../../../src/persistence/file_evidence.py#L141)：`not path.is_file() or file_sha256(path) != blob_hash`，不满足时跳过本分支。

**调用与被调用**：
- `self._blob_path`（调用点 [file_evidence.py:140](../../../src/persistence/file_evidence.py#L140)）→ [FileEvidenceStore._blob_path](file_evidence.md)，静态可定位。
- `path.is_file`（[file_evidence.py:141](../../../src/persistence/file_evidence.py#L141)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `file_sha256`（调用点 [file_evidence.py:141](../../../src/persistence/file_evidence.py#L141)）→ [file_sha256](../core/ids.md)，静态可定位。
- `EvidenceIntegrityError`（调用点 [file_evidence.py:142](../../../src/persistence/file_evidence.py#L142)）→ [EvidenceIntegrityError](../core/errors.md)，静态可定位。
- `path.read_bytes`（[file_evidence.py:143](../../../src/persistence/file_evidence.py#L143)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- 静态可定位的调用方：[FileEvidenceStore.crop](file_evidence.md)。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：`EvidenceIntegrityError(f<字符串常量>)`。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。
- 恢复/幂等性：仅在代码有检查点、事务、请求编号或显式去重时才成立；此函数不能单凭名称视为可安全重试。


---

# FileEvidenceStore.crop ⭐⭐

**位置与等级**：[file_evidence.py:145](../../../src/persistence/file_evidence.py#L145)；局部辅助逻辑，需理解其调用条件与失败传播。

**签名**：`async def crop(self, evidence_id: str) -> bytes`。

**作用**：处理 `crop` 对应步骤；下列步骤依据函数体的实际控制流和调用点整理。

**输入与输出**：
- 输入：`evidence_id`（str）。
- 输出类型：`bytes`；具体返回路径见流程步骤。

**处理流程**：
1. 更新 `evidence`，值来自 `self._load_ref(evidence_id)`。
2. 更新 `content`，值来自 `await self.get_blob(evidence.source_hash)`。
3. 检查 `evidence.bbox is None`；按条件分流，else 分支不存在。
4. 更新 `box`，值来自 `evidence.bbox`。
5. 检查 `evidence.coordinate_space == CoordinateSpace.PDF_POINTS`；按条件分流，else 分支不存在。
6. 进入上下文 `Image.open(BytesIO(content))`，由上下文管理器控制资源释放或事务范围。

**关键条件与保护**：
- [file_evidence.py:148](../../../src/persistence/file_evidence.py#L148)：`evidence.bbox is None`，不满足时跳过本分支。
- [file_evidence.py:151](../../../src/persistence/file_evidence.py#L151)：`evidence.coordinate_space == CoordinateSpace.PDF_POINTS`，不满足时跳过本分支。
- [file_evidence.py:153](../../../src/persistence/file_evidence.py#L153)：`evidence.page_number is None`，不满足时跳过本分支。
- [file_evidence.py:165](../../../src/persistence/file_evidence.py#L165)：`evidence.coordinate_space == CoordinateSpace.NORMALIZED`，不满足时有 else 分支。
- [file_evidence.py:180](../../../src/persistence/file_evidence.py#L180)：`cropped.mode not in {'RGB', 'RGBA', 'L', 'LA', 'P', '1'}`，不满足时跳过本分支。

**调用与被调用**：
- `self._load_ref`（调用点 [file_evidence.py:146](../../../src/persistence/file_evidence.py#L146)）→ [FileEvidenceStore._load_ref](file_evidence.md)，静态可定位。
- `self.get_blob`（调用点 [file_evidence.py:147](../../../src/persistence/file_evidence.py#L147)）→ [FileEvidenceStore.get_blob](file_evidence.md)，静态可定位。
- `pymupdf.open`（[file_evidence.py:152](../../../src/persistence/file_evidence.py#L152)）：来自 `pymupdf`；具体实现可能由依赖注入或运行时分派决定。
- `EvidenceIntegrityError`（调用点 [file_evidence.py:154](../../../src/persistence/file_evidence.py#L154)）→ [EvidenceIntegrityError](../core/errors.md)，静态可定位。
- `page.get_pixmap`（[file_evidence.py:156](../../../src/persistence/file_evidence.py#L156)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `pymupdf.Matrix`（[file_evidence.py:157](../../../src/persistence/file_evidence.py#L157)）：来自 `pymupdf`；具体实现可能由依赖注入或运行时分派决定。
- `pymupdf.Rect`（[file_evidence.py:158](../../../src/persistence/file_evidence.py#L158)）：来自 `pymupdf`；具体实现可能由依赖注入或运行时分派决定。
- `bytes`（[file_evidence.py:163](../../../src/persistence/file_evidence.py#L163)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `pixmap.tobytes`（[file_evidence.py:163](../../../src/persistence/file_evidence.py#L163)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `Image.open`（[file_evidence.py:164](../../../src/persistence/file_evidence.py#L164)）：来自 `PIL.Image`；具体实现可能由依赖注入或运行时分派决定。
- `BytesIO`（[file_evidence.py:164](../../../src/persistence/file_evidence.py#L164)）：来自 `io.BytesIO`；具体实现可能由依赖注入或运行时分派决定。
- `int`（[file_evidence.py:167](../../../src/persistence/file_evidence.py#L167)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `image.crop`（[file_evidence.py:179](../../../src/persistence/file_evidence.py#L179)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `cropped.convert`（[file_evidence.py:181](../../../src/persistence/file_evidence.py#L181)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `cropped.save`（[file_evidence.py:183](../../../src/persistence/file_evidence.py#L183)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `output.getvalue`（[file_evidence.py:184](../../../src/persistence/file_evidence.py#L184)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- 静态扫描未定位直接调用方；可能通过路由注册、LangGraph 节点、协议方法或依赖注入动态调用，不据此判断为死代码。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：`EvidenceIntegrityError(<字符串常量>)`。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。
- 恢复/幂等性：仅在代码有检查点、事务、请求编号或显式去重时才成立；此函数不能单凭名称视为可安全重试。


---

# FileEvidenceStore.get ⭐⭐

**位置与等级**：[file_evidence.py:186](../../../src/persistence/file_evidence.py#L186)；局部辅助逻辑，需理解其调用条件与失败传播。

**签名**：`async def get(self, evidence_id: str) -> EvidenceRef`。

**作用**：处理 `get` 对应步骤；下列步骤依据函数体的实际控制流和调用点整理。

**输入与输出**：
- 输入：`evidence_id`（str）。
- 输出类型：`EvidenceRef`；具体返回路径见流程步骤。

**处理流程**：
1. 返回 `self._load_ref(evidence_id)`。

**调用与被调用**：
- `self._load_ref`（调用点 [file_evidence.py:187](../../../src/persistence/file_evidence.py#L187)）→ [FileEvidenceStore._load_ref](file_evidence.md)，静态可定位。
- 静态扫描未定位直接调用方；可能通过路由注册、LangGraph 节点、协议方法或依赖注入动态调用，不据此判断为死代码。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：未见 `raise`；下游异常可能继续上抛。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。
- 恢复/幂等性：仅在代码有检查点、事务、请求编号或显式去重时才成立；此函数不能单凭名称视为可安全重试。


---

# FileEvidenceStore.exists ⭐⭐

**位置与等级**：[file_evidence.py:189](../../../src/persistence/file_evidence.py#L189)；局部辅助逻辑，需理解其调用条件与失败传播。

**签名**：`async def exists(self, evidence_id: str) -> bool`。

**作用**：处理 `exists` 对应步骤；下列步骤依据函数体的实际控制流和调用点整理。

**输入与输出**：
- 输入：`evidence_id`（str）。
- 输出类型：`bool`；具体返回路径见流程步骤。

**处理流程**：
1. 调用 `self._require_available`，结果未直接赋值。
2. 返回 `self._ref_path(evidence_id).is_file()`。

**调用与被调用**：
- `self._require_available`（调用点 [file_evidence.py:190](../../../src/persistence/file_evidence.py#L190)）→ [FileEvidenceStore._require_available](file_evidence.md)，静态可定位。
- `self._ref_path(evidence_id).is_file`（[file_evidence.py:191](../../../src/persistence/file_evidence.py#L191)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `self._ref_path`（调用点 [file_evidence.py:191](../../../src/persistence/file_evidence.py#L191)）→ [FileEvidenceStore._ref_path](file_evidence.md)，静态可定位。
- 静态扫描未定位直接调用方；可能通过路由注册、LangGraph 节点、协议方法或依赖注入动态调用，不据此判断为死代码。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：未见 `raise`；下游异常可能继续上抛。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。
- 恢复/幂等性：仅在代码有检查点、事务、请求编号或显式去重时才成立；此函数不能单凭名称视为可安全重试。


---

# FileEvidenceStore._require_available ⭐⭐

**位置与等级**：[file_evidence.py:193](../../../src/persistence/file_evidence.py#L193)；局部辅助逻辑，需理解其调用条件与失败传播。

**签名**：`def _require_available(self) -> None`。

**作用**：内部辅助步骤；将参数转换为本模块所需的中间对象或操作结果。

**输入与输出**：
- 输入：无业务参数（或仅隐式接收实例）。
- 输出类型：`None`；具体返回路径见流程步骤。

**处理流程**：
1. 遍历 `(self.refs_dir, self.blobs_dir)`，逐项处理 `directory`。

**调用与被调用**：
- `os.scandir`（[file_evidence.py:196](../../../src/persistence/file_evidence.py#L196)）：来自 `os`；具体实现可能由依赖注入或运行时分派决定。
- `next`（[file_evidence.py:197](../../../src/persistence/file_evidence.py#L197)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- 静态可定位的调用方：[FileEvidenceStore.exists](file_evidence.md)、[FileEvidenceStore.verify](file_evidence.md)。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：未见 `raise`；下游异常可能继续上抛。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。
- 恢复/幂等性：仅在代码有检查点、事务、请求编号或显式去重时才成立；此函数不能单凭名称视为可安全重试。


---

# FileEvidenceStore.verify ⭐⭐

**位置与等级**：[file_evidence.py:199](../../../src/persistence/file_evidence.py#L199)；局部辅助逻辑，需理解其调用条件与失败传播。

**签名**：`async def verify(self, evidence_id: str) -> bool`。

**作用**：处理 `verify` 对应步骤；下列步骤依据函数体的实际控制流和调用点整理。

**输入与输出**：
- 输入：`evidence_id`（str）。
- 输出类型：`bool`；具体返回路径见流程步骤。

**处理流程**：
1. 调用 `self._require_available`，结果未直接赋值。
2. 捕获 (EvidenceIntegrityError, FileNotFoundError)；另检查 finally/else 的清理和传播。
3. 返回 `True`。

**调用与被调用**：
- `self._require_available`（调用点 [file_evidence.py:200](../../../src/persistence/file_evidence.py#L200)）→ [FileEvidenceStore._require_available](file_evidence.md)，静态可定位。
- `self._load_ref`（调用点 [file_evidence.py:202](../../../src/persistence/file_evidence.py#L202)）→ [FileEvidenceStore._load_ref](file_evidence.md)，静态可定位。
- 静态扫描未定位直接调用方；可能通过路由注册、LangGraph 节点、协议方法或依赖注入动态调用，不据此判断为死代码。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：未见 `raise`；下游异常可能继续上抛。
- 本地捕获：`(EvidenceIntegrityError, FileNotFoundError)`。
- 恢复/幂等性：仅在代码有检查点、事务、请求编号或显式去重时才成立；此函数不能单凭名称视为可安全重试。


---
