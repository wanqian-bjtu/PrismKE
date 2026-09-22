源码：[embedding.py:1](../../../src/providers/embedding.py#L1) | 基准：`dev/v0.10@f2f34d7` | 本文件符号数：14

**模块职责**：Local dense embedding providers used by entity resolution.
**在系统中的位置**：LLM、OCR、VLM、Embedding、Reflection 与语义建议的外部能力接口和实现。
**直接依赖**：[src.core.ids](../core/ids.md)；外部/标准库：`__future__`、`asyncio`、`hashlib`、`json`、`math`、`os`、`pathlib`、`typing`、`uuid`。
**主要调用方（静态导入）**：[providers/__init__.py](__init__.md)、[workflow/nodes.py](../workflow/nodes.md)。
**阅读提示**：下列流程根据当前源码控制流整理；`self`/接口对象的实际类型可能在运行时注入，未能静态解析的调用会明确标注。链接指向源码行或对应讲解文件。

---

# DisabledEmbeddingProvider ⭐⭐⭐

**位置与等级**：[embedding.py:17](../../../src/providers/embedding.py#L17)；关键支撑逻辑，影响候选、证据或接口的正确传递。

**职责**：外部能力实现或协议；调用是否耗费模型额度取决于具体实现。基类：无显式基类。

**字段与类级约束**：
- 类体未直接声明字段；实例状态请看 `__init__` 及方法中的赋值。

**内部成员**：`DisabledEmbeddingProvider.fingerprint`、`DisabledEmbeddingProvider.encode`


---

# DisabledEmbeddingProvider.fingerprint ⭐⭐⭐

**位置与等级**：[embedding.py:18](../../../src/providers/embedding.py#L18)；关键支撑逻辑，影响候选、证据或接口的正确传递。

**签名**：`def fingerprint(self) -> str`。

**作用**：处理 `fingerprint` 对应步骤；下列步骤依据函数体的实际控制流和调用点整理。

**输入与输出**：
- 输入：无业务参数（或仅隐式接收实例）。
- 输出类型：`str`；具体返回路径见流程步骤。

**处理流程**：
1. 返回 `'embedding:disabled'`。

**调用与被调用**：
- 无显式函数调用，或仅声明协议/常量。
- 静态扫描未定位直接调用方；可能通过路由注册、LangGraph 节点、协议方法或依赖注入动态调用，不据此判断为死代码。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：未见 `raise`；下游异常可能继续上抛。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。


---

# DisabledEmbeddingProvider.encode ⭐⭐⭐

**位置与等级**：[embedding.py:21](../../../src/providers/embedding.py#L21)；关键支撑逻辑，影响候选、证据或接口的正确传递。

**签名**：`async def encode(self, texts: list[str]) -> list[list[float]]`。

**作用**：处理 `encode` 对应步骤；下列步骤依据函数体的实际控制流和调用点整理。

**输入与输出**：
- 输入：`texts`（list[str]）。
- 输出类型：`list[list[float]]`；具体返回路径见流程步骤。

**处理流程**：
1. 检查 `texts`；按条件分流，else 分支不存在。
2. 返回 `[]`。

**关键条件与保护**：
- [embedding.py:22](../../../src/providers/embedding.py#L22)：`texts`，不满足时跳过本分支。

**调用与被调用**：
- `RuntimeError`（[embedding.py:23](../../../src/providers/embedding.py#L23)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- 静态扫描未定位直接调用方；可能通过路由注册、LangGraph 节点、协议方法或依赖注入动态调用，不据此判断为死代码。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：`RuntimeError(<字符串常量>)`。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。


---

# MockEmbeddingProvider ⭐⭐⭐

**位置与等级**：[embedding.py:27](../../../src/providers/embedding.py#L27)；关键支撑逻辑，影响候选、证据或接口的正确传递。

**职责**：外部能力实现或协议；调用是否耗费模型额度取决于具体实现。基类：无显式基类。
**源码说明**：Deterministic low-dimensional vectors for offline tests.

**字段与类级约束**：
- `dimension`：类级默认或常量，取值由 `32` 决定。

**内部成员**：`MockEmbeddingProvider.fingerprint`、`MockEmbeddingProvider.encode`、`MockEmbeddingProvider._vector`


---

# MockEmbeddingProvider.fingerprint ⭐⭐⭐

**位置与等级**：[embedding.py:32](../../../src/providers/embedding.py#L32)；关键支撑逻辑，影响候选、证据或接口的正确传递。

**签名**：`def fingerprint(self) -> str`。

**作用**：处理 `fingerprint` 对应步骤；下列步骤依据函数体的实际控制流和调用点整理。

**输入与输出**：
- 输入：无业务参数（或仅隐式接收实例）。
- 输出类型：`str`；具体返回路径见流程步骤。

**处理流程**：
1. 返回 `'embedding:mock:v1:32'`。

**调用与被调用**：
- 无显式函数调用，或仅声明协议/常量。
- 静态扫描未定位直接调用方；可能通过路由注册、LangGraph 节点、协议方法或依赖注入动态调用，不据此判断为死代码。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：未见 `raise`；下游异常可能继续上抛。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。


---

# MockEmbeddingProvider.encode ⭐⭐⭐

**位置与等级**：[embedding.py:35](../../../src/providers/embedding.py#L35)；关键支撑逻辑，影响候选、证据或接口的正确传递。

**签名**：`async def encode(self, texts: list[str]) -> list[list[float]]`。

**作用**：处理 `encode` 对应步骤；下列步骤依据函数体的实际控制流和调用点整理。

**输入与输出**：
- 输入：`texts`（list[str]）。
- 输出类型：`list[list[float]]`；具体返回路径见流程步骤。

**处理流程**：
1. 返回 `[self._vector(text) for text in texts]`。

**调用与被调用**：
- `self._vector`（调用点 [embedding.py:36](../../../src/providers/embedding.py#L36)）→ [MockEmbeddingProvider._vector](embedding.md)，静态可定位。
- 静态扫描未定位直接调用方；可能通过路由注册、LangGraph 节点、协议方法或依赖注入动态调用，不据此判断为死代码。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：未见 `raise`；下游异常可能继续上抛。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。


---

# MockEmbeddingProvider._vector ⭐⭐

**位置与等级**：[embedding.py:39](../../../src/providers/embedding.py#L39)；局部辅助逻辑，需理解其调用条件与失败传播。

**签名**：`def _vector(cls, text: str) -> list[float]`。

**装饰器/路由**：`classmethod`。

**作用**：内部辅助步骤；将参数转换为本模块所需的中间对象或操作结果。

**输入与输出**：
- 输入：`text`（str）。
- 输出类型：`list[float]`；具体返回路径见流程步骤。

**处理流程**：
1. 更新 `vector`，值来自 `[0.0] * cls.dimension`。
2. 更新 `normalized`，值来自 `<字符串常量>.join(text.casefold().split())`。
3. 更新 `tokens`，值来自 `normalized.split() or [normalized]`。
4. 遍历 `tokens`，逐项处理 `token`。
5. 更新 `norm`，值来自 `math.sqrt(sum((item * item for item in vector))) or 1.0`。
6. 返回 `[item / norm for item in vector]`。

**调用与被调用**：
- `<字符串常量>.join`（[embedding.py:41](../../../src/providers/embedding.py#L41)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `text.casefold().split`（[embedding.py:41](../../../src/providers/embedding.py#L41)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `text.casefold`（[embedding.py:41](../../../src/providers/embedding.py#L41)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `normalized.split`（[embedding.py:42](../../../src/providers/embedding.py#L42)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `hashlib.sha256(token.encode('utf-8')).digest`（[embedding.py:44](../../../src/providers/embedding.py#L44)）：来自 `hashlib`；具体实现可能由依赖注入或运行时分派决定。
- `hashlib.sha256`（[embedding.py:44](../../../src/providers/embedding.py#L44)）：来自 `hashlib`；具体实现可能由依赖注入或运行时分派决定。
- `token.encode`（[embedding.py:44](../../../src/providers/embedding.py#L44)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `enumerate`（[embedding.py:45](../../../src/providers/embedding.py#L45)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `math.sqrt`（[embedding.py:48](../../../src/providers/embedding.py#L48)）：来自 `math`；具体实现可能由依赖注入或运行时分派决定。
- `sum`（[embedding.py:48](../../../src/providers/embedding.py#L48)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- 静态可定位的调用方：[MockEmbeddingProvider.encode](embedding.md)。

**状态、副作用与异常**：
- 显式状态/容器赋值：`vector[slot]`。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：未见 `raise`；下游异常可能继续上抛。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。


---

# BGEM3EmbeddingProvider ⭐⭐⭐

**位置与等级**：[embedding.py:52](../../../src/providers/embedding.py#L52)；关键支撑逻辑，影响候选、证据或接口的正确传递。

**职责**：外部能力实现或协议；调用是否耗费模型额度取决于具体实现。基类：无显式基类。
**源码说明**：Lazy, cached BGE-M3 dense encoder.

**字段与类级约束**：
- `dimension`：类级默认或常量，取值由 `1024` 决定。

**内部成员**：`BGEM3EmbeddingProvider.__init__`、`BGEM3EmbeddingProvider.fingerprint`、`BGEM3EmbeddingProvider._cache_path`、`BGEM3EmbeddingProvider._load_model`、`BGEM3EmbeddingProvider._encode_missing`、`BGEM3EmbeddingProvider.encode`


---

# BGEM3EmbeddingProvider.__init__ ⭐⭐⭐

**位置与等级**：[embedding.py:57](../../../src/providers/embedding.py#L57)；关键支撑逻辑，影响候选、证据或接口的正确传递。

**签名**：`def __init__(self, model_name: str, model_revision: str, device: str, use_fp16: bool, batch_size: int, max_tokens: int, cache_dir: Path, model_cache_dir: Path, allow_download: bool=False) -> None`。

**作用**：初始化对象并保存依赖或配置；需检查是否创建持久化资源。

**输入与输出**：
- 输入：`model_name`（str）；`model_revision`（str）；`device`（str）；`use_fp16`（bool）；`batch_size`（int）；`max_tokens`（int）；`cache_dir`（Path）；`model_cache_dir`（Path）；`allow_download`（bool；默认 `False`）。
- 输出类型：`None`；具体返回路径见流程步骤。

**处理流程**：
1. 更新 `self.model_name`，值来自 `model_name`。
2. 更新 `self.model_revision`，值来自 `model_revision`。
3. 更新 `self.device`，值来自 `device`。
4. 更新 `self.use_fp16`，值来自 `use_fp16`。
5. 更新 `self.batch_size`，值来自 `batch_size`。
6. 更新 `self.max_tokens`，值来自 `max_tokens`。
7. 更新 `self.cache_dir`，值来自 `cache_dir`。
8. 更新 `self.model_cache_dir`，值来自 `model_cache_dir`。
9. 更新 `self.allow_download`，值来自 `allow_download`。
10. 调用 `self.cache_dir.mkdir`，结果未直接赋值。
11. 调用 `self.model_cache_dir.mkdir`，结果未直接赋值。
12. 更新 `self._model`，值来自 `None`。
13. 更新 `self._lock`，值来自 `asyncio.Lock()`。

**调用与被调用**：
- `self.cache_dir.mkdir`（[embedding.py:78](../../../src/providers/embedding.py#L78)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `self.model_cache_dir.mkdir`（[embedding.py:79](../../../src/providers/embedding.py#L79)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `asyncio.Lock`（[embedding.py:81](../../../src/providers/embedding.py#L81)）：来自 `asyncio`；具体实现可能由依赖注入或运行时分派决定。
- 静态扫描未定位直接调用方；可能通过路由注册、LangGraph 节点、协议方法或依赖注入动态调用，不据此判断为死代码。

**状态、副作用与异常**：
- 显式状态/容器赋值：`self.model_name`、`self.model_revision`、`self.device`、`self.use_fp16`、`self.batch_size`、`self.max_tokens`、`self.cache_dir`、`self.model_cache_dir`、`self.allow_download`、`self._model`、`self._lock`。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：未见 `raise`；下游异常可能继续上抛。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。


---

# BGEM3EmbeddingProvider.fingerprint ⭐⭐⭐

**位置与等级**：[embedding.py:83](../../../src/providers/embedding.py#L83)；关键支撑逻辑，影响候选、证据或接口的正确传递。

**签名**：`def fingerprint(self) -> str`。

**作用**：处理 `fingerprint` 对应步骤；下列步骤依据函数体的实际控制流和调用点整理。

**输入与输出**：
- 输入：无业务参数（或仅隐式接收实例）。
- 输出类型：`str`；具体返回路径见流程步骤。

**处理流程**：
1. 返回 `canonical_hash({'provider': 'bge-m3', 'model': self.model_name, 'revision': self.model_revision, 'dimens…`。

**调用与被调用**：
- `canonical_hash`（调用点 [embedding.py:84](../../../src/providers/embedding.py#L84)）→ [canonical_hash](../core/ids.md)，静态可定位。
- 静态可定位的调用方：[BGEM3EmbeddingProvider._cache_path](embedding.md)。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：未见 `raise`；下游异常可能继续上抛。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。


---

# BGEM3EmbeddingProvider._cache_path ⭐⭐

**位置与等级**：[embedding.py:95](../../../src/providers/embedding.py#L95)；局部辅助逻辑，需理解其调用条件与失败传播。

**签名**：`def _cache_path(self, text: str) -> Path`。

**作用**：内部辅助步骤；将参数转换为本模块所需的中间对象或操作结果。

**输入与输出**：
- 输入：`text`（str）。
- 输出类型：`Path`；具体返回路径见流程步骤。

**处理流程**：
1. 更新 `key`，值来自 `canonical_hash({'fingerprint': self.fingerprint(), 'text': text})`。
2. 返回 `self.cache_dir / key[:2] / f<字符串常量>`。

**调用与被调用**：
- `canonical_hash`（调用点 [embedding.py:96](../../../src/providers/embedding.py#L96)）→ [canonical_hash](../core/ids.md)，静态可定位。
- `self.fingerprint`（调用点 [embedding.py:96](../../../src/providers/embedding.py#L96)）→ [BGEM3EmbeddingProvider.fingerprint](embedding.md)，静态可定位。
- 静态可定位的调用方：[BGEM3EmbeddingProvider.encode](embedding.md)。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：未见 `raise`；下游异常可能继续上抛。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。


---

# BGEM3EmbeddingProvider._load_model ⭐⭐

**位置与等级**：[embedding.py:99](../../../src/providers/embedding.py#L99)；局部辅助逻辑，需理解其调用条件与失败传播。

**签名**：`def _load_model(self) -> Any`。

**作用**：内部辅助步骤；将参数转换为本模块所需的中间对象或操作结果。

**输入与输出**：
- 输入：无业务参数（或仅隐式接收实例）。
- 输出类型：`Any`；具体返回路径见流程步骤。

**处理流程**：
1. 检查 `self._model is None`；按条件分流，else 分支不存在。
2. 返回 `self._model`。

**关键条件与保护**：
- [embedding.py:100](../../../src/providers/embedding.py#L100)：`self._model is None`，不满足时跳过本分支。
- [embedding.py:111](../../../src/providers/embedding.py#L111)：`self.device.startswith('cuda') and (not torch.cuda.is_available())`，不满足时跳过本分支。

**调用与被调用**：
- `os.environ.setdefault`（[embedding.py:101](../../../src/providers/embedding.py#L101)）：来自 `os`；具体实现可能由依赖注入或运行时分派决定。
- `str`（[embedding.py:101](../../../src/providers/embedding.py#L101)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `self.model_cache_dir.resolve`（[embedding.py:101](../../../src/providers/embedding.py#L101)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `RuntimeError`（[embedding.py:108](../../../src/providers/embedding.py#L108)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `self.device.startswith`（[embedding.py:111](../../../src/providers/embedding.py#L111)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `torch.cuda.is_available`（[embedding.py:111](../../../src/providers/embedding.py#L111)）：来自 `torch`；具体实现可能由依赖注入或运行时分派决定。
- `Path`（[embedding.py:115](../../../src/providers/embedding.py#L115)）：来自 `pathlib.Path`；具体实现可能由依赖注入或运行时分派决定。
- `model_path.exists`（[embedding.py:119](../../../src/providers/embedding.py#L119)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `snapshot_download`（[embedding.py:120](../../../src/providers/embedding.py#L120)）：来自 `huggingface_hub.snapshot_download`；具体实现可能由依赖注入或运行时分派决定。
- `BGEM3FlagModel`（[embedding.py:146](../../../src/providers/embedding.py#L146)）：来自 `FlagEmbedding.BGEM3FlagModel`；具体实现可能由依赖注入或运行时分派决定。
- 静态可定位的调用方：[BGEM3EmbeddingProvider._encode_missing](embedding.md)。

**状态、副作用与异常**：
- 显式状态/容器赋值：`self._model`。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：`RuntimeError(<字符串常量>)`。
- 本地捕获：`ImportError`、`LocalEntryNotFoundError`。


---

# BGEM3EmbeddingProvider._encode_missing ⭐⭐

**位置与等级**：[embedding.py:153](../../../src/providers/embedding.py#L153)；局部辅助逻辑，需理解其调用条件与失败传播。

**签名**：`def _encode_missing(self, texts: list[str]) -> list[list[float]]`。

**作用**：内部辅助步骤；将参数转换为本模块所需的中间对象或操作结果。

**输入与输出**：
- 输入：`texts`（list[str]）。
- 输出类型：`list[list[float]]`；具体返回路径见流程步骤。

**处理流程**：
1. 更新 `model`，值来自 `self._load_model()`。
2. 进入上下文 `torch.inference_mode()`，由上下文管理器控制资源释放或事务范围。
3. 更新 `vectors`，值来自 `result['dense_vecs']`。
4. 返回 `[[float(value) for value in vector] for vector in vectors]`。

**调用与被调用**：
- `self._load_model`（调用点 [embedding.py:156](../../../src/providers/embedding.py#L156)）→ [BGEM3EmbeddingProvider._load_model](embedding.md)，静态可定位。
- `torch.inference_mode`（[embedding.py:157](../../../src/providers/embedding.py#L157)）：来自 `torch`；具体实现可能由依赖注入或运行时分派决定。
- `model.encode`（[embedding.py:158](../../../src/providers/embedding.py#L158)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `float`（[embedding.py:167](../../../src/providers/embedding.py#L167)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- 静态扫描未定位直接调用方；可能通过路由注册、LangGraph 节点、协议方法或依赖注入动态调用，不据此判断为死代码。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：未见 `raise`；下游异常可能继续上抛。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。


---

# BGEM3EmbeddingProvider.encode ⭐⭐⭐

**位置与等级**：[embedding.py:169](../../../src/providers/embedding.py#L169)；关键支撑逻辑，影响候选、证据或接口的正确传递。

**签名**：`async def encode(self, texts: list[str]) -> list[list[float]]`。

**作用**：处理 `encode` 对应步骤；下列步骤依据函数体的实际控制流和调用点整理。

**输入与输出**：
- 输入：`texts`（list[str]）。
- 输出类型：`list[list[float]]`；具体返回路径见流程步骤。

**处理流程**：
1. 检查 `not texts`；按条件分流，else 分支不存在。
2. 进入上下文 `self._lock`，由上下文管理器控制资源释放或事务范围。

**关键条件与保护**：
- [embedding.py:170](../../../src/providers/embedding.py#L170)：`not texts`，不满足时跳过本分支。
- [embedding.py:178](../../../src/providers/embedding.py#L178)：`path.is_file()`，不满足时跳过本分支。
- [embedding.py:182](../../../src/providers/embedding.py#L182)：`len(vector) == self.dimension and all((math.isfinite(value) for value in vector))`，不满足时跳过本分支。
- [embedding.py:191](../../../src/providers/embedding.py#L191)：`missing_texts`，不满足时跳过本分支。
- [embedding.py:196](../../../src/providers/embedding.py#L196)：`len(vector) != self.dimension`，不满足时跳过本分支。
- [embedding.py:200](../../../src/providers/embedding.py#L200)：`not all((math.isfinite(value) for value in vector))`，不满足时跳过本分支。

**调用与被调用**：
- `len`（[embedding.py:173](../../../src/providers/embedding.py#L173)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `enumerate`（[embedding.py:176](../../../src/providers/embedding.py#L176)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `self._cache_path`（调用点 [embedding.py:177](../../../src/providers/embedding.py#L177)）→ [BGEM3EmbeddingProvider._cache_path](embedding.md)，静态可定位。
- `path.is_file`（[embedding.py:178](../../../src/providers/embedding.py#L178)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `json.loads`（[embedding.py:180](../../../src/providers/embedding.py#L180)）：来自 `json`；具体实现可能由依赖注入或运行时分派决定。
- `path.read_text`（[embedding.py:180](../../../src/providers/embedding.py#L180)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `float`（[embedding.py:181](../../../src/providers/embedding.py#L181)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `all`（[embedding.py:182](../../../src/providers/embedding.py#L182)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `math.isfinite`（[embedding.py:183](../../../src/providers/embedding.py#L183)）：来自 `math`；具体实现可能由依赖注入或运行时分派决定。
- `missing_texts.append`（[embedding.py:189](../../../src/providers/embedding.py#L189)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `missing_indexes.append`（[embedding.py:190](../../../src/providers/embedding.py#L190)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `asyncio.to_thread`（[embedding.py:192](../../../src/providers/embedding.py#L192)）：来自 `asyncio`；具体实现可能由依赖注入或运行时分派决定。
- `zip`（[embedding.py:193](../../../src/providers/embedding.py#L193)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `ValueError`（[embedding.py:197](../../../src/providers/embedding.py#L197)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `path.parent.mkdir`（[embedding.py:203](../../../src/providers/embedding.py#L203)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `path.with_name`（[embedding.py:204](../../../src/providers/embedding.py#L204)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `uuid4`（[embedding.py:204](../../../src/providers/embedding.py#L204)）：来自 `uuid.uuid4`；具体实现可能由依赖注入或运行时分派决定。
- `temporary.open`（[embedding.py:206](../../../src/providers/embedding.py#L206)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `json.dump`（[embedding.py:207](../../../src/providers/embedding.py#L207)）：来自 `json`；具体实现可能由依赖注入或运行时分派决定。
- `stream.flush`（[embedding.py:208](../../../src/providers/embedding.py#L208)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `os.fsync`（[embedding.py:209](../../../src/providers/embedding.py#L209)）：来自 `os`；具体实现可能由依赖注入或运行时分派决定。
- `stream.fileno`（[embedding.py:209](../../../src/providers/embedding.py#L209)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `os.replace`（[embedding.py:210](../../../src/providers/embedding.py#L210)）：来自 `os`；具体实现可能由依赖注入或运行时分派决定。
- `temporary.unlink`（[embedding.py:212](../../../src/providers/embedding.py#L212)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- 静态扫描未定位直接调用方；可能通过路由注册、LangGraph 节点、协议方法或依赖注入动态调用，不据此判断为死代码。

**状态、副作用与异常**：
- 显式状态/容器赋值：`output[index]`。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：`ValueError(f<字符串常量>)`、`ValueError(<字符串常量>)`。
- 本地捕获：`(OSError, ValueError, KeyError, TypeError)`。


---
