源码：[service.py:1](../../../../src/governance/validation/service.py#L1) | 基准：`dev/v0.10@f2f34d7` | 本文件符号数：9

**模块职责**：Validation does not repair facts or invoke models.
**在系统中的位置**：候选及提交前的统一结构、Schema、引用和证据校验。
**阅读重点**：ValidationService 对候选和 GraphCommit 执行统一校验。非法候选隔离不等于忽略；阻断问题未处理前不能写图，人工批准也不能绕过硬约束。
**直接依赖**：[src.core.errors](../../core/errors.md)、[src.core.ids](../../core/ids.md)、[src.domain](../../domain/__init__.md)、[src.governance.claim_normalization](../claim_normalization.md)、[src.persistence.base](../../persistence/base.md)；外部/标准库：`PIL`、`__future__`、`collections`、`io`、`math`、`pymupdf`、`typing`。
**主要调用方（静态导入）**：[governance/validation/__init__.py](__init__.md)。
**阅读提示**：下列流程根据当前源码控制流整理；`self`/接口对象的实际类型可能在运行时注入，未能静态解析的调用会明确标注。链接指向源码行或对应讲解文件。

## 核心路径解读

- `candidates` 逐条检查提及的实体类型、关系声明及 domain/range，验证 EvidenceRef 是否存在、哈希与存储记录是否一致、定位是否有效；问题进入独立 ValidationIssue 集合。
- 一条候选失败只隔离该候选，不能把 Provider 级网络/鉴权/整批 JSON 失败包装成空候选。未知关系在宽松模式下也不能写图。
- `commit` 对每个新建或恢复的活动 Claim 重查 Schema 上下文、实体状态、证据、Document/MediaAsset 引用及物理定位。关闭历史 Claim 与新增活动事实要求不同；写入前失败应抛 GraphIntegrityError。

---

# ValidationService ⭐⭐⭐⭐

**位置与等级**：[service.py:30](../../../../src/governance/validation/service.py#L30)；承担主要 Agent、应用服务或审核/执行入口，跨模块影响显著。

**职责**：跨步骤服务；组合依赖并暴露可复用业务入口。基类：无显式基类。

**字段与类级约束**：
- 类体未直接声明字段；实例状态请看 `__init__` 及方法中的赋值。

**内部成员**：`ValidationService.blocked_candidate_ids`、`ValidationService.physical_location_error`、`ValidationService.issue`、`ValidationService.merge`、`ValidationService.location_error`、`ValidationService.candidates`、`ValidationService.commit`


---

# ValidationService.blocked_candidate_ids ⭐⭐

**位置与等级**：[service.py:32](../../../../src/governance/validation/service.py#L32)；局部辅助逻辑，需理解其调用条件与失败传播。

**签名**：`def blocked_candidate_ids(candidates: list[CandidateClaim], result: ValidationResult) -> set[str]`。

**装饰器/路由**：`staticmethod`。

**作用**：处理 `blocked_candidate_ids` 对应步骤；下列步骤依据函数体的实际控制流和调用点整理。

**输入与输出**：
- 输入：`candidates`（list[CandidateClaim]；待逐项检查/治理的候选集合）；`result`（ValidationResult）。
- 输出类型：`set[str]`；具体返回路径见流程步骤。

**处理流程**：
1. 更新 `targets`，值来自 `{i.target_id for i in result.issues if i.severity == 'blocking' and i.status == 'open'}`。
2. 返回 `{c.id for c in candidates if c.id in targets or targets.intersection(c.visual_observation_ids)}`。

**调用与被调用**：
- `targets.intersection`（[service.py:41](../../../../src/governance/validation/service.py#L41)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- 静态扫描未定位直接调用方；可能通过路由注册、LangGraph 节点、协议方法或依赖注入动态调用，不据此判断为死代码。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：未见 `raise`；下游异常可能继续上抛。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。


---

# ValidationService.physical_location_error ⭐⭐

**位置与等级**：[service.py:45](../../../../src/governance/validation/service.py#L45)；局部辅助逻辑，需理解其调用条件与失败传播。

**签名**：`async def physical_location_error(ref: EvidenceRef, store: EvidenceStore) -> str | None`。

**装饰器/路由**：`staticmethod`。

**作用**：处理 `physical_location_error` 对应步骤；下列步骤依据函数体的实际控制流和调用点整理。

**输入与输出**：
- 输入：`ref`（EvidenceRef）；`store`（EvidenceStore）。
- 输出类型：`str | None`；具体返回路径见流程步骤。

**处理流程**：
1. 更新 `content`，值来自 `await store.get_blob(ref.source_hash)`。
2. 检查 `ref.bbox is not None`；按条件分流，else 分支不存在。
3. 检查 `ref.char_end is not None and ref.char_end > len(content.decode('utf-8', errors='replace'))`；按条件分流，else 分支不存在。
4. 返回 `None`。

**关键条件与保护**：
- [service.py:47](../../../../src/governance/validation/service.py#L47)：`ref.bbox is not None`，不满足时跳过本分支。
- [service.py:48](../../../../src/governance/validation/service.py#L48)：`ref.coordinate_space == 'pdf_points'`，不满足时有 else 分支。
- [service.py:50](../../../../src/governance/validation/service.py#L50)：`ref.page_number is None or not 1 <= ref.page_number <= len(pdf)`，不满足时跳过本分支。
- [service.py:57](../../../../src/governance/validation/service.py#L57)：`ref.canvas_width != width or ref.canvas_height != height`，不满足时跳过本分支。
- [service.py:59](../../../../src/governance/validation/service.py#L59)：`ref.char_end is not None and ref.char_end > len(content.decode('utf-8', errors='replace'))`，不满足时跳过本分支。

**调用与被调用**：
- `store.get_blob`（[service.py:46](../../../../src/governance/validation/service.py#L46)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `pymupdf.open`（[service.py:49](../../../../src/governance/validation/service.py#L49)）：来自 `pymupdf`；具体实现可能由依赖注入或运行时分派决定。
- `len`（[service.py:50](../../../../src/governance/validation/service.py#L50)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `float`（[service.py:53](../../../../src/governance/validation/service.py#L53)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `Image.open`（[service.py:55](../../../../src/governance/validation/service.py#L55)）：来自 `PIL.Image`；具体实现可能由依赖注入或运行时分派决定。
- `BytesIO`（[service.py:55](../../../../src/governance/validation/service.py#L55)）：来自 `io.BytesIO`；具体实现可能由依赖注入或运行时分派决定。
- `content.decode`（[service.py:60](../../../../src/governance/validation/service.py#L60)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- 静态可定位的调用方：[ValidationService.commit](service.md)。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：未见 `raise`；下游异常可能继续上抛。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。


---

# ValidationService.issue ⭐⭐

**位置与等级**：[service.py:66](../../../../src/governance/validation/service.py#L66)；局部辅助逻辑，需理解其调用条件与失败传播。

**签名**：`def issue(code: str, stage: Any, target_type: Any, target_id: str, field_path: str, message: str, evidence_ids: list[str] | None=None, summary: dict[str, Any] | None=None) -> ValidationIssue`。

**装饰器/路由**：`staticmethod`。

**作用**：处理 `issue` 对应步骤；下列步骤依据函数体的实际控制流和调用点整理。

**输入与输出**：
- 输入：`code`（str）；`stage`（Any）；`target_type`（Any）；`target_id`（str）；`field_path`（str）；`message`（str）；`evidence_ids`（list[str] | None；默认 `None`）；`summary`（dict[str, Any] | None；默认 `None`）。
- 输出类型：`ValidationIssue`；具体返回路径见流程步骤。

**处理流程**：
1. 返回 `ValidationIssue(id=stable_id('validation', code, stage, target_type, target_id, field_path), code=code, …`。

**调用与被调用**：
- `ValidationIssue`（[service.py:76](../../../../src/governance/validation/service.py#L76)）：来自 `src.domain.ValidationIssue`；具体实现可能由依赖注入或运行时分派决定。
- `stable_id`（调用点 [service.py:77](../../../../src/governance/validation/service.py#L77)）→ [stable_id](../../core/ids.md)，静态可定位。
- 静态可定位的调用方：[ValidationService.candidates.add](service.md)。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：未见 `raise`；下游异常可能继续上抛。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。


---

# ValidationService.merge ⭐⭐

**位置与等级**：[service.py:89](../../../../src/governance/validation/service.py#L89)；局部辅助逻辑，需理解其调用条件与失败传播。

**签名**：`def merge(previous: ValidationResult, issues: Iterable[ValidationIssue], fingerprint: str='', passed_count: int=0) -> ValidationResult`。

**装饰器/路由**：`staticmethod`。

**作用**：处理 `merge` 对应步骤；下列步骤依据函数体的实际控制流和调用点整理。

**输入与输出**：
- 输入：`previous`（ValidationResult）；`issues`（Iterable[ValidationIssue]）；`fingerprint`（str；默认 `''`）；`passed_count`（int；默认 `0`）。
- 输出类型：`ValidationResult`；具体返回路径见流程步骤。

**处理流程**：
1. 更新 `merged`，值来自 `{item.id: item for item in previous.issues}`。
2. 遍历 `issues`，逐项处理 `item`。
3. 更新 `values`，值来自 `list(merged.values())`。
4. 返回 `ValidationResult(input_fingerprint=fingerprint or previous.input_fingerprint, issues=values, passed_coun…`。

**关键条件与保护**：
- [service.py:97](../../../../src/governance/validation/service.py#L97)：`item.id not in merged`，不满足时跳过本分支。

**调用与被调用**：
- `list`（[service.py:99](../../../../src/governance/validation/service.py#L99)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `merged.values`（[service.py:99](../../../../src/governance/validation/service.py#L99)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `ValidationResult`（[service.py:100](../../../../src/governance/validation/service.py#L100)）：来自 `src.domain.ValidationResult`；具体实现可能由依赖注入或运行时分派决定。
- `sum`（[service.py:104](../../../../src/governance/validation/service.py#L104)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- 静态扫描未定位直接调用方；可能通过路由注册、LangGraph 节点、协议方法或依赖注入动态调用，不据此判断为死代码。

**状态、副作用与异常**：
- 显式状态/容器赋值：`merged[item.id]`。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：未见 `raise`；下游异常可能继续上抛。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。


---

# ValidationService.location_error ⭐⭐

**位置与等级**：[service.py:108](../../../../src/governance/validation/service.py#L108)；局部辅助逻辑，需理解其调用条件与失败传播。

**签名**：`def location_error(ref: EvidenceRef, document: DocumentIR | None=None) -> str | None`。

**装饰器/路由**：`staticmethod`。

**作用**：处理 `location_error` 对应步骤；下列步骤依据函数体的实际控制流和调用点整理。

**输入与输出**：
- 输入：`ref`（EvidenceRef）；`document`（DocumentIR | None；默认 `None`；解析后的文档及其文本、媒体、证据定位）。
- 输出类型：`str | None`；具体返回路径见流程步骤。

**处理流程**：
1. 检查 `(ref.char_start is None) != (ref.char_end is None)`；按条件分流，else 分支不存在。
2. 检查 `ref.char_start is not None and ref.char_end is not None and (ref.char_start < 0 or ref.char_end <= ref.c…`；按条件分流，else 分支不存在。
3. 检查 `ref.page_number is not None and ref.page_number < 1`；按条件分流，else 分支不存在。
4. 检查 `document is not None`；按条件分流，else 分支不存在。
5. 检查 `ref.bbox is not None`；按条件分流，else 分支不存在。
6. 返回 `None`。

**关键条件与保护**：
- [service.py:109](../../../../src/governance/validation/service.py#L109)：`(ref.char_start is None) != (ref.char_end is None)`，不满足时跳过本分支。
- [service.py:111](../../../../src/governance/validation/service.py#L111)：`ref.char_start is not None and ref.char_end is not None and (ref.char_start < 0 or ref.char_end <= ref.char_start)`，不满足时跳过本分支。
- [service.py:117](../../../../src/governance/validation/service.py#L117)：`ref.page_number is not None and ref.page_number < 1`，不满足时跳过本分支。
- [service.py:119](../../../../src/governance/validation/service.py#L119)：`document is not None`，不满足时跳过本分支。
- [service.py:120](../../../../src/governance/validation/service.py#L120)：`ref.document_id != document.id`，不满足时跳过本分支。
- [service.py:122](../../../../src/governance/validation/service.py#L122)：`ref.media_asset_id and ref.media_asset_id not in {a.id for a in document.media_assets}`，不满足时跳过本分支。
- [service.py:126](../../../../src/governance/validation/service.py#L126)：`document.pages and ref.page_number is not None and (ref.page_number not in {p.page_number for p in document.pages})`，不满足时跳过本分支。
- [service.py:132](../../../../src/governance/validation/service.py#L132)：`ref.char_start is not None`，不满足时跳过本分支。
- [service.py:134](../../../../src/governance/validation/service.py#L134)：`not blocks or any((b.char_start != ref.char_start or b.char_end != ref.char_end for b in blocks))`，不满足时跳过本分支。
- [service.py:138](../../../../src/governance/validation/service.py#L138)：`ref.bbox is not None`，不满足时跳过本分支。
- [service.py:140](../../../../src/governance/validation/service.py#L140)：`not all((math.isfinite(v) for v in (b.x0, b.y0, b.x1, b.y1)))`，不满足时跳过本分支。
- [service.py:142](../../../../src/governance/validation/service.py#L142)：`ref.coordinate_space is None or ref.canvas_width is None or ref.canvas_height is None`，不满足时跳过本分支。
- 另有 1 个条件判断，参见源码；不要将本列表当作全部分支。

**调用与被调用**：
- `any`（[service.py:134](../../../../src/governance/validation/service.py#L134)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `all`（[service.py:140](../../../../src/governance/validation/service.py#L140)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `math.isfinite`（[service.py:140](../../../../src/governance/validation/service.py#L140)）：来自 `math`；具体实现可能由依赖注入或运行时分派决定。
- 静态可定位的调用方：[ValidationService.candidates](service.md)、[ValidationService.commit](service.md)。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：未见 `raise`；下游异常可能继续上抛。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。


---

# ValidationService.candidates ⭐⭐⭐⭐⭐

**位置与等级**：[service.py:157](../../../../src/governance/validation/service.py#L157)；位于工作流推进、硬校验或原子事务的关键边界；错误可能影响审核停顿或图状态。

**签名**：`async def candidates(self, candidates: list[CandidateClaim], schema: SchemaIndex, document: DocumentIR, evidence_store: EvidenceStore, entities: dict[str, CanonicalEntity] | None=None, mention_map: dict[str, str] | None=None) -> list[ValidationIssue]`。

**作用**：逐项校验抽取候选并汇总问题；单项错误须与整批 Provider 失败区分。

**输入与输出**：
- 输入：`candidates`（list[CandidateClaim]；待逐项检查/治理的候选集合）；`schema`（SchemaIndex；当前任务的 Schema 或索引，约束实体与关系）；`document`（DocumentIR；解析后的文档及其文本、媒体、证据定位）；`evidence_store`（EvidenceStore；证据元数据和原始内容的存储接口）；`entities`（dict[str, CanonicalEntity] | None；默认 `None`）；`mention_map`（dict[str, str] | None；默认 `None`）。
- 输出类型：`list[ValidationIssue]`；具体返回路径见流程步骤。

**处理流程**：
1. 更新 `issues`，值来自 `[]`。
2. 更新 `refs`，值来自 `{r.id: r for r in document.evidence}`。
3. 更新 `type_ids`，值来自 `{t.id for t in schema.schema.entity_types}`。
4. 遍历 `candidates`，逐项处理 `c`。
5. 返回 `issues`。

**关键条件与保护**：
- [service.py:193](../../../../src/governance/validation/service.py#L193)：`not set(mention.evidence_ids) <= refs.keys()`，不满足时跳过本分支。
- [service.py:195](../../../../src/governance/validation/service.py#L195)：`not set(c.visual_observation_ids) <= {o.id for o in document.visual_observations}`，不满足时跳过本分支。
- [service.py:204](../../../../src/governance/validation/service.py#L204)：`normalized not in type_ids`，不满足时跳过本分支。
- [service.py:208](../../../../src/governance/validation/service.py#L208)：`schema.relation(c.relation) is None`，不满足时跳过本分支。
- [service.py:211](../../../../src/governance/validation/service.py#L211)：`relation and relation.domain`，不满足时跳过本分支。
- [service.py:213](../../../../src/governance/validation/service.py#L213)：`subject_type not in relation.domain`，不满足时跳过本分支。
- [service.py:220](../../../../src/governance/validation/service.py#L220)：`relation and relation.range and isinstance(c.object, EntityMention)`，不满足时跳过本分支。
- [service.py:222](../../../../src/governance/validation/service.py#L222)：`object_type not in relation.range`，不满足时跳过本分支。
- [service.py:229](../../../../src/governance/validation/service.py#L229)：`relation and relation.range and (not isinstance(c.object, EntityMention))`，不满足时跳过本分支。
- [service.py:236](../../../../src/governance/validation/service.py#L236)：`not c.evidence_ids`，不满足时跳过本分支。
- [service.py:239](../../../../src/governance/validation/service.py#L239)：`eid not in refs`，不满足时跳过本分支。
- [service.py:243](../../../../src/governance/validation/service.py#L243)：`not await evidence_store.exists(eid)`，不满足时有 else 分支。
- 另有 6 个条件判断，参见源码；不要将本列表当作全部分支。

**调用与被调用**：
- `isinstance`（[service.py:191](../../../../src/governance/validation/service.py#L191)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `set`（[service.py:193](../../../../src/governance/validation/service.py#L193)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `refs.keys`（[service.py:193](../../../../src/governance/validation/service.py#L193)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `add`（[service.py:194](../../../../src/governance/validation/service.py#L194)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `schema.entity_type`（[service.py:203](../../../../src/governance/validation/service.py#L203)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `schema.relation`（[service.py:208](../../../../src/governance/validation/service.py#L208)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `evidence_store.exists`（[service.py:243](../../../../src/governance/validation/service.py#L243)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `evidence_store.verify`（[service.py:245](../../../../src/governance/validation/service.py#L245)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `evidence_store.get`（[service.py:247](../../../../src/governance/validation/service.py#L247)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `self.location_error`（调用点 [service.py:254](../../../../src/governance/validation/service.py#L254)）→ [ValidationService.location_error](service.md)，静态可定位。
- `any`（[service.py:258](../../../../src/governance/validation/service.py#L258)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `normalize_claims`（调用点 [service.py:269](../../../../src/governance/validation/service.py#L269)）→ [normalize_claims](../claim_normalization.md)，静态可定位。
- 静态扫描未定位直接调用方；可能通过路由注册、LangGraph 节点、协议方法或依赖注入动态调用，不据此判断为死代码。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：未见 `raise`；下游异常可能继续上抛。
- 本地捕获：`SchemaValidationError`。


---

# ValidationService.candidates.add ⭐⭐⭐⭐⭐

**位置与等级**：[service.py:171](../../../../src/governance/validation/service.py#L171)；位于工作流推进、硬校验或原子事务的关键边界；错误可能影响审核停顿或图状态。

**签名**：`def add(code: str, stage: Any, field: str, message: str, c: CandidateClaim=c) -> None`。

**作用**：处理 `add` 对应步骤；下列步骤依据函数体的实际控制流和调用点整理。

**输入与输出**：
- 输入：`code`（str）；`stage`（Any）；`field`（str）；`message`（str）；`c`（CandidateClaim；默认 `c`）。
- 输出类型：`None`；具体返回路径见流程步骤。

**处理流程**：
1. 调用 `issues.append`，结果未直接赋值。

**调用与被调用**：
- `issues.append`（[service.py:172](../../../../src/governance/validation/service.py#L172)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `self.issue`（调用点 [service.py:173](../../../../src/governance/validation/service.py#L173)）→ [ValidationService.issue](service.md)，静态可定位。
- `isinstance`（[service.py:185](../../../../src/governance/validation/service.py#L185)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- 静态扫描未定位直接调用方；可能通过路由注册、LangGraph 节点、协议方法或依赖注入动态调用，不据此判断为死代码。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：未见 `raise`；下游异常可能继续上抛。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。


---

# ValidationService.commit ⭐⭐⭐⭐⭐

**位置与等级**：[service.py:279](../../../../src/governance/validation/service.py#L279)；位于工作流推进、硬校验或原子事务的关键边界；错误可能影响审核停顿或图状态。

**签名**：`async def commit(self, transaction: GraphCommit, entities: dict[str, CanonicalEntity], evidence: dict[str, EvidenceRef], document_ids: set[str], evidence_store: EvidenceStore | None) -> None`。

**作用**：对 GraphCommit 中活动事实执行最终硬校验；只验证 Schema、实体、文档与证据，不亲自写入图谱。

**输入与输出**：
- 输入：`transaction`（GraphCommit；待提交 GraphCommit；必须在最终写入边界重新校验）；`entities`（dict[str, CanonicalEntity]）；`evidence`（dict[str, EvidenceRef]）；`document_ids`（set[str]）；`evidence_store`（EvidenceStore | None；证据元数据和原始内容的存储接口）。
- 输出类型：`None`；具体返回路径见流程步骤。

**处理流程**：
1. 更新 `context`，值来自 `transaction.validation_context`。
2. 更新 `failures`，值来自 `[]`。
3. 更新 `active`，值来自 `[c for c in transaction.claims if c.tx_to is None]`。
4. 检查 `active and (context is None or context.policy_version != 'validation-v1')`；按条件分流，else 分支不存在。
5. 遍历 `active`，逐项处理 `claim`。
6. 检查 `failures`；按条件分流，else 分支不存在。

**关键条件与保护**：
- [service.py:290](../../../../src/governance/validation/service.py#L290)：`active and (context is None or context.policy_version != 'validation-v1')`，不满足时跳过本分支。
- [service.py:296](../../../../src/governance/validation/service.py#L296)：`output_schema is None or sid != canonical_hash(output_schema.model_dump(mode='json'))`，不满足时跳过本分支。
- [service.py:306](../../../../src/governance/validation/service.py#L306)：`relation is None`，不满足时跳过本分支。
- [service.py:308](../../../../src/governance/validation/service.py#L308)：`subject is None or not subject.active or (claim.object_entity_id and (obj is None or not obj.active))`，不满足时跳过本分支。
- [service.py:314](../../../../src/governance/validation/service.py#L314)：`subject and subject.entity_type not in known_types or (obj and obj.entity_type not in known_types)`，不满足时跳过本分支。
- [service.py:321](../../../../src/governance/validation/service.py#L321)：`relation and subject and relation.domain and (subject.entity_type not in relation.domain)`，不满足时跳过本分支。
- [service.py:328](../../../../src/governance/validation/service.py#L328)：`relation and relation.range and (obj is None or obj.entity_type not in relation.range)`，不满足时跳过本分支。
- [service.py:334](../../../../src/governance/validation/service.py#L334)：`not claim.evidence_ids`，不满足时跳过本分支。
- [service.py:338](../../../../src/governance/validation/service.py#L338)：`ref is None or ref.document_id not in document_ids`，不满足时有 else 分支。
- [service.py:340](../../../../src/governance/validation/service.py#L340)：`evidence_store is None`，不满足时有 else 分支。
- [service.py:342](../../../../src/governance/validation/service.py#L342)：`not await evidence_store.verify(eid) or await evidence_store.get(eid) != ref`，不满足时有 else 分支。
- [service.py:344](../../../../src/governance/validation/service.py#L344)：`self.location_error(ref)`，不满足时有 else 分支。
- 另有 3 个条件判断，参见源码；不要将本列表当作全部分支。

**调用与被调用**：
- `GraphIntegrityError`（调用点 [service.py:291](../../../../src/governance/validation/service.py#L291)）→ [GraphIntegrityError](../../core/errors.md)，静态可定位。
- `context.claim_schema_ids.get`（[service.py:294](../../../../src/governance/validation/service.py#L294)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `context.schemas.get`（[service.py:295](../../../../src/governance/validation/service.py#L295)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `canonical_hash`（调用点 [service.py:296](../../../../src/governance/validation/service.py#L296)）→ [canonical_hash](../../core/ids.md)，静态可定位。
- `output_schema.model_dump`（[service.py:297](../../../../src/governance/validation/service.py#L297)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `failures.append`（[service.py:299](../../../../src/governance/validation/service.py#L299)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `SchemaIndex`（[service.py:301](../../../../src/governance/validation/service.py#L301)）：来自 `src.domain.SchemaIndex`；具体实现可能由依赖注入或运行时分派决定。
- `index.relation_by_id`（[service.py:302](../../../../src/governance/validation/service.py#L302)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `entities.get`（[service.py:303](../../../../src/governance/validation/service.py#L303)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `evidence.get`（[service.py:337](../../../../src/governance/validation/service.py#L337)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `evidence_store.verify`（[service.py:342](../../../../src/governance/validation/service.py#L342)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `evidence_store.get`（[service.py:342](../../../../src/governance/validation/service.py#L342)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `self.location_error`（调用点 [service.py:344](../../../../src/governance/validation/service.py#L344)）→ [ValidationService.location_error](service.md)，静态可定位。
- `context.document_asset_ids.get`（[service.py:349](../../../../src/governance/validation/service.py#L349)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `self.physical_location_error`（调用点 [service.py:352](../../../../src/governance/validation/service.py#L352)）→ [ValidationService.physical_location_error](service.md)，静态可定位。
- `<字符串常量>.join`（[service.py:355](../../../../src/governance/validation/service.py#L355)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `sorted`（[service.py:355](../../../../src/governance/validation/service.py#L355)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `set`（[service.py:355](../../../../src/governance/validation/service.py#L355)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `len`（[service.py:356](../../../../src/governance/validation/service.py#L356)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- 静态扫描未定位直接调用方；可能通过路由注册、LangGraph 节点、协议方法或依赖注入动态调用，不据此判断为死代码。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：`GraphIntegrityError(<字符串常量>)`、`GraphIntegrityError(f<字符串常量>)`。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。


---
