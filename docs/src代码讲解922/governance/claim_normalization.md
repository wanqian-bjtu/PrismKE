源码：[claim_normalization.py:1](../../../src/governance/claim_normalization.py#L1) | 基准：`dev/v0.10@f2f34d7` | 本文件符号数：4

**模块职责**：Schema-aware claim normalization and supporting-evidence merging.
**在系统中的位置**：实体解析、事实规范化、冲突、风险、审核及实体操作的确定性规则。
**直接依赖**：[src.core.errors](../core/errors.md)、[src.core.ids](../core/ids.md)、[src.domain](../domain/__init__.md)；外部/标准库：`__future__`。
**主要调用方（静态导入）**：[governance/__init__.py](__init__.md)、[governance/validation/service.py](validation/service.md)。
**阅读提示**：下列流程根据当前源码控制流整理；`self`/接口对象的实际类型可能在运行时注入，未能静态解析的调用会明确标注。链接指向源码行或对应讲解文件。

---

# collect_mentions ⭐⭐

**位置与等级**：[claim_normalization.py:17](../../../src/governance/claim_normalization.py#L17)；局部辅助逻辑，需理解其调用条件与失败传播。

**签名**：`def collect_mentions(candidates: list[CandidateClaim]) -> list[EntityMention]`。

**作用**：处理 `collect_mentions` 对应步骤；下列步骤依据函数体的实际控制流和调用点整理。

**输入与输出**：
- 输入：`candidates`（list[CandidateClaim]；待逐项检查/治理的候选集合）。
- 输出类型：`list[EntityMention]`；具体返回路径见流程步骤。

**处理流程**：
1. 更新 `result`，值来自 `{}`。
2. 遍历 `candidates`，逐项处理 `candidate`。
3. 返回 `list(result.values())`。

**关键条件与保护**：
- [claim_normalization.py:21](../../../src/governance/claim_normalization.py#L21)：`isinstance(candidate.object, EntityMention)`，不满足时跳过本分支。

**调用与被调用**：
- `isinstance`（[claim_normalization.py:21](../../../src/governance/claim_normalization.py#L21)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `list`（[claim_normalization.py:23](../../../src/governance/claim_normalization.py#L23)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `result.values`（[claim_normalization.py:23](../../../src/governance/claim_normalization.py#L23)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- 静态扫描未定位直接调用方；可能通过路由注册、LangGraph 节点、协议方法或依赖注入动态调用，不据此判断为死代码。

**状态、副作用与异常**：
- 显式状态/容器赋值：`result[candidate.subject.id]`、`result[candidate.object.id]`。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：未见 `raise`；下游异常可能继续上抛。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。


---

# _fact_identity ⭐⭐

**位置与等级**：[claim_normalization.py:26](../../../src/governance/claim_normalization.py#L26)；局部辅助逻辑，需理解其调用条件与失败传播。

**签名**：`def _fact_identity(schema: SchemaIndex, subject_id: str, relation_id: str, object_entity_id: str | None, object_literal: str | None, qualifiers: object) -> tuple[object, ...]`。

**作用**：内部辅助步骤；将参数转换为本模块所需的中间对象或操作结果。

**输入与输出**：
- 输入：`schema`（SchemaIndex；当前任务的 Schema 或索引，约束实体与关系）；`subject_id`（str）；`relation_id`（str）；`object_entity_id`（str | None）；`object_literal`（str | None）；`qualifiers`（object）。
- 输出类型：`tuple[object, ...]`；具体返回路径见流程步骤。

**处理流程**：
1. 更新 `relation`，值来自 `schema.relation_by_id(relation_id)`。
2. 更新 `object_key`，值来自 `object_entity_id or f<字符串常量><字符串常量>`。
3. 更新 `canonical_subject`，值来自 `subject_id`。
4. 更新 `canonical_relation`，值来自 `relation_id`。
5. 更新 `canonical_object`，值来自 `object_key`。
6. 检查 `relation and relation.symmetric and object_entity_id`；按条件分流，else 分支存在。
7. 返回 `(canonical_subject, canonical_relation, canonical_object, qualifiers)`。

**关键条件与保护**：
- [claim_normalization.py:39](../../../src/governance/claim_normalization.py#L39)：`relation and relation.symmetric and object_entity_id`，不满足时有 else 分支。
- [claim_normalization.py:41](../../../src/governance/claim_normalization.py#L41)：`relation and relation.inverse_relation and object_entity_id`，不满足时跳过本分支。
- [claim_normalization.py:43](../../../src/governance/claim_normalization.py#L43)：`relation_id != canonical_relation`，不满足时跳过本分支。

**调用与被调用**：
- `schema.relation_by_id`（[claim_normalization.py:34](../../../src/governance/claim_normalization.py#L34)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `normalize_label`（[claim_normalization.py:35](../../../src/governance/claim_normalization.py#L35)）：来自 `src.domain.normalize_label`；具体实现可能由依赖注入或运行时分派决定。
- `sorted`（[claim_normalization.py:40](../../../src/governance/claim_normalization.py#L40)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `min`（[claim_normalization.py:42](../../../src/governance/claim_normalization.py#L42)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- 静态可定位的调用方：[normalize_claims](claim_normalization.md)。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：未见 `raise`；下游异常可能继续上抛。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。


---

# normalize_claims ⭐⭐⭐⭐

**位置与等级**：[claim_normalization.py:48](../../../src/governance/claim_normalization.py#L48)；承担主要 Agent、应用服务或审核/执行入口，跨模块影响显著。

**签名**：`def normalize_claims(candidates: list[CandidateClaim], schema: SchemaIndex, entities: dict[str, CanonicalEntity], mention_to_entity: dict[str, str]) -> list[Claim]`。

**作用**：将实体提及和候选关系规范化为 Claim，同时保留证据来源。

**输入与输出**：
- 输入：`candidates`（list[CandidateClaim]；待逐项检查/治理的候选集合）；`schema`（SchemaIndex；当前任务的 Schema 或索引，约束实体与关系）；`entities`（dict[str, CanonicalEntity]）；`mention_to_entity`（dict[str, str]）。
- 输出类型：`list[Claim]`；具体返回路径见流程步骤。

**处理流程**：
1. 更新 `claims`，值来自 `[]`。
2. 遍历 `candidates`，逐项处理 `candidate`。
3. 返回 `merge_supporting_claims(claims)`。

**关键条件与保护**：
- [claim_normalization.py:57](../../../src/governance/claim_normalization.py#L57)：`relation is None`，不满足时有 else 分支。
- [claim_normalization.py:58](../../../src/governance/claim_normalization.py#L58)：`schema.schema.strict`，不满足时跳过本分支。
- [claim_normalization.py:68](../../../src/governance/claim_normalization.py#L68)：`isinstance(candidate.object, EntityMention)`，不满足时有 else 分支。
- [claim_normalization.py:73](../../../src/governance/claim_normalization.py#L73)：`relation and object_type`，不满足时跳过本分支。
- [claim_normalization.py:76](../../../src/governance/claim_normalization.py#L76)：`not (subject_matches and object_matches) and relation.inverse_relation`，不满足时跳过本分支。
- [claim_normalization.py:78](../../../src/governance/claim_normalization.py#L78)：`inverse`，不满足时跳过本分支。
- [claim_normalization.py:81](../../../src/governance/claim_normalization.py#L81)：`inverse_subject_matches and inverse_object_matches`，不满足时跳过本分支。
- [claim_normalization.py:84](../../../src/governance/claim_normalization.py#L84)：`relation and relation.domain and (subject_type not in relation.domain)`，不满足时跳过本分支。
- [claim_normalization.py:88](../../../src/governance/claim_normalization.py#L88)：`relation and object_type and relation.range and (object_type not in relation.range)`，不满足时跳过本分支。

**调用与被调用**：
- `schema.relation`（[claim_normalization.py:56](../../../src/governance/claim_normalization.py#L56)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `SchemaValidationError`（调用点 [claim_normalization.py:59](../../../src/governance/claim_normalization.py#L59)）→ [SchemaValidationError](../core/errors.md)，静态可定位。
- `candidate.relation.strip`（[claim_normalization.py:60](../../../src/governance/claim_normalization.py#L60)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `isinstance`（[claim_normalization.py:68](../../../src/governance/claim_normalization.py#L68)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `candidate.object.strip`（[claim_normalization.py:72](../../../src/governance/claim_normalization.py#L72)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `schema.relation_by_id`（[claim_normalization.py:77](../../../src/governance/claim_normalization.py#L77)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `_fact_identity`（调用点 [claim_normalization.py:92](../../../src/governance/claim_normalization.py#L92)）→ [_fact_identity](claim_normalization.md)，静态可定位。
- `claims.append`（[claim_normalization.py:100](../../../src/governance/claim_normalization.py#L100)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `Claim`（[claim_normalization.py:101](../../../src/governance/claim_normalization.py#L101)）：来自 `src.domain.Claim`；具体实现可能由依赖注入或运行时分派决定。
- `stable_id`（调用点 [claim_normalization.py:102](../../../src/governance/claim_normalization.py#L102)）→ [stable_id](../core/ids.md)，静态可定位。
- `merge_supporting_claims`（调用点 [claim_normalization.py:117](../../../src/governance/claim_normalization.py#L117)）→ [merge_supporting_claims](claim_normalization.md)，静态可定位。
- 静态可定位的调用方：[ValidationService.candidates](validation/service.md)。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：`SchemaValidationError(f<字符串常量>)`。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。


---

# merge_supporting_claims ⭐⭐

**位置与等级**：[claim_normalization.py:120](../../../src/governance/claim_normalization.py#L120)；局部辅助逻辑，需理解其调用条件与失败传播。

**签名**：`def merge_supporting_claims(claims: list[Claim]) -> list[Claim]`。

**作用**：处理 `merge_supporting_claims` 对应步骤；下列步骤依据函数体的实际控制流和调用点整理。

**输入与输出**：
- 输入：`claims`（list[Claim]；待处理的规范事实集合）。
- 输出类型：`list[Claim]`；具体返回路径见流程步骤。

**处理流程**：
1. 更新 `merged`，值来自 `{}`。
2. 遍历 `claims`，逐项处理 `claim`。
3. 返回 `list(merged.values())`。

**关键条件与保护**：
- [claim_normalization.py:124](../../../src/governance/claim_normalization.py#L124)：`current is None`，不满足时跳过本分支。

**调用与被调用**：
- `merged.get`（[claim_normalization.py:123](../../../src/governance/claim_normalization.py#L123)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `sorted`（[claim_normalization.py:127](../../../src/governance/claim_normalization.py#L127)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `set`（[claim_normalization.py:127](../../../src/governance/claim_normalization.py#L127)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `max`（[claim_normalization.py:131](../../../src/governance/claim_normalization.py#L131)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `list`（[claim_normalization.py:142](../../../src/governance/claim_normalization.py#L142)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `merged.values`（[claim_normalization.py:142](../../../src/governance/claim_normalization.py#L142)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- 静态可定位的调用方：[normalize_claims](claim_normalization.md)。

**状态、副作用与异常**：
- 显式状态/容器赋值：`merged[claim.id]`、`current.evidence_ids`、`current.source_candidate_ids`、`current.confidence`、`current.cross_modal_support`、`current.coarse_visual_evidence`、`current.context_only_visual_claim`、`current.uncalibrated_visual_confidence`。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：未见 `raise`；下游异常可能继续上抛。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。


---
