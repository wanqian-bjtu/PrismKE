源码：[ocr.py:1](../../../src/providers/ocr.py#L1) | 基准：`dev/v0.10@f2f34d7` | 本文件符号数：12

**模块职责**：Disabled, mock, and PaddleOCR implementations.
**在系统中的位置**：LLM、OCR、VLM、Embedding、Reflection 与语义建议的外部能力接口和实现。
**直接依赖**：[src.core.execution_control](../core/execution_control.md)、[src.core.ids](../core/ids.md)、[src.domain](../domain/__init__.md)、[src.parsing.visual_assets](../parsing/visual_assets.md)；外部/标准库：`__future__`、`asyncio`、`importlib`、`typing`。
**主要调用方（静态导入）**：[providers/__init__.py](__init__.md)。
**阅读提示**：下列流程根据当前源码控制流整理；`self`/接口对象的实际类型可能在运行时注入，未能静态解析的调用会明确标注。链接指向源码行或对应讲解文件。

---

# DisabledOCRProvider ⭐⭐⭐

**位置与等级**：[ocr.py:25](../../../src/providers/ocr.py#L25)；关键支撑逻辑，影响候选、证据或接口的正确传递。

**职责**：外部能力实现或协议；调用是否耗费模型额度取决于具体实现。基类：无显式基类。

**字段与类级约束**：
- 类体未直接声明字段；实例状态请看 `__init__` 及方法中的赋值。

**内部成员**：`DisabledOCRProvider.fingerprint`、`DisabledOCRProvider.recognize`


---

# DisabledOCRProvider.fingerprint ⭐⭐⭐

**位置与等级**：[ocr.py:26](../../../src/providers/ocr.py#L26)；关键支撑逻辑，影响候选、证据或接口的正确传递。

**签名**：`def fingerprint(self) -> str`。

**作用**：处理 `fingerprint` 对应步骤；下列步骤依据函数体的实际控制流和调用点整理。

**输入与输出**：
- 输入：无业务参数（或仅隐式接收实例）。
- 输出类型：`str`；具体返回路径见流程步骤。

**处理流程**：
1. 返回 `'disabled'`。

**调用与被调用**：
- 无显式函数调用，或仅声明协议/常量。
- 静态扫描未定位直接调用方；可能通过路由注册、LangGraph 节点、协议方法或依赖注入动态调用，不据此判断为死代码。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：未见 `raise`；下游异常可能继续上抛。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。


---

# DisabledOCRProvider.recognize ⭐⭐⭐

**位置与等级**：[ocr.py:29](../../../src/providers/ocr.py#L29)；关键支撑逻辑，影响候选、证据或接口的正确传递。

**签名**：`async def recognize(self, request: OCRRequest) -> OCRResult`。

**作用**：处理 `recognize` 对应步骤；下列步骤依据函数体的实际控制流和调用点整理。

**输入与输出**：
- 输入：`request`（OCRRequest）。
- 输出类型：`OCRResult`；具体返回路径见流程步骤。

**处理流程**：
1. 返回 `OCRResult()`。

**调用与被调用**：
- `OCRResult`（[ocr.py:31](../../../src/providers/ocr.py#L31)）：来自 `src.domain.OCRResult`；具体实现可能由依赖注入或运行时分派决定。
- 静态扫描未定位直接调用方；可能通过路由注册、LangGraph 节点、协议方法或依赖注入动态调用，不据此判断为死代码。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：未见 `raise`；下游异常可能继续上抛。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。


---

# MockOCRProvider ⭐⭐⭐

**位置与等级**：[ocr.py:34](../../../src/providers/ocr.py#L34)；关键支撑逻辑，影响候选、证据或接口的正确传递。

**职责**：外部能力实现或协议；调用是否耗费模型额度取决于具体实现。基类：`DisabledOCRProvider`。

**字段与类级约束**：
- 类体未直接声明字段；实例状态请看 `__init__` 及方法中的赋值。

**内部成员**：`MockOCRProvider.fingerprint`


---

# MockOCRProvider.fingerprint ⭐⭐⭐

**位置与等级**：[ocr.py:35](../../../src/providers/ocr.py#L35)；关键支撑逻辑，影响候选、证据或接口的正确传递。

**签名**：`def fingerprint(self) -> str`。

**作用**：处理 `fingerprint` 对应步骤；下列步骤依据函数体的实际控制流和调用点整理。

**输入与输出**：
- 输入：无业务参数（或仅隐式接收实例）。
- 输出类型：`str`；具体返回路径见流程步骤。

**处理流程**：
1. 返回 `stable_id('provider', 'mock-ocr', 'v1')`。

**调用与被调用**：
- `stable_id`（调用点 [ocr.py:36](../../../src/providers/ocr.py#L36)）→ [stable_id](../core/ids.md)，静态可定位。
- 静态扫描未定位直接调用方；可能通过路由注册、LangGraph 节点、协议方法或依赖注入动态调用，不据此判断为死代码。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：未见 `raise`；下游异常可能继续上抛。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。


---

# PaddleOCRProvider ⭐⭐⭐

**位置与等级**：[ocr.py:39](../../../src/providers/ocr.py#L39)；关键支撑逻辑，影响候选、证据或接口的正确传递。

**职责**：外部能力实现或协议；调用是否耗费模型额度取决于具体实现。基类：无显式基类。

**字段与类级约束**：
- 类体未直接声明字段；实例状态请看 `__init__` 及方法中的赋值。

**内部成员**：`PaddleOCRProvider.__init__`、`PaddleOCRProvider.fingerprint`、`PaddleOCRProvider._get_engine`、`PaddleOCRProvider._payload`、`PaddleOCRProvider._recognize_sync`、`PaddleOCRProvider.recognize`


---

# PaddleOCRProvider.__init__ ⭐⭐⭐

**位置与等级**：[ocr.py:40](../../../src/providers/ocr.py#L40)；关键支撑逻辑，影响候选、证据或接口的正确传递。

**签名**：`def __init__(self, device: str='cpu', lang: str='ch', model: str='PP-OCRv5') -> None`。

**作用**：初始化对象并保存依赖或配置；需检查是否创建持久化资源。

**输入与输出**：
- 输入：`device`（str；默认 `'cpu'`）；`lang`（str；默认 `'ch'`）；`model`（str；默认 `'PP-OCRv5'`）。
- 输出类型：`None`；具体返回路径见流程步骤。

**处理流程**：
1. 更新 `(self.device, self.lang, self.model)`，值来自 `(device, lang, model)`。
2. 更新 `self._engine`，值来自 `None`。

**调用与被调用**：
- 无显式函数调用，或仅声明协议/常量。
- 静态扫描未定位直接调用方；可能通过路由注册、LangGraph 节点、协议方法或依赖注入动态调用，不据此判断为死代码。

**状态、副作用与异常**：
- 显式状态/容器赋值：`self._engine`。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：未见 `raise`；下游异常可能继续上抛。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。


---

# PaddleOCRProvider.fingerprint ⭐⭐⭐

**位置与等级**：[ocr.py:44](../../../src/providers/ocr.py#L44)；关键支撑逻辑，影响候选、证据或接口的正确传递。

**签名**：`def fingerprint(self) -> str`。

**作用**：处理 `fingerprint` 对应步骤；下列步骤依据函数体的实际控制流和调用点整理。

**输入与输出**：
- 输入：无业务参数（或仅隐式接收实例）。
- 输出类型：`str`；具体返回路径见流程步骤。

**处理流程**：
1. 返回 `stable_id('provider', 'paddleocr', self.device, self.lang, self.model, 'v2')`。

**调用与被调用**：
- `stable_id`（调用点 [ocr.py:45](../../../src/providers/ocr.py#L45)）→ [stable_id](../core/ids.md)，静态可定位。
- 静态扫描未定位直接调用方；可能通过路由注册、LangGraph 节点、协议方法或依赖注入动态调用，不据此判断为死代码。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：未见 `raise`；下游异常可能继续上抛。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。


---

# PaddleOCRProvider._get_engine ⭐⭐

**位置与等级**：[ocr.py:47](../../../src/providers/ocr.py#L47)；局部辅助逻辑，需理解其调用条件与失败传播。

**签名**：`def _get_engine(self) -> Any`。

**作用**：内部辅助步骤；将参数转换为本模块所需的中间对象或操作结果。

**输入与输出**：
- 输入：无业务参数（或仅隐式接收实例）。
- 输出类型：`Any`；具体返回路径见流程步骤。

**处理流程**：
1. 检查 `self._engine is None`；按条件分流，else 分支不存在。
2. 返回 `self._engine`。

**关键条件与保护**：
- [ocr.py:48](../../../src/providers/ocr.py#L48)：`self._engine is None`，不满足时跳过本分支。
- [ocr.py:54](../../../src/providers/ocr.py#L54)：`self.device == 'cpu'`，不满足时跳过本分支。

**调用与被调用**：
- `import_module`（[ocr.py:50](../../../src/providers/ocr.py#L50)）：来自 `importlib.import_module`；具体实现可能由依赖注入或运行时分派决定。
- `RuntimeError`（[ocr.py:52](../../../src/providers/ocr.py#L52)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `paddleocr.PaddleOCR`（[ocr.py:56](../../../src/providers/ocr.py#L56)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- 静态可定位的调用方：[PaddleOCRProvider._recognize_sync](ocr.md)。

**状态、副作用与异常**：
- 显式状态/容器赋值：`engine_options['enable_mkldnn']`、`self._engine`。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：`RuntimeError(<字符串常量>)`。
- 本地捕获：`ImportError`。


---

# PaddleOCRProvider._payload ⭐⭐

**位置与等级**：[ocr.py:68](../../../src/providers/ocr.py#L68)；局部辅助逻辑，需理解其调用条件与失败传播。

**签名**：`def _payload(result: Any) -> dict[str, Any]`。

**装饰器/路由**：`staticmethod`。

**作用**：内部辅助步骤；将参数转换为本模块所需的中间对象或操作结果。

**输入与输出**：
- 输入：`result`（Any）。
- 输出类型：`dict[str, Any]`；具体返回路径见流程步骤。

**处理流程**：
1. 更新 `value`，值来自 `getattr(result, 'json', {})`。
2. 检查 `callable(value)`；按条件分流，else 分支不存在。
3. 检查 `not isinstance(value, dict)`；按条件分流，else 分支不存在。
4. 更新 `nested`，值来自 `value.get('res', value)`。
5. 返回 `nested if isinstance(nested, dict) else {}`。

**关键条件与保护**：
- [ocr.py:70](../../../src/providers/ocr.py#L70)：`callable(value)`，不满足时跳过本分支。
- [ocr.py:72](../../../src/providers/ocr.py#L72)：`not isinstance(value, dict)`，不满足时跳过本分支。

**调用与被调用**：
- `getattr`（[ocr.py:69](../../../src/providers/ocr.py#L69)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `callable`（[ocr.py:70](../../../src/providers/ocr.py#L70)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `value`（[ocr.py:71](../../../src/providers/ocr.py#L71)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `isinstance`（[ocr.py:72](../../../src/providers/ocr.py#L72)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `value.get`（[ocr.py:74](../../../src/providers/ocr.py#L74)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- 静态可定位的调用方：[PaddleOCRProvider._recognize_sync](ocr.md)。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：未见 `raise`；下游异常可能继续上抛。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。


---

# PaddleOCRProvider._recognize_sync ⭐⭐

**位置与等级**：[ocr.py:77](../../../src/providers/ocr.py#L77)；局部辅助逻辑，需理解其调用条件与失败传播。

**签名**：`def _recognize_sync(self, request: OCRRequest) -> OCRResult`。

**作用**：内部辅助步骤；将参数转换为本模块所需的中间对象或操作结果。

**输入与输出**：
- 输入：`request`（OCRRequest）。
- 输出类型：`OCRResult`；具体返回路径见流程步骤。

**处理流程**：
1. 更新 `blocks`，值来自 `[]`。
2. 更新 `evidence`，值来自 `[]`。
3. 更新 `warnings`，值来自 `[]`。
4. 更新 `assets`，值来自 `[asset for asset in select_analysis_assets(request.document) if not (asset.origin == 'pdf_page_rend…`。
5. 检查 `not assets`；按条件分流，else 分支不存在。
6. 更新 `engine`，值来自 `self._get_engine()`。
7. 遍历 `assets`，逐项处理 `asset`。
8. 返回 `OCRResult(text_blocks=blocks, evidence=evidence, warnings=warnings)`。

**关键条件与保护**：
- [ocr.py:86](../../../src/providers/ocr.py#L86)：`not assets`，不满足时跳过本分支。
- [ocr.py:99](../../../src/providers/ocr.py#L99)：`not text`，不满足时跳过本分支。
- [ocr.py:104](../../../src/providers/ocr.py#L104)：`polygon is not None`，不满足时跳过本分支。
- [ocr.py:141](../../../src/providers/ocr.py#L141)：`score < 0.5`，不满足时跳过本分支。

**调用与被调用**：
- `select_analysis_assets`（调用点 [ocr.py:83](../../../src/providers/ocr.py#L83)）→ [select_analysis_assets](../parsing/visual_assets.md)，静态可定位。
- `OCRResult`（[ocr.py:87](../../../src/providers/ocr.py#L87)）：来自 `src.domain.OCRResult`；具体实现可能由依赖注入或运行时分派决定。
- `self._get_engine`（调用点 [ocr.py:88](../../../src/providers/ocr.py#L88)）→ [PaddleOCRProvider._get_engine](ocr.md)，静态可定位。
- `check_execution`（调用点 [ocr.py:90](../../../src/providers/ocr.py#L90)）→ [check_execution](../core/execution_control.md)，静态可定位。
- `enumerate`（[ocr.py:92](../../../src/providers/ocr.py#L92)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `engine.predict`（[ocr.py:92](../../../src/providers/ocr.py#L92)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `self._payload`（调用点 [ocr.py:93](../../../src/providers/ocr.py#L93)）→ [PaddleOCRProvider._payload](ocr.md)，静态可定位。
- `payload.get`（[ocr.py:94](../../../src/providers/ocr.py#L94)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `str(raw_text).strip`（[ocr.py:98](../../../src/providers/ocr.py#L98)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `str`（[ocr.py:98](../../../src/providers/ocr.py#L98)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `len`（[ocr.py:101](../../../src/providers/ocr.py#L101)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `float`（[ocr.py:101](../../../src/providers/ocr.py#L101)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `list`（[ocr.py:105](../../../src/providers/ocr.py#L105)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `BBox`（[ocr.py:108](../../../src/providers/ocr.py#L108)）：来自 `src.domain.BBox`；具体实现可能由依赖注入或运行时分派决定。
- `min`（[ocr.py:108](../../../src/providers/ocr.py#L108)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `max`（[ocr.py:108](../../../src/providers/ocr.py#L108)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `stable_id`（调用点 [ocr.py:109](../../../src/providers/ocr.py#L109)）→ [stable_id](../core/ids.md)，静态可定位。
- `TextBlock`（[ocr.py:112](../../../src/providers/ocr.py#L112)）：来自 `src.domain.TextBlock`；具体实现可能由依赖注入或运行时分派决定。
- `EvidenceRef`（[ocr.py:122](../../../src/providers/ocr.py#L122)）：来自 `src.domain.EvidenceRef`；具体实现可能由依赖注入或运行时分派决定。
- `blocks.append`（[ocr.py:139](../../../src/providers/ocr.py#L139)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `evidence.append`（[ocr.py:140](../../../src/providers/ocr.py#L140)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `warnings.append`（[ocr.py:142](../../../src/providers/ocr.py#L142)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `type`（[ocr.py:148](../../../src/providers/ocr.py#L148)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- 静态扫描未定位直接调用方；可能通过路由注册、LangGraph 节点、协议方法或依赖注入动态调用，不据此判断为死代码。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：`重新抛出`。
- 本地捕获：`ExecutionPaused`、`Exception`。


---

# PaddleOCRProvider.recognize ⭐⭐⭐

**位置与等级**：[ocr.py:151](../../../src/providers/ocr.py#L151)；关键支撑逻辑，影响候选、证据或接口的正确传递。

**签名**：`async def recognize(self, request: OCRRequest) -> OCRResult`。

**作用**：处理 `recognize` 对应步骤；下列步骤依据函数体的实际控制流和调用点整理。

**输入与输出**：
- 输入：`request`（OCRRequest）。
- 输出类型：`OCRResult`；具体返回路径见流程步骤。

**处理流程**：
1. 返回 `await asyncio.to_thread(self._recognize_sync, request)`。

**调用与被调用**：
- `asyncio.to_thread`（[ocr.py:152](../../../src/providers/ocr.py#L152)）：来自 `asyncio`；具体实现可能由依赖注入或运行时分派决定。
- 静态扫描未定位直接调用方；可能通过路由注册、LangGraph 节点、协议方法或依赖注入动态调用，不据此判断为死代码。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：未见 `raise`；下游异常可能继续上抛。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。


---
