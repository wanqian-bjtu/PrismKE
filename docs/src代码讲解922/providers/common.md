源码：[common.py:1](../../../src/providers/common.py#L1) | 基准：`dev/v0.10@f2f34d7` | 本文件符号数：3

**模块职责**：Shared conversion from provider payloads to domain claims.
**在系统中的位置**：LLM、OCR、VLM、Embedding、Reflection 与语义建议的外部能力接口和实现。
**直接依赖**：[src.core.ids](../core/ids.md)、[src.domain](../domain/__init__.md)；外部/标准库：`__future__`、`json`、`typing`。
**主要调用方（静态导入）**：[providers/mock.py](mock.md)、[providers/openai_compatible.py](openai_compatible.md)、[providers/reflection.py](reflection.md)、[providers/semantic.py](semantic.md)、[providers/vlm.py](vlm.md)。
**阅读提示**：下列流程根据当前源码控制流整理；`self`/接口对象的实际类型可能在运行时注入，未能静态解析的调用会明确标注。链接指向源码行或对应讲解文件。

---

# parse_json_object ⭐⭐⭐

**位置与等级**：[common.py:19](../../../src/providers/common.py#L19)；关键支撑逻辑，影响候选、证据或接口的正确传递。

**签名**：`def parse_json_object(content: str) -> dict[str, Any]`。

**作用**：处理 `parse_json_object` 对应步骤；下列步骤依据函数体的实际控制流和调用点整理。

**输入与输出**：
- 输入：`content`（str）。
- 输出类型：`dict[str, Any]`；具体返回路径见流程步骤。

**处理流程**：
1. 检查 `not isinstance(content, str)`；按条件分流，else 分支不存在。
2. 更新 `text`，值来自 `content.strip()`。
3. 检查 `text.startswith(<字符串常量>) and text.endswith(<字符串常量>)`；按条件分流，else 分支不存在。
4. 更新 `payload`，值来自 `json.loads(text)`。
5. 检查 `not isinstance(payload, dict)`；按条件分流，else 分支不存在。
6. 返回 `payload`。

**关键条件与保护**：
- [common.py:20](../../../src/providers/common.py#L20)：`not isinstance(content, str)`，不满足时跳过本分支。
- [common.py:23](../../../src/providers/common.py#L23)：`text.startswith(<字符串常量>) and text.endswith(<字符串常量>)`，不满足时跳过本分支。
- [common.py:25](../../../src/providers/common.py#L25)：`opening.strip().casefold() in {<字符串常量>, <字符串常量>}`，不满足时跳过本分支。
- [common.py:28](../../../src/providers/common.py#L28)：`not isinstance(payload, dict)`，不满足时跳过本分支。

**调用与被调用**：
- `isinstance`（[common.py:20](../../../src/providers/common.py#L20)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `TypeError`（[common.py:21](../../../src/providers/common.py#L21)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `content.strip`（[common.py:22](../../../src/providers/common.py#L22)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `text.startswith`（[common.py:23](../../../src/providers/common.py#L23)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `text.endswith`（[common.py:23](../../../src/providers/common.py#L23)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `text.partition`（[common.py:24](../../../src/providers/common.py#L24)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `opening.strip().casefold`（[common.py:25](../../../src/providers/common.py#L25)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `opening.strip`（[common.py:25](../../../src/providers/common.py#L25)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `remainder[:-3].strip`（[common.py:26](../../../src/providers/common.py#L26)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `json.loads`（[common.py:27](../../../src/providers/common.py#L27)）：来自 `json`；具体实现可能由依赖注入或运行时分派决定。
- `json.JSONDecodeError`（[common.py:29](../../../src/providers/common.py#L29)）：来自 `json`；具体实现可能由依赖注入或运行时分派决定。
- 静态可定位的调用方：[OpenAICompatibleLLMProvider.extract](openai_compatible.md)、[OpenAICompatibleReflectionProvider.reflect](reflection.md)、[OpenAICompatibleSemanticAdvisor._ask](semantic.md)、[OpenAICompatibleVLMProvider.extract](vlm.md)。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：`TypeError(<字符串常量>)`、`json.JSONDecodeError(<字符串常量>, text, 0)`。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。


---

# _source_surface_name ⭐⭐

**位置与等级**：[common.py:33](../../../src/providers/common.py#L33)；局部辅助逻辑，需理解其调用条件与失败传播。

**签名**：`def _source_surface_name(value: str, entity_type: str, context: str, output_schema: OutputSchema | None) -> str`。

**作用**：内部辅助步骤；将参数转换为本模块所需的中间对象或操作结果。

**输入与输出**：
- 输入：`value`（str）；`entity_type`（str）；`context`（str）；`output_schema`（OutputSchema | None）。
- 输出类型：`str`；具体返回路径见流程步骤。

**处理流程**：
1. 检查 `output_schema is None or not context`；按条件分流，else 分支不存在。
2. 更新 `normalized_context`，值来自 `normalize_label(context)`。
3. 更新 `normalized_value`，值来自 `normalize_label(value)`。
4. 检查 `not normalized_value.startswith('entity:') and normalized_value in normalized_context`；按条件分流，else 分支不存在。
5. 更新 `canonical_type`，值来自 `SchemaIndex(output_schema).entity_type(entity_type) or entity_type`。
6. 更新 `matches`，值来自 `{}`。
7. 遍历 `output_schema.entity_catalog`，逐项处理 `entity`。
8. 检查 `len(matches) != 1`；按条件分流，else 分支不存在。
9. 返回 `max(next(iter(matches.values())), key=len)`。

**关键条件与保护**：
- [common.py:39](../../../src/providers/common.py#L39)：`output_schema is None or not context`，不满足时跳过本分支。
- [common.py:43](../../../src/providers/common.py#L43)：`not normalized_value.startswith('entity:') and normalized_value in normalized_context`，不满足时跳过本分支。
- [common.py:49](../../../src/providers/common.py#L49)：`entity.type != canonical_type`，不满足时跳过本分支。
- [common.py:52](../../../src/providers/common.py#L52)：`normalize_label(surface) in normalized_context`，不满足时跳过本分支。
- [common.py:54](../../../src/providers/common.py#L54)：`len(matches) != 1`，不满足时跳过本分支。

**调用与被调用**：
- `normalize_label`（[common.py:41](../../../src/providers/common.py#L41)）：来自 `src.domain.normalize_label`；具体实现可能由依赖注入或运行时分派决定。
- `normalized_value.startswith`（[common.py:43](../../../src/providers/common.py#L43)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `SchemaIndex(output_schema).entity_type`（[common.py:46](../../../src/providers/common.py#L46)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `SchemaIndex`（[common.py:46](../../../src/providers/common.py#L46)）：来自 `src.domain.SchemaIndex`；具体实现可能由依赖注入或运行时分派决定。
- `matches.setdefault(entity.id, []).append`（[common.py:53](../../../src/providers/common.py#L53)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `matches.setdefault`（[common.py:53](../../../src/providers/common.py#L53)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `len`（[common.py:54](../../../src/providers/common.py#L54)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `max`（[common.py:56](../../../src/providers/common.py#L56)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `next`（[common.py:56](../../../src/providers/common.py#L56)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `iter`（[common.py:56](../../../src/providers/common.py#L56)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `matches.values`（[common.py:56](../../../src/providers/common.py#L56)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- 静态可定位的调用方：[candidate_from_payload](common.md)。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：未见 `raise`；下游异常可能继续上抛。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。


---

# candidate_from_payload ⭐⭐⭐

**位置与等级**：[common.py:59](../../../src/providers/common.py#L59)；关键支撑逻辑，影响候选、证据或接口的正确传递。

**签名**：`def candidate_from_payload(item: dict[str, Any], evidence_id: str, context: str, *, modality: Modality=Modality.TEXT, source_tool: str='text_extraction', visual_observation_ids: list[str] | None=None, output_schema: OutputSchema | None=None) -> CandidateClaim`。

**作用**：处理 `candidate_from_payload` 对应步骤；下列步骤依据函数体的实际控制流和调用点整理。

**输入与输出**：
- 输入：`item`（dict[str, Any]）；`evidence_id`（str）；`context`（str）；`modality`（Modality；默认 `Modality.TEXT`）；`source_tool`（str；默认 `'text_extraction'`）；`visual_observation_ids`（list[str] | None；默认 `None`）；`output_schema`（OutputSchema | None；默认 `None`）。
- 输出类型：`CandidateClaim`；具体返回路径见流程步骤。

**处理流程**：
1. 更新 `subject_name`，值来自 `str(item['subject']).strip()`。
2. 更新 `object_name`，值来自 `str(item['object']).strip()`。
3. 更新 `subject_type`，值来自 `str(item.get('subject_type', 'Unknown')).strip()`。
4. 更新 `object_type`，值来自 `item.get('object_type')`。
5. 更新 `subject_name`，值来自 `_source_surface_name(subject_name, subject_type, context, output_schema)`。
6. 检查 `object_type`；按条件分流，else 分支不存在。
7. 更新 `subject`，值来自 `EntityMention(id=stable_id('mention', subject_name, subject_type, evidence_id), name=subject_name, …`。
8. 检查 `object_type`；按条件分流，else 分支存在。
9. 更新 `relation`，值来自 `str(item['relation']).strip()`。
10. 返回 `CandidateClaim(id=stable_id('candidate', subject.id, relation, object_name, evidence_id), subject=subjec…`。

**关键条件与保护**：
- [common.py:74](../../../src/providers/common.py#L74)：`object_type`，不满足时跳过本分支。
- [common.py:84](../../../src/providers/common.py#L84)：`object_type`，不满足时有 else 分支。

**调用与被调用**：
- `str(item['subject']).strip`（[common.py:69](../../../src/providers/common.py#L69)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `str`（[common.py:69](../../../src/providers/common.py#L69)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `str(item['object']).strip`（[common.py:70](../../../src/providers/common.py#L70)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `str(item.get('subject_type', 'Unknown')).strip`（[common.py:71](../../../src/providers/common.py#L71)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `item.get`（[common.py:71](../../../src/providers/common.py#L71)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `_source_surface_name`（调用点 [common.py:73](../../../src/providers/common.py#L73)）→ [_source_surface_name](common.md)，静态可定位。
- `EntityMention`（[common.py:76](../../../src/providers/common.py#L76)）：来自 `src.domain.EntityMention`；具体实现可能由依赖注入或运行时分派决定。
- `stable_id`（调用点 [common.py:77](../../../src/providers/common.py#L77)）→ [stable_id](../core/ids.md)，静态可定位。
- `str(item['relation']).strip`（[common.py:95](../../../src/providers/common.py#L95)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `CandidateClaim`（[common.py:96](../../../src/providers/common.py#L96)）：来自 `src.domain.CandidateClaim`；具体实现可能由依赖注入或运行时分派决定。
- `float`（[common.py:101](../../../src/providers/common.py#L101)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `dict`（[common.py:103](../../../src/providers/common.py#L103)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- 静态可定位的调用方：[MockLLMProvider.extract](mock.md)、[OpenAICompatibleLLMProvider.extract](openai_compatible.md)、[OpenAICompatibleVLMProvider.extract](vlm.md)。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：未见 `raise`；下游异常可能继续上抛。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。


---
