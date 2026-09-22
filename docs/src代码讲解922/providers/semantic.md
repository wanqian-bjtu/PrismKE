源码：[semantic.py:1](../../../src/providers/semantic.py#L1) | 基准：`dev/v0.10@f2f34d7` | 本文件符号数：16

**模块职责**：Bounded OpenAI-compatible advice for uncertain agent decisions.
**在系统中的位置**：LLM、OCR、VLM、Embedding、Reflection 与语义建议的外部能力接口和实现。
**直接依赖**：[src.core.errors](../core/errors.md)、[src.core.ids](../core/ids.md)、[src.domain](../domain/__init__.md)、[src.providers.common](common.md)、[src.providers.http_client](http_client.md)；外部/标准库：`__future__`、`httpx`、`json`、`pydantic`、`typing`。
**主要调用方（静态导入）**：[workflow/nodes.py](../workflow/nodes.md)、[workflow/service.py](../workflow/service.md)。
**阅读提示**：下列流程根据当前源码控制流整理；`self`/接口对象的实际类型可能在运行时注入，未能静态解析的调用会明确标注。链接指向源码行或对应讲解文件。

---

# _candidate_object ⭐⭐

**位置与等级**：[semantic.py:28](../../../src/providers/semantic.py#L28)；局部辅助逻辑，需理解其调用条件与失败传播。

**签名**：`def _candidate_object(value: EntityMention | str) -> str`。

**作用**：内部辅助步骤；将参数转换为本模块所需的中间对象或操作结果。

**输入与输出**：
- 输入：`value`（EntityMention | str）。
- 输出类型：`str`；具体返回路径见流程步骤。

**处理流程**：
1. 返回 `value.name if isinstance(value, EntityMention) else value`。

**调用与被调用**：
- `isinstance`（[semantic.py:29](../../../src/providers/semantic.py#L29)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- 静态可定位的调用方：[MockSemanticAdvisor.advise_fusion](semantic.md)、[OpenAICompatibleSemanticAdvisor.advise_fusion.summary](semantic.md)。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：未见 `raise`；下游异常可能继续上抛。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。


---

# DisabledSemanticAdvisor ⭐⭐⭐

**位置与等级**：[semantic.py:32](../../../src/providers/semantic.py#L32)；关键支撑逻辑，影响候选、证据或接口的正确传递。

**职责**：本模块的对象实现或数据契约；具体语义由字段、基类和方法共同决定。基类：无显式基类。

**字段与类级约束**：
- 类体未直接声明字段；实例状态请看 `__init__` 及方法中的赋值。

**内部成员**：`DisabledSemanticAdvisor.fingerprint`、`DisabledSemanticAdvisor.advise_entity`、`DisabledSemanticAdvisor.advise_fusion`


---

# DisabledSemanticAdvisor.fingerprint ⭐⭐⭐

**位置与等级**：[semantic.py:33](../../../src/providers/semantic.py#L33)；关键支撑逻辑，影响候选、证据或接口的正确传递。

**签名**：`def fingerprint(self) -> str`。

**作用**：处理 `fingerprint` 对应步骤；下列步骤依据函数体的实际控制流和调用点整理。

**输入与输出**：
- 输入：无业务参数（或仅隐式接收实例）。
- 输出类型：`str`；具体返回路径见流程步骤。

**处理流程**：
1. 返回 `'semantic:disabled'`。

**调用与被调用**：
- 无显式函数调用，或仅声明协议/常量。
- 静态扫描未定位直接调用方；可能通过路由注册、LangGraph 节点、协议方法或依赖注入动态调用，不据此判断为死代码。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：未见 `raise`；下游异常可能继续上抛。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。


---

# DisabledSemanticAdvisor.advise_entity ⭐⭐⭐

**位置与等级**：[semantic.py:36](../../../src/providers/semantic.py#L36)；关键支撑逻辑，影响候选、证据或接口的正确传递。

**签名**：`async def advise_entity(self, request: EntityAdviceRequest) -> tuple[EntityAdvice, ProviderCallRecord | None]`。

**作用**：处理 `advise_entity` 对应步骤；下列步骤依据函数体的实际控制流和调用点整理。

**输入与输出**：
- 输入：`request`（EntityAdviceRequest）。
- 输出类型：`tuple[EntityAdvice, ProviderCallRecord | None]`；具体返回路径见流程步骤。

**处理流程**：
1. 抛出 `ProviderConfigurationError(<字符串常量>)`。

**调用与被调用**：
- `ProviderConfigurationError`（调用点 [semantic.py:40](../../../src/providers/semantic.py#L40)）→ [ProviderConfigurationError](../core/errors.md)，静态可定位。
- 静态扫描未定位直接调用方；可能通过路由注册、LangGraph 节点、协议方法或依赖注入动态调用，不据此判断为死代码。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：`ProviderConfigurationError(<字符串常量>)`。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。


---

# DisabledSemanticAdvisor.advise_fusion ⭐⭐⭐

**位置与等级**：[semantic.py:42](../../../src/providers/semantic.py#L42)；关键支撑逻辑，影响候选、证据或接口的正确传递。

**签名**：`async def advise_fusion(self, request: FusionAdviceRequest) -> tuple[FusionAdvice, ProviderCallRecord | None]`。

**作用**：处理 `advise_fusion` 对应步骤；下列步骤依据函数体的实际控制流和调用点整理。

**输入与输出**：
- 输入：`request`（FusionAdviceRequest）。
- 输出类型：`tuple[FusionAdvice, ProviderCallRecord | None]`；具体返回路径见流程步骤。

**处理流程**：
1. 抛出 `ProviderConfigurationError(<字符串常量>)`。

**调用与被调用**：
- `ProviderConfigurationError`（调用点 [semantic.py:46](../../../src/providers/semantic.py#L46)）→ [ProviderConfigurationError](../core/errors.md)，静态可定位。
- 静态扫描未定位直接调用方；可能通过路由注册、LangGraph 节点、协议方法或依赖注入动态调用，不据此判断为死代码。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：`ProviderConfigurationError(<字符串常量>)`。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。


---

# MockSemanticAdvisor ⭐⭐⭐

**位置与等级**：[semantic.py:49](../../../src/providers/semantic.py#L49)；关键支撑逻辑，影响候选、证据或接口的正确传递。

**职责**：本模块的对象实现或数据契约；具体语义由字段、基类和方法共同决定。基类：无显式基类。

**字段与类级约束**：
- 类体未直接声明字段；实例状态请看 `__init__` 及方法中的赋值。

**内部成员**：`MockSemanticAdvisor.fingerprint`、`MockSemanticAdvisor.advise_entity`、`MockSemanticAdvisor.advise_fusion`


---

# MockSemanticAdvisor.fingerprint ⭐⭐⭐

**位置与等级**：[semantic.py:50](../../../src/providers/semantic.py#L50)；关键支撑逻辑，影响候选、证据或接口的正确传递。

**签名**：`def fingerprint(self) -> str`。

**作用**：处理 `fingerprint` 对应步骤；下列步骤依据函数体的实际控制流和调用点整理。

**输入与输出**：
- 输入：无业务参数（或仅隐式接收实例）。
- 输出类型：`str`；具体返回路径见流程步骤。

**处理流程**：
1. 返回 `'semantic:mock:v1'`。

**调用与被调用**：
- 无显式函数调用，或仅声明协议/常量。
- 静态扫描未定位直接调用方；可能通过路由注册、LangGraph 节点、协议方法或依赖注入动态调用，不据此判断为死代码。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：未见 `raise`；下游异常可能继续上抛。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。


---

# MockSemanticAdvisor.advise_entity ⭐⭐⭐

**位置与等级**：[semantic.py:53](../../../src/providers/semantic.py#L53)；关键支撑逻辑，影响候选、证据或接口的正确传递。

**签名**：`async def advise_entity(self, request: EntityAdviceRequest) -> tuple[EntityAdvice, ProviderCallRecord | None]`。

**作用**：处理 `advise_entity` 对应步骤；下列步骤依据函数体的实际控制流和调用点整理。

**输入与输出**：
- 输入：`request`（EntityAdviceRequest）。
- 输出类型：`tuple[EntityAdvice, ProviderCallRecord | None]`；具体返回路径见流程步骤。

**处理流程**：
1. 更新 `selected`，值来自 `request.candidates[0].entity_id if request.candidates else None`。
2. 返回 `(EntityAdvice(action='review', selected_entity_id=selected, reason_code='mock_ambiguous_identity'), None)`。

**调用与被调用**：
- `EntityAdvice`（[semantic.py:58](../../../src/providers/semantic.py#L58)）：来自 `src.domain.EntityAdvice`；具体实现可能由依赖注入或运行时分派决定。
- 静态扫描未定位直接调用方；可能通过路由注册、LangGraph 节点、协议方法或依赖注入动态调用，不据此判断为死代码。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：未见 `raise`；下游异常可能继续上抛。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。


---

# MockSemanticAdvisor.advise_fusion ⭐⭐⭐

**位置与等级**：[semantic.py:66](../../../src/providers/semantic.py#L66)；关键支撑逻辑，影响候选、证据或接口的正确传递。

**签名**：`async def advise_fusion(self, request: FusionAdviceRequest) -> tuple[FusionAdvice, ProviderCallRecord | None]`。

**作用**：处理 `advise_fusion` 对应步骤；下列步骤依据函数体的实际控制流和调用点整理。

**输入与输出**：
- 输入：`request`（FusionAdviceRequest）。
- 输出类型：`tuple[FusionAdvice, ProviderCallRecord | None]`；具体返回路径见流程步骤。

**处理流程**：
1. 更新 `decision`，值来自 `'conflict' if request.left.relation == request.right.relation and _candidate_object(request.left.ob…`。
2. 返回 `(FusionAdvice(decision=decision, reason_code='mock_pair_assessment'), None)`。

**调用与被调用**：
- `_candidate_object`（调用点 [semantic.py:72](../../../src/providers/semantic.py#L72)）→ [_candidate_object](semantic.md)，静态可定位。
- `FusionAdvice`（[semantic.py:75](../../../src/providers/semantic.py#L75)）：来自 `src.domain.FusionAdvice`；具体实现可能由依赖注入或运行时分派决定。
- 静态扫描未定位直接调用方；可能通过路由注册、LangGraph 节点、协议方法或依赖注入动态调用，不据此判断为死代码。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：未见 `raise`；下游异常可能继续上抛。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。


---

# OpenAICompatibleSemanticAdvisor ⭐⭐⭐

**位置与等级**：[semantic.py:78](../../../src/providers/semantic.py#L78)；关键支撑逻辑，影响候选、证据或接口的正确传递。

**职责**：本模块的对象实现或数据契约；具体语义由字段、基类和方法共同决定。基类：无显式基类。

**字段与类级约束**：
- 类体未直接声明字段；实例状态请看 `__init__` 及方法中的赋值。

**内部成员**：`OpenAICompatibleSemanticAdvisor.__init__`、`OpenAICompatibleSemanticAdvisor.fingerprint`、`OpenAICompatibleSemanticAdvisor._ask`、`OpenAICompatibleSemanticAdvisor.advise_entity`、`OpenAICompatibleSemanticAdvisor.advise_fusion`


---

# OpenAICompatibleSemanticAdvisor.__init__ ⭐⭐⭐

**位置与等级**：[semantic.py:79](../../../src/providers/semantic.py#L79)；关键支撑逻辑，影响候选、证据或接口的正确传递。

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
- `base_url.rstrip`（[semantic.py:87](../../../src/providers/semantic.py#L87)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- 静态扫描未定位直接调用方；可能通过路由注册、LangGraph 节点、协议方法或依赖注入动态调用，不据此判断为死代码。

**状态、副作用与异常**：
- 显式状态/容器赋值：`self.base_url`、`self.api_key`、`self.model`、`self.timeout`、`self.transport`。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：未见 `raise`；下游异常可能继续上抛。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。


---

# OpenAICompatibleSemanticAdvisor.fingerprint ⭐⭐⭐

**位置与等级**：[semantic.py:93](../../../src/providers/semantic.py#L93)；关键支撑逻辑，影响候选、证据或接口的正确传递。

**签名**：`def fingerprint(self) -> str`。

**作用**：处理 `fingerprint` 对应步骤；下列步骤依据函数体的实际控制流和调用点整理。

**输入与输出**：
- 输入：无业务参数（或仅隐式接收实例）。
- 输出类型：`str`；具体返回路径见流程步骤。

**处理流程**：
1. 返回 `stable_id('semantic-advisor', self.base_url.casefold(), self.model, ENTITY_PROMPT_VERSION, FUSION_PROMPT…`。

**调用与被调用**：
- `stable_id`（调用点 [semantic.py:94](../../../src/providers/semantic.py#L94)）→ [stable_id](../core/ids.md)，静态可定位。
- `self.base_url.casefold`（[semantic.py:96](../../../src/providers/semantic.py#L96)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- 静态可定位的调用方：[OpenAICompatibleSemanticAdvisor._ask](semantic.md)。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：未见 `raise`；下游异常可能继续上抛。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。


---

# OpenAICompatibleSemanticAdvisor._ask ⭐⭐

**位置与等级**：[semantic.py:102](../../../src/providers/semantic.py#L102)；局部辅助逻辑，需理解其调用条件与失败传播。

**签名**：`async def _ask(self, operation_id: str, provider: Literal['governance', 'fusion'], prompt_version: str, payload: dict[str, Any]) -> tuple[dict[str, Any], ProviderCallRecord]`。

**作用**：内部辅助步骤；将参数转换为本模块所需的中间对象或操作结果。

**输入与输出**：
- 输入：`operation_id`（str）；`provider`（Literal['governance', 'fusion']）；`prompt_version`（str）；`payload`（dict[str, Any]）。
- 输出类型：`tuple[dict[str, Any], ProviderCallRecord]`；具体返回路径见流程步骤。

**处理流程**：
1. 更新 `body`，值来自 `{'model': self.model, 'temperature': 0, <字符串常量>: 256, 'response_format': {'type': 'json_object'}, '…`。
2. 更新 `(response, record)`，值来自 `await post_chat_completion(base_url=self.base_url, api_key=self.api_key, body=body, timeout=self.ti…`。
3. 捕获 (KeyError, IndexError, TypeError, ValueError)；另检查 finally/else 的清理和传播。

**调用与被调用**：
- `json.dumps`（[semantic.py:124](../../../src/providers/semantic.py#L124)）：来自 `json`；具体实现可能由依赖注入或运行时分派决定。
- `post_chat_completion`（调用点 [semantic.py:127](../../../src/providers/semantic.py#L127)）→ [post_chat_completion](http_client.md)，静态可定位。
- `self.fingerprint`（调用点 [semantic.py:136](../../../src/providers/semantic.py#L136)）→ [OpenAICompatibleSemanticAdvisor.fingerprint](semantic.md)，静态可定位。
- `parse_json_object`（调用点 [semantic.py:139](../../../src/providers/semantic.py#L139)）→ [parse_json_object](common.md)，静态可定位。
- `ProviderResponseError`（调用点 [semantic.py:141](../../../src/providers/semantic.py#L141)）→ [ProviderResponseError](../core/errors.md)，静态可定位。
- 静态可定位的调用方：[OpenAICompatibleSemanticAdvisor.advise_entity](semantic.md)、[OpenAICompatibleSemanticAdvisor.advise_fusion](semantic.md)。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：`ProviderResponseError(<字符串常量>, call_records=[record])`。
- 本地捕获：`(KeyError, IndexError, TypeError, ValueError)`。


---

# OpenAICompatibleSemanticAdvisor.advise_entity ⭐⭐⭐

**位置与等级**：[semantic.py:145](../../../src/providers/semantic.py#L145)；关键支撑逻辑，影响候选、证据或接口的正确传递。

**签名**：`async def advise_entity(self, request: EntityAdviceRequest) -> tuple[EntityAdvice, ProviderCallRecord | None]`。

**作用**：处理 `advise_entity` 对应步骤；下列步骤依据函数体的实际控制流和调用点整理。

**输入与输出**：
- 输入：`request`（EntityAdviceRequest）。
- 输出类型：`tuple[EntityAdvice, ProviderCallRecord | None]`；具体返回路径见流程步骤。

**处理流程**：
1. 更新 `entities`，值来自 `{item.id: item for item in request.candidate_entities}`。
2. 更新 `options`，值来自 `[{'entity_id': item.entity_id, 'name': entities[item.entity_id].name, 'type': entities[item.entity_…`。
3. 更新 `(payload, record)`，值来自 `await self._ask(request.mention.id, 'governance', ENTITY_PROMPT_VERSION, {'task': <字符串常量>, 'mention…`。
4. 捕获 ValidationError；另检查 finally/else 的清理和传播。
5. 更新 `allowed`，值来自 `{item.entity_id for item in request.candidates}`。
6. 检查 `advice.selected_entity_id is not None and advice.selected_entity_id not in allowed`；按条件分流，else 分支不存在。
7. 检查 `advice.action == 'link' and advice.selected_entity_id is None`；按条件分流，else 分支不存在。
8. 返回 `(advice, record)`。

**关键条件与保护**：
- [semantic.py:183](../../../src/providers/semantic.py#L183)：`advice.selected_entity_id is not None and advice.selected_entity_id not in allowed`，不满足时跳过本分支。
- [semantic.py:187](../../../src/providers/semantic.py#L187)：`advice.action == 'link' and advice.selected_entity_id is None`，不满足时跳过本分支。

**调用与被调用**：
- `self._ask`（调用点 [semantic.py:161](../../../src/providers/semantic.py#L161)）→ [OpenAICompatibleSemanticAdvisor._ask](semantic.md)，静态可定位。
- `EntityAdvice.model_validate`（[semantic.py:177](../../../src/providers/semantic.py#L177)）：来自 `src.domain.EntityAdvice`；具体实现可能由依赖注入或运行时分派决定。
- `ProviderResponseError`（调用点 [semantic.py:179](../../../src/providers/semantic.py#L179)）→ [ProviderResponseError](../core/errors.md)，静态可定位。
- 静态扫描未定位直接调用方；可能通过路由注册、LangGraph 节点、协议方法或依赖注入动态调用，不据此判断为死代码。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：`ProviderResponseError(<字符串常量>, call_records=[record])`。
- 本地捕获：`ValidationError`。


---

# OpenAICompatibleSemanticAdvisor.advise_fusion ⭐⭐⭐

**位置与等级**：[semantic.py:193](../../../src/providers/semantic.py#L193)；关键支撑逻辑，影响候选、证据或接口的正确传递。

**签名**：`async def advise_fusion(self, request: FusionAdviceRequest) -> tuple[FusionAdvice, ProviderCallRecord | None]`。

**作用**：处理 `advise_fusion` 对应步骤；下列步骤依据函数体的实际控制流和调用点整理。

**输入与输出**：
- 输入：`request`（FusionAdviceRequest）。
- 输出类型：`tuple[FusionAdvice, ProviderCallRecord | None]`；具体返回路径见流程步骤。

**处理流程**：
1. 更新 `(payload, record)`，值来自 `await self._ask(stable_id('fusion-pair', request.left.id, request.right.id), 'fusion', FUSION_PROMP…`。
2. 捕获 ValidationError；另检查 finally/else 的清理和传播。

**调用与被调用**：
- `self._ask`（调用点 [semantic.py:206](../../../src/providers/semantic.py#L206)）→ [OpenAICompatibleSemanticAdvisor._ask](semantic.md)，静态可定位。
- `stable_id`（调用点 [semantic.py:207](../../../src/providers/semantic.py#L207)）→ [stable_id](../core/ids.md)，静态可定位。
- `summary`（[semantic.py:214](../../../src/providers/semantic.py#L214)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `FusionAdvice.model_validate`（[semantic.py:219](../../../src/providers/semantic.py#L219)）：来自 `src.domain.FusionAdvice`；具体实现可能由依赖注入或运行时分派决定。
- `ProviderResponseError`（调用点 [semantic.py:221](../../../src/providers/semantic.py#L221)）→ [ProviderResponseError](../core/errors.md)，静态可定位。
- 静态扫描未定位直接调用方；可能通过路由注册、LangGraph 节点、协议方法或依赖注入动态调用，不据此判断为死代码。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：`ProviderResponseError(<字符串常量>, call_records=[record])`。
- 本地捕获：`ValidationError`。


---

# OpenAICompatibleSemanticAdvisor.advise_fusion.summary ⭐⭐⭐

**位置与等级**：[semantic.py:196](../../../src/providers/semantic.py#L196)；关键支撑逻辑，影响候选、证据或接口的正确传递。

**签名**：`def summary(candidate: Any) -> dict[str, Any]`。

**作用**：处理 `summary` 对应步骤；下列步骤依据函数体的实际控制流和调用点整理。

**输入与输出**：
- 输入：`candidate`（Any；尚未成为正式 Claim 的候选）。
- 输出类型：`dict[str, Any]`；具体返回路径见流程步骤。

**处理流程**：
1. 返回 `{'id': candidate.id, 'subject': candidate.subject.name, 'relation': candidate.relation, 'object': _candi…`。

**调用与被调用**：
- `_candidate_object`（调用点 [semantic.py:201](../../../src/providers/semantic.py#L201)）→ [_candidate_object](semantic.md)，静态可定位。
- 静态扫描未定位直接调用方；可能通过路由注册、LangGraph 节点、协议方法或依赖注入动态调用，不据此判断为死代码。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：未见 `raise`；下游异常可能继续上抛。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。


---
