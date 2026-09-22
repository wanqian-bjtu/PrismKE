源码：[validation.py:1](../../../src/providers/validation.py#L1) | 基准：`dev/v0.10@f2f34d7` | 本文件符号数：2

**模块职责**：Per-item structure quarantine without storing raw model responses.
**在系统中的位置**：LLM、OCR、VLM、Embedding、Reflection 与语义建议的外部能力接口和实现。
**直接依赖**：[src.core.ids](../core/ids.md)、[src.domain](../domain/__init__.md)、[src.governance.validation](../governance/validation/__init__.md)；外部/标准库：`__future__`、`math`、`typing`。
**主要调用方（静态导入）**：[providers/openai_compatible.py](openai_compatible.md)、[providers/vlm.py](vlm.md)。
**阅读提示**：下列流程根据当前源码控制流整理；`self`/接口对象的实际类型可能在运行时注入，未能静态解析的调用会明确标注。链接指向源码行或对应讲解文件。

---

# summarize ⭐⭐⭐

**位置与等级**：[validation.py:23](../../../src/providers/validation.py#L23)；关键支撑逻辑，影响候选、证据或接口的正确传递。

**签名**：`def summarize(item: Any) -> dict[str, Any]`。

**作用**：处理 `summarize` 对应步骤；下列步骤依据函数体的实际控制流和调用点整理。

**输入与输出**：
- 输入：`item`（Any）。
- 输出类型：`dict[str, Any]`；具体返回路径见流程步骤。

**处理流程**：
1. 检查 `not isinstance(item, dict)`；按条件分流，else 分支不存在。
2. 返回 `{k: v[:200] if isinstance(v, str) else v for k in FIELDS if isinstance((v := item.get(k)), (str, int, fl…`。

**关键条件与保护**：
- [validation.py:24](../../../src/providers/validation.py#L24)：`not isinstance(item, dict)`，不满足时跳过本分支。

**调用与被调用**：
- `isinstance`（[validation.py:24](../../../src/providers/validation.py#L24)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `type`（[validation.py:25](../../../src/providers/validation.py#L25)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `item.get`（[validation.py:29](../../../src/providers/validation.py#L29)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `v.startswith`（[validation.py:30](../../../src/providers/validation.py#L30)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `math.isfinite`（[validation.py:31](../../../src/providers/validation.py#L31)）：来自 `math`；具体实现可能由依赖注入或运行时分派决定。
- 静态可定位的调用方：[OpenAICompatibleLLMProvider.extract](openai_compatible.md)、[validate_item](validation.md)、[OpenAICompatibleVLMProvider.extract](vlm.md)。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：未见 `raise`；下游异常可能继续上抛。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。


---

# validate_item ⭐⭐⭐⭐

**位置与等级**：[validation.py:35](../../../src/providers/validation.py#L35)；承担主要 Agent、应用服务或审核/执行入口，跨模块影响显著。

**签名**：`def validate_item(item: Any, operation_id: str, index: int, target_type: Any='candidate') -> ValidationIssue | None`。

**作用**：处理 `validate_item` 对应步骤；下列步骤依据函数体的实际控制流和调用点整理。

**输入与输出**：
- 输入：`item`（Any）；`operation_id`（str）；`index`（int）；`target_type`（Any；默认 `'candidate'`）。
- 输出类型：`ValidationIssue | None`；具体返回路径见流程步骤。

**处理流程**：
1. 更新 `field`，值来自 `''`。
2. 检查 `not isinstance(item, dict)`；按条件分流，else 分支存在。
3. 检查 `not field`；按条件分流，else 分支不存在。
4. 返回 `ValidationService.issue('INVALID_CANDIDATE_STRUCTURE', 'structure', target_type, stable_id('invalid-cand…`。

**关键条件与保护**：
- [validation.py:39](../../../src/providers/validation.py#L39)：`not isinstance(item, dict)`，不满足时有 else 分支。
- [validation.py:43](../../../src/providers/validation.py#L43)：`not isinstance(item.get(key), str) or not item[key].strip()`，不满足时跳过本分支。
- [validation.py:47](../../../src/providers/validation.py#L47)：`isinstance(confidence, bool) or not isinstance(confidence, (int, float)) or (not math.isfinite(confidence)) or (no…`，不满足时跳过本分支。
- [validation.py:54](../../../src/providers/validation.py#L54)：`'qualifiers' in item and (not isinstance(item['qualifiers'], dict))`，不满足时跳过本分支。
- [validation.py:56](../../../src/providers/validation.py#L56)：`item.get('object_type') is not None and (not isinstance(item['object_type'], str) or not item['object_type'].strip…`，不满足时跳过本分支。
- [validation.py:60](../../../src/providers/validation.py#L60)：`'evidence_id' in item and (not isinstance(item['evidence_id'], str) or not item['evidence_id'].strip())`，不满足时跳过本分支。
- [validation.py:64](../../../src/providers/validation.py#L64)：`'evidence_ids' in item and (not isinstance(item['evidence_ids'], list) or not item['evidence_ids'] or any((not isi…`，不满足时跳过本分支。
- [validation.py:70](../../../src/providers/validation.py#L70)：`not field`，不满足时跳过本分支。

**调用与被调用**：
- `isinstance`（[validation.py:39](../../../src/providers/validation.py#L39)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `item.get`（[validation.py:43](../../../src/providers/validation.py#L43)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `item[key].strip`（[validation.py:43](../../../src/providers/validation.py#L43)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `math.isfinite`（[validation.py:50](../../../src/providers/validation.py#L50)）：来自 `math`；具体实现可能由依赖注入或运行时分派决定。
- `item['object_type'].strip`（[validation.py:57](../../../src/providers/validation.py#L57)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `item['evidence_id'].strip`（[validation.py:61](../../../src/providers/validation.py#L61)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `any`（[validation.py:67](../../../src/providers/validation.py#L67)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `ValidationService.issue`（[validation.py:72](../../../src/providers/validation.py#L72)）：来自 `src.governance.validation.ValidationService`；具体实现可能由依赖注入或运行时分派决定。
- `stable_id`（调用点 [validation.py:76](../../../src/providers/validation.py#L76)）→ [stable_id](../core/ids.md)，静态可定位。
- `summarize`（调用点 [validation.py:79](../../../src/providers/validation.py#L79)）→ [summarize](validation.md)，静态可定位。
- 静态可定位的调用方：[OpenAICompatibleLLMProvider.extract](openai_compatible.md)、[OpenAICompatibleVLMProvider.extract](vlm.md)。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：未见 `raise`；下游异常可能继续上抛。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。


---
