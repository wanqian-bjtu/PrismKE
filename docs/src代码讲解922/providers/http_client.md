源码：[http_client.py:1](../../../src/providers/http_client.py#L1) | 基准：`dev/v0.10@f2f34d7` | 本文件符号数：5

**模块职责**：Shared, sanitized OpenAI-compatible HTTP transport.
**在系统中的位置**：LLM、OCR、VLM、Embedding、Reflection 与语义建议的外部能力接口和实现。
**直接依赖**：[src.core.errors](../core/errors.md)、[src.core.execution_control](../core/execution_control.md)、[src.core.ids](../core/ids.md)、[src.domain](../domain/__init__.md)、[src.providers.pricing](pricing.md)；外部/标准库：`__future__`、`asyncio`、`httpx`、`re`、`time`、`typing`。
**主要调用方（静态导入）**：[providers/openai_compatible.py](openai_compatible.md)、[providers/reflection.py](reflection.md)、[providers/semantic.py](semantic.md)、[providers/vlm.py](vlm.md)。
**阅读提示**：下列流程根据当前源码控制流整理；`self`/接口对象的实际类型可能在运行时注入，未能静态解析的调用会明确标注。链接指向源码行或对应讲解文件。

---

# _usage ⭐⭐

**位置与等级**：[http_client.py:19](../../../src/providers/http_client.py#L19)；局部辅助逻辑，需理解其调用条件与失败传播。

**签名**：`def _usage(payload: dict[str, Any]) -> tuple[int | None, int | None, int | None]`。

**作用**：内部辅助步骤；将参数转换为本模块所需的中间对象或操作结果。

**输入与输出**：
- 输入：`payload`（dict[str, Any]）。
- 输出类型：`tuple[int | None, int | None, int | None]`；具体返回路径见流程步骤。

**处理流程**：
1. 更新 `usage`，值来自 `payload.get('usage') or {}`。
2. 检查 `not isinstance(usage, dict)`；按条件分流，else 分支不存在。
3. 更新 `input_raw`，值来自 `usage.get(<字符串常量>, usage.get(<字符串常量>))`。
4. 更新 `output_raw`，值来自 `usage.get(<字符串常量>, usage.get(<字符串常量>))`。
5. 检查 `type(input_raw) is not int or type(output_raw) is not int`；按条件分流，else 分支不存在。
6. 更新 `(input_tokens, output_tokens)`，值来自 `(input_raw, output_raw)`。
7. 检查 `min(input_tokens, output_tokens) < 0`；按条件分流，else 分支不存在。
8. 更新 `total_tokens`，值来自 `usage.get(<字符串常量>, input_tokens + output_tokens)`。
9. 检查 `type(total_tokens) is not int or total_tokens != input_tokens + output_tokens`；按条件分流，else 分支不存在。
10. 返回 `(input_tokens, output_tokens, total_tokens)`。

**关键条件与保护**：
- [http_client.py:21](../../../src/providers/http_client.py#L21)：`not isinstance(usage, dict)`，不满足时跳过本分支。
- [http_client.py:25](../../../src/providers/http_client.py#L25)：`type(input_raw) is not int or type(output_raw) is not int`，不满足时跳过本分支。
- [http_client.py:28](../../../src/providers/http_client.py#L28)：`min(input_tokens, output_tokens) < 0`，不满足时跳过本分支。
- [http_client.py:31](../../../src/providers/http_client.py#L31)：`type(total_tokens) is not int or total_tokens != input_tokens + output_tokens`，不满足时跳过本分支。

**调用与被调用**：
- `payload.get`（[http_client.py:20](../../../src/providers/http_client.py#L20)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `isinstance`（[http_client.py:21](../../../src/providers/http_client.py#L21)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `usage.get`（[http_client.py:23](../../../src/providers/http_client.py#L23)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `type`（[http_client.py:25](../../../src/providers/http_client.py#L25)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `min`（[http_client.py:28](../../../src/providers/http_client.py#L28)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- 静态可定位的调用方：[_record](http_client.md)、[post_chat_completion](http_client.md)。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：未见 `raise`；下游异常可能继续上抛。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。


---

# _failure ⭐⭐

**位置与等级**：[http_client.py:36](../../../src/providers/http_client.py#L36)；局部辅助逻辑，需理解其调用条件与失败传播。

**签名**：`def _failure(status: int | None, kind: str) -> tuple[str, str]`。

**作用**：内部辅助步骤；将参数转换为本模块所需的中间对象或操作结果。

**输入与输出**：
- 输入：`status`（int | None）；`kind`（str）。
- 输出类型：`tuple[str, str]`；具体返回路径见流程步骤。

**处理流程**：
1. 检查 `status == 401`；按条件分流，else 分支不存在。
2. 检查 `status == 403`；按条件分流，else 分支不存在。
3. 检查 `status == 404`；按条件分流，else 分支不存在。
4. 检查 `status == 429`；按条件分流，else 分支不存在。
5. 检查 `status is not None and status >= 500`；按条件分流，else 分支不存在。
6. 检查 `kind == 'timeout'`；按条件分流，else 分支不存在。
7. 检查 `kind == 'network'`；按条件分流，else 分支不存在。
8. 返回 `('request_failed', <字符串常量>)`。

**关键条件与保护**：
- [http_client.py:37](../../../src/providers/http_client.py#L37)：`status == 401`，不满足时跳过本分支。
- [http_client.py:39](../../../src/providers/http_client.py#L39)：`status == 403`，不满足时跳过本分支。
- [http_client.py:41](../../../src/providers/http_client.py#L41)：`status == 404`，不满足时跳过本分支。
- [http_client.py:43](../../../src/providers/http_client.py#L43)：`status == 429`，不满足时跳过本分支。
- [http_client.py:45](../../../src/providers/http_client.py#L45)：`status is not None and status >= 500`，不满足时跳过本分支。
- [http_client.py:47](../../../src/providers/http_client.py#L47)：`kind == 'timeout'`，不满足时跳过本分支。
- [http_client.py:49](../../../src/providers/http_client.py#L49)：`kind == 'network'`，不满足时跳过本分支。

**调用与被调用**：
- 无显式函数调用，或仅声明协议/常量。
- 静态可定位的调用方：[post_chat_completion](http_client.md)。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：未见 `raise`；下游异常可能继续上抛。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。


---

# _record ⭐⭐

**位置与等级**：[http_client.py:54](../../../src/providers/http_client.py#L54)；局部辅助逻辑，需理解其调用条件与失败传播。

**签名**：`def _record(*, provider: Literal['llm', 'vlm', 'governance', 'fusion'], operation_id: str, requested_model: str, prompt_version: str, started: float, retry_count: int, status: Literal['succeeded', 'failed'], payload: dict[str, Any] | None=None, error_code: str | None=None) -> ProviderCallRecord`。

**作用**：内部辅助步骤；将参数转换为本模块所需的中间对象或操作结果。

**输入与输出**：
- 输入：`provider`（Literal['llm', 'vlm', 'governance', 'fusion']）；`operation_id`（str）；`requested_model`（str）；`prompt_version`（str）；`started`（float）；`retry_count`（int）；`status`（Literal['succeeded', 'failed']）；`payload`（dict[str, Any] | None；默认 `None`）；`error_code`（str | None；默认 `None`）。
- 输出类型：`ProviderCallRecord`；具体返回路径见流程步骤。

**处理流程**：
1. 更新 `payload`，值来自 `payload or {}`。
2. 更新 `(input_tokens, output_tokens, total_tokens)`，值来自 `_usage(payload)`。
3. 更新 `response_model`，值来自 `str(payload['model']) if payload.get('model') else None`。
4. 更新 `(estimated_cost, snapshot)`，值来自 `estimate_cost_cny(response_model or requested_model, input_tokens, output_tokens) if input_tokens i…`。
5. 更新 `request_id`，值来自 `payload.get('id')`。
6. 返回 `ProviderCallRecord(id=stable_id('provider-call', provider, operation_id, requested_model, str(request_id…`。

**调用与被调用**：
- `_usage`（调用点 [http_client.py:67](../../../src/providers/http_client.py#L67)）→ [_usage](http_client.md)，静态可定位。
- `payload.get`（[http_client.py:68](../../../src/providers/http_client.py#L68)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `str`（[http_client.py:68](../../../src/providers/http_client.py#L68)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `estimate_cost_cny`（调用点 [http_client.py:70](../../../src/providers/http_client.py#L70)）→ [estimate_cost_cny](pricing.md)，静态可定位。
- `ProviderCallRecord`（[http_client.py:75](../../../src/providers/http_client.py#L75)）：来自 `src.domain.ProviderCallRecord`；具体实现可能由依赖注入或运行时分派决定。
- `stable_id`（调用点 [http_client.py:76](../../../src/providers/http_client.py#L76)）→ [stable_id](../core/ids.md)，静态可定位。
- `round`（[http_client.py:93](../../../src/providers/http_client.py#L93)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `perf_counter`（[http_client.py:93](../../../src/providers/http_client.py#L93)）：来自 `time.perf_counter`；具体实现可能由依赖注入或运行时分派决定。
- 静态可定位的调用方：[post_chat_completion](http_client.md)。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：未见 `raise`；下游异常可能继续上抛。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。


---

# post_chat_completion ⭐⭐⭐

**位置与等级**：[http_client.py:103](../../../src/providers/http_client.py#L103)；关键支撑逻辑，影响候选、证据或接口的正确传递。

**签名**：`async def post_chat_completion(*, base_url: str, api_key: str, body: dict[str, Any], timeout: float, provider: Literal['llm', 'vlm', 'governance', 'fusion'], operation_id: str, prompt_version: str, transport: httpx.AsyncBaseTransport | None=None, provider_fingerprint: str | None=None) -> tuple[dict[str, Any], ProviderCallRecord]`。

**作用**：Post one chat completion with bounded retry and sanitized failures.

**输入与输出**：
- 输入：`base_url`（str）；`api_key`（str）；`body`（dict[str, Any]）；`timeout`（float）；`provider`（Literal['llm', 'vlm', 'governance', 'fusion']）；`operation_id`（str）；`prompt_version`（str）；`transport`（httpx.AsyncBaseTransport | None；默认 `None`）；`provider_fingerprint`（str | None；默认 `None`）。
- 输出类型：`tuple[dict[str, Any], ProviderCallRecord]`；具体返回路径见流程步骤。

**处理流程**：
1. 更新 `started`，值来自 `perf_counter()`。
2. 更新 `headers`，值来自 `{'Authorization': f<字符串常量>}`。
3. 更新 `retry_count`，值来自 `0`。
4. 更新 `delay`，值来自 `0.5`。
5. 更新 `control`，值来自 `current_execution.get()`。
6. 遍历 `range(3)`，逐项处理 `attempt`。
7. 抛出 `RuntimeError('unreachable')`。

**关键条件与保护**：
- [http_client.py:132](../../../src/providers/http_client.py#L132)：`control`，不满足时跳过本分支。
- [http_client.py:145](../../../src/providers/http_client.py#L145)：`cached is not None`，不满足时跳过本分支。
- [http_client.py:161](../../../src/providers/http_client.py#L161)：`control and response.is_error`，不满足时跳过本分支。
- [http_client.py:165](../../../src/providers/http_client.py#L165)：`(response.status_code == 429 or (response.status_code >= 500 and (not control))) and attempt < 2`，不满足时跳过本分支。
- [http_client.py:172](../../../src/providers/http_client.py#L172)：`response.is_error`，不满足时跳过本分支。
- [http_client.py:188](../../../src/providers/http_client.py#L188)：`control`，不满足时跳过本分支。
- [http_client.py:201](../../../src/providers/http_client.py#L201)：`control`，不满足时跳过本分支。
- [http_client.py:239](../../../src/providers/http_client.py#L239)：`control`，不满足时跳过本分支。
- [http_client.py:241](../../../src/providers/http_client.py#L241)：`attempt < 2 and (not control)`，不满足时跳过本分支。
- [http_client.py:259](../../../src/providers/http_client.py#L259)：`control`，不满足时跳过本分支。
- [http_client.py:261](../../../src/providers/http_client.py#L261)：`attempt < 2 and (not control)`，不满足时跳过本分支。
- [http_client.py:279](../../../src/providers/http_client.py#L279)：`control`，不满足时跳过本分支。

**调用与被调用**：
- `perf_counter`（[http_client.py:117](../../../src/providers/http_client.py#L117)）：来自 `time.perf_counter`；具体实现可能由依赖注入或运行时分派决定。
- `current_execution.get`（[http_client.py:121](../../../src/providers/http_client.py#L121)）：来自 `src.core.execution_control.current_execution`；具体实现可能由依赖注入或运行时分派决定。
- `range`（[http_client.py:122](../../../src/providers/http_client.py#L122)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `stable_id`（调用点 [http_client.py:123](../../../src/providers/http_client.py#L123)）→ [stable_id](../core/ids.md)，静态可定位。
- `base_url.rstrip`（[http_client.py:127](../../../src/providers/http_client.py#L127)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `canonical_hash`（调用点 [http_client.py:129](../../../src/providers/http_client.py#L129)）→ [canonical_hash](../core/ids.md)，静态可定位。
- `control.begin_request`（[http_client.py:133](../../../src/providers/http_client.py#L133)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `str`（[http_client.py:138](../../../src/providers/http_client.py#L138)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `_record`（调用点 [http_client.py:146](../../../src/providers/http_client.py#L146)）→ [_record](http_client.md)，静态可定位。
- `httpx.AsyncClient`（[http_client.py:157](../../../src/providers/http_client.py#L157)）：来自 `httpx`；具体实现可能由依赖注入或运行时分派决定。
- `client.post`（[http_client.py:158](../../../src/providers/http_client.py#L158)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `control.finish_request`（[http_client.py:162](../../../src/providers/http_client.py#L162)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `asyncio.sleep`（[http_client.py:169](../../../src/providers/http_client.py#L169)）：来自 `asyncio`；具体实现可能由依赖注入或运行时分派决定。
- `_failure`（调用点 [http_client.py:173](../../../src/providers/http_client.py#L173)）→ [_failure](http_client.md)，静态可定位。
- `ProviderRequestError`（调用点 [http_client.py:184](../../../src/providers/http_client.py#L184)）→ [ProviderRequestError](../core/errors.md)，静态可定位。
- `dict`（[http_client.py:186](../../../src/providers/http_client.py#L186)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `response.json`（[http_client.py:186](../../../src/providers/http_client.py#L186)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `scrub`（[http_client.py:222](../../../src/providers/http_client.py#L222)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `_usage`（调用点 [http_client.py:223](../../../src/providers/http_client.py#L223)）→ [_usage](http_client.md)，静态可定位。
- `RuntimeError`（[http_client.py:282](../../../src/providers/http_client.py#L282)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- 静态可定位的调用方：[OpenAICompatibleLLMProvider._post](openai_compatible.md)、[OpenAICompatibleReflectionProvider.reflect](reflection.md)、[OpenAICompatibleSemanticAdvisor._ask](semantic.md)、[OpenAICompatibleVLMProvider._post](vlm.md)。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：`ProviderRequestError(message, call_record=record)`、`ProviderRequestError(<字符串常量>, call_record=record)`、`重新抛出`、`RuntimeError('unreachable')`。
- 本地捕获：`ValueError`、`ProviderRequestError`、`httpx.TimeoutException`、`httpx.NetworkError`、`asyncio.CancelledError`。


---

# post_chat_completion.scrub ⭐⭐⭐

**位置与等级**：[http_client.py:205](../../../src/providers/http_client.py#L205)；关键支撑逻辑，影响候选、证据或接口的正确传递。

**签名**：`def scrub(value: Any) -> Any`。

**作用**：处理 `scrub` 对应步骤；下列步骤依据函数体的实际控制流和调用点整理。

**输入与输出**：
- 输入：`value`（Any）。
- 输出类型：`Any`；具体返回路径见流程步骤。

**处理流程**：
1. 检查 `isinstance(value, str)`；按条件分流，else 分支不存在。
2. 检查 `isinstance(value, dict)`；按条件分流，else 分支不存在。
3. 检查 `isinstance(value, list)`；按条件分流，else 分支不存在。
4. 返回 `value`。

**关键条件与保护**：
- [http_client.py:206](../../../src/providers/http_client.py#L206)：`isinstance(value, str)`，不满足时跳过本分支。
- [http_client.py:212](../../../src/providers/http_client.py#L212)：`isinstance(value, dict)`，不满足时跳过本分支。
- [http_client.py:218](../../../src/providers/http_client.py#L218)：`isinstance(value, list)`，不满足时跳过本分支。

**调用与被调用**：
- `isinstance`（[http_client.py:206](../../../src/providers/http_client.py#L206)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `re.sub`（[http_client.py:207](../../../src/providers/http_client.py#L207)）：来自 `re`；具体实现可能由依赖注入或运行时分派决定。
- `value.replace`（[http_client.py:210](../../../src/providers/http_client.py#L210)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `scrub`（[http_client.py:214](../../../src/providers/http_client.py#L214)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `value.items`（[http_client.py:215](../../../src/providers/http_client.py#L215)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- 静态扫描未定位直接调用方；可能通过路由注册、LangGraph 节点、协议方法或依赖注入动态调用，不据此判断为死代码。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：未见 `raise`；下游异常可能继续上抛。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。


---
