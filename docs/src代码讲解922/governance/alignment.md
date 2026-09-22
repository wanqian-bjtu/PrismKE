源码：[alignment.py:1](../../../src/governance/alignment.py#L1) | 基准：`dev/v0.10@f2f34d7` | 本文件符号数：5

**模块职责**：Deterministic, auditable cross-modal candidate alignment.
**在系统中的位置**：实体解析、事实规范化、冲突、风险、审核及实体操作的确定性规则。
**直接依赖**：[src.core.ids](../core/ids.md)、[src.domain](../domain/__init__.md)；外部/标准库：`__future__`、`collections`。
**主要调用方（静态导入）**：[governance/__init__.py](__init__.md)。
**阅读提示**：下列流程根据当前源码控制流整理；`self`/接口对象的实际类型可能在运行时注入，未能静态解析的调用会明确标注。链接指向源码行或对应讲解文件。

---

# _object_key ⭐⭐

**位置与等级**：[alignment.py:18](../../../src/governance/alignment.py#L18)；局部辅助逻辑，需理解其调用条件与失败传播。

**签名**：`def _object_key(candidate: CandidateClaim) -> str`。

**作用**：内部辅助步骤；将参数转换为本模块所需的中间对象或操作结果。

**输入与输出**：
- 输入：`candidate`（CandidateClaim；尚未成为正式 Claim 的候选）。
- 输出类型：`str`；具体返回路径见流程步骤。

**处理流程**：
1. 更新 `value`，值来自 `candidate.object.name if isinstance(candidate.object, EntityMention) else candidate.object`。
2. 返回 `normalize_label(value)`。

**调用与被调用**：
- `isinstance`（[alignment.py:20](../../../src/governance/alignment.py#L20)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `normalize_label`（[alignment.py:22](../../../src/governance/alignment.py#L22)）：来自 `src.domain.normalize_label`；具体实现可能由依赖注入或运行时分派决定。
- 静态可定位的调用方：[_signature](alignment.md)、[MultimodalAlignmentService.align](alignment.md)。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：未见 `raise`；下游异常可能继续上抛。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。


---

# _relation_key ⭐⭐

**位置与等级**：[alignment.py:25](../../../src/governance/alignment.py#L25)；局部辅助逻辑，需理解其调用条件与失败传播。

**签名**：`def _relation_key(candidate: CandidateClaim, schema: SchemaIndex) -> str`。

**作用**：内部辅助步骤；将参数转换为本模块所需的中间对象或操作结果。

**输入与输出**：
- 输入：`candidate`（CandidateClaim；尚未成为正式 Claim 的候选）；`schema`（SchemaIndex；当前任务的 Schema 或索引，约束实体与关系）。
- 输出类型：`str`；具体返回路径见流程步骤。

**处理流程**：
1. 更新 `relation`，值来自 `schema.relation(candidate.relation)`。
2. 返回 `relation.id if relation else normalize_label(candidate.relation)`。

**调用与被调用**：
- `schema.relation`（[alignment.py:26](../../../src/governance/alignment.py#L26)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `normalize_label`（[alignment.py:27](../../../src/governance/alignment.py#L27)）：来自 `src.domain.normalize_label`；具体实现可能由依赖注入或运行时分派决定。
- 静态可定位的调用方：[_signature](alignment.md)、[MultimodalAlignmentService.align](alignment.md)。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：未见 `raise`；下游异常可能继续上抛。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。


---

# _signature ⭐⭐

**位置与等级**：[alignment.py:30](../../../src/governance/alignment.py#L30)；局部辅助逻辑，需理解其调用条件与失败传播。

**签名**：`def _signature(candidate: CandidateClaim, schema: SchemaIndex) -> tuple[str, str, str]`。

**作用**：内部辅助步骤；将参数转换为本模块所需的中间对象或操作结果。

**输入与输出**：
- 输入：`candidate`（CandidateClaim；尚未成为正式 Claim 的候选）；`schema`（SchemaIndex；当前任务的 Schema 或索引，约束实体与关系）。
- 输出类型：`tuple[str, str, str]`；具体返回路径见流程步骤。

**处理流程**：
1. 返回 `(normalize_label(candidate.subject.name), _relation_key(candidate, schema), _object_key(candidate))`。

**调用与被调用**：
- `normalize_label`（[alignment.py:32](../../../src/governance/alignment.py#L32)）：来自 `src.domain.normalize_label`；具体实现可能由依赖注入或运行时分派决定。
- `_relation_key`（调用点 [alignment.py:33](../../../src/governance/alignment.py#L33)）→ [_relation_key](alignment.md)，静态可定位。
- `_object_key`（调用点 [alignment.py:34](../../../src/governance/alignment.py#L34)）→ [_object_key](alignment.md)，静态可定位。
- 静态可定位的调用方：[MultimodalAlignmentService.align](alignment.md)。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：未见 `raise`；下游异常可能继续上抛。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。


---

# MultimodalAlignmentService ⭐⭐⭐⭐

**位置与等级**：[alignment.py:38](../../../src/governance/alignment.py#L38)；承担主要 Agent、应用服务或审核/执行入口，跨模块影响显著。

**职责**：跨步骤服务；组合依赖并暴露可复用业务入口。基类：无显式基类。

**字段与类级约束**：
- 类体未直接声明字段；实例状态请看 `__init__` 及方法中的赋值。

**内部成员**：`MultimodalAlignmentService.align`


---

# MultimodalAlignmentService.align ⭐⭐

**位置与等级**：[alignment.py:39](../../../src/governance/alignment.py#L39)；局部辅助逻辑，需理解其调用条件与失败传播。

**签名**：`def align(self, text_candidates: list[CandidateClaim], visual_candidates: list[CandidateClaim], schema: SchemaIndex) -> tuple[list[CandidateClaim], list[AlignmentRecord]]`。

**作用**：处理 `align` 对应步骤；下列步骤依据函数体的实际控制流和调用点整理。

**输入与输出**：
- 输入：`text_candidates`（list[CandidateClaim]）；`visual_candidates`（list[CandidateClaim]）；`schema`（SchemaIndex；当前任务的 Schema 或索引，约束实体与关系）。
- 输出类型：`tuple[list[CandidateClaim], list[AlignmentRecord]]`；具体返回路径见流程步骤。

**处理流程**：
1. 更新 `all_candidates`，值来自 `[*text_candidates, *visual_candidates]`。
2. 更新 `groups`，值来自 `defaultdict(list)`。
3. 遍历 `all_candidates`，逐项处理 `candidate`。
4. 更新 `aligned`，值来自 `[]`。
5. 更新 `records`，值来自 `[]`。
6. 遍历 `groups.items()`，逐项处理 `(signature, members)`。
7. 更新 `by_subject_relation`，值来自 `defaultdict(list)`。
8. 遍历 `all_candidates`，逐项处理 `candidate`。
9. 遍历 `by_subject_relation.values()`，逐项处理 `members`。
10. 遍历 `text_candidates`，逐项处理 `text_candidate`。
11. 返回 `(aligned, records)`。

**关键条件与保护**：
- [alignment.py:54](../../../src/governance/alignment.py#L54)：`len(members) == 1`，不满足时跳过本分支。
- [alignment.py:107](../../../src/governance/alignment.py#L107)：`len(objects) > 1 and Modality.IMAGE in modality_set and {Modality.TEXT, Modality.OCR} & modality_set`，不满足时跳过本分支。
- [alignment.py:124](../../../src/governance/alignment.py#L124)：`normalize_label(text_candidate.subject.name) != normalize_label(visual_candidate.subject.name)`，不满足时跳过本分支。
- [alignment.py:128](../../../src/governance/alignment.py#L128)：`_relation_key(text_candidate, schema) == _relation_key(visual_candidate, schema)`，不满足时跳过本分支。

**调用与被调用**：
- `defaultdict`（[alignment.py:46](../../../src/governance/alignment.py#L46)）：来自 `collections.defaultdict`；具体实现可能由依赖注入或运行时分派决定。
- `groups[_signature(candidate, schema)].append`（[alignment.py:48](../../../src/governance/alignment.py#L48)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `_signature`（调用点 [alignment.py:48](../../../src/governance/alignment.py#L48)）→ [_signature](alignment.md)，静态可定位。
- `groups.items`（[alignment.py:51](../../../src/governance/alignment.py#L51)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `sorted`（[alignment.py:52](../../../src/governance/alignment.py#L52)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `len`（[alignment.py:54](../../../src/governance/alignment.py#L54)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `aligned.append`（[alignment.py:55](../../../src/governance/alignment.py#L55)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `records.append`（[alignment.py:56](../../../src/governance/alignment.py#L56)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `AlignmentRecord`（[alignment.py:57](../../../src/governance/alignment.py#L57)）：来自 `src.domain.AlignmentRecord`；具体实现可能由依赖注入或运行时分派决定。
- `stable_id`（调用点 [alignment.py:58](../../../src/governance/alignment.py#L58)）→ [stable_id](../core/ids.md)，静态可定位。
- `members[0].model_copy`（[alignment.py:68](../../../src/governance/alignment.py#L68)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `min`（[alignment.py:76](../../../src/governance/alignment.py#L76)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `max`（[alignment.py:77](../../../src/governance/alignment.py#L77)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `all`（[alignment.py:81](../../../src/governance/alignment.py#L81)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `any`（[alignment.py:82](../../../src/governance/alignment.py#L82)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `by_subject_relation[sig[:2]].append`（[alignment.py:103](../../../src/governance/alignment.py#L103)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `by_subject_relation.values`（[alignment.py:104](../../../src/governance/alignment.py#L104)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `_object_key`（调用点 [alignment.py:105](../../../src/governance/alignment.py#L105)）→ [_object_key](alignment.md)，静态可定位。
- `normalize_label`（[alignment.py:124](../../../src/governance/alignment.py#L124)）：来自 `src.domain.normalize_label`；具体实现可能由依赖注入或运行时分派决定。
- `_relation_key`（调用点 [alignment.py:128](../../../src/governance/alignment.py#L128)）→ [_relation_key](alignment.md)，静态可定位。
- 静态扫描未定位直接调用方；可能通过路由注册、LangGraph 节点、协议方法或依赖注入动态调用，不据此判断为死代码。

**状态、副作用与异常**：
- 显式状态/容器赋值：`primary.evidence_ids`、`primary.visual_observation_ids`、`primary.modalities`、`primary.confidence`、`primary.id`、`primary.cross_modal_support`、`primary.coarse_visual_evidence`、`primary.context_only_visual_claim`、`primary.uncalibrated_visual_confidence`。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：未见 `raise`；下游异常可能继续上抛。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。


---
