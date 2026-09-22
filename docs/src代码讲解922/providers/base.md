源码：[base.py:1](../../../src/providers/base.py#L1) | 基准：`dev/v0.10@f2f34d7` | 本文件符号数：19

**模块职责**：Model provider extension boundaries.
**在系统中的位置**：LLM、OCR、VLM、Embedding、Reflection 与语义建议的外部能力接口和实现。
**直接依赖**：[src.domain](../domain/__init__.md)；外部/标准库：`__future__`、`typing`。
**主要调用方（静态导入）**：[agents/entity_governance_agent.py](../agents/entity_governance_agent.md)、[agents/fusion_review_agent.py](../agents/fusion_review_agent.md)、[agents/multimodal_extraction_agent.py](../agents/multimodal_extraction_agent.md)、[cli.py](../cli.md)、[evaluation/document_validation.py](../evaluation/document_validation.md)、[evaluation/entity_linking.py](../evaluation/entity_linking.md)、[evaluation/reflection.py](../evaluation/reflection.md)、[governance/entity_index.py](../governance/entity_index.md)、[governance/entity_operations.py](../governance/entity_operations.md)、[governance/entity_resolution.py](../governance/entity_resolution.md)、[workflow/cases.py](../workflow/cases.md)、[workflow/execution.py](../workflow/execution.md)。
**阅读提示**：下列流程根据当前源码控制流整理；`self`/接口对象的实际类型可能在运行时注入，未能静态解析的调用会明确标注。链接指向源码行或对应讲解文件。

---

# SemanticAdvisor ⭐⭐⭐

**位置与等级**：[base.py:23](../../../src/providers/base.py#L23)；关键支撑逻辑，影响候选、证据或接口的正确传递。

**职责**：本模块的对象实现或数据契约；具体语义由字段、基类和方法共同决定。基类：`Protocol`。

**字段与类级约束**：
- 类体未直接声明字段；实例状态请看 `__init__` 及方法中的赋值。

**内部成员**：`SemanticAdvisor.fingerprint`、`SemanticAdvisor.advise_entity`、`SemanticAdvisor.advise_fusion`


---

# SemanticAdvisor.fingerprint ⭐⭐⭐

**位置与等级**：[base.py:24](../../../src/providers/base.py#L24)；关键支撑逻辑，影响候选、证据或接口的正确传递。

**签名**：`def fingerprint(self) -> str`。

**作用**：处理 `fingerprint` 对应步骤；下列步骤依据函数体的实际控制流和调用点整理。

**输入与输出**：
- 输入：无业务参数（或仅隐式接收实例）。
- 输出类型：`str`；具体返回路径见流程步骤。

**处理流程**：函数体无可展开的语句级步骤；可能是协议定义、空实现或简单表达式，请结合源码。

**调用与被调用**：
- 无显式函数调用，或仅声明协议/常量。
- 静态扫描未定位直接调用方；可能通过路由注册、LangGraph 节点、协议方法或依赖注入动态调用，不据此判断为死代码。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：未见 `raise`；下游异常可能继续上抛。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。


---

# SemanticAdvisor.advise_entity ⭐⭐⭐

**位置与等级**：[base.py:26](../../../src/providers/base.py#L26)；关键支撑逻辑，影响候选、证据或接口的正确传递。

**签名**：`async def advise_entity(self, request: EntityAdviceRequest) -> tuple[EntityAdvice, ProviderCallRecord | None]`。

**作用**：处理 `advise_entity` 对应步骤；下列步骤依据函数体的实际控制流和调用点整理。

**输入与输出**：
- 输入：`request`（EntityAdviceRequest）。
- 输出类型：`tuple[EntityAdvice, ProviderCallRecord | None]`；具体返回路径见流程步骤。

**处理流程**：函数体无可展开的语句级步骤；可能是协议定义、空实现或简单表达式，请结合源码。

**调用与被调用**：
- 无显式函数调用，或仅声明协议/常量。
- 静态扫描未定位直接调用方；可能通过路由注册、LangGraph 节点、协议方法或依赖注入动态调用，不据此判断为死代码。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：未见 `raise`；下游异常可能继续上抛。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。


---

# SemanticAdvisor.advise_fusion ⭐⭐⭐

**位置与等级**：[base.py:30](../../../src/providers/base.py#L30)；关键支撑逻辑，影响候选、证据或接口的正确传递。

**签名**：`async def advise_fusion(self, request: FusionAdviceRequest) -> tuple[FusionAdvice, ProviderCallRecord | None]`。

**作用**：处理 `advise_fusion` 对应步骤；下列步骤依据函数体的实际控制流和调用点整理。

**输入与输出**：
- 输入：`request`（FusionAdviceRequest）。
- 输出类型：`tuple[FusionAdvice, ProviderCallRecord | None]`；具体返回路径见流程步骤。

**处理流程**：函数体无可展开的语句级步骤；可能是协议定义、空实现或简单表达式，请结合源码。

**调用与被调用**：
- 无显式函数调用，或仅声明协议/常量。
- 静态扫描未定位直接调用方；可能通过路由注册、LangGraph 节点、协议方法或依赖注入动态调用，不据此判断为死代码。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：未见 `raise`；下游异常可能继续上抛。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。


---

# LLMProvider ⭐⭐⭐

**位置与等级**：[base.py:35](../../../src/providers/base.py#L35)；关键支撑逻辑，影响候选、证据或接口的正确传递。

**职责**：外部能力实现或协议；调用是否耗费模型额度取决于具体实现。基类：`Protocol`。

**字段与类级约束**：
- 类体未直接声明字段；实例状态请看 `__init__` 及方法中的赋值。

**内部成员**：`LLMProvider.fingerprint`、`LLMProvider.extract`


---

# LLMProvider.fingerprint ⭐⭐⭐

**位置与等级**：[base.py:36](../../../src/providers/base.py#L36)；关键支撑逻辑，影响候选、证据或接口的正确传递。

**签名**：`def fingerprint(self) -> str`。

**作用**：处理 `fingerprint` 对应步骤；下列步骤依据函数体的实际控制流和调用点整理。

**输入与输出**：
- 输入：无业务参数（或仅隐式接收实例）。
- 输出类型：`str`；具体返回路径见流程步骤。

**处理流程**：函数体无可展开的语句级步骤；可能是协议定义、空实现或简单表达式，请结合源码。

**调用与被调用**：
- 无显式函数调用，或仅声明协议/常量。
- 静态扫描未定位直接调用方；可能通过路由注册、LangGraph 节点、协议方法或依赖注入动态调用，不据此判断为死代码。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：未见 `raise`；下游异常可能继续上抛。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。


---

# LLMProvider.extract ⭐⭐⭐⭐

**位置与等级**：[base.py:38](../../../src/providers/base.py#L38)；承担主要 Agent、应用服务或审核/执行入口，跨模块影响显著。

**签名**：`async def extract(self, request: ExtractionRequest) -> ExtractionResult`。

**作用**：处理 `extract` 对应步骤；下列步骤依据函数体的实际控制流和调用点整理。

**输入与输出**：
- 输入：`request`（ExtractionRequest）。
- 输出类型：`ExtractionResult`；具体返回路径见流程步骤。

**处理流程**：函数体无可展开的语句级步骤；可能是协议定义、空实现或简单表达式，请结合源码。

**调用与被调用**：
- 无显式函数调用，或仅声明协议/常量。
- 静态扫描未定位直接调用方；可能通过路由注册、LangGraph 节点、协议方法或依赖注入动态调用，不据此判断为死代码。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：未见 `raise`；下游异常可能继续上抛。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。


---

# VLMProvider ⭐⭐⭐

**位置与等级**：[base.py:41](../../../src/providers/base.py#L41)；关键支撑逻辑，影响候选、证据或接口的正确传递。

**职责**：外部能力实现或协议；调用是否耗费模型额度取决于具体实现。基类：`Protocol`。

**字段与类级约束**：
- 类体未直接声明字段；实例状态请看 `__init__` 及方法中的赋值。

**内部成员**：`VLMProvider.fingerprint`、`VLMProvider.extract`


---

# VLMProvider.fingerprint ⭐⭐⭐

**位置与等级**：[base.py:42](../../../src/providers/base.py#L42)；关键支撑逻辑，影响候选、证据或接口的正确传递。

**签名**：`def fingerprint(self) -> str`。

**作用**：处理 `fingerprint` 对应步骤；下列步骤依据函数体的实际控制流和调用点整理。

**输入与输出**：
- 输入：无业务参数（或仅隐式接收实例）。
- 输出类型：`str`；具体返回路径见流程步骤。

**处理流程**：函数体无可展开的语句级步骤；可能是协议定义、空实现或简单表达式，请结合源码。

**调用与被调用**：
- 无显式函数调用，或仅声明协议/常量。
- 静态扫描未定位直接调用方；可能通过路由注册、LangGraph 节点、协议方法或依赖注入动态调用，不据此判断为死代码。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：未见 `raise`；下游异常可能继续上抛。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。


---

# VLMProvider.extract ⭐⭐⭐⭐

**位置与等级**：[base.py:44](../../../src/providers/base.py#L44)；承担主要 Agent、应用服务或审核/执行入口，跨模块影响显著。

**签名**：`async def extract(self, request: VisualExtractionRequest) -> ExtractionResult`。

**作用**：处理 `extract` 对应步骤；下列步骤依据函数体的实际控制流和调用点整理。

**输入与输出**：
- 输入：`request`（VisualExtractionRequest）。
- 输出类型：`ExtractionResult`；具体返回路径见流程步骤。

**处理流程**：函数体无可展开的语句级步骤；可能是协议定义、空实现或简单表达式，请结合源码。

**调用与被调用**：
- 无显式函数调用，或仅声明协议/常量。
- 静态扫描未定位直接调用方；可能通过路由注册、LangGraph 节点、协议方法或依赖注入动态调用，不据此判断为死代码。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：未见 `raise`；下游异常可能继续上抛。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。


---

# OCRProvider ⭐⭐⭐

**位置与等级**：[base.py:47](../../../src/providers/base.py#L47)；关键支撑逻辑，影响候选、证据或接口的正确传递。

**职责**：外部能力实现或协议；调用是否耗费模型额度取决于具体实现。基类：`Protocol`。

**字段与类级约束**：
- 类体未直接声明字段；实例状态请看 `__init__` 及方法中的赋值。

**内部成员**：`OCRProvider.fingerprint`、`OCRProvider.recognize`


---

# OCRProvider.fingerprint ⭐⭐⭐

**位置与等级**：[base.py:48](../../../src/providers/base.py#L48)；关键支撑逻辑，影响候选、证据或接口的正确传递。

**签名**：`def fingerprint(self) -> str`。

**作用**：处理 `fingerprint` 对应步骤；下列步骤依据函数体的实际控制流和调用点整理。

**输入与输出**：
- 输入：无业务参数（或仅隐式接收实例）。
- 输出类型：`str`；具体返回路径见流程步骤。

**处理流程**：函数体无可展开的语句级步骤；可能是协议定义、空实现或简单表达式，请结合源码。

**调用与被调用**：
- 无显式函数调用，或仅声明协议/常量。
- 静态扫描未定位直接调用方；可能通过路由注册、LangGraph 节点、协议方法或依赖注入动态调用，不据此判断为死代码。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：未见 `raise`；下游异常可能继续上抛。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。


---

# OCRProvider.recognize ⭐⭐⭐

**位置与等级**：[base.py:50](../../../src/providers/base.py#L50)；关键支撑逻辑，影响候选、证据或接口的正确传递。

**签名**：`async def recognize(self, request: OCRRequest) -> OCRResult`。

**作用**：处理 `recognize` 对应步骤；下列步骤依据函数体的实际控制流和调用点整理。

**输入与输出**：
- 输入：`request`（OCRRequest）。
- 输出类型：`OCRResult`；具体返回路径见流程步骤。

**处理流程**：函数体无可展开的语句级步骤；可能是协议定义、空实现或简单表达式，请结合源码。

**调用与被调用**：
- 无显式函数调用，或仅声明协议/常量。
- 静态扫描未定位直接调用方；可能通过路由注册、LangGraph 节点、协议方法或依赖注入动态调用，不据此判断为死代码。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：未见 `raise`；下游异常可能继续上抛。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。


---

# EmbeddingProvider ⭐⭐⭐

**位置与等级**：[base.py:53](../../../src/providers/base.py#L53)；关键支撑逻辑，影响候选、证据或接口的正确传递。

**职责**：外部能力实现或协议；调用是否耗费模型额度取决于具体实现。基类：`Protocol`。

**字段与类级约束**：
- 类体未直接声明字段；实例状态请看 `__init__` 及方法中的赋值。

**内部成员**：`EmbeddingProvider.fingerprint`、`EmbeddingProvider.encode`


---

# EmbeddingProvider.fingerprint ⭐⭐⭐

**位置与等级**：[base.py:54](../../../src/providers/base.py#L54)；关键支撑逻辑，影响候选、证据或接口的正确传递。

**签名**：`def fingerprint(self) -> str`。

**作用**：处理 `fingerprint` 对应步骤；下列步骤依据函数体的实际控制流和调用点整理。

**输入与输出**：
- 输入：无业务参数（或仅隐式接收实例）。
- 输出类型：`str`；具体返回路径见流程步骤。

**处理流程**：函数体无可展开的语句级步骤；可能是协议定义、空实现或简单表达式，请结合源码。

**调用与被调用**：
- 无显式函数调用，或仅声明协议/常量。
- 静态扫描未定位直接调用方；可能通过路由注册、LangGraph 节点、协议方法或依赖注入动态调用，不据此判断为死代码。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：未见 `raise`；下游异常可能继续上抛。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。


---

# EmbeddingProvider.encode ⭐⭐⭐

**位置与等级**：[base.py:56](../../../src/providers/base.py#L56)；关键支撑逻辑，影响候选、证据或接口的正确传递。

**签名**：`async def encode(self, texts: list[str]) -> list[list[float]]`。

**作用**：处理 `encode` 对应步骤；下列步骤依据函数体的实际控制流和调用点整理。

**输入与输出**：
- 输入：`texts`（list[str]）。
- 输出类型：`list[list[float]]`；具体返回路径见流程步骤。

**处理流程**：函数体无可展开的语句级步骤；可能是协议定义、空实现或简单表达式，请结合源码。

**调用与被调用**：
- 无显式函数调用，或仅声明协议/常量。
- 静态扫描未定位直接调用方；可能通过路由注册、LangGraph 节点、协议方法或依赖注入动态调用，不据此判断为死代码。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：未见 `raise`；下游异常可能继续上抛。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。


---

# ReflectionProvider ⭐⭐⭐⭐

**位置与等级**：[base.py:59](../../../src/providers/base.py#L59)；承担主要 Agent、应用服务或审核/执行入口，跨模块影响显著。

**职责**：外部能力实现或协议；调用是否耗费模型额度取决于具体实现。基类：`Protocol`。

**字段与类级约束**：
- 类体未直接声明字段；实例状态请看 `__init__` 及方法中的赋值。

**内部成员**：`ReflectionProvider.fingerprint`、`ReflectionProvider.reflect`


---

# ReflectionProvider.fingerprint ⭐⭐⭐⭐

**位置与等级**：[base.py:60](../../../src/providers/base.py#L60)；承担主要 Agent、应用服务或审核/执行入口，跨模块影响显著。

**签名**：`def fingerprint(self) -> str`。

**作用**：处理 `fingerprint` 对应步骤；下列步骤依据函数体的实际控制流和调用点整理。

**输入与输出**：
- 输入：无业务参数（或仅隐式接收实例）。
- 输出类型：`str`；具体返回路径见流程步骤。

**处理流程**：函数体无可展开的语句级步骤；可能是协议定义、空实现或简单表达式，请结合源码。

**调用与被调用**：
- 无显式函数调用，或仅声明协议/常量。
- 静态扫描未定位直接调用方；可能通过路由注册、LangGraph 节点、协议方法或依赖注入动态调用，不据此判断为死代码。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：未见 `raise`；下游异常可能继续上抛。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。


---

# ReflectionProvider.reflect ⭐⭐⭐⭐

**位置与等级**：[base.py:62](../../../src/providers/base.py#L62)；承担主要 Agent、应用服务或审核/执行入口，跨模块影响显著。

**签名**：`async def reflect(self, request: ReflectionRequest) -> ReflectionResult`。

**作用**：处理 `reflect` 对应步骤；下列步骤依据函数体的实际控制流和调用点整理。

**输入与输出**：
- 输入：`request`（ReflectionRequest）。
- 输出类型：`ReflectionResult`；具体返回路径见流程步骤。

**处理流程**：函数体无可展开的语句级步骤；可能是协议定义、空实现或简单表达式，请结合源码。

**调用与被调用**：
- 无显式函数调用，或仅声明协议/常量。
- 静态扫描未定位直接调用方；可能通过路由注册、LangGraph 节点、协议方法或依赖注入动态调用，不据此判断为死代码。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：未见 `raise`；下游异常可能继续上抛。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。


---
