源码：[errors.py:1](../../../src/core/errors.py#L1) | 基准：`dev/v0.10@f2f34d7` | 本文件符号数：12

**模块职责**：PrismKE-specific exceptions.
**在系统中的位置**：全局设置、稳定标识、执行控制与错误类型；为其他层提供通用约束。
**直接依赖**：无显式项目内模块导入；外部/标准库：`collections`。
**主要调用方（静态导入）**：[agents/budget.py](../agents/budget.md)、[agents/entity_governance_agent.py](../agents/entity_governance_agent.md)、[agents/fusion_review_agent.py](../agents/fusion_review_agent.md)、[agents/multimodal_extraction_agent.py](../agents/multimodal_extraction_agent.md)、[api/app.py](../api/app.md)、[cli.py](../cli.md)、[domain/schema.py](../domain/schema.md)、[governance/claim_normalization.py](../governance/claim_normalization.md)、[governance/entity_operations.py](../governance/entity_operations.md)、[governance/entity_resolution.py](../governance/entity_resolution.md)、[governance/review_guards.py](../governance/review_guards.md)、[governance/validation/service.py](../governance/validation/service.md)。
**阅读提示**：下列流程根据当前源码控制流整理；`self`/接口对象的实际类型可能在运行时注入，未能静态解析的调用会明确标注。链接指向源码行或对应讲解文件。

---

# PrismKEError ⭐⭐⭐

**位置与等级**：[errors.py:6](../../../src/core/errors.py#L6)；关键支撑逻辑，影响候选、证据或接口的正确传递。

**职责**：失败类型；调用方可据此区分可恢复、阻断和一般错误。基类：`Exception`。
**源码说明**：Base error for recoverable PrismKE failures.

**字段与类级约束**：
- 类体未直接声明字段；实例状态请看 `__init__` 及方法中的赋值。

**内部成员**：此类未直接定义方法；字段/继承行为见源码。


---

# UnsupportedDocumentError ⭐⭐⭐

**位置与等级**：[errors.py:10](../../../src/core/errors.py#L10)；关键支撑逻辑，影响候选、证据或接口的正确传递。

**职责**：失败类型；调用方可据此区分可恢复、阻断和一般错误。基类：`PrismKEError`。
**源码说明**：Raised when no parser supports an input document.

**字段与类级约束**：
- 类体未直接声明字段；实例状态请看 `__init__` 及方法中的赋值。

**内部成员**：此类未直接定义方法；字段/继承行为见源码。


---

# SchemaValidationError ⭐⭐⭐

**位置与等级**：[errors.py:14](../../../src/core/errors.py#L14)；关键支撑逻辑，影响候选、证据或接口的正确传递。

**职责**：失败类型；调用方可据此区分可恢复、阻断和一般错误。基类：`PrismKEError`。
**源码说明**：Raised when extracted knowledge violates a schema.

**字段与类级约束**：
- 类体未直接声明字段；实例状态请看 `__init__` 及方法中的赋值。

**内部成员**：此类未直接定义方法；字段/继承行为见源码。


---

# EvidenceRequiredError ⭐⭐⭐

**位置与等级**：[errors.py:18](../../../src/core/errors.py#L18)；关键支撑逻辑，影响候选、证据或接口的正确传递。

**职责**：失败类型；调用方可据此区分可恢复、阻断和一般错误。基类：`PrismKEError`。
**源码说明**：Raised when a claim without evidence reaches persistence.

**字段与类级约束**：
- 类体未直接声明字段；实例状态请看 `__init__` 及方法中的赋值。

**内部成员**：此类未直接定义方法；字段/继承行为见源码。


---

# EvidenceIntegrityError ⭐⭐⭐

**位置与等级**：[errors.py:22](../../../src/core/errors.py#L22)；关键支撑逻辑，影响候选、证据或接口的正确传递。

**职责**：失败类型；调用方可据此区分可恢复、阻断和一般错误。基类：`PrismKEError`。
**源码说明**：Raised when stored evidence is missing, changed, or inconsistent.

**字段与类级约束**：
- 类体未直接声明字段；实例状态请看 `__init__` 及方法中的赋值。

**内部成员**：此类未直接定义方法；字段/继承行为见源码。


---

# GraphIntegrityError ⭐⭐⭐

**位置与等级**：[errors.py:26](../../../src/core/errors.py#L26)；关键支撑逻辑，影响候选、证据或接口的正确传递。

**职责**：失败类型；调用方可据此区分可恢复、阻断和一般错误。基类：`PrismKEError`。
**源码说明**：Raised when a graph transaction violates referential integrity.

**字段与类级约束**：
- 类体未直接声明字段；实例状态请看 `__init__` 及方法中的赋值。

**内部成员**：此类未直接定义方法；字段/继承行为见源码。


---

# ProviderConfigurationError ⭐⭐⭐

**位置与等级**：[errors.py:30](../../../src/core/errors.py#L30)；关键支撑逻辑，影响候选、证据或接口的正确传递。

**职责**：失败类型；调用方可据此区分可恢复、阻断和一般错误。基类：`PrismKEError`。
**源码说明**：Raised when an explicitly selected provider is not configured.

**字段与类级约束**：
- 类体未直接声明字段；实例状态请看 `__init__` 及方法中的赋值。

**内部成员**：此类未直接定义方法；字段/继承行为见源码。


---

# ProviderRequestError ⭐⭐⭐

**位置与等级**：[errors.py:34](../../../src/core/errors.py#L34)；关键支撑逻辑，影响候选、证据或接口的正确传递。

**职责**：失败类型；调用方可据此区分可恢复、阻断和一般错误。基类：`PrismKEError`。
**源码说明**：Raised for a sanitized external provider request failure.

**字段与类级约束**：
- 类体未直接声明字段；实例状态请看 `__init__` 及方法中的赋值。

**内部成员**：`ProviderRequestError.__init__`


---

# ProviderRequestError.__init__ ⭐⭐

**位置与等级**：[errors.py:37](../../../src/core/errors.py#L37)；局部辅助逻辑，需理解其调用条件与失败传播。

**签名**：`def __init__(self, message: str, *, call_record: object | None=None) -> None`。

**作用**：初始化对象并保存依赖或配置；需检查是否创建持久化资源。

**输入与输出**：
- 输入：`message`（str）；`call_record`（object | None；默认 `None`）。
- 输出类型：`None`；具体返回路径见流程步骤。

**处理流程**：
1. 调用 `super().__init__`，结果未直接赋值。
2. 更新 `self.call_record`，值来自 `call_record`。

**调用与被调用**：
- `super().__init__`（[errors.py:38](../../../src/core/errors.py#L38)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `super`（[errors.py:38](../../../src/core/errors.py#L38)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- 静态扫描未定位直接调用方；可能通过路由注册、LangGraph 节点、协议方法或依赖注入动态调用，不据此判断为死代码。

**状态、副作用与异常**：
- 显式状态/容器赋值：`self.call_record`。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：未见 `raise`；下游异常可能继续上抛。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。


---

# ProviderResponseError ⭐⭐⭐

**位置与等级**：[errors.py:42](../../../src/core/errors.py#L42)；关键支撑逻辑，影响候选、证据或接口的正确传递。

**职责**：失败类型；调用方可据此区分可恢复、阻断和一般错误。基类：`PrismKEError`。
**源码说明**：Raised when a provider returns an unusable response payload.

**字段与类级约束**：
- 类体未直接声明字段；实例状态请看 `__init__` 及方法中的赋值。

**内部成员**：`ProviderResponseError.__init__`


---

# ProviderResponseError.__init__ ⭐⭐

**位置与等级**：[errors.py:45](../../../src/core/errors.py#L45)；局部辅助逻辑，需理解其调用条件与失败传播。

**签名**：`def __init__(self, message: str, *, call_records: Sequence[object] | None=None) -> None`。

**作用**：初始化对象并保存依赖或配置；需检查是否创建持久化资源。

**输入与输出**：
- 输入：`message`（str）；`call_records`（Sequence[object] | None；默认 `None`）。
- 输出类型：`None`；具体返回路径见流程步骤。

**处理流程**：
1. 调用 `super().__init__`，结果未直接赋值。
2. 更新 `self.call_records`，值来自 `list(call_records or [])`。

**调用与被调用**：
- `super().__init__`（[errors.py:46](../../../src/core/errors.py#L46)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `super`（[errors.py:46](../../../src/core/errors.py#L46)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `list`（[errors.py:47](../../../src/core/errors.py#L47)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- 静态扫描未定位直接调用方；可能通过路由注册、LangGraph 节点、协议方法或依赖注入动态调用，不据此判断为死代码。

**状态、副作用与异常**：
- 显式状态/容器赋值：`self.call_records`。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：未见 `raise`；下游异常可能继续上抛。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。


---

# LegacyCheckpointError ⭐⭐⭐

**位置与等级**：[errors.py:50](../../../src/core/errors.py#L50)；关键支撑逻辑，影响候选、证据或接口的正确传递。

**职责**：失败类型；调用方可据此区分可恢复、阻断和一般错误。基类：`PrismKEError`。
**源码说明**：Raised when a run predates the current checkpoint format.

**字段与类级约束**：
- 类体未直接声明字段；实例状态请看 `__init__` 及方法中的赋值。

**内部成员**：此类未直接定义方法；字段/继承行为见源码。


---
