源码：[vlm.py:1](../../../src/providers/vlm.py#L1) | 基准：`dev/v0.10@f2f34d7` | 本文件符号数：12

**模块职责**：OpenAI-compatible multimodal extraction provider.
**在系统中的位置**：LLM、OCR、VLM、Embedding、Reflection 与语义建议的外部能力接口和实现。
**直接依赖**：[src.core.errors](../core/errors.md)、[src.core.ids](../core/ids.md)、[src.domain](../domain/__init__.md)、[src.governance.validation](../governance/validation/__init__.md)、[src.providers.common](common.md)、[src.providers.http_client](http_client.md)、[src.providers.validation](validation.md)；外部/标准库：`PIL`、`__future__`、`base64`、`httpx`、`io`、`json`、`math`、`typing`。
**主要调用方（静态导入）**：[evaluation/document_validation.py](../evaluation/document_validation.md)、[providers/__init__.py](__init__.md)。
**阅读提示**：下列流程根据当前源码控制流整理；`self`/接口对象的实际类型可能在运行时注入，未能静态解析的调用会明确标注。链接指向源码行或对应讲解文件。

---

# _visual_prompt ⭐⭐

**位置与等级**：[vlm.py:42](../../../src/providers/vlm.py#L42)；局部辅助逻辑，需理解其调用条件与失败传播。

**签名**：`def _visual_prompt(request: VisualExtractionRequest) -> str`。

**作用**：内部辅助步骤；将参数转换为本模块所需的中间对象或操作结果。

**输入与输出**：
- 输入：`request`（VisualExtractionRequest）。
- 输出类型：`str`；具体返回路径见流程步骤。

**处理流程**：
1. 更新 `ocr_text`，值来自 `[block.text for block in request.ocr_blocks]`。
2. 返回 `f<字符串常量>`。

**调用与被调用**：
- `request.output_schema.model_dump_json`（[vlm.py:63](../../../src/providers/vlm.py#L63)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `json.dumps`（[vlm.py:64](../../../src/providers/vlm.py#L64)）：来自 `json`；具体实现可能由依赖注入或运行时分派决定。
- 静态可定位的调用方：[OpenAICompatibleVLMProvider.extract](vlm.md)。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：未见 `raise`；下游异常可能继续上抛。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。


---

# _candidate_names ⭐⭐

**位置与等级**：[vlm.py:69](../../../src/providers/vlm.py#L69)；局部辅助逻辑，需理解其调用条件与失败传播。

**签名**：`def _candidate_names(candidate: CandidateClaim) -> list[str]`。

**作用**：内部辅助步骤；将参数转换为本模块所需的中间对象或操作结果。

**输入与输出**：
- 输入：`candidate`（CandidateClaim；尚未成为正式 Claim 的候选）。
- 输出类型：`list[str]`；具体返回路径见流程步骤。

**处理流程**：
1. 更新 `names`，值来自 `[candidate.subject.name]`。
2. 更新 `obj`，值来自 `candidate.object.name if isinstance(candidate.object, EntityMention) else candidate.object`。
3. 调用 `names.append`，结果未直接赋值。
4. 返回 `[str(name) for name in names if str(name).strip()]`。

**调用与被调用**：
- `isinstance`（[vlm.py:71](../../../src/providers/vlm.py#L71)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `names.append`（[vlm.py:72](../../../src/providers/vlm.py#L72)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `str`（[vlm.py:73](../../../src/providers/vlm.py#L73)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `str(name).strip`（[vlm.py:73](../../../src/providers/vlm.py#L73)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- 静态可定位的调用方：[_is_context_only_visual_claim](vlm.md)。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：未见 `raise`；下游异常可能继续上抛。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。


---

# _is_context_only_visual_claim ⭐⭐

**位置与等级**：[vlm.py:76](../../../src/providers/vlm.py#L76)；局部辅助逻辑，需理解其调用条件与失败传播。

**签名**：`def _is_context_only_visual_claim(candidate: CandidateClaim, observation: VisualObservation | None, ocr_text: str, auxiliary_context: str) -> bool`。

**作用**：内部辅助步骤；将参数转换为本模块所需的中间对象或操作结果。

**输入与输出**：
- 输入：`candidate`（CandidateClaim；尚未成为正式 Claim 的候选）；`observation`（VisualObservation | None）；`ocr_text`（str）；`auxiliary_context`（str）。
- 输出类型：`bool`；具体返回路径见流程步骤。

**处理流程**：
1. 更新 `primary_parts`，值来自 `[ocr_text]`。
2. 检查 `observation is not None`；按条件分流，else 分支不存在。
3. 更新 `primary`，值来自 `normalize_label(<字符串常量>.join(primary_parts))`。
4. 更新 `auxiliary`，值来自 `normalize_label(auxiliary_context)`。
5. 遍历 `_candidate_names(candidate)`，逐项处理 `name`。
6. 返回 `False`。

**关键条件与保护**：
- [vlm.py:83](../../../src/providers/vlm.py#L83)：`observation is not None`，不满足时跳过本分支。
- [vlm.py:95](../../../src/providers/vlm.py#L95)：`normalized and normalized in auxiliary and (normalized not in primary)`，不满足时跳过本分支。

**调用与被调用**：
- `primary_parts.extend`（[vlm.py:84](../../../src/providers/vlm.py#L84)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `json.dumps`（[vlm.py:88](../../../src/providers/vlm.py#L88)）：来自 `json`；具体实现可能由依赖注入或运行时分派决定。
- `normalize_label`（[vlm.py:91](../../../src/providers/vlm.py#L91)）：来自 `src.domain.normalize_label`；具体实现可能由依赖注入或运行时分派决定。
- `<字符串常量>.join`（[vlm.py:91](../../../src/providers/vlm.py#L91)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `_candidate_names`（调用点 [vlm.py:93](../../../src/providers/vlm.py#L93)）→ [_candidate_names](vlm.md)，静态可定位。
- 静态可定位的调用方：[OpenAICompatibleVLMProvider.extract](vlm.md)。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：未见 `raise`；下游异常可能继续上抛。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。


---

# DisabledVLMProvider ⭐⭐⭐

**位置与等级**：[vlm.py:100](../../../src/providers/vlm.py#L100)；关键支撑逻辑，影响候选、证据或接口的正确传递。

**职责**：外部能力实现或协议；调用是否耗费模型额度取决于具体实现。基类：无显式基类。

**字段与类级约束**：
- 类体未直接声明字段；实例状态请看 `__init__` 及方法中的赋值。

**内部成员**：`DisabledVLMProvider.fingerprint`、`DisabledVLMProvider.extract`


---

# DisabledVLMProvider.fingerprint ⭐⭐⭐

**位置与等级**：[vlm.py:101](../../../src/providers/vlm.py#L101)；关键支撑逻辑，影响候选、证据或接口的正确传递。

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

# DisabledVLMProvider.extract ⭐⭐⭐⭐

**位置与等级**：[vlm.py:104](../../../src/providers/vlm.py#L104)；承担主要 Agent、应用服务或审核/执行入口，跨模块影响显著。

**签名**：`async def extract(self, request: VisualExtractionRequest) -> ExtractionResult`。

**作用**：处理 `extract` 对应步骤；下列步骤依据函数体的实际控制流和调用点整理。

**输入与输出**：
- 输入：`request`（VisualExtractionRequest）。
- 输出类型：`ExtractionResult`；具体返回路径见流程步骤。

**处理流程**：
1. 返回 `ExtractionResult()`。

**调用与被调用**：
- `ExtractionResult`（[vlm.py:106](../../../src/providers/vlm.py#L106)）：来自 `src.domain.ExtractionResult`；具体实现可能由依赖注入或运行时分派决定。
- 静态扫描未定位直接调用方；可能通过路由注册、LangGraph 节点、协议方法或依赖注入动态调用，不据此判断为死代码。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：未见 `raise`；下游异常可能继续上抛。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。


---

# OpenAICompatibleVLMProvider ⭐⭐⭐

**位置与等级**：[vlm.py:109](../../../src/providers/vlm.py#L109)；关键支撑逻辑，影响候选、证据或接口的正确传递。

**职责**：外部能力实现或协议；调用是否耗费模型额度取决于具体实现。基类：无显式基类。

**字段与类级约束**：
- 类体未直接声明字段；实例状态请看 `__init__` 及方法中的赋值。

**内部成员**：`OpenAICompatibleVLMProvider.__init__`、`OpenAICompatibleVLMProvider.fingerprint`、`OpenAICompatibleVLMProvider._image_data_url`、`OpenAICompatibleVLMProvider._post`、`OpenAICompatibleVLMProvider.extract`


---

# OpenAICompatibleVLMProvider.__init__ ⭐⭐⭐

**位置与等级**：[vlm.py:110](../../../src/providers/vlm.py#L110)；关键支撑逻辑，影响候选、证据或接口的正确传递。

**签名**：`def __init__(self, base_url: str, api_key: str, model: str, timeout: float=120.0, max_image_edge: int=2048, transport: httpx.AsyncBaseTransport | None=None) -> None`。

**作用**：初始化对象并保存依赖或配置；需检查是否创建持久化资源。

**输入与输出**：
- 输入：`base_url`（str）；`api_key`（str）；`model`（str）；`timeout`（float；默认 `120.0`）；`max_image_edge`（int；默认 `2048`）；`transport`（httpx.AsyncBaseTransport | None；默认 `None`）。
- 输出类型：`None`；具体返回路径见流程步骤。

**处理流程**：
1. 更新 `self.base_url`，值来自 `base_url.rstrip('/')`。
2. 更新 `self.api_key`，值来自 `api_key`。
3. 更新 `self.model`，值来自 `model`。
4. 更新 `self.timeout`，值来自 `timeout`。
5. 更新 `self.max_image_edge`，值来自 `max_image_edge`。
6. 更新 `self.transport`，值来自 `transport`。

**调用与被调用**：
- `base_url.rstrip`（[vlm.py:119](../../../src/providers/vlm.py#L119)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- 静态扫描未定位直接调用方；可能通过路由注册、LangGraph 节点、协议方法或依赖注入动态调用，不据此判断为死代码。

**状态、副作用与异常**：
- 显式状态/容器赋值：`self.base_url`、`self.api_key`、`self.model`、`self.timeout`、`self.max_image_edge`、`self.transport`。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：未见 `raise`；下游异常可能继续上抛。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。


---

# OpenAICompatibleVLMProvider.fingerprint ⭐⭐⭐

**位置与等级**：[vlm.py:126](../../../src/providers/vlm.py#L126)；关键支撑逻辑，影响候选、证据或接口的正确传递。

**签名**：`def fingerprint(self) -> str`。

**作用**：处理 `fingerprint` 对应步骤；下列步骤依据函数体的实际控制流和调用点整理。

**输入与输出**：
- 输入：无业务参数（或仅隐式接收实例）。
- 输出类型：`str`；具体返回路径见流程步骤。

**处理流程**：
1. 返回 `stable_id('provider', 'openai-compatible-vlm', self.base_url.casefold(), self.model, PROMPT_VERSION, PRO…`。

**调用与被调用**：
- `stable_id`（调用点 [vlm.py:127](../../../src/providers/vlm.py#L127)）→ [stable_id](../core/ids.md)，静态可定位。
- `self.base_url.casefold`（[vlm.py:130](../../../src/providers/vlm.py#L130)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- 静态可定位的调用方：[OpenAICompatibleVLMProvider._post](vlm.md)。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：未见 `raise`；下游异常可能继续上抛。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。


---

# OpenAICompatibleVLMProvider._image_data_url ⭐⭐

**位置与等级**：[vlm.py:137](../../../src/providers/vlm.py#L137)；局部辅助逻辑，需理解其调用条件与失败传播。

**签名**：`def _image_data_url(self, path: str) -> str`。

**作用**：内部辅助步骤；将参数转换为本模块所需的中间对象或操作结果。

**输入与输出**：
- 输入：`path`（str）。
- 输出类型：`str`；具体返回路径见流程步骤。

**处理流程**：
1. 进入上下文 `Image.open(path)`，由上下文管理器控制资源释放或事务范围。
2. 返回 `f<字符串常量>ascii<字符串常量>`。

**关键条件与保护**：
- [vlm.py:141](../../../src/providers/vlm.py#L141)：`image.mode not in {'RGB', 'RGBA', 'L', 'LA', 'P', '1'}`，不满足时跳过本分支。
- [vlm.py:143](../../../src/providers/vlm.py#L143)：`max(image.size) > self.max_image_edge`，不满足时跳过本分支。

**调用与被调用**：
- `Image.open`（[vlm.py:138](../../../src/providers/vlm.py#L138)）：来自 `PIL.Image`；具体实现可能由依赖注入或运行时分派决定。
- `image.load`（[vlm.py:140](../../../src/providers/vlm.py#L140)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `image.convert`（[vlm.py:142](../../../src/providers/vlm.py#L142)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `max`（[vlm.py:143](../../../src/providers/vlm.py#L143)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `image.thumbnail`（[vlm.py:144](../../../src/providers/vlm.py#L144)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `BytesIO`（[vlm.py:145](../../../src/providers/vlm.py#L145)）：来自 `io.BytesIO`；具体实现可能由依赖注入或运行时分派决定。
- `image.save`（[vlm.py:146](../../../src/providers/vlm.py#L146)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `base64.b64encode(output.getvalue()).decode`（[vlm.py:147](../../../src/providers/vlm.py#L147)）：来自 `base64`；具体实现可能由依赖注入或运行时分派决定。
- `base64.b64encode`（[vlm.py:147](../../../src/providers/vlm.py#L147)）：来自 `base64`；具体实现可能由依赖注入或运行时分派决定。
- `output.getvalue`（[vlm.py:147](../../../src/providers/vlm.py#L147)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- 静态可定位的调用方：[OpenAICompatibleVLMProvider.extract](vlm.md)。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：未见 `raise`；下游异常可能继续上抛。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。


---

# OpenAICompatibleVLMProvider._post ⭐⭐

**位置与等级**：[vlm.py:149](../../../src/providers/vlm.py#L149)；局部辅助逻辑，需理解其调用条件与失败传播。

**签名**：`async def _post(self, body: dict[str, Any], operation_id: str) -> tuple[dict[str, Any], ProviderCallRecord]`。

**作用**：内部辅助步骤；将参数转换为本模块所需的中间对象或操作结果。

**输入与输出**：
- 输入：`body`（dict[str, Any]）；`operation_id`（str）。
- 输出类型：`tuple[dict[str, Any], ProviderCallRecord]`；具体返回路径见流程步骤。

**处理流程**：
1. 返回 `await post_chat_completion(base_url=self.base_url, api_key=self.api_key, body=body, timeout=self.timeout…`。

**调用与被调用**：
- `post_chat_completion`（调用点 [vlm.py:152](../../../src/providers/vlm.py#L152)）→ [post_chat_completion](http_client.md)，静态可定位。
- `self.fingerprint`（调用点 [vlm.py:160](../../../src/providers/vlm.py#L160)）→ [OpenAICompatibleVLMProvider.fingerprint](vlm.md)，静态可定位。
- 静态可定位的调用方：[OpenAICompatibleVLMProvider.extract](vlm.md)。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：未见 `raise`；下游异常可能继续上抛。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。


---

# OpenAICompatibleVLMProvider.extract ⭐⭐⭐⭐

**位置与等级**：[vlm.py:164](../../../src/providers/vlm.py#L164)；承担主要 Agent、应用服务或审核/执行入口，跨模块影响显著。

**签名**：`async def extract(self, request: VisualExtractionRequest) -> ExtractionResult`。

**作用**：处理 `extract` 对应步骤；下列步骤依据函数体的实际控制流和调用点整理。

**输入与输出**：
- 输入：`request`（VisualExtractionRequest）。
- 输出类型：`ExtractionResult`；具体返回路径见流程步骤。

**处理流程**：
1. 更新 `asset`，值来自 `request.asset`。
2. 更新 `prompt`，值来自 `_visual_prompt(request)`。
3. 更新 `body`，值来自 `{'model': self.model, 'messages': [{'role': 'user', 'content': [{'type': 'text', 'text': prompt}, {…`。
4. 更新 `(response, first_record)`，值来自 `await self._post(body, asset.id)`。
5. 更新 `records`，值来自 `[first_record]`。
6. 捕获 (KeyError, IndexError, TypeError)；另检查 finally/else 的清理和传播。
7. 捕获 (TypeError, json.JSONDecodeError)；另检查 finally/else 的清理和传播。
8. 更新 `issues`，值来自 `[]`。
9. 检查 `not isinstance(payload.get('claims'), list) or not isinstance(payload.get('observations', []), list)`；按条件分流，else 分支不存在。
10. 更新 `observations`，值来自 `[]`。
11. 更新 `observations_by_index`，值来自 `{}`。
12. 更新 `evidence`，值来自 `[]`。
13. 更新 `warnings`，值来自 `[]`。
14. 更新 `uncalibrated_observations`，值来自 `set()`。
15. 遍历 `enumerate(payload.get('observations', []))`，逐项处理 `(index, item)`。
16. 更新 `candidates`，值来自 `[]`。
17. 更新 `ocr_context`，值来自 `<字符串常量>.join((block.text for block in request.ocr_blocks))`。
18. 更新 `grounding_context`，值来自 `ocr_context or asset.context_text`。
19. 遍历 `enumerate(payload.get('claims', []))`，逐项处理 `(index, item)`。
20. 返回 `ExtractionResult(candidates=candidates, observations=observations, evidence=evidence, warnings=warnings,…`。

**关键条件与保护**：
- [vlm.py:216](../../../src/providers/vlm.py#L216)：`not isinstance(payload.get('claims'), list) or not isinstance(payload.get('observations', []), list)`，不满足时跳过本分支。
- [vlm.py:228](../../../src/providers/vlm.py#L228)：`not isinstance(item, dict) or not isinstance(item.get('attributes', {}), dict)`，不满足时跳过本分支。
- [vlm.py:242](../../../src/providers/vlm.py#L242)：`raw_bbox is not None`，不满足时跳过本分支。
- [vlm.py:244](../../../src/providers/vlm.py#L244)：`not isinstance(raw_bbox, list) or len(raw_bbox) != 4`，不满足时跳过本分支。
- [vlm.py:247](../../../src/providers/vlm.py#L247)：`not all((math.isfinite(v) and 0 <= v <= 1 for v in values))`，不满足时跳过本分支。
- [vlm.py:254](../../../src/providers/vlm.py#L254)：`not math.isfinite(confidence) or not 0 <= confidence <= 1`，不满足时跳过本分支。
- [vlm.py:275](../../../src/providers/vlm.py#L275)：`raw_bbox is not None and bbox is None or index in uncalibrated_observations`，不满足时跳过本分支。
- [vlm.py:287](../../../src/providers/vlm.py#L287)：`bbox is not None`，不满足时跳过本分支。
- [vlm.py:324](../../../src/providers/vlm.py#L324)：`issue is not None`，不满足时跳过本分支。
- [vlm.py:343](../../../src/providers/vlm.py#L343)：`_is_context_only_visual_claim(candidate, observation, ocr_context, asset.context_text)`，不满足时跳过本分支。
- [vlm.py:351](../../../src/providers/vlm.py#L351)：`isinstance(oi, int) and oi in uncalibrated_observations or (observation is None and uncalibrated_observations)`，不满足时跳过本分支。

**调用与被调用**：
- `_visual_prompt`（调用点 [vlm.py:166](../../../src/providers/vlm.py#L166)）→ [_visual_prompt](vlm.md)，静态可定位。
- `self._image_data_url`（调用点 [vlm.py:176](../../../src/providers/vlm.py#L176)）→ [OpenAICompatibleVLMProvider._image_data_url](vlm.md)，静态可定位。
- `self._post`（调用点 [vlm.py:184](../../../src/providers/vlm.py#L184)）→ [OpenAICompatibleVLMProvider._post](vlm.md)，静态可定位。
- `ProviderResponseError`（调用点 [vlm.py:189](../../../src/providers/vlm.py#L189)）→ [ProviderResponseError](../core/errors.md)，静态可定位。
- `parse_json_object`（调用点 [vlm.py:194](../../../src/providers/vlm.py#L194)）→ [parse_json_object](common.md)，静态可定位。
- `dict`（[vlm.py:196](../../../src/providers/vlm.py#L196)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `cast`（[vlm.py:197](../../../src/providers/vlm.py#L197)）：来自 `typing.cast`；具体实现可能由依赖注入或运行时分派决定。
- `str`（[vlm.py:200](../../../src/providers/vlm.py#L200)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `records.append`（[vlm.py:207](../../../src/providers/vlm.py#L207)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `isinstance`（[vlm.py:216](../../../src/providers/vlm.py#L216)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `payload.get`（[vlm.py:216](../../../src/providers/vlm.py#L216)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `set`（[vlm.py:226](../../../src/providers/vlm.py#L226)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `enumerate`（[vlm.py:227](../../../src/providers/vlm.py#L227)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `item.get`（[vlm.py:228](../../../src/providers/vlm.py#L228)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `issues.append`（[vlm.py:229](../../../src/providers/vlm.py#L229)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `ValidationService.issue`（[vlm.py:230](../../../src/providers/vlm.py#L230)）：来自 `src.governance.validation.ValidationService`；具体实现可能由依赖注入或运行时分派决定。
- `stable_id`（调用点 [vlm.py:234](../../../src/providers/vlm.py#L234)）→ [stable_id](../core/ids.md)，静态可定位。
- `len`（[vlm.py:244](../../../src/providers/vlm.py#L244)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `ValueError`（[vlm.py:245](../../../src/providers/vlm.py#L245)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `float`（[vlm.py:246](../../../src/providers/vlm.py#L246)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `all`（[vlm.py:247](../../../src/providers/vlm.py#L247)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `math.isfinite`（[vlm.py:247](../../../src/providers/vlm.py#L247)）：来自 `math`；具体实现可能由依赖注入或运行时分派决定。
- `BBox`（[vlm.py:249](../../../src/providers/vlm.py#L249)）：来自 `src.domain.BBox`；具体实现可能由依赖注入或运行时分派决定。
- `warnings.append`（[vlm.py:251](../../../src/providers/vlm.py#L251)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `uncalibrated_observations.add`（[vlm.py:258](../../../src/providers/vlm.py#L258)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `evidence.append`（[vlm.py:288](../../../src/providers/vlm.py#L288)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `EvidenceRef`（[vlm.py:289](../../../src/providers/vlm.py#L289)）：来自 `src.domain.EvidenceRef`；具体实现可能由依赖注入或运行时分派决定。
- `observations.append`（[vlm.py:306](../../../src/providers/vlm.py#L306)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `VisualObservation`（[vlm.py:307](../../../src/providers/vlm.py#L307)）：来自 `src.domain.VisualObservation`；具体实现可能由依赖注入或运行时分派决定。
- `<字符串常量>.join`（[vlm.py:320](../../../src/providers/vlm.py#L320)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- 此处列出前 30 个不同调用表达式，另有 9 个，需按源码继续追踪。
- 静态扫描未定位直接调用方；可能通过路由注册、LangGraph 节点、协议方法或依赖注入动态调用，不据此判断为死代码。

**状态、副作用与异常**：
- 显式状态/容器赋值：`repair_body['messages']`、`observations_by_index[index]`、`candidate.context_only_visual_claim`、`candidate.uncalibrated_visual_confidence`。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：`ProviderResponseError(<字符串常量>, call_records=records)`、`ValueError(<字符串常量>)`。
- 本地捕获：`(KeyError, IndexError, TypeError)`、`(TypeError, json.JSONDecodeError)`、`(KeyError, IndexError, TypeError, json.JSONDecodeError)`、`(TypeError, ValueError)`、`(KeyError, TypeError, ValueError)`。


---
