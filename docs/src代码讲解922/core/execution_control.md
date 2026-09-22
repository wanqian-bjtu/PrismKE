源码：[execution_control.py:1](../../../src/core/execution_control.py#L1) | 基准：`dev/v0.10@f2f34d7` | 本文件符号数：12

**模块职责**：Cooperative control propagates into LangGraph branches and native OCR threads.
**在系统中的位置**：全局设置、稳定标识、执行控制与错误类型；为其他层提供通用约束。
**直接依赖**：无显式项目内模块导入；外部/标准库：`collections`、`contextvars`、`pydantic`、`typing`。
**主要调用方（静态导入）**：[agents/multimodal_extraction_agent.py](../agents/multimodal_extraction_agent.md)、[providers/http_client.py](../providers/http_client.md)、[providers/ocr.py](../providers/ocr.md)、[workflow/execution.py](../workflow/execution.md)、[workflow/graph.py](../workflow/graph.md)、[workflow/nodes.py](../workflow/nodes.md)、[workflow/reviews.py](../workflow/reviews.md)。
**阅读提示**：下列流程根据当前源码控制流整理；`self`/接口对象的实际类型可能在运行时注入，未能静态解析的调用会明确标注。链接指向源码行或对应讲解文件。

---

# ExecutionPaused ⭐⭐⭐

**位置与等级**：[execution_control.py:10](../../../src/core/execution_control.py#L10)；关键支撑逻辑，影响候选、证据或接口的正确传递。

**职责**：本模块的对象实现或数据契约；具体语义由字段、基类和方法共同决定。基类：`Exception`。
**源码说明**：A control boundary, not a failed extraction or a retry.

**字段与类级约束**：
- 类体未直接声明字段；实例状态请看 `__init__` 及方法中的赋值。

**内部成员**：此类未直接定义方法；字段/继承行为见源码。


---

# ExecutionControl ⭐⭐⭐

**位置与等级**：[execution_control.py:14](../../../src/core/execution_control.py#L14)；关键支撑逻辑，影响候选、证据或接口的正确传递。

**职责**：本模块的对象实现或数据契约；具体语义由字段、基类和方法共同决定。基类：`Protocol`。

**字段与类级约束**：
- 类体未直接声明字段；实例状态请看 `__init__` 及方法中的赋值。

**内部成员**：`ExecutionControl.check`、`ExecutionControl.node`、`ExecutionControl.commit_started`、`ExecutionControl.commit_finished`、`ExecutionControl.begin_request`、`ExecutionControl.finish_request`、`ExecutionControl.result`、`ExecutionControl.put_result`


---

# ExecutionControl.check ⭐⭐

**位置与等级**：[execution_control.py:15](../../../src/core/execution_control.py#L15)；局部辅助逻辑，需理解其调用条件与失败传播。

**签名**：`def check(self) -> None`。

**作用**：处理 `check` 对应步骤；下列步骤依据函数体的实际控制流和调用点整理。

**输入与输出**：
- 输入：无业务参数（或仅隐式接收实例）。
- 输出类型：`None`；具体返回路径见流程步骤。

**处理流程**：函数体无可展开的语句级步骤；可能是协议定义、空实现或简单表达式，请结合源码。

**调用与被调用**：
- 无显式函数调用，或仅声明协议/常量。
- 静态扫描未定位直接调用方；可能通过路由注册、LangGraph 节点、协议方法或依赖注入动态调用，不据此判断为死代码。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：未见 `raise`；下游异常可能继续上抛。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。


---

# ExecutionControl.node ⭐⭐

**位置与等级**：[execution_control.py:16](../../../src/core/execution_control.py#L16)；局部辅助逻辑，需理解其调用条件与失败传播。

**签名**：`def node(self, name: str) -> None`。

**作用**：处理 `node` 对应步骤；下列步骤依据函数体的实际控制流和调用点整理。

**输入与输出**：
- 输入：`name`（str）。
- 输出类型：`None`；具体返回路径见流程步骤。

**处理流程**：函数体无可展开的语句级步骤；可能是协议定义、空实现或简单表达式，请结合源码。

**调用与被调用**：
- 无显式函数调用，或仅声明协议/常量。
- 静态扫描未定位直接调用方；可能通过路由注册、LangGraph 节点、协议方法或依赖注入动态调用，不据此判断为死代码。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：未见 `raise`；下游异常可能继续上抛。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。


---

# ExecutionControl.commit_started ⭐⭐

**位置与等级**：[execution_control.py:17](../../../src/core/execution_control.py#L17)；局部辅助逻辑，需理解其调用条件与失败传播。

**签名**：`def commit_started(self, revision_id: str) -> None`。

**作用**：处理 `commit_started` 对应步骤；下列步骤依据函数体的实际控制流和调用点整理。

**输入与输出**：
- 输入：`revision_id`（str）。
- 输出类型：`None`；具体返回路径见流程步骤。

**处理流程**：函数体无可展开的语句级步骤；可能是协议定义、空实现或简单表达式，请结合源码。

**调用与被调用**：
- 无显式函数调用，或仅声明协议/常量。
- 静态扫描未定位直接调用方；可能通过路由注册、LangGraph 节点、协议方法或依赖注入动态调用，不据此判断为死代码。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：未见 `raise`；下游异常可能继续上抛。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。


---

# ExecutionControl.commit_finished ⭐⭐

**位置与等级**：[execution_control.py:18](../../../src/core/execution_control.py#L18)；局部辅助逻辑，需理解其调用条件与失败传播。

**签名**：`def commit_finished(self) -> None`。

**作用**：处理 `commit_finished` 对应步骤；下列步骤依据函数体的实际控制流和调用点整理。

**输入与输出**：
- 输入：无业务参数（或仅隐式接收实例）。
- 输出类型：`None`；具体返回路径见流程步骤。

**处理流程**：函数体无可展开的语句级步骤；可能是协议定义、空实现或简单表达式，请结合源码。

**调用与被调用**：
- 无显式函数调用，或仅声明协议/常量。
- 静态扫描未定位直接调用方；可能通过路由注册、LangGraph 节点、协议方法或依赖注入动态调用，不据此判断为死代码。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：未见 `raise`；下游异常可能继续上抛。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。


---

# ExecutionControl.begin_request ⭐⭐

**位置与等级**：[execution_control.py:19](../../../src/core/execution_control.py#L19)；局部辅助逻辑，需理解其调用条件与失败传播。

**签名**：`def begin_request(self, key: str, metadata: dict[str, Any]) -> dict[str, Any] | None`。

**作用**：处理 `begin_request` 对应步骤；下列步骤依据函数体的实际控制流和调用点整理。

**输入与输出**：
- 输入：`key`（str）；`metadata`（dict[str, Any]）。
- 输出类型：`dict[str, Any] | None`；具体返回路径见流程步骤。

**处理流程**：函数体无可展开的语句级步骤；可能是协议定义、空实现或简单表达式，请结合源码。

**调用与被调用**：
- 无显式函数调用，或仅声明协议/常量。
- 静态扫描未定位直接调用方；可能通过路由注册、LangGraph 节点、协议方法或依赖注入动态调用，不据此判断为死代码。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：未见 `raise`；下游异常可能继续上抛。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。


---

# ExecutionControl.finish_request ⭐⭐

**位置与等级**：[execution_control.py:20](../../../src/core/execution_control.py#L20)；局部辅助逻辑，需理解其调用条件与失败传播。

**签名**：`def finish_request(self, key: str, status: str, payload: dict[str, Any] | None, usage_known: bool) -> None`。

**作用**：处理 `finish_request` 对应步骤；下列步骤依据函数体的实际控制流和调用点整理。

**输入与输出**：
- 输入：`key`（str）；`status`（str）；`payload`（dict[str, Any] | None）；`usage_known`（bool）。
- 输出类型：`None`；具体返回路径见流程步骤。

**处理流程**：函数体无可展开的语句级步骤；可能是协议定义、空实现或简单表达式，请结合源码。

**调用与被调用**：
- 无显式函数调用，或仅声明协议/常量。
- 静态扫描未定位直接调用方；可能通过路由注册、LangGraph 节点、协议方法或依赖注入动态调用，不据此判断为死代码。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：未见 `raise`；下游异常可能继续上抛。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。


---

# ExecutionControl.result ⭐⭐

**位置与等级**：[execution_control.py:23](../../../src/core/execution_control.py#L23)；局部辅助逻辑，需理解其调用条件与失败传播。

**签名**：`def result(self, key: str) -> dict[str, Any] | None`。

**作用**：处理 `result` 对应步骤；下列步骤依据函数体的实际控制流和调用点整理。

**输入与输出**：
- 输入：`key`（str）。
- 输出类型：`dict[str, Any] | None`；具体返回路径见流程步骤。

**处理流程**：函数体无可展开的语句级步骤；可能是协议定义、空实现或简单表达式，请结合源码。

**调用与被调用**：
- 无显式函数调用，或仅声明协议/常量。
- 静态扫描未定位直接调用方；可能通过路由注册、LangGraph 节点、协议方法或依赖注入动态调用，不据此判断为死代码。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：未见 `raise`；下游异常可能继续上抛。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。


---

# ExecutionControl.put_result ⭐⭐

**位置与等级**：[execution_control.py:24](../../../src/core/execution_control.py#L24)；局部辅助逻辑，需理解其调用条件与失败传播。

**签名**：`def put_result(self, key: str, value: dict[str, Any]) -> None`。

**作用**：处理 `put_result` 对应步骤；下列步骤依据函数体的实际控制流和调用点整理。

**输入与输出**：
- 输入：`key`（str）；`value`（dict[str, Any]）。
- 输出类型：`None`；具体返回路径见流程步骤。

**处理流程**：函数体无可展开的语句级步骤；可能是协议定义、空实现或简单表达式，请结合源码。

**调用与被调用**：
- 无显式函数调用，或仅声明协议/常量。
- 静态扫描未定位直接调用方；可能通过路由注册、LangGraph 节点、协议方法或依赖注入动态调用，不据此判断为死代码。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：未见 `raise`；下游异常可能继续上抛。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。


---

# check_execution ⭐⭐

**位置与等级**：[execution_control.py:31](../../../src/core/execution_control.py#L31)；局部辅助逻辑，需理解其调用条件与失败传播。

**签名**：`def check_execution() -> None`。

**作用**：处理 `check_execution` 对应步骤；下列步骤依据函数体的实际控制流和调用点整理。

**输入与输出**：
- 输入：无业务参数（或仅隐式接收实例）。
- 输出类型：`None`；具体返回路径见流程步骤。

**处理流程**：
1. 更新 `control`，值来自 `current_execution.get()`。
2. 检查 `control`；按条件分流，else 分支不存在。

**关键条件与保护**：
- [execution_control.py:33](../../../src/core/execution_control.py#L33)：`control`，不满足时跳过本分支。

**调用与被调用**：
- `current_execution.get`（[execution_control.py:32](../../../src/core/execution_control.py#L32)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `control.check`（[execution_control.py:34](../../../src/core/execution_control.py#L34)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- 静态可定位的调用方：[MultimodalExtractionAgent.extract_visual](../agents/multimodal_extraction_agent.md)、[PaddleOCRProvider._recognize_sync](../providers/ocr.md)。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：未见 `raise`；下游异常可能继续上抛。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。


---

# cached_operation ⭐⭐

**位置与等级**：[execution_control.py:37](../../../src/core/execution_control.py#L37)；局部辅助逻辑，需理解其调用条件与失败传播。

**签名**：`async def cached_operation(key: str, model: type[Model], call: Callable[[], Awaitable[Model]]) -> Model`。

**作用**：处理 `cached_operation` 对应步骤；下列步骤依据函数体的实际控制流和调用点整理。

**输入与输出**：
- 输入：`key`（str）；`model`（type[Model]）；`call`（Callable[[], Awaitable[Model]]）。
- 输出类型：`Model`；具体返回路径见流程步骤。

**处理流程**：
1. 更新 `control`，值来自 `current_execution.get()`。
2. 检查 `not control`；按条件分流，else 分支不存在。
3. 调用 `control.check`，结果未直接赋值。
4. 更新 `old`，值来自 `control.result(key)`。
5. 检查 `old is not None`；按条件分流，else 分支不存在。
6. 更新 `value`，值来自 `await call()`。
7. 调用 `control.put_result`，结果未直接赋值。
8. 返回 `value`。

**关键条件与保护**：
- [execution_control.py:41](../../../src/core/execution_control.py#L41)：`not control`，不满足时跳过本分支。
- [execution_control.py:45](../../../src/core/execution_control.py#L45)：`old is not None`，不满足时跳过本分支。

**调用与被调用**：
- `current_execution.get`（[execution_control.py:40](../../../src/core/execution_control.py#L40)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `call`（[execution_control.py:42](../../../src/core/execution_control.py#L42)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `control.check`（[execution_control.py:43](../../../src/core/execution_control.py#L43)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `control.result`（[execution_control.py:44](../../../src/core/execution_control.py#L44)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `model.model_validate`（[execution_control.py:46](../../../src/core/execution_control.py#L46)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `control.put_result`（[execution_control.py:48](../../../src/core/execution_control.py#L48)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `value.model_dump`（[execution_control.py:48](../../../src/core/execution_control.py#L48)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- 静态可定位的调用方：[MultimodalExtractionAgent.recognize](../agents/multimodal_extraction_agent.md)、[MultimodalExtractionAgent.extract_text](../agents/multimodal_extraction_agent.md)、[MultimodalExtractionAgent.extract_visual](../agents/multimodal_extraction_agent.md)。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：未见 `raise`；下游异常可能继续上抛。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。


---
