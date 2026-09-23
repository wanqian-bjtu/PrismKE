源码：[mock.py:1](../../../src/providers/mock.py#L1) | 基准：`dev/v0.10@f2f34d7` | 本文件符号数：6

**模块职责**：Deterministic providers for tests and offline demonstrations.
**在系统中的位置**：LLM、OCR、VLM、Embedding、Reflection 与语义建议的外部能力接口和实现。
**直接依赖**：[src.core.ids](../core/ids.md)、[src.domain](../domain/__init__.md)、[src.providers.common](common.md)；外部/标准库：无。
**主要调用方（静态导入）**：[providers/__init__.py](__init__.md)、[workflow/review_workspace.py](../workflow/review_workspace.md)。
**阅读提示**：下列流程根据当前源码控制流整理；`self`/接口对象的实际类型可能在运行时注入，未能静态解析的调用会明确标注。链接指向源码行或对应讲解文件。

---

# MockLLMProvider ⭐⭐⭐

**位置与等级**：[mock.py:8](../../../src/providers/mock.py#L8)；关键支撑逻辑，影响候选、证据或接口的正确传递。

**职责**：外部能力实现或协议；调用是否耗费模型额度取决于具体实现。基类：无显式基类。
**源码说明**：Parse pipe-delimited facts embedded in documents.

**字段与类级约束**：
- 类体未直接声明字段；实例状态请看 `__init__` 及方法中的赋值。

**内部成员**：`MockLLMProvider.fingerprint`、`MockLLMProvider.extract`


---

# MockLLMProvider.fingerprint ⭐⭐⭐

**位置与等级**：[mock.py:11](../../../src/providers/mock.py#L11)；关键支撑逻辑，影响候选、证据或接口的正确传递。

**签名**：`def fingerprint(self) -> str`。

**作用**：处理 `fingerprint` 对应步骤；下列步骤依据函数体的实际控制流和调用点整理。

**输入与输出**：
- 输入：无业务参数（或仅隐式接收实例）。
- 输出类型：`str`；具体返回路径见流程步骤。

**处理流程**：
1. 返回 `stable_id('provider', 'mock', 'v1')`。

**调用与被调用**：
- `stable_id`（调用点 [mock.py:12](../../../src/providers/mock.py#L12)）→ [stable_id](../core/ids.md)，静态可定位。
- 静态扫描未定位直接调用方；可能通过路由注册、LangGraph 节点、协议方法或依赖注入动态调用，不据此判断为死代码。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：未见 `raise`；下游异常可能继续上抛。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。


---

# MockLLMProvider.extract ⭐⭐⭐⭐

**位置与等级**：[mock.py:14](../../../src/providers/mock.py#L14)；承担主要 Agent、应用服务或审核/执行入口，跨模块影响显著。

**签名**：`async def extract(self, request: ExtractionRequest) -> ExtractionResult`。

**作用**：处理 `extract` 对应步骤；下列步骤依据函数体的实际控制流和调用点整理。

**输入与输出**：
- 输入：`request`（ExtractionRequest）。
- 输出类型：`ExtractionResult`；具体返回路径见流程步骤。

**处理流程**：
1. 更新 `candidates`，值来自 `[]`。
2. 更新 `warnings`，值来自 `[]`。
3. 遍历 `request.document.text_blocks`，逐项处理 `block`。
4. 返回 `ExtractionResult(candidates=candidates, warnings=warnings)`。

**关键条件与保护**：
- [mock.py:19](../../../src/providers/mock.py#L19)：`len(parts) != 6`，不满足时跳过本分支。

**调用与被调用**：
- `part.strip`（[mock.py:18](../../../src/providers/mock.py#L18)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `block.text.split`（[mock.py:18](../../../src/providers/mock.py#L18)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `len`（[mock.py:19](../../../src/providers/mock.py#L19)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `float`（[mock.py:29](../../../src/providers/mock.py#L29)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `candidates.append`（[mock.py:31](../../../src/providers/mock.py#L31)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `candidate_from_payload`（调用点 [mock.py:31](../../../src/providers/mock.py#L31)）→ [candidate_from_payload](common.md)，静态可定位。
- `warnings.append`（[mock.py:33](../../../src/providers/mock.py#L33)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `ExtractionResult`（[mock.py:34](../../../src/providers/mock.py#L34)）：来自 `src.domain.ExtractionResult`；具体实现可能由依赖注入或运行时分派决定。
- 静态扫描未定位直接调用方；可能通过路由注册、LangGraph 节点、协议方法或依赖注入动态调用，不据此判断为死代码。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：未见 `raise`；下游异常可能继续上抛。
- 本地捕获：`(ValueError, KeyError)`。


---

# MockVLMProvider ⭐⭐⭐

**位置与等级**：[mock.py:37](../../../src/providers/mock.py#L37)；关键支撑逻辑，影响候选、证据或接口的正确传递。

**职责**：外部能力实现或协议；调用是否耗费模型额度取决于具体实现。基类：无显式基类。

**字段与类级约束**：
- 类体未直接声明字段；实例状态请看 `__init__` 及方法中的赋值。

**内部成员**：`MockVLMProvider.fingerprint`、`MockVLMProvider.extract`


---

# MockVLMProvider.fingerprint ⭐⭐⭐

**位置与等级**：[mock.py:38](../../../src/providers/mock.py#L38)；关键支撑逻辑，影响候选、证据或接口的正确传递。

**签名**：`def fingerprint(self) -> str`。

**作用**：处理 `fingerprint` 对应步骤；下列步骤依据函数体的实际控制流和调用点整理。

**输入与输出**：
- 输入：无业务参数（或仅隐式接收实例）。
- 输出类型：`str`；具体返回路径见流程步骤。

**处理流程**：
1. 返回 `stable_id('provider', 'mock-vlm', 'v1')`。

**调用与被调用**：
- `stable_id`（调用点 [mock.py:39](../../../src/providers/mock.py#L39)）→ [stable_id](../core/ids.md)，静态可定位。
- 静态扫描未定位直接调用方；可能通过路由注册、LangGraph 节点、协议方法或依赖注入动态调用，不据此判断为死代码。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：未见 `raise`；下游异常可能继续上抛。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。


---

# MockVLMProvider.extract ⭐⭐⭐⭐

**位置与等级**：[mock.py:41](../../../src/providers/mock.py#L41)；承担主要 Agent、应用服务或审核/执行入口，跨模块影响显著。

**签名**：`async def extract(self, request: VisualExtractionRequest) -> ExtractionResult`。

**作用**：处理 `extract` 对应步骤；下列步骤依据函数体的实际控制流和调用点整理。

**输入与输出**：
- 输入：`request`（VisualExtractionRequest）。
- 输出类型：`ExtractionResult`；具体返回路径见流程步骤。

**处理流程**：
1. 返回 `ExtractionResult(warnings=['mock_vlm_returned_no_visual_claims'])`。

**调用与被调用**：
- `ExtractionResult`（[mock.py:43](../../../src/providers/mock.py#L43)）：来自 `src.domain.ExtractionResult`；具体实现可能由依赖注入或运行时分派决定。
- 静态扫描未定位直接调用方；可能通过路由注册、LangGraph 节点、协议方法或依赖注入动态调用，不据此判断为死代码。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：未见 `raise`；下游异常可能继续上抛。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。


---
