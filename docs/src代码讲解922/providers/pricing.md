源码：[pricing.py:1](../../../src/providers/pricing.py#L1) | 基准：`dev/v0.10@f2f34d7` | 本文件符号数：1

**模块职责**：Versioned list-price estimates for provider call telemetry.
**在系统中的位置**：LLM、OCR、VLM、Embedding、Reflection 与语义建议的外部能力接口和实现。
**直接依赖**：无显式项目内模块导入；外部/标准库：`__future__`。
**主要调用方（静态导入）**：[providers/http_client.py](http_client.md)。
**阅读提示**：下列流程根据当前源码控制流整理；`self`/接口对象的实际类型可能在运行时注入，未能静态解析的调用会明确标注。链接指向源码行或对应讲解文件。

---

# estimate_cost_cny ⭐⭐⭐

**位置与等级**：[pricing.py:12](../../../src/providers/pricing.py#L12)；关键支撑逻辑，影响候选、证据或接口的正确传递。

**签名**：`def estimate_cost_cny(model: str, input_tokens: int, output_tokens: int) -> tuple[float | None, str | None]`。

**作用**：Estimate short-context list price without pretending to be a bill.

**输入与输出**：
- 输入：`model`（str）；`input_tokens`（int）；`output_tokens`（int）。
- 输出类型：`tuple[float | None, str | None]`；具体返回路径见流程步骤。

**处理流程**：
1. 更新 `rates`，值来自 `_PER_MILLION_CNY.get(model)`。
2. 检查 `rates is None or input_tokens > 32000`；按条件分流，else 分支不存在。
3. 更新 `(input_rate, output_rate)`，值来自 `rates`。
4. 更新 `cost`，值来自 `(input_tokens * input_rate + output_tokens * output_rate) / 1000000`。
5. 返回 `(round(cost, 8), PRICING_SNAPSHOT)`。

**关键条件与保护**：
- [pricing.py:18](../../../src/providers/pricing.py#L18)：`rates is None or input_tokens > 32000`，不满足时跳过本分支。

**调用与被调用**：
- `_PER_MILLION_CNY.get`（[pricing.py:17](../../../src/providers/pricing.py#L17)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `round`（[pricing.py:22](../../../src/providers/pricing.py#L22)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- 静态可定位的调用方：[_record](http_client.md)。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：未见 `raise`；下游异常可能继续上抛。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。


---
