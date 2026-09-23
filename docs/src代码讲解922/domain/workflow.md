源码：[workflow.py:1](../../../src/domain/workflow.py#L1) | 基准：`dev/v0.10@f2f34d7` | 本文件符号数：8

**模块职责**：Provider request contracts and persisted workflow state.
**在系统中的位置**：文档、知识、Schema、运行、审核、校验、案例等结构化领域契约。
**直接依赖**：[src.domain.agents](agents.md)、[src.domain.cases](cases.md)、[src.domain.documents](documents.md)、[src.domain.knowledge](knowledge.md)、[src.domain.schema](schema.md)、[src.domain.validation](validation.md)；外部/标准库：`__future__`、`pydantic`、`typing`。
**主要调用方（静态导入）**：[agents/trace.py](../agents/trace.md)、[domain/__init__.py](__init__.md)。
**阅读提示**：下列流程根据当前源码控制流整理；`self`/接口对象的实际类型可能在运行时注入，未能静态解析的调用会明确标注。链接指向源码行或对应讲解文件。

---

# ExtractionRequest ⭐⭐⭐⭐

**位置与等级**：[workflow.py:34](../../../src/domain/workflow.py#L34)；承担主要 Agent、应用服务或审核/执行入口，跨模块影响显著。

**职责**：输入契约，集中表达调用前需要的字段与约束。基类：`BaseModel`。

**字段与类级约束**：
- `document`：`DocumentIR`。
- `output_schema`：`OutputSchema`；默认 `Field(alias='schema')`。
- `model_config`：类级默认或常量，取值由 `ConfigDict(populate_by_name=True)` 决定。

**内部成员**：此类未直接定义方法；字段/继承行为见源码。


---

# VisualExtractionRequest ⭐⭐⭐⭐

**位置与等级**：[workflow.py:41](../../../src/domain/workflow.py#L41)；承担主要 Agent、应用服务或审核/执行入口，跨模块影响显著。

**职责**：输入契约，集中表达调用前需要的字段与约束。基类：`ExtractionRequest`。

**字段与类级约束**：
- `asset`：`MediaAsset`。
- `ocr_blocks`：`list[TextBlock]`；默认 `Field(default_factory=list)`。

**内部成员**：此类未直接定义方法；字段/继承行为见源码。


---

# ProviderCallRecord ⭐⭐⭐

**位置与等级**：[workflow.py:46](../../../src/domain/workflow.py#L46)；关键支撑逻辑，影响候选、证据或接口的正确传递。

**职责**：Pydantic 领域/接口模型；实例创建时按字段类型和验证器约束数据。基类：`BaseModel`。
**源码说明**：Sanitized metadata for one external model request.

**字段与类级约束**：
- `id`：`str`。
- `provider`：`Literal['llm', 'vlm', 'governance', 'fusion']`。
- `operation_id`：`str`。
- `requested_model`：`str`。
- `response_model`：`str | None`；默认 `None`。
- `request_id`：`str | None`；默认 `None`。
- `input_tokens`：`int | None`；默认 `Field(default=None, ge=0)`。
- `output_tokens`：`int | None`；默认 `Field(default=None, ge=0)`。
- `total_tokens`：`int | None`；默认 `Field(default=None, ge=0)`。
- `latency_ms`：`float`；默认 `Field(ge=0.0)`。
- `retry_count`：`int`；默认 `Field(default=0, ge=0)`。
- `status`：`Literal['succeeded', 'failed']`。
- `error_code`：`str | None`；默认 `None`。
- `prompt_version`：`str`。
- `estimated_cost_cny`：`float | None`；默认 `Field(default=None, ge=0.0)`。
- `pricing_snapshot`：`str | None`；默认 `None`。

**内部成员**：此类未直接定义方法；字段/继承行为见源码。


---

# ExtractionResult ⭐⭐⭐⭐

**位置与等级**：[workflow.py:67](../../../src/domain/workflow.py#L67)；承担主要 Agent、应用服务或审核/执行入口，跨模块影响显著。

**职责**：输出契约，供后续节点、API 或报告消费。基类：`BaseModel`。

**字段与类级约束**：
- `candidates`：`list[CandidateClaim]`；默认 `Field(default_factory=list)`。
- `observations`：`list[VisualObservation]`；默认 `Field(default_factory=list)`。
- `evidence`：`list[EvidenceRef]`；默认 `Field(default_factory=list)`。
- `warnings`：`list[str]`；默认 `Field(default_factory=list)`。
- `call_records`：`list[ProviderCallRecord]`；默认 `Field(default_factory=list)`。
- `validation`：`ValidationResult`；默认 `Field(default_factory=ValidationResult)`。

**内部成员**：此类未直接定义方法；字段/继承行为见源码。


---

# OCRRequest ⭐⭐⭐

**位置与等级**：[workflow.py:76](../../../src/domain/workflow.py#L76)；关键支撑逻辑，影响候选、证据或接口的正确传递。

**职责**：输入契约，集中表达调用前需要的字段与约束。基类：`BaseModel`。

**字段与类级约束**：
- `document`：`DocumentIR`。

**内部成员**：此类未直接定义方法；字段/继承行为见源码。


---

# OCRResult ⭐⭐⭐

**位置与等级**：[workflow.py:80](../../../src/domain/workflow.py#L80)；关键支撑逻辑，影响候选、证据或接口的正确传递。

**职责**：输出契约，供后续节点、API 或报告消费。基类：`BaseModel`。

**字段与类级约束**：
- `text_blocks`：`list[TextBlock]`；默认 `Field(default_factory=list)`。
- `evidence`：`list[EvidenceRef]`；默认 `Field(default_factory=list)`。
- `warnings`：`list[str]`；默认 `Field(default_factory=list)`。

**内部成员**：此类未直接定义方法；字段/继承行为见源码。


---

# ResolutionDecision ⭐⭐⭐

**位置与等级**：[workflow.py:86](../../../src/domain/workflow.py#L86)；关键支撑逻辑，影响候选、证据或接口的正确传递。

**职责**：Pydantic 领域/接口模型；实例创建时按字段类型和验证器约束数据。基类：`BaseModel`。

**字段与类级约束**：
- `mention_id`：`str`。
- `entity`：`CanonicalEntity`。
- `method`：`str`。
- `confidence`：`float`；默认 `Field(ge=0.0, le=1.0)`。
- `requires_review`：`bool`；默认 `False`。

**内部成员**：此类未直接定义方法；字段/继承行为见源码。


---

# WorkflowState ⭐⭐⭐

**位置与等级**：[workflow.py:94](../../../src/domain/workflow.py#L94)；关键支撑逻辑，影响候选、证据或接口的正确传递。

**职责**：Pydantic 领域/接口模型；实例创建时按字段类型和验证器约束数据。基类：`BaseModel`。

**字段与类级约束**：
- `model_config`：类级默认或常量，取值由 `ConfigDict(arbitrary_types_allowed=True, populate_by_name=True)` 决定。
- `original_candidates`：`list[CandidateClaim]`；默认 `Field(default_factory=list)`。
- `superseded_review_tasks`：`list[ReviewTask]`；默认 `Field(default_factory=list)`。
- `review_sync_pending`：`bool`；默认 `False`。
- `pending_correction_id`：`str | None`；默认 `None`。
- `correction_tail_only`：`bool`；默认 `False`。
- `run_id`：`str`。
- `input_path`：`str`。
- `schema_path`：`str`。
- `provider_name`：`str`；默认 `'mock'`。
- `provider_fingerprint`：`str`；默认 `'legacy'`。
- `ocr_provider_name`：`str`；默认 `'disabled'`。
- `ocr_provider_fingerprint`：`str`；默认 `'disabled'`。
- `vlm_provider_name`：`str`；默认 `'disabled'`。
- `vlm_provider_fingerprint`：`str`；默认 `'disabled'`。
- `embedding_provider_name`：`str`；默认 `'disabled'`。
- `embedding_provider_fingerprint`：`str`；默认 `'disabled'`。
- `case_mode`：`Literal['none', 'good', 'good_bad']`；默认 `'none'`。
- `case_snapshot_fingerprint`：`str`；默认 `'cases:disabled'`。
- `case_snapshot_ids`：`list[str]`；默认 `Field(default_factory=list)`。
- `case_retrieval_policy_version`：`str | None`；默认 `None`。
- `reflection_enabled`：`bool`；默认 `False`。
- `reflection_provider_name`：`str`；默认 `'disabled'`。
- `reflection_provider_fingerprint`：`str`；默认 `'reflection:disabled'`。
- `reflection_policy_version`：`str | None`；默认 `None`。
- `reflection_max_attempts`：`int`；默认 `0`。
- `reflection_token_budget`：`int`；默认 `0`。
- `reflection_time_budget_seconds`：`float`；默认 `0.0`。
- `allow_remote_assets`：`bool`；默认 `False`。
- `pipeline_version`：`str`；默认 `'0.4.0'`。
- `entity_resolution_policy_version`：`str | None`；默认 `None`。
- `current_node`：`str`；默认 `'ingest'`。
- `failed_node`：`str | None`；默认 `None`。
- `status`：`Literal['running', 'awaiting_review', 'completed', 'failed']`；默认 `'running'`。
- `document`：`DocumentIR | None`；默认 `None`。

**内部成员**：此类未直接定义方法；字段/继承行为见源码。


---
