源码：[runner.py:1](../../../src/evaluation/runner.py#L1) | 基准：`dev/v0.10@f2f34d7` | 本文件符号数：11

**模块职责**：Run a public evaluation manifest through the application service.
**在系统中的位置**：离线评测、预算账本、标注导出及报告；不等于生产工作流。
**直接依赖**：[src.domain](../domain/__init__.md)、[src.evaluation.models](models.md)、[src.workflow](../workflow/__init__.md)；外部/标准库：`__future__`、`orjson`、`pathlib`。
**主要调用方（静态导入）**：[evaluation/__init__.py](__init__.md)。
**阅读提示**：下列流程根据当前源码控制流整理；`self`/接口对象的实际类型可能在运行时注入，未能静态解析的调用会明确标注。链接指向源码行或对应讲解文件。

---

# _normalize ⭐⭐

**位置与等级**：[runner.py:19](../../../src/evaluation/runner.py#L19)；局部辅助逻辑，需理解其调用条件与失败传播。

**签名**：`def _normalize(value: str) -> str`。

**作用**：内部辅助步骤；将参数转换为本模块所需的中间对象或操作结果。

**输入与输出**：
- 输入：`value`（str）。
- 输出类型：`str`；具体返回路径见流程步骤。

**处理流程**：
1. 返回 `<字符串常量>.join(value.casefold().split())`。

**调用与被调用**：
- `<字符串常量>.join`（[runner.py:20](../../../src/evaluation/runner.py#L20)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `value.casefold().split`（[runner.py:20](../../../src/evaluation/runner.py#L20)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `value.casefold`（[runner.py:20](../../../src/evaluation/runner.py#L20)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- 静态可定位的调用方：[_canonical_entity_name](runner.md)、[_canonical_claim](runner.md)。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：未见 `raise`；下游异常可能继续上抛。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。


---

# _safe_ratio ⭐⭐

**位置与等级**：[runner.py:23](../../../src/evaluation/runner.py#L23)；局部辅助逻辑，需理解其调用条件与失败传播。

**签名**：`def _safe_ratio(numerator: int | float, denominator: int | float) -> float`。

**作用**：内部辅助步骤；将参数转换为本模块所需的中间对象或操作结果。

**输入与输出**：
- 输入：`numerator`（int | float）；`denominator`（int | float）。
- 输出类型：`float`；具体返回路径见流程步骤。

**处理流程**：
1. 返回 `float(numerator / denominator) if denominator else 0.0`。

**调用与被调用**：
- `float`（[runner.py:24](../../../src/evaluation/runner.py#L24)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- 静态可定位的调用方：[evaluate_manifest](runner.md)。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：未见 `raise`；下游异常可能继续上抛。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。


---

# _f1 ⭐⭐

**位置与等级**：[runner.py:27](../../../src/evaluation/runner.py#L27)；局部辅助逻辑，需理解其调用条件与失败传播。

**签名**：`def _f1(precision: float, recall: float) -> float`。

**作用**：内部辅助步骤；将参数转换为本模块所需的中间对象或操作结果。

**输入与输出**：
- 输入：`precision`（float）；`recall`（float）。
- 输出类型：`float`；具体返回路径见流程步骤。

**处理流程**：
1. 返回 `2 * precision * recall / (precision + recall) if precision + recall else 0.0`。

**调用与被调用**：
- 无显式函数调用，或仅声明协议/常量。
- 静态可定位的调用方：[evaluate_manifest](runner.md)。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：未见 `raise`；下游异常可能继续上抛。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。


---

# _safe_error ⭐⭐

**位置与等级**：[runner.py:31](../../../src/evaluation/runner.py#L31)；局部辅助逻辑，需理解其调用条件与失败传播。

**签名**：`def _safe_error(exc: Exception, service: PrismKEService) -> str`。

**作用**：内部辅助步骤；将参数转换为本模块所需的中间对象或操作结果。

**输入与输出**：
- 输入：`exc`（Exception）；`service`（PrismKEService）。
- 输出类型：`str`；具体返回路径见流程步骤。

**处理流程**：
1. 更新 `message`，值来自 `f<字符串常量>`。
2. 更新 `secrets`，值来自 `(service.settings.llm_api_key, service.settings.vlm_api_key)`。
3. 遍历 `secrets`，逐项处理 `secret`。
4. 返回 `message`。

**关键条件与保护**：
- [runner.py:35](../../../src/evaluation/runner.py#L35)：`secret`，不满足时跳过本分支。

**调用与被调用**：
- `type`（[runner.py:32](../../../src/evaluation/runner.py#L32)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `message.replace`（[runner.py:36](../../../src/evaluation/runner.py#L36)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- 静态可定位的调用方：[evaluate_manifest](runner.md)。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：未见 `raise`；下游异常可能继续上抛。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。


---

# _canonical_entity_name ⭐⭐

**位置与等级**：[runner.py:40](../../../src/evaluation/runner.py#L40)；局部辅助逻辑，需理解其调用条件与失败传播。

**签名**：`def _canonical_entity_name(value: str, schema: SchemaIndex | None) -> str`。

**作用**：内部辅助步骤；将参数转换为本模块所需的中间对象或操作结果。

**输入与输出**：
- 输入：`value`（str）；`schema`（SchemaIndex | None；当前任务的 Schema 或索引，约束实体与关系）。
- 输出类型：`str`；具体返回路径见流程步骤。

**处理流程**：
1. 检查 `schema is None`；按条件分流，else 分支不存在。
2. 更新 `normalized`，值来自 `normalize_label(value)`。
3. 更新 `matches`，值来自 `{item.name for item in schema.schema.entity_catalog if normalized in {normalize_label(name) for nam…`。
4. 返回 `_normalize(next(iter(matches))) if len(matches) == 1 else _normalize(value)`。

**关键条件与保护**：
- [runner.py:41](../../../src/evaluation/runner.py#L41)：`schema is None`，不满足时跳过本分支。

**调用与被调用**：
- `_normalize`（调用点 [runner.py:42](../../../src/evaluation/runner.py#L42)）→ [_normalize](runner.md)，静态可定位。
- `normalize_label`（[runner.py:43](../../../src/evaluation/runner.py#L43)）：来自 `src.domain.normalize_label`；具体实现可能由依赖注入或运行时分派决定。
- `len`（[runner.py:49](../../../src/evaluation/runner.py#L49)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `next`（[runner.py:49](../../../src/evaluation/runner.py#L49)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `iter`（[runner.py:49](../../../src/evaluation/runner.py#L49)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- 静态可定位的调用方：[_canonical_claim](runner.md)。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：未见 `raise`；下游异常可能继续上抛。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。


---

# _canonical_claim ⭐⭐

**位置与等级**：[runner.py:52](../../../src/evaluation/runner.py#L52)；局部辅助逻辑，需理解其调用条件与失败传播。

**签名**：`def _canonical_claim(subject: str, relation: str, obj: str, schema: SchemaIndex | None) -> tuple[str, str, str]`。

**作用**：内部辅助步骤；将参数转换为本模块所需的中间对象或操作结果。

**输入与输出**：
- 输入：`subject`（str）；`relation`（str）；`obj`（str）；`schema`（SchemaIndex | None；当前任务的 Schema 或索引，约束实体与关系）。
- 输出类型：`tuple[str, str, str]`；具体返回路径见流程步骤。

**处理流程**：
1. 更新 `canonical_subject`，值来自 `_canonical_entity_name(subject, schema)`。
2. 更新 `canonical_object`，值来自 `_canonical_entity_name(obj, schema)`。
3. 检查 `schema is None`；按条件分流，else 分支不存在。
4. 更新 `relation_def`，值来自 `schema.relation(relation)`。
5. 检查 `relation_def is None`；按条件分流，else 分支不存在。
6. 更新 `relation_id`，值来自 `relation_def.id`。
7. 检查 `relation_def.symmetric`；按条件分流，else 分支存在。
8. 返回 `(canonical_subject, _normalize(relation_id), canonical_object)`。

**关键条件与保护**：
- [runner.py:60](../../../src/evaluation/runner.py#L60)：`schema is None`，不满足时跳过本分支。
- [runner.py:63](../../../src/evaluation/runner.py#L63)：`relation_def is None`，不满足时跳过本分支。
- [runner.py:66](../../../src/evaluation/runner.py#L66)：`relation_def.symmetric`，不满足时有 else 分支。
- [runner.py:68](../../../src/evaluation/runner.py#L68)：`relation_def.inverse_relation`，不满足时跳过本分支。
- [runner.py:70](../../../src/evaluation/runner.py#L70)：`relation_id != canonical_relation`，不满足时跳过本分支。

**调用与被调用**：
- `_canonical_entity_name`（调用点 [runner.py:58](../../../src/evaluation/runner.py#L58)）→ [_canonical_entity_name](runner.md)，静态可定位。
- `_normalize`（调用点 [runner.py:61](../../../src/evaluation/runner.py#L61)）→ [_normalize](runner.md)，静态可定位。
- `schema.relation`（[runner.py:62](../../../src/evaluation/runner.py#L62)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `sorted`（[runner.py:67](../../../src/evaluation/runner.py#L67)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `min`（[runner.py:69](../../../src/evaluation/runner.py#L69)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- 静态可定位的调用方：[_predicted_claims](runner.md)、[_gold_claims](runner.md)。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：未见 `raise`；下游异常可能继续上抛。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。


---

# _predicted_claims ⭐⭐

**位置与等级**：[runner.py:76](../../../src/evaluation/runner.py#L76)；局部辅助逻辑，需理解其调用条件与失败传播。

**签名**：`def _predicted_claims(state: WorkflowState, schema: SchemaIndex | None) -> set[tuple[str, str, str]]`。

**作用**：内部辅助步骤；将参数转换为本模块所需的中间对象或操作结果。

**输入与输出**：
- 输入：`state`（WorkflowState；跨节点 WorkflowState；调用方须保持证据与状态一致）；`schema`（SchemaIndex | None；当前任务的 Schema 或索引，约束实体与关系）。
- 输出类型：`set[tuple[str, str, str]]`；具体返回路径见流程步骤。

**处理流程**：
1. 更新 `entities`，值来自 `{entity.id: entity.name for entity in state.entities}`。
2. 更新 `predicted`，值来自 `set()`。
3. 遍历 `state.claims`，逐项处理 `claim`。
4. 返回 `predicted`。

**关键条件与保护**：
- [runner.py:88](../../../src/evaluation/runner.py#L88)：`obj is not None`，不满足时跳过本分支。

**调用与被调用**：
- `set`（[runner.py:80](../../../src/evaluation/runner.py#L80)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `entities.get`（[runner.py:82](../../../src/evaluation/runner.py#L82)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `predicted.add`（[runner.py:89](../../../src/evaluation/runner.py#L89)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `_canonical_claim`（调用点 [runner.py:89](../../../src/evaluation/runner.py#L89)）→ [_canonical_claim](runner.md)，静态可定位。
- 静态可定位的调用方：[_case_result](runner.md)。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：未见 `raise`；下游异常可能继续上抛。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。


---

# _gold_claims ⭐⭐

**位置与等级**：[runner.py:93](../../../src/evaluation/runner.py#L93)；局部辅助逻辑，需理解其调用条件与失败传播。

**签名**：`def _gold_claims(case: EvaluationCase, schema: SchemaIndex | None) -> set[tuple[str, str, str]]`。

**作用**：内部辅助步骤；将参数转换为本模块所需的中间对象或操作结果。

**输入与输出**：
- 输入：`case`（EvaluationCase）；`schema`（SchemaIndex | None；当前任务的 Schema 或索引，约束实体与关系）。
- 输出类型：`set[tuple[str, str, str]]`；具体返回路径见流程步骤。

**处理流程**：
1. 返回 `{_canonical_claim(item.subject, item.relation, item.object, schema) for item in case.claims}`。

**调用与被调用**：
- `_canonical_claim`（调用点 [runner.py:95](../../../src/evaluation/runner.py#L95)）→ [_canonical_claim](runner.md)，静态可定位。
- 静态可定位的调用方：[_case_result](runner.md)。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：未见 `raise`；下游异常可能继续上抛。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。


---

# _entity_names ⭐⭐

**位置与等级**：[runner.py:99](../../../src/evaluation/runner.py#L99)；局部辅助逻辑，需理解其调用条件与失败传播。

**签名**：`def _entity_names(claims: set[tuple[str, str, str]]) -> set[str]`。

**作用**：内部辅助步骤；将参数转换为本模块所需的中间对象或操作结果。

**输入与输出**：
- 输入：`claims`（set[tuple[str, str, str]]；待处理的规范事实集合）。
- 输出类型：`set[str]`；具体返回路径见流程步骤。

**处理流程**：
1. 返回 `{value for subject, _, obj in claims for value in (subject, obj)}`。

**调用与被调用**：
- 无显式函数调用，或仅声明协议/常量。
- 静态可定位的调用方：[_case_result](runner.md)。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：未见 `raise`；下游异常可能继续上抛。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。


---

# _case_result ⭐⭐

**位置与等级**：[runner.py:103](../../../src/evaluation/runner.py#L103)；局部辅助逻辑，需理解其调用条件与失败传播。

**签名**：`def _case_result(case: EvaluationCase, state: WorkflowState) -> EvaluationCaseResult`。

**作用**：内部辅助步骤；将参数转换为本模块所需的中间对象或操作结果。

**输入与输出**：
- 输入：`case`（EvaluationCase）；`state`（WorkflowState；跨节点 WorkflowState；调用方须保持证据与状态一致）。
- 输出类型：`EvaluationCaseResult`；具体返回路径见流程步骤。

**处理流程**：
1. 更新 `schema`，值来自 `SchemaIndex(state.output_schema) if state.output_schema else None`。
2. 更新 `predicted`，值来自 `_predicted_claims(state, schema)`。
3. 更新 `gold`，值来自 `_gold_claims(case, schema)`。
4. 更新 `predicted_entities`，值来自 `_entity_names(predicted)`。
5. 更新 `gold_entities`，值来自 `_entity_names(gold)`。
6. 更新 `evidence`，值来自 `state.document.evidence if state.document else []`。
7. 更新 `bboxes`，值来自 `[item for item in evidence if item.bbox is not None]`。
8. 更新 `valid_bboxes`，值来自 `0`。
9. 遍历 `bboxes`，逐项处理 `item`。
10. 更新 `decisions`，值来自 `{item.decision for item in state.alignment_records}`。
11. 更新 `localization`，值来自 `{item.localization_level.value for item in evidence if item.localization_level is not None}`。
12. 更新 `calls`，值来自 `state.provider_calls`。
13. 返回 `EvaluationCaseResult(id=case.id, status=state.status, claim_true_positive=len(predicted & gold), claim_f…`。

**关键条件与保护**：
- [runner.py:114](../../../src/evaluation/runner.py#L114)：`item.coordinate_space != CoordinateSpace.NORMALIZED or all((0 <= value <= 1 for value in (item.bbox.x0, item.bbox.…`，不满足时跳过本分支。

**调用与被调用**：
- `SchemaIndex`（[runner.py:104](../../../src/evaluation/runner.py#L104)）：来自 `src.domain.SchemaIndex`；具体实现可能由依赖注入或运行时分派决定。
- `_predicted_claims`（调用点 [runner.py:105](../../../src/evaluation/runner.py#L105)）→ [_predicted_claims](runner.md)，静态可定位。
- `_gold_claims`（调用点 [runner.py:106](../../../src/evaluation/runner.py#L106)）→ [_gold_claims](runner.md)，静态可定位。
- `_entity_names`（调用点 [runner.py:107](../../../src/evaluation/runner.py#L107)）→ [_entity_names](runner.md)，静态可定位。
- `all`（[runner.py:114](../../../src/evaluation/runner.py#L114)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `EvaluationCaseResult`（调用点 [runner.py:123](../../../src/evaluation/runner.py#L123)）→ [EvaluationCaseResult](models.md)，静态可定位。
- `len`（[runner.py:126](../../../src/evaluation/runner.py#L126)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `sum`（[runner.py:132](../../../src/evaluation/runner.py#L132)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `bool`（[runner.py:132](../../../src/evaluation/runner.py#L132)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `set`（[runner.py:136](../../../src/evaluation/runner.py#L136)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `round`（[runner.py:142](../../../src/evaluation/runner.py#L142)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- 静态可定位的调用方：[evaluate_manifest](runner.md)。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：未见 `raise`；下游异常可能继续上抛。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。


---

# evaluate_manifest ⭐⭐

**位置与等级**：[runner.py:147](../../../src/evaluation/runner.py#L147)；局部辅助逻辑，需理解其调用条件与失败传播。

**签名**：`async def evaluate_manifest(manifest_path: Path, service: PrismKEService, *, provider_name: str, ocr_provider_name: str, vlm_provider_name: str) -> EvaluationReport`。

**作用**：Evaluate every case and keep failures isolated to their case.

**输入与输出**：
- 输入：`manifest_path`（Path）；`service`（PrismKEService）；`provider_name`（str）；`ocr_provider_name`（str）；`vlm_provider_name`（str）。
- 输出类型：`EvaluationReport`；具体返回路径见流程步骤。

**处理流程**：
1. 更新 `manifest_path`，值来自 `manifest_path.resolve()`。
2. 更新 `root`，值来自 `manifest_path.parent`。
3. 更新 `manifest`，值来自 `EvaluationManifest.model_validate(orjson.loads(manifest_path.read_bytes()))`。
4. 更新 `schema_path`，值来自 `(root / manifest.schema_path).resolve()`。
5. 更新 `results`，值来自 `[]`。
6. 遍历 `manifest.cases`，逐项处理 `case`。
7. 更新 `claim_tp`，值来自 `sum((item.claim_true_positive for item in results))`。
8. 更新 `claim_fp`，值来自 `sum((item.claim_false_positive for item in results))`。
9. 更新 `claim_fn`，值来自 `sum((item.claim_false_negative for item in results))`。
10. 更新 `entity_tp`，值来自 `sum((item.entity_true_positive for item in results))`。
11. 更新 `entity_fp`，值来自 `sum((item.entity_false_positive for item in results))`。
12. 更新 `entity_fn`，值来自 `sum((item.entity_false_negative for item in results))`。
13. 更新 `claim_precision`，值来自 `_safe_ratio(claim_tp, claim_tp + claim_fp)`。
14. 更新 `claim_recall`，值来自 `_safe_ratio(claim_tp, claim_tp + claim_fn)`。
15. 更新 `entity_precision`，值来自 `_safe_ratio(entity_tp, entity_tp + entity_fp)`。
16. 更新 `entity_recall`，值来自 `_safe_ratio(entity_tp, entity_tp + entity_fn)`。
17. 更新 `total_claims`，值来自 `sum((item.total_claims for item in results))`。
18. 更新 `total_bboxes`，值来自 `sum((item.total_bboxes for item in results))`。
19. 返回 `EvaluationReport(manifest_version=manifest.version, requested_model=service.settings.vlm_model, cases=re…`。

**调用与被调用**：
- `manifest_path.resolve`（[runner.py:157](../../../src/evaluation/runner.py#L157)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `EvaluationManifest.model_validate`（[runner.py:159](../../../src/evaluation/runner.py#L159)）：来自 `src.evaluation.models.EvaluationManifest`；具体实现可能由依赖注入或运行时分派决定。
- `orjson.loads`（[runner.py:159](../../../src/evaluation/runner.py#L159)）：来自 `orjson`；具体实现可能由依赖注入或运行时分派决定。
- `manifest_path.read_bytes`（[runner.py:159](../../../src/evaluation/runner.py#L159)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `(root / manifest.schema_path).resolve`（[runner.py:160](../../../src/evaluation/runner.py#L160)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `service.run`（[runner.py:164](../../../src/evaluation/runner.py#L164)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `(root / case.input).resolve`（[runner.py:165](../../../src/evaluation/runner.py#L165)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `results.append`（[runner.py:171](../../../src/evaluation/runner.py#L171)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `_case_result`（调用点 [runner.py:171](../../../src/evaluation/runner.py#L171)）→ [_case_result](runner.md)，静态可定位。
- `EvaluationCaseResult`（调用点 [runner.py:174](../../../src/evaluation/runner.py#L174)）→ [EvaluationCaseResult](models.md)，静态可定位。
- `_safe_error`（调用点 [runner.py:177](../../../src/evaluation/runner.py#L177)）→ [_safe_error](runner.md)，静态可定位。
- `sum`（[runner.py:180](../../../src/evaluation/runner.py#L180)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `_safe_ratio`（调用点 [runner.py:186](../../../src/evaluation/runner.py#L186)）→ [_safe_ratio](runner.md)，静态可定位。
- `EvaluationReport`（调用点 [runner.py:192](../../../src/evaluation/runner.py#L192)）→ [EvaluationReport](models.md)，静态可定位。
- `round`（[runner.py:198](../../../src/evaluation/runner.py#L198)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `_f1`（调用点 [runner.py:200](../../../src/evaluation/runner.py#L200)）→ [_f1](runner.md)，静态可定位。
- `len`（[runner.py:213](../../../src/evaluation/runner.py#L213)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- 静态扫描未定位直接调用方；可能通过路由注册、LangGraph 节点、协议方法或依赖注入动态调用，不据此判断为死代码。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：未见 `raise`；下游异常可能继续上抛。
- 本地捕获：`Exception`。


---
