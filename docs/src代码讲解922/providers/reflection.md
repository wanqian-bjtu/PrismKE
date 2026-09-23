源码：[reflection.py:1](../../../src/providers/reflection.py#L1) | 基准：`dev/v0.10@f2f34d7` | 本文件符号数：11

**模块职责**：Bounded Reflection providers for candidate repair.
**在系统中的位置**：LLM、OCR、VLM、Embedding、Reflection 与语义建议的外部能力接口和实现。
**直接依赖**：[src.core.ids](../core/ids.md)、[src.domain](../domain/__init__.md)、[src.providers.common](common.md)、[src.providers.http_client](http_client.md)；外部/标准库：`__future__`、`collections`、`httpx`、`json`、`typing`。
**主要调用方（静态导入）**：[providers/__init__.py](__init__.md)。
**阅读提示**：下列流程根据当前源码控制流整理；`self`/接口对象的实际类型可能在运行时注入，未能静态解析的调用会明确标注。链接指向源码行或对应讲解文件。

---

# DisabledReflectionProvider ⭐⭐⭐⭐

**位置与等级**：[reflection.py:20](../../../src/providers/reflection.py#L20)；承担主要 Agent、应用服务或审核/执行入口，跨模块影响显著。

**职责**：外部能力实现或协议；调用是否耗费模型额度取决于具体实现。基类：无显式基类。

**字段与类级约束**：
- 类体未直接声明字段；实例状态请看 `__init__` 及方法中的赋值。

**内部成员**：`DisabledReflectionProvider.fingerprint`、`DisabledReflectionProvider.reflect`


---

# DisabledReflectionProvider.fingerprint ⭐⭐⭐⭐

**位置与等级**：[reflection.py:21](../../../src/providers/reflection.py#L21)；承担主要 Agent、应用服务或审核/执行入口，跨模块影响显著。

**签名**：`def fingerprint(self) -> str`。

**作用**：处理 `fingerprint` 对应步骤；下列步骤依据函数体的实际控制流和调用点整理。

**输入与输出**：
- 输入：无业务参数（或仅隐式接收实例）。
- 输出类型：`str`；具体返回路径见流程步骤。

**处理流程**：
1. 返回 `'reflection:disabled'`。

**调用与被调用**：
- 无显式函数调用，或仅声明协议/常量。
- 静态扫描未定位直接调用方；可能通过路由注册、LangGraph 节点、协议方法或依赖注入动态调用，不据此判断为死代码。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：未见 `raise`；下游异常可能继续上抛。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。


---

# DisabledReflectionProvider.reflect ⭐⭐⭐⭐

**位置与等级**：[reflection.py:24](../../../src/providers/reflection.py#L24)；承担主要 Agent、应用服务或审核/执行入口，跨模块影响显著。

**签名**：`async def reflect(self, request: ReflectionRequest) -> ReflectionResult`。

**作用**：处理 `reflect` 对应步骤；下列步骤依据函数体的实际控制流和调用点整理。

**输入与输出**：
- 输入：`request`（ReflectionRequest）。
- 输出类型：`ReflectionResult`；具体返回路径见流程步骤。

**处理流程**：
1. 返回 `ReflectionResult(warnings=['reflection_disabled'])`。

**调用与被调用**：
- `ReflectionResult`（[reflection.py:25](../../../src/providers/reflection.py#L25)）：来自 `src.domain.ReflectionResult`；具体实现可能由依赖注入或运行时分派决定。
- 静态扫描未定位直接调用方；可能通过路由注册、LangGraph 节点、协议方法或依赖注入动态调用，不据此判断为死代码。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：未见 `raise`；下游异常可能继续上抛。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。


---

# MockReflectionProvider ⭐⭐⭐⭐

**位置与等级**：[reflection.py:28](../../../src/providers/reflection.py#L28)；承担主要 Agent、应用服务或审核/执行入口，跨模块影响显著。

**职责**：外部能力实现或协议；调用是否耗费模型额度取决于具体实现。基类：无显式基类。

**字段与类级约束**：
- 类体未直接声明字段；实例状态请看 `__init__` 及方法中的赋值。

**内部成员**：`MockReflectionProvider.__init__`、`MockReflectionProvider.fingerprint`、`MockReflectionProvider.reflect`


---

# MockReflectionProvider.__init__ ⭐⭐⭐⭐

**位置与等级**：[reflection.py:29](../../../src/providers/reflection.py#L29)；承担主要 Agent、应用服务或审核/执行入口，跨模块影响显著。

**签名**：`def __init__(self, repair: Callable[[ReflectionRequest], CandidateClaim | None] | None=None) -> None`。

**作用**：初始化对象并保存依赖或配置；需检查是否创建持久化资源。

**输入与输出**：
- 输入：`repair`（Callable[[ReflectionRequest], CandidateClaim | None] | None；默认 `None`）。
- 输出类型：`None`；具体返回路径见流程步骤。

**处理流程**：
1. 更新 `self.repair`，值来自 `repair`。

**调用与被调用**：
- 无显式函数调用，或仅声明协议/常量。
- 静态扫描未定位直接调用方；可能通过路由注册、LangGraph 节点、协议方法或依赖注入动态调用，不据此判断为死代码。

**状态、副作用与异常**：
- 显式状态/容器赋值：`self.repair`。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：未见 `raise`；下游异常可能继续上抛。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。


---

# MockReflectionProvider.fingerprint ⭐⭐⭐⭐

**位置与等级**：[reflection.py:34](../../../src/providers/reflection.py#L34)；承担主要 Agent、应用服务或审核/执行入口，跨模块影响显著。

**签名**：`def fingerprint(self) -> str`。

**作用**：处理 `fingerprint` 对应步骤；下列步骤依据函数体的实际控制流和调用点整理。

**输入与输出**：
- 输入：无业务参数（或仅隐式接收实例）。
- 输出类型：`str`；具体返回路径见流程步骤。

**处理流程**：
1. 返回 `'reflection:mock:v1'`。

**调用与被调用**：
- 无显式函数调用，或仅声明协议/常量。
- 静态扫描未定位直接调用方；可能通过路由注册、LangGraph 节点、协议方法或依赖注入动态调用，不据此判断为死代码。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：未见 `raise`；下游异常可能继续上抛。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。


---

# MockReflectionProvider.reflect ⭐⭐⭐⭐

**位置与等级**：[reflection.py:37](../../../src/providers/reflection.py#L37)；承担主要 Agent、应用服务或审核/执行入口，跨模块影响显著。

**签名**：`async def reflect(self, request: ReflectionRequest) -> ReflectionResult`。

**作用**：处理 `reflect` 对应步骤；下列步骤依据函数体的实际控制流和调用点整理。

**输入与输出**：
- 输入：`request`（ReflectionRequest）。
- 输出类型：`ReflectionResult`；具体返回路径见流程步骤。

**处理流程**：
1. 更新 `candidate`，值来自 `self.repair(request) if self.repair else request.candidate.model_copy(deep=True)`。
2. 返回 `ReflectionResult(candidate=candidate, input_tokens=0, output_tokens=0, total_tokens=0)`。

**调用与被调用**：
- `self.repair`（[reflection.py:38](../../../src/providers/reflection.py#L38)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `request.candidate.model_copy`（[reflection.py:38](../../../src/providers/reflection.py#L38)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `ReflectionResult`（[reflection.py:39](../../../src/providers/reflection.py#L39)）：来自 `src.domain.ReflectionResult`；具体实现可能由依赖注入或运行时分派决定。
- 静态扫描未定位直接调用方；可能通过路由注册、LangGraph 节点、协议方法或依赖注入动态调用，不据此判断为死代码。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：未见 `raise`；下游异常可能继续上抛。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。


---

# OpenAICompatibleReflectionProvider ⭐⭐⭐⭐

**位置与等级**：[reflection.py:44](../../../src/providers/reflection.py#L44)；承担主要 Agent、应用服务或审核/执行入口，跨模块影响显著。

**职责**：外部能力实现或协议；调用是否耗费模型额度取决于具体实现。基类：无显式基类。

**字段与类级约束**：
- 类体未直接声明字段；实例状态请看 `__init__` 及方法中的赋值。

**内部成员**：`OpenAICompatibleReflectionProvider.__init__`、`OpenAICompatibleReflectionProvider.fingerprint`、`OpenAICompatibleReflectionProvider.reflect`


---

# OpenAICompatibleReflectionProvider.__init__ ⭐⭐⭐⭐

**位置与等级**：[reflection.py:45](../../../src/providers/reflection.py#L45)；承担主要 Agent、应用服务或审核/执行入口，跨模块影响显著。

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
- `base_url.rstrip`（[reflection.py:53](../../../src/providers/reflection.py#L53)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- 静态扫描未定位直接调用方；可能通过路由注册、LangGraph 节点、协议方法或依赖注入动态调用，不据此判断为死代码。

**状态、副作用与异常**：
- 显式状态/容器赋值：`self.base_url`、`self.api_key`、`self.model`、`self.timeout`、`self.transport`。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：未见 `raise`；下游异常可能继续上抛。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。


---

# OpenAICompatibleReflectionProvider.fingerprint ⭐⭐⭐⭐

**位置与等级**：[reflection.py:59](../../../src/providers/reflection.py#L59)；承担主要 Agent、应用服务或审核/执行入口，跨模块影响显著。

**签名**：`def fingerprint(self) -> str`。

**作用**：处理 `fingerprint` 对应步骤；下列步骤依据函数体的实际控制流和调用点整理。

**输入与输出**：
- 输入：无业务参数（或仅隐式接收实例）。
- 输出类型：`str`；具体返回路径见流程步骤。

**处理流程**：
1. 返回 `stable_id('reflection-provider', 'openai-compatible', self.base_url.casefold(), self.model, PROMPT_VERSI…`。

**调用与被调用**：
- `stable_id`（调用点 [reflection.py:60](../../../src/providers/reflection.py#L60)）→ [stable_id](../core/ids.md)，静态可定位。
- `self.base_url.casefold`（[reflection.py:63](../../../src/providers/reflection.py#L63)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- 静态可定位的调用方：[OpenAICompatibleReflectionProvider.reflect](reflection.md)。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：未见 `raise`；下游异常可能继续上抛。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。


---

# OpenAICompatibleReflectionProvider.reflect ⭐⭐⭐⭐

**位置与等级**：[reflection.py:69](../../../src/providers/reflection.py#L69)；承担主要 Agent、应用服务或审核/执行入口，跨模块影响显著。

**签名**：`async def reflect(self, request: ReflectionRequest) -> ReflectionResult`。

**作用**：处理 `reflect` 对应步骤；下列步骤依据函数体的实际控制流和调用点整理。

**输入与输出**：
- 输入：`request`（ReflectionRequest）。
- 输出类型：`ReflectionResult`；具体返回路径见流程步骤。

**处理流程**：
1. 更新 `cases`，值来自 `[item.model_dump(mode='json') for item in request.retrieved_cases]`。
2. 更新 `issues_json`，值来自 `json.dumps([item.model_dump(mode='json') for item in request.issues], ensure_ascii=False)`。
3. 更新 `prompt`，值来自 `f""<字符串常量>candidate<字符串常量>""`。
4. 更新 `body`，值来自 `{'model': self.model, 'messages': [{'role': 'user', 'content': prompt}], 'temperature': 0, 'respons…`。
5. 更新 `(response, call)`，值来自 `await post_chat_completion(base_url=self.base_url, api_key=self.api_key, body=body, timeout=self.ti…`。
6. 捕获 (KeyError, IndexError, TypeError, ValueError)；另检查 finally/else 的清理和传播。
7. 检查 `candidate is not None and (not set(candidate.evidence_ids) <= set(request.allowed_evidence_ids))`；按条件分流，else 分支存在。
8. 返回 `ReflectionResult(candidate=candidate, raw_response_model=call.response_model, input_tokens=call.input_to…`。

**关键条件与保护**：
- [reflection.py:124](../../../src/providers/reflection.py#L124)：`candidate is not None and (not set(candidate.evidence_ids) <= set(request.allowed_evidence_ids))`，不满足时有 else 分支。

**调用与被调用**：
- `item.model_dump`（[reflection.py:70](../../../src/providers/reflection.py#L70)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `json.dumps`（[reflection.py:71](../../../src/providers/reflection.py#L71)）：来自 `json`；具体实现可能由依赖注入或运行时分派决定。
- `request.output_schema.model_dump_json`（[reflection.py:85](../../../src/providers/reflection.py#L85)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `request.candidate.model_dump_json`（[reflection.py:87](../../../src/providers/reflection.py#L87)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `min`（[reflection.py:96](../../../src/providers/reflection.py#L96)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `max`（[reflection.py:96](../../../src/providers/reflection.py#L96)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `post_chat_completion`（调用点 [reflection.py:99](../../../src/providers/reflection.py#L99)）→ [post_chat_completion](http_client.md)，静态可定位。
- `self.fingerprint`（调用点 [reflection.py:107](../../../src/providers/reflection.py#L107)）→ [OpenAICompatibleReflectionProvider.fingerprint](reflection.md)，静态可定位。
- `parse_json_object`（调用点 [reflection.py:111](../../../src/providers/reflection.py#L111)）→ [parse_json_object](common.md)，静态可定位。
- `payload.get`（[reflection.py:112](../../../src/providers/reflection.py#L112)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `CandidateClaim.model_validate`（[reflection.py:113](../../../src/providers/reflection.py#L113)）：来自 `src.domain.CandidateClaim`；具体实现可能由依赖注入或运行时分派决定。
- `ReflectionResult`（[reflection.py:115](../../../src/providers/reflection.py#L115)）：来自 `src.domain.ReflectionResult`；具体实现可能由依赖注入或运行时分派决定。
- `type`（[reflection.py:122](../../../src/providers/reflection.py#L122)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `set`（[reflection.py:124](../../../src/providers/reflection.py#L124)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- 静态扫描未定位直接调用方；可能通过路由注册、LangGraph 节点、协议方法或依赖注入动态调用，不据此判断为死代码。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：未见 `raise`；下游异常可能继续上抛。
- 本地捕获：`(KeyError, IndexError, TypeError, ValueError)`。


---
