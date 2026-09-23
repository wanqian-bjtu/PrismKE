源码：[knowledge.py:1](../../../src/domain/knowledge.py#L1) | 基准：`dev/v0.10@f2f34d7` | 本文件符号数：25

**模块职责**：Entities, claims, reviews, conflicts, and graph transactions.
**在系统中的位置**：文档、知识、Schema、运行、审核、校验、案例等结构化领域契约。
**直接依赖**：[src.domain.documents](documents.md)、[src.domain.reviews](reviews.md)、[src.domain.validation](validation.md)；外部/标准库：`__future__`、`datetime`、`enum`、`pydantic`、`typing`。
**主要调用方（静态导入）**：[domain/__init__.py](__init__.md)、[domain/agents.py](agents.md)、[domain/cases.py](cases.md)、[domain/workflow.py](workflow.md)。
**阅读提示**：下列流程根据当前源码控制流整理；`self`/接口对象的实际类型可能在运行时注入，未能静态解析的调用会明确标注。链接指向源码行或对应讲解文件。

---

# utc_now ⭐⭐

**位置与等级**：[knowledge.py:16](../../../src/domain/knowledge.py#L16)；局部辅助逻辑，需理解其调用条件与失败传播。

**签名**：`def utc_now() -> datetime`。

**作用**：处理 `utc_now` 对应步骤；下列步骤依据函数体的实际控制流和调用点整理。

**输入与输出**：
- 输入：无业务参数（或仅隐式接收实例）。
- 输出类型：`datetime`；具体返回路径见流程步骤。

**处理流程**：
1. 返回 `datetime.now(UTC)`。

**调用与被调用**：
- `datetime.now`（[knowledge.py:17](../../../src/domain/knowledge.py#L17)）：来自 `datetime.datetime`；具体实现可能由依赖注入或运行时分派决定。
- 静态扫描未定位直接调用方；可能通过路由注册、LangGraph 节点、协议方法或依赖注入动态调用，不据此判断为死代码。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：未见 `raise`；下游异常可能继续上抛。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。


---

# ClaimStatus ⭐⭐⭐

**位置与等级**：[knowledge.py:20](../../../src/domain/knowledge.py#L20)；关键支撑逻辑，影响候选、证据或接口的正确传递。

**职责**：本模块的对象实现或数据契约；具体语义由字段、基类和方法共同决定。基类：`StrEnum`。

**字段与类级约束**：
- `PENDING`：类级默认或常量，取值由 `'pending'` 决定。
- `AUTO_APPROVED`：类级默认或常量，取值由 `'auto_approved'` 决定。
- `REVIEW_REQUIRED`：类级默认或常量，取值由 `'review_required'` 决定。
- `APPROVED`：类级默认或常量，取值由 `'approved'` 决定。
- `REJECTED`：类级默认或常量，取值由 `'rejected'` 决定。

**内部成员**：此类未直接定义方法；字段/继承行为见源码。


---

# ReviewDecision ⭐⭐⭐⭐

**位置与等级**：[knowledge.py:28](../../../src/domain/knowledge.py#L28)；承担主要 Agent、应用服务或审核/执行入口，跨模块影响显著。

**职责**：本模块的对象实现或数据契约；具体语义由字段、基类和方法共同决定。基类：`StrEnum`。

**字段与类级约束**：
- `APPROVE`：类级默认或常量，取值由 `'approve'` 决定。
- `REJECT`：类级默认或常量，取值由 `'reject'` 决定。
- `DEFER`：类级默认或常量，取值由 `'defer'` 决定。

**内部成员**：此类未直接定义方法；字段/继承行为见源码。


---

# EntityMention ⭐⭐⭐

**位置与等级**：[knowledge.py:34](../../../src/domain/knowledge.py#L34)；关键支撑逻辑，影响候选、证据或接口的正确传递。

**职责**：Pydantic 领域/接口模型；实例创建时按字段类型和验证器约束数据。基类：`BaseModel`。

**字段与类级约束**：
- `id`：`str`。
- `name`：`str`。
- `entity_type`：`str`。
- `context`：`str`；默认 `''`。
- `modality`：`Modality`；默认 `Modality.TEXT`。
- `evidence_ids`：`list[str]`；默认 `Field(min_length=1)`。

**内部成员**：此类未直接定义方法；字段/继承行为见源码。


---

# CanonicalEntity ⭐⭐⭐

**位置与等级**：[knowledge.py:43](../../../src/domain/knowledge.py#L43)；关键支撑逻辑，影响候选、证据或接口的正确传递。

**职责**：Pydantic 领域/接口模型；实例创建时按字段类型和验证器约束数据。基类：`BaseModel`。

**字段与类级约束**：
- `id`：`str`。
- `name`：`str`。
- `entity_type`：`str`。
- `aliases`：`list[str]`；默认 `Field(default_factory=list)`。
- `attributes`：`dict[str, Any]`；默认 `Field(default_factory=dict)`。
- `context_summary`：`str | None`；默认 `None`。
- `source_evidence_ids`：`list[str]`；默认 `Field(default_factory=list)`。
- `active`：`bool`；默认 `True`。
- `created_at`：`datetime`；默认 `Field(default_factory=utc_now)`。

**内部成员**：`CanonicalEntity.embedding_source`


---

# CanonicalEntity.embedding_source ⭐⭐

**位置与等级**：[knowledge.py:54](../../../src/domain/knowledge.py#L54)；局部辅助逻辑，需理解其调用条件与失败传播。

**签名**：`def embedding_source(self) -> dict[str, Any]`。

**作用**：处理 `embedding_source` 对应步骤；下列步骤依据函数体的实际控制流和调用点整理。

**输入与输出**：
- 输入：无业务参数（或仅隐式接收实例）。
- 输出类型：`dict[str, Any]`；具体返回路径见流程步骤。

**处理流程**：
1. 返回 `self.model_dump(include={'name', 'aliases', 'entity_type', 'attributes', 'context_summary', 'active'})`。

**调用与被调用**：
- `self.model_dump`（[knowledge.py:55](../../../src/domain/knowledge.py#L55)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- 静态扫描未定位直接调用方；可能通过路由注册、LangGraph 节点、协议方法或依赖注入动态调用，不据此判断为死代码。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：未见 `raise`；下游异常可能继续上抛。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。


---

# CandidateClaim ⭐⭐⭐

**位置与等级**：[knowledge.py:67](../../../src/domain/knowledge.py#L67)；关键支撑逻辑，影响候选、证据或接口的正确传递。

**职责**：Pydantic 领域/接口模型；实例创建时按字段类型和验证器约束数据。基类：`BaseModel`。

**字段与类级约束**：
- `id`：`str`。
- `subject`：`EntityMention`。
- `relation`：`str`。
- `object`：`EntityMention | str`。
- `confidence`：`float`；默认 `Field(ge=0.0, le=1.0)`。
- `evidence_ids`：`list[str]`；默认 `Field(min_length=1)`。
- `qualifiers`：`dict[str, Any]`；默认 `Field(default_factory=dict)`。
- `modalities`：`list[Modality]`；默认 `Field(default_factory=lambda: [Modality.TEXT])`。
- `source_tool`：`str`；默认 `'text_extraction'`。
- `visual_observation_ids`：`list[str]`；默认 `Field(default_factory=list)`。
- `cross_modal_support`：`bool`；默认 `False`。
- `coarse_visual_evidence`：`bool`；默认 `False`。
- `context_only_visual_claim`：`bool`；默认 `False`。
- `uncalibrated_visual_confidence`：`bool`；默认 `False`。

**内部成员**：此类未直接定义方法；字段/继承行为见源码。


---

# AlignmentRecord ⭐⭐⭐

**位置与等级**：[knowledge.py:84](../../../src/domain/knowledge.py#L84)；关键支撑逻辑，影响候选、证据或接口的正确传递。

**职责**：Pydantic 领域/接口模型；实例创建时按字段类型和验证器约束数据。基类：`BaseModel`。

**字段与类级约束**：
- `id`：`str`。
- `candidate_ids`：`list[str]`；默认 `Field(min_length=1)`。
- `modalities`：`list[Modality]`；默认 `Field(min_length=1)`。
- `decision`：`Literal['support', 'conflict', 'related', 'independent']`。
- `confidence_before`：`list[float]`；默认 `Field(default_factory=list)`。
- `confidence_after`：`float | None`；默认 `Field(default=None, ge=0.0, le=1.0)`。
- `reasons`：`list[str]`；默认 `Field(default_factory=list)`。

**内部成员**：此类未直接定义方法；字段/继承行为见源码。


---

# Claim ⭐⭐⭐

**位置与等级**：[knowledge.py:94](../../../src/domain/knowledge.py#L94)；关键支撑逻辑，影响候选、证据或接口的正确传递。

**职责**：Pydantic 领域/接口模型；实例创建时按字段类型和验证器约束数据。基类：`BaseModel`。

**字段与类级约束**：
- `id`：`str`。
- `subject_id`：`str`。
- `relation_id`：`str`。
- `object_entity_id`：`str | None`；默认 `None`。
- `object_literal`：`str | None`；默认 `None`。
- `confidence`：`float`；默认 `Field(ge=0.0, le=1.0)`。
- `status`：`ClaimStatus`；默认 `ClaimStatus.PENDING`。
- `evidence_ids`：`list[str]`；默认 `Field(min_length=1)`。
- `source_candidate_ids`：`list[str]`；默认 `Field(default_factory=list)`。
- `source_run_ids`：`list[str]`；默认 `Field(default_factory=list)`。
- `qualifiers`：`dict[str, Any]`；默认 `Field(default_factory=dict)`。
- `cross_modal_support`：`bool`；默认 `False`。
- `coarse_visual_evidence`：`bool`；默认 `False`。
- `context_only_visual_claim`：`bool`；默认 `False`。
- `uncalibrated_visual_confidence`：`bool`；默认 `False`。
- `valid_from`：`datetime | None`；默认 `None`。
- `valid_to`：`datetime | None`；默认 `None`。
- `tx_from`：`datetime`；默认 `Field(default_factory=utc_now)`。
- `tx_to`：`datetime | None`；默认 `None`。

**内部成员**：`Claim.validate_claim`


---

# Claim.validate_claim ⭐⭐⭐⭐

**位置与等级**：[knowledge.py:116](../../../src/domain/knowledge.py#L116)；承担主要 Agent、应用服务或审核/执行入口，跨模块影响显著。

**签名**：`def validate_claim(self) -> Claim`。

**装饰器/路由**：`model_validator(mode='after')`。

**作用**：处理 `validate_claim` 对应步骤；下列步骤依据函数体的实际控制流和调用点整理。

**输入与输出**：
- 输入：无业务参数（或仅隐式接收实例）。
- 输出类型：`Claim`；具体返回路径见流程步骤。

**处理流程**：
1. 检查 `(self.object_entity_id is None) == (self.object_literal is None)`；按条件分流，else 分支不存在。
2. 检查 `self.valid_from and self.valid_to and (self.valid_from > self.valid_to)`；按条件分流，else 分支不存在。
3. 返回 `self`。

**关键条件与保护**：
- [knowledge.py:117](../../../src/domain/knowledge.py#L117)：`(self.object_entity_id is None) == (self.object_literal is None)`，不满足时跳过本分支。
- [knowledge.py:119](../../../src/domain/knowledge.py#L119)：`self.valid_from and self.valid_to and (self.valid_from > self.valid_to)`，不满足时跳过本分支。

**调用与被调用**：
- `ValueError`（[knowledge.py:118](../../../src/domain/knowledge.py#L118)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `model_validator`（[knowledge.py:115](../../../src/domain/knowledge.py#L115)）：来自 `pydantic.model_validator`；具体实现可能由依赖注入或运行时分派决定。
- 静态扫描未定位直接调用方；可能通过路由注册、LangGraph 节点、协议方法或依赖注入动态调用，不据此判断为死代码。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：`ValueError(<字符串常量>)`。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。


---

# ConflictSet ⭐⭐⭐⭐

**位置与等级**：[knowledge.py:124](../../../src/domain/knowledge.py#L124)；承担主要 Agent、应用服务或审核/执行入口，跨模块影响显著。

**职责**：Pydantic 领域/接口模型；实例创建时按字段类型和验证器约束数据。基类：`BaseModel`。

**字段与类级约束**：
- `id`：`str`。
- `claim_ids`：`list[str]`；默认 `Field(min_length=2)`。
- `reason`：`str`。
- `status`：`Literal['open', 'resolved']`；默认 `'open'`。

**内部成员**：此类未直接定义方法；字段/继承行为见源码。


---

# ReviewTask ⭐⭐⭐⭐

**位置与等级**：[knowledge.py:131](../../../src/domain/knowledge.py#L131)；承担主要 Agent、应用服务或审核/执行入口，跨模块影响显著。

**职责**：Pydantic 领域/接口模型；实例创建时按字段类型和验证器约束数据。基类：`BaseModel`。

**字段与类级约束**：
- `id`：`str`。
- `run_id`：`str`。
- `claim_id`：`str`。
- `reasons`：`list[str]`；默认 `Field(min_length=1)`。
- `status`：`Literal['pending', 'resolved']`；默认 `'pending'`。
- `decision`：`ReviewDecision | None`；默认 `None`。
- `created_at`：`datetime`；默认 `Field(default_factory=utc_now)`。
- `resolved_at`：`datetime | None`；默认 `None`。
- `reviewer`：`str | None`；默认 `None`。
- `review_comment`：`str | None`；默认 `None`。
- `version`：`int`；默认 `0`。
- `last_event_id`：`str | None`；默认 `None`。

**内部成员**：此类未直接定义方法；字段/继承行为见源码。


---

# EntityCandidate ⭐⭐⭐

**位置与等级**：[knowledge.py:146](../../../src/domain/knowledge.py#L146)；关键支撑逻辑，影响候选、证据或接口的正确传递。

**职责**：Pydantic 领域/接口模型；实例创建时按字段类型和验证器约束数据。基类：`BaseModel`。

**字段与类级约束**：
- `entity_id`：`str`。
- `retrieval_score`：`float`；默认 `Field(ge=-1.0, le=1.0)`。
- `name_score`：`float`；默认 `Field(ge=0.0, le=1.0)`。
- `semantic_name_score`：`float | None`；默认 `Field(default=None, ge=-1.0, le=1.0)`。
- `context_score`：`float`；默认 `Field(ge=-1.0, le=1.0)`。
- `neighborhood_score`：`float`；默认 `Field(default=0.0, ge=0.0, le=1.0)`。
- `final_score`：`float`；默认 `Field(ge=0.0, le=1.0)`。
- `reasons`：`list[str]`；默认 `Field(default_factory=list)`。

**内部成员**：此类未直接定义方法；字段/继承行为见源码。


---

# EntityResolutionDecision ⭐⭐⭐

**位置与等级**：[knowledge.py:157](../../../src/domain/knowledge.py#L157)；关键支撑逻辑，影响候选、证据或接口的正确传递。

**职责**：Pydantic 领域/接口模型；实例创建时按字段类型和验证器约束数据。基类：`BaseModel`。

**字段与类级约束**：
- `mention_id`：`str`。
- `candidates`：`list[EntityCandidate]`；默认 `Field(default_factory=list)`。
- `selected_entity_id`：`str | None`；默认 `None`。
- `method`：`Literal['exact', 'vector', 'review', 'nil']`。
- `confidence`：`float`；默认 `Field(ge=0.0, le=1.0)`。
- `margin`：`float | None`；默认 `None`。
- `requires_review`：`bool`；默认 `False`。
- `advised_entity_id`：`str | None`；默认 `None`。
- `advised_action`：`Literal['link', 'review', 'nil'] | None`；默认 `None`。
- `reasons`：`list[str]`；默认 `Field(default_factory=list)`。

**内部成员**：此类未直接定义方法；字段/继承行为见源码。


---

# EntityEmbedding ⭐⭐⭐

**位置与等级**：[knowledge.py:170](../../../src/domain/knowledge.py#L170)；关键支撑逻辑，影响候选、证据或接口的正确传递。

**职责**：Pydantic 领域/接口模型；实例创建时按字段类型和验证器约束数据。基类：`BaseModel`。

**字段与类级约束**：
- `entity_id`：`str`。
- `model_fingerprint`：`str`。
- `text_hash`：`str`。
- `dimension`：`int`；默认 `Field(gt=0)`。
- `vector`：`list[float]`；默认 `Field(min_length=1)`。

**内部成员**：`EntityEmbedding.validate_dimension`


---

# EntityEmbedding.validate_dimension ⭐⭐⭐⭐

**位置与等级**：[knowledge.py:178](../../../src/domain/knowledge.py#L178)；承担主要 Agent、应用服务或审核/执行入口，跨模块影响显著。

**签名**：`def validate_dimension(self) -> EntityEmbedding`。

**装饰器/路由**：`model_validator(mode='after')`。

**作用**：处理 `validate_dimension` 对应步骤；下列步骤依据函数体的实际控制流和调用点整理。

**输入与输出**：
- 输入：无业务参数（或仅隐式接收实例）。
- 输出类型：`EntityEmbedding`；具体返回路径见流程步骤。

**处理流程**：
1. 检查 `len(self.vector) != self.dimension`；按条件分流，else 分支不存在。
2. 返回 `self`。

**关键条件与保护**：
- [knowledge.py:179](../../../src/domain/knowledge.py#L179)：`len(self.vector) != self.dimension`，不满足时跳过本分支。

**调用与被调用**：
- `len`（[knowledge.py:179](../../../src/domain/knowledge.py#L179)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `ValueError`（[knowledge.py:180](../../../src/domain/knowledge.py#L180)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `model_validator`（[knowledge.py:177](../../../src/domain/knowledge.py#L177)）：来自 `pydantic.model_validator`；具体实现可能由依赖注入或运行时分派决定。
- 静态扫描未定位直接调用方；可能通过路由注册、LangGraph 节点、协议方法或依赖注入动态调用，不据此判断为死代码。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：`ValueError(<字符串常量>)`。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。


---

# EntityReviewTask ⭐⭐⭐⭐

**位置与等级**：[knowledge.py:184](../../../src/domain/knowledge.py#L184)；承担主要 Agent、应用服务或审核/执行入口，跨模块影响显著。

**职责**：Pydantic 领域/接口模型；实例创建时按字段类型和验证器约束数据。基类：`BaseModel`。

**字段与类级约束**：
- `id`：`str`。
- `run_id`：`str`。
- `mention_id`：`str | None`；默认 `None`。
- `operation_id`：`str | None`；默认 `None`。
- `task_type`：`Literal['link', 'deduplicate', 'merge', 'split']`。
- `candidates`：`list[EntityCandidate]`；默认 `Field(default_factory=list)`。
- `reasons`：`list[str]`；默认 `Field(min_length=1)`。
- `status`：`Literal['pending', 'resolved']`；默认 `'pending'`。
- `decision`：`Literal['link', 'create', 'approve', 'reject', 'defer'] | None`；默认 `None`。
- `selected_entity_id`：`str | None`；默认 `None`。
- `proposed_entity_id`：`str | None`；默认 `None`。
- `advised_entity_id`：`str | None`；默认 `None`。
- `advised_action`：`Literal['link', 'review', 'nil'] | None`；默认 `None`。
- `created_at`：`datetime`；默认 `Field(default_factory=utc_now)`。
- `resolved_at`：`datetime | None`；默认 `None`。
- `reviewer`：`str | None`；默认 `None`。
- `review_comment`：`str | None`；默认 `None`。
- `version`：`int`；默认 `0`。
- `last_event_id`：`str | None`；默认 `None`。

**内部成员**：此类未直接定义方法；字段/继承行为见源码。


---

# EntityOperation ⭐⭐⭐

**位置与等级**：[knowledge.py:207](../../../src/domain/knowledge.py#L207)；关键支撑逻辑，影响候选、证据或接口的正确传递。

**职责**：Pydantic 领域/接口模型；实例创建时按字段类型和验证器约束数据。基类：`BaseModel`。

**字段与类级约束**：
- `id`：`str`。
- `operation_type`：`Literal['merge', 'split']`。
- `source_entity_ids`：`list[str]`；默认 `Field(min_length=1)`。
- `target_entity_ids`：`list[str]`；默认 `Field(default_factory=list)`。
- `affected_claim_ids`：`list[str]`；默认 `Field(default_factory=list)`。
- `before`：`dict[str, Any]`；默认 `Field(default_factory=dict)`。
- `after`：`dict[str, Any]`；默认 `Field(default_factory=dict)`。
- `reasons`：`list[str]`；默认 `Field(min_length=1)`。
- `evidence_ids`：`list[str]`；默认 `Field(default_factory=list)`。
- `status`：`Literal['pending', 'approved', 'rejected', 'applied', 'rolled_back']`；默认 `'pending'`。
- `reviewer`：`str | None`；默认 `None`。
- `reviewed_at`：`datetime | None`；默认 `None`。

**内部成员**：此类未直接定义方法；字段/继承行为见源码。


---

# GraphDocument ⭐⭐⭐

**位置与等级**：[knowledge.py:222](../../../src/domain/knowledge.py#L222)；关键支撑逻辑，影响候选、证据或接口的正确传递。

**职责**：Pydantic 领域/接口模型；实例创建时按字段类型和验证器约束数据。基类：`BaseModel`。
**源码说明**：Portable document metadata stored in a graph backend.

**字段与类级约束**：
- `id`：`str`。
- `filename`：`str`。
- `content_hash`：`str`。
- `media_type`：`str`。
- `imported_at`：`datetime`；默认 `Field(default_factory=utc_now)`。

**内部成员**：此类未直接定义方法；字段/继承行为见源码。


---

# GraphChange ⭐⭐⭐

**位置与等级**：[knowledge.py:232](../../../src/domain/knowledge.py#L232)；关键支撑逻辑，影响候选、证据或接口的正确传递。

**职责**：Pydantic 领域/接口模型；实例创建时按字段类型和验证器约束数据。基类：`BaseModel`。

**字段与类级约束**：
- `resource_type`：`Literal['entity', 'claim', 'conflict', 'entity_operation']`。
- `resource_id`：`str`。
- `action`：`Literal['create', 'update', 'close', 'restore']`。
- `before`：`dict[str, Any] | None`；默认 `None`。
- `after`：`dict[str, Any] | None`；默认 `None`。

**内部成员**：此类未直接定义方法；字段/继承行为见源码。


---

# GraphRevision ⭐⭐⭐

**位置与等级**：[knowledge.py:240](../../../src/domain/knowledge.py#L240)；关键支撑逻辑，影响候选、证据或接口的正确传递。

**职责**：Pydantic 领域/接口模型；实例创建时按字段类型和验证器约束数据。基类：`BaseModel`。

**字段与类级约束**：
- `id`：`str`。
- `run_id`：`str`。
- `parent_id`：`str | None`；默认 `None`。
- `entity_ids`：`list[str]`；默认 `Field(default_factory=list)`。
- `claim_ids`：`list[str]`；默认 `Field(default_factory=list)`。
- `conflict_ids`：`list[str]`；默认 `Field(default_factory=list)`。
- `changes`：`list[GraphChange]`；默认 `Field(default_factory=list)`。
- `validation_context`：`CommitValidationContext | None`；默认 `None`。
- `commit_fingerprint`：`str | None`；默认 `None`。
- `review_events`：`list[dict[str, Any]]`；默认 `Field(default_factory=list)`。
- `correction_guard`：`CorrectionGuard | None`；默认 `None`。
- `created_at`：`datetime`；默认 `Field(default_factory=utc_now)`。

**内部成员**：此类未直接定义方法；字段/继承行为见源码。


---

# GraphCommit ⭐⭐⭐

**位置与等级**：[knowledge.py:255](../../../src/domain/knowledge.py#L255)；关键支撑逻辑，影响候选、证据或接口的正确传递。

**职责**：Pydantic 领域/接口模型；实例创建时按字段类型和验证器约束数据。基类：`BaseModel`。

**字段与类级约束**：
- `documents`：`list[GraphDocument]`；默认 `Field(default_factory=list)`。
- `evidence`：`list[EvidenceRef]`；默认 `Field(default_factory=list)`。
- `entities`：`list[CanonicalEntity]`；默认 `Field(default_factory=list)`。
- `claims`：`list[Claim]`；默认 `Field(default_factory=list)`。
- `conflicts`：`list[ConflictSet]`；默认 `Field(default_factory=list)`。
- `entity_operations`：`list[EntityOperation]`；默认 `Field(default_factory=list)`。
- `entity_embeddings`：`list[EntityEmbedding]`；默认 `Field(default_factory=list)`。
- `revision`：`GraphRevision`。
- `validation_context`：`CommitValidationContext | None`；默认 `None`。
- `correction_guard`：`CorrectionGuard | None`；默认 `None`。

**内部成员**：此类未直接定义方法；字段/继承行为见源码。


---

# GraphHealth ⭐⭐⭐

**位置与等级**：[knowledge.py:268](../../../src/domain/knowledge.py#L268)；关键支撑逻辑，影响候选、证据或接口的正确传递。

**职责**：Pydantic 领域/接口模型；实例创建时按字段类型和验证器约束数据。基类：`BaseModel`。

**字段与类级约束**：
- `backend`：`Literal['json', 'neo4j']`。
- `healthy`：`bool`。
- `message`：`str`；默认 `'ok'`。

**内部成员**：此类未直接定义方法；字段/继承行为见源码。


---

# GraphNeighborhood ⭐⭐⭐

**位置与等级**：[knowledge.py:274](../../../src/domain/knowledge.py#L274)；关键支撑逻辑，影响候选、证据或接口的正确传递。

**职责**：Pydantic 领域/接口模型；实例创建时按字段类型和验证器约束数据。基类：`BaseModel`。

**字段与类级约束**：
- `center_entity_id`：`str`。
- `depth`：`int`；默认 `Field(default=1, ge=1, le=3)`。
- `entities`：`list[CanonicalEntity]`；默认 `Field(default_factory=list)`。
- `claims`：`list[Claim]`；默认 `Field(default_factory=list)`。

**内部成员**：此类未直接定义方法；字段/继承行为见源码。


---

# RevisionDiff ⭐⭐⭐

**位置与等级**：[knowledge.py:281](../../../src/domain/knowledge.py#L281)；关键支撑逻辑，影响候选、证据或接口的正确传递。

**职责**：Pydantic 领域/接口模型；实例创建时按字段类型和验证器约束数据。基类：`BaseModel`。

**字段与类级约束**：
- `from_revision_id`：`str`。
- `to_revision_id`：`str`。
- `changes`：`list[GraphChange]`；默认 `Field(default_factory=list)`。
- `legacy_id_only`：`bool`；默认 `False`。
- `entity_ids`：`list[str]`；默认 `Field(default_factory=list)`。
- `claim_ids`：`list[str]`；默认 `Field(default_factory=list)`。
- `conflict_ids`：`list[str]`；默认 `Field(default_factory=list)`。

**内部成员**：此类未直接定义方法；字段/继承行为见源码。


---
