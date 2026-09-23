源码：[openai_compatible.py:1](../../../src/providers/openai_compatible.py#L1) | 基准：`dev/v0.10@f2f34d7` | 本文件符号数：5

**模块职责**：OpenAI-compatible text extraction provider.
**在系统中的位置**：LLM、OCR、VLM、Embedding、Reflection 与语义建议的外部能力接口和实现。
**直接依赖**：[src.core.errors](../core/errors.md)、[src.core.ids](../core/ids.md)、[src.domain](../domain/__init__.md)、[src.governance.validation](../governance/validation/__init__.md)、[src.providers.common](common.md)、[src.providers.http_client](http_client.md)、[src.providers.validation](validation.md)；外部/标准库：`__future__`、`httpx`、`json`、`typing`。
**主要调用方（静态导入）**：[evaluation/document_validation.py](../evaluation/document_validation.md)、[providers/__init__.py](__init__.md)。
**阅读提示**：下列流程根据当前源码控制流整理；`self`/接口对象的实际类型可能在运行时注入，未能静态解析的调用会明确标注。链接指向源码行或对应讲解文件。

---

# OpenAICompatibleLLMProvider ⭐⭐⭐

**位置与等级**：[openai_compatible.py:23](../../../src/providers/openai_compatible.py#L23)；关键支撑逻辑，影响候选、证据或接口的正确传递。

**职责**：外部能力实现或协议；调用是否耗费模型额度取决于具体实现。基类：无显式基类。

**字段与类级约束**：
- 类体未直接声明字段；实例状态请看 `__init__` 及方法中的赋值。

**内部成员**：`OpenAICompatibleLLMProvider.__init__`、`OpenAICompatibleLLMProvider.fingerprint`、`OpenAICompatibleLLMProvider._post`、`OpenAICompatibleLLMProvider.extract`


---

# OpenAICompatibleLLMProvider.__init__ ⭐⭐⭐

**位置与等级**：[openai_compatible.py:24](../../../src/providers/openai_compatible.py#L24)；关键支撑逻辑，影响候选、证据或接口的正确传递。

**签名**：`def __init__(self, base_url: str, api_key: str, model: str, timeout: float=60.0, transport: httpx.AsyncBaseTransport | None=None) -> None`。

**作用**：初始化对象并保存依赖或配置；需检查是否创建持久化资源。

**输入与输出**：
- 输入：`base_url`（str）；`api_key`（str）；`model`（str）；`timeout`（float；默认 `60.0`）；`transport`（httpx.AsyncBaseTransport | None；默认 `None`）。
- 输出类型：`None`；具体返回路径见流程步骤。

**处理流程**：
1. 更新 `self.base_url`，值来自 `base_url.rstrip('/')`。
2. 更新 `self.api_key`，值来自 `api_key`。
3. 更新 `self.model`，值来自 `model`。
4. 更新 `self.timeout`，值来自 `timeout`。
5. 更新 `self.transport`，值来自 `transport`。

**调用与被调用**：
- `base_url.rstrip`（[openai_compatible.py:32](../../../src/providers/openai_compatible.py#L32)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- 静态扫描未定位直接调用方；可能通过路由注册、LangGraph 节点、协议方法或依赖注入动态调用，不据此判断为死代码。

**状态、副作用与异常**：
- 显式状态/容器赋值：`self.base_url`、`self.api_key`、`self.model`、`self.timeout`、`self.transport`。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：未见 `raise`；下游异常可能继续上抛。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。


---

# OpenAICompatibleLLMProvider.fingerprint ⭐⭐⭐

**位置与等级**：[openai_compatible.py:38](../../../src/providers/openai_compatible.py#L38)；关键支撑逻辑，影响候选、证据或接口的正确传递。

**签名**：`def fingerprint(self) -> str`。

**作用**：处理 `fingerprint` 对应步骤；下列步骤依据函数体的实际控制流和调用点整理。

**输入与输出**：
- 输入：无业务参数（或仅隐式接收实例）。
- 输出类型：`str`；具体返回路径见流程步骤。

**处理流程**：
1. 返回 `stable_id('provider', 'openai-compatible', self.base_url.casefold(), self.model, PROMPT_VERSION, PROTOCO…`。

**调用与被调用**：
- `stable_id`（调用点 [openai_compatible.py:39](../../../src/providers/openai_compatible.py#L39)）→ [stable_id](../core/ids.md)，静态可定位。
- `self.base_url.casefold`（[openai_compatible.py:42](../../../src/providers/openai_compatible.py#L42)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- 静态可定位的调用方：[OpenAICompatibleLLMProvider._post](openai_compatible.md)。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：未见 `raise`；下游异常可能继续上抛。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。


---

# OpenAICompatibleLLMProvider._post ⭐⭐

**位置与等级**：[openai_compatible.py:49](../../../src/providers/openai_compatible.py#L49)；局部辅助逻辑，需理解其调用条件与失败传播。

**签名**：`async def _post(self, body: dict[str, Any], operation_id: str) -> tuple[dict[str, Any], ProviderCallRecord]`。

**作用**：内部辅助步骤；将参数转换为本模块所需的中间对象或操作结果。

**输入与输出**：
- 输入：`body`（dict[str, Any]）；`operation_id`（str）。
- 输出类型：`tuple[dict[str, Any], ProviderCallRecord]`；具体返回路径见流程步骤。

**处理流程**：
1. 返回 `await post_chat_completion(base_url=self.base_url, api_key=self.api_key, body=body, timeout=self.timeout…`。

**调用与被调用**：
- `post_chat_completion`（调用点 [openai_compatible.py:52](../../../src/providers/openai_compatible.py#L52)）→ [post_chat_completion](http_client.md)，静态可定位。
- `self.fingerprint`（调用点 [openai_compatible.py:60](../../../src/providers/openai_compatible.py#L60)）→ [OpenAICompatibleLLMProvider.fingerprint](openai_compatible.md)，静态可定位。
- 静态可定位的调用方：[OpenAICompatibleLLMProvider.extract](openai_compatible.md)。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：未见 `raise`；下游异常可能继续上抛。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。


---

# OpenAICompatibleLLMProvider.extract ⭐⭐⭐⭐

**位置与等级**：[openai_compatible.py:64](../../../src/providers/openai_compatible.py#L64)；承担主要 Agent、应用服务或审核/执行入口，跨模块影响显著。

**签名**：`async def extract(self, request: ExtractionRequest) -> ExtractionResult`。

**作用**：处理 `extract` 对应步骤；下列步骤依据函数体的实际控制流和调用点整理。

**输入与输出**：
- 输入：`request`（ExtractionRequest）。
- 输出类型：`ExtractionResult`；具体返回路径见流程步骤。

**处理流程**：
1. 更新 `blocks`，值来自 `[{'evidence_id': block.evidence_id, 'text': block.text} for block in request.document.text_blocks]`。
2. 更新 `prompt`，值来自 `f<字符串常量>`。
3. 更新 `body`，值来自 `{'model': self.model, 'messages': [{'role': 'user', 'content': prompt}], 'temperature': 0, 'respons…`。
4. 更新 `(response, first_record)`，值来自 `await self._post(body, request.document.id)`。
5. 更新 `records`，值来自 `[first_record]`。
6. 捕获 (KeyError, IndexError, TypeError, json.JSONDecodeError)；另检查 finally/else 的清理和传播。
7. 更新 `evidence`，值来自 `{item.id: item for item in request.document.evidence}`。
8. 更新 `blocks_by_evidence`，值来自 `{item.evidence_id: item for item in request.document.text_blocks}`。
9. 更新 `candidates`，值来自 `[]`。
10. 更新 `warnings`，值来自 `[]`。
11. 更新 `issues`，值来自 `[]`。
12. 更新 `items`，值来自 `payload.get('claims')`。
13. 检查 `not isinstance(items, list)`；按条件分流，else 分支不存在。
14. 遍历 `enumerate(items)`，逐项处理 `(position, item)`。
15. 返回 `ExtractionResult(candidates=candidates, warnings=warnings, call_records=records, validation=ValidationSe…`。

**关键条件与保护**：
- [openai_compatible.py:116](../../../src/providers/openai_compatible.py#L116)：`not isinstance(items, list)`，不满足时跳过本分支。
- [openai_compatible.py:120](../../../src/providers/openai_compatible.py#L120)：`issue is not None`，不满足时跳过本分支。
- [openai_compatible.py:124](../../../src/providers/openai_compatible.py#L124)：`evidence_id not in evidence`，不满足时跳过本分支。

**调用与被调用**：
- `request.output_schema.model_dump_json`（[openai_compatible.py:79](../../../src/providers/openai_compatible.py#L79)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `json.dumps`（[openai_compatible.py:80](../../../src/providers/openai_compatible.py#L80)）：来自 `json`；具体实现可能由依赖注入或运行时分派决定。
- `self._post`（调用点 [openai_compatible.py:88](../../../src/providers/openai_compatible.py#L88)）→ [OpenAICompatibleLLMProvider._post](openai_compatible.md)，静态可定位。
- `parse_json_object`（调用点 [openai_compatible.py:92](../../../src/providers/openai_compatible.py#L92)）→ [parse_json_object](common.md)，静态可定位。
- `dict`（[openai_compatible.py:94](../../../src/providers/openai_compatible.py#L94)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `cast`（[openai_compatible.py:95](../../../src/providers/openai_compatible.py#L95)）：来自 `typing.cast`；具体实现可能由依赖注入或运行时分派决定。
- `str`（[openai_compatible.py:98](../../../src/providers/openai_compatible.py#L98)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `records.append`（[openai_compatible.py:102](../../../src/providers/openai_compatible.py#L102)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `ProviderResponseError`（调用点 [openai_compatible.py:106](../../../src/providers/openai_compatible.py#L106)）→ [ProviderResponseError](../core/errors.md)，静态可定位。
- `payload.get`（[openai_compatible.py:115](../../../src/providers/openai_compatible.py#L115)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `isinstance`（[openai_compatible.py:116](../../../src/providers/openai_compatible.py#L116)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `enumerate`（[openai_compatible.py:118](../../../src/providers/openai_compatible.py#L118)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `validate_item`（调用点 [openai_compatible.py:119](../../../src/providers/openai_compatible.py#L119)）→ [validate_item](validation.md)，静态可定位。
- `issues.append`（[openai_compatible.py:121](../../../src/providers/openai_compatible.py#L121)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `item.get`（[openai_compatible.py:123](../../../src/providers/openai_compatible.py#L123)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `warnings.append`（[openai_compatible.py:125](../../../src/providers/openai_compatible.py#L125)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `ValidationService.issue`（[openai_compatible.py:127](../../../src/providers/openai_compatible.py#L127)）：来自 `src.governance.validation.ValidationService`；具体实现可能由依赖注入或运行时分派决定。
- `stable_id`（调用点 [openai_compatible.py:131](../../../src/providers/openai_compatible.py#L131)）→ [stable_id](../core/ids.md)，静态可定位。
- `summarize`（调用点 [openai_compatible.py:135](../../../src/providers/openai_compatible.py#L135)）→ [summarize](validation.md)，静态可定位。
- `blocks_by_evidence.get`（[openai_compatible.py:139](../../../src/providers/openai_compatible.py#L139)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `candidates.append`（[openai_compatible.py:140](../../../src/providers/openai_compatible.py#L140)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `candidate_from_payload`（调用点 [openai_compatible.py:141](../../../src/providers/openai_compatible.py#L141)）→ [candidate_from_payload](common.md)，静态可定位。
- `ExtractionResult`（[openai_compatible.py:148](../../../src/providers/openai_compatible.py#L148)）：来自 `src.domain.ExtractionResult`；具体实现可能由依赖注入或运行时分派决定。
- `ValidationService.merge`（[openai_compatible.py:152](../../../src/providers/openai_compatible.py#L152)）：来自 `src.governance.validation.ValidationService`；具体实现可能由依赖注入或运行时分派决定。
- `ValidationResult`（[openai_compatible.py:152](../../../src/providers/openai_compatible.py#L152)）：来自 `src.domain.ValidationResult`；具体实现可能由依赖注入或运行时分派决定。
- 静态扫描未定位直接调用方；可能通过路由注册、LangGraph 节点、协议方法或依赖注入动态调用，不据此判断为死代码。

**状态、副作用与异常**：
- 显式状态/容器赋值：`repair_body['messages']`。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：`ProviderResponseError(<字符串常量>, call_records=records)`。
- 本地捕获：`(KeyError, IndexError, TypeError, json.JSONDecodeError)`。


---
