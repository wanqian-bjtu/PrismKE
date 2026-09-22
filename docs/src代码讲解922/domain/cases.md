源码：[cases.py:1](../../../src/domain/cases.py#L1) | 基准：`dev/v0.10@f2f34d7` | 本文件符号数：7

**模块职责**：Immutable review cases and bounded Reflection contracts.
**在系统中的位置**：文档、知识、Schema、运行、审核、校验、案例等结构化领域契约。
**直接依赖**：[src.domain.knowledge](knowledge.md)、[src.domain.schema](schema.md)、[src.domain.validation](validation.md)；外部/标准库：`__future__`、`datetime`、`pydantic`、`typing`。
**主要调用方（静态导入）**：[domain/__init__.py](__init__.md)、[domain/workflow.py](workflow.md)。
**阅读提示**：下列流程根据当前源码控制流整理；`self`/接口对象的实际类型可能在运行时注入，未能静态解析的调用会明确标注。链接指向源码行或对应讲解文件。

---

# CaseRecord ⭐⭐⭐

**位置与等级**：[cases.py:15](../../../src/domain/cases.py#L15)；关键支撑逻辑，影响候选、证据或接口的正确传递。

**职责**：Pydantic 领域/接口模型；实例创建时按字段类型和验证器约束数据。基类：`BaseModel`。

**字段与类级约束**：
- `model_config`：类级默认或常量，取值由 `ConfigDict(frozen=True)` 决定。
- `id`：`str`。
- `run_id`：`str`。
- `case_type`：`Literal['good', 'bad']`。
- `task_type`：`Literal['entity', 'claim']`。
- `schema_fingerprint`：`str`。
- `language`：`str`。
- `input_summary`：`str`。
- `candidate_snapshot`：`dict[str, Any]`。
- `decision`：`str`。
- `reasons`：`list[str]`；默认 `Field(default_factory=list)`。
- `evidence_ids`：`list[str]`；默认 `Field(default_factory=list)`。
- `source_review_event_id`：`str`。
- `supersedes_case_id`：`str | None`；默认 `None`。
- `created_at`：`datetime`；默认 `Field(default_factory=lambda: datetime.now(UTC))`。

**内部成员**：此类未直接定义方法；字段/继承行为见源码。


---

# CaseStatusEvent ⭐⭐⭐

**位置与等级**：[cases.py:34](../../../src/domain/cases.py#L34)；关键支撑逻辑，影响候选、证据或接口的正确传递。

**职责**：Pydantic 领域/接口模型；实例创建时按字段类型和验证器约束数据。基类：`BaseModel`。

**字段与类级约束**：
- `model_config`：类级默认或常量，取值由 `ConfigDict(frozen=True)` 决定。
- `id`：`str`。
- `case_id`：`str`。
- `action`：`Literal['disable']`。
- `operator`：`str`；默认 `Field(min_length=1)`。
- `reason`：`str`；默认 `Field(min_length=1)`。
- `source_event_id`：`str | None`；默认 `None`。
- `created_at`：`datetime`；默认 `Field(default_factory=lambda: datetime.now(UTC))`。

**内部成员**：此类未直接定义方法；字段/继承行为见源码。


---

# CaseEmbedding ⭐⭐⭐

**位置与等级**：[cases.py:46](../../../src/domain/cases.py#L46)；关键支撑逻辑，影响候选、证据或接口的正确传递。

**职责**：Pydantic 领域/接口模型；实例创建时按字段类型和验证器约束数据。基类：`BaseModel`。

**字段与类级约束**：
- `model_config`：类级默认或常量，取值由 `ConfigDict(frozen=True)` 决定。
- `case_id`：`str`。
- `model_fingerprint`：`str`。
- `text_hash`：`str`。
- `dimension`：`int`；默认 `Field(gt=0)`。
- `vector`：`list[float]`。

**内部成员**：此类未直接定义方法；字段/继承行为见源码。


---

# RetrievedCase ⭐⭐⭐

**位置与等级**：[cases.py:56](../../../src/domain/cases.py#L56)；关键支撑逻辑，影响候选、证据或接口的正确传递。

**职责**：Pydantic 领域/接口模型；实例创建时按字段类型和验证器约束数据。基类：`BaseModel`。

**字段与类级约束**：
- `case_id`：`str`。
- `case_type`：`Literal['good', 'bad']`。
- `task_type`：`Literal['entity', 'claim']`。
- `score`：`float`；默认 `Field(ge=-1.0, le=1.0)`。
- `decision`：`str`。
- `input_summary`：`str`。
- `reasons`：`list[str]`；默认 `Field(default_factory=list)`。
- `evidence_ids`：`list[str]`；默认 `Field(default_factory=list)`。
- `use_location`：`str`。

**内部成员**：此类未直接定义方法；字段/继承行为见源码。


---

# ReflectionRequest ⭐⭐⭐⭐

**位置与等级**：[cases.py:68](../../../src/domain/cases.py#L68)；承担主要 Agent、应用服务或审核/执行入口，跨模块影响显著。

**职责**：输入契约，集中表达调用前需要的字段与约束。基类：`BaseModel`。

**字段与类级约束**：
- `run_id`：`str`。
- `candidate`：`CandidateClaim`。
- `issues`：`list[ValidationIssue]`。
- `retrieved_cases`：`list[RetrievedCase]`；默认 `Field(default_factory=list)`。
- `output_schema`：`OutputSchema`。
- `allowed_evidence_ids`：`list[str]`。
- `attempt`：`int`；默认 `Field(ge=1, le=2)`。
- `remaining_tokens`：`int`；默认 `Field(ge=0)`。

**内部成员**：此类未直接定义方法；字段/继承行为见源码。


---

# ReflectionResult ⭐⭐⭐⭐

**位置与等级**：[cases.py:79](../../../src/domain/cases.py#L79)；承担主要 Agent、应用服务或审核/执行入口，跨模块影响显著。

**职责**：输出契约，供后续节点、API 或报告消费。基类：`BaseModel`。

**字段与类级约束**：
- `candidate`：`CandidateClaim | None`；默认 `None`。
- `raw_response_model`：`str | None`；默认 `None`。
- `input_tokens`：`int | None`；默认 `Field(default=None, ge=0)`。
- `output_tokens`：`int | None`；默认 `Field(default=None, ge=0)`。
- `total_tokens`：`int | None`；默认 `Field(default=None, ge=0)`。
- `latency_ms`：`float`；默认 `Field(default=0.0, ge=0.0)`。
- `request_id`：`str | None`；默认 `None`。
- `warnings`：`list[str]`；默认 `Field(default_factory=list)`。

**内部成员**：此类未直接定义方法；字段/继承行为见源码。


---

# ReflectionAttempt ⭐⭐⭐⭐

**位置与等级**：[cases.py:90](../../../src/domain/cases.py#L90)；承担主要 Agent、应用服务或审核/执行入口，跨模块影响显著。

**职责**：Pydantic 领域/接口模型；实例创建时按字段类型和验证器约束数据。基类：`BaseModel`。

**字段与类级约束**：
- `id`：`str`。
- `run_id`：`str`。
- `candidate_id`：`str`。
- `attempt`：`int`；默认 `Field(ge=1, le=2)`。
- `issue_ids`：`list[str]`。
- `retrieved_case_ids`：`list[str]`。
- `input_candidate`：`dict[str, Any]`。
- `output_candidate`：`dict[str, Any] | None`；默认 `None`。
- `model_fingerprint`：`str`。
- `prompt_version`：`str`。
- `request_id`：`str | None`；默认 `None`。
- `response_model`：`str | None`；默认 `None`。
- `token_usage`：`int | None`；默认 `Field(default=None, ge=0)`。
- `latency_ms`：`float`；默认 `Field(default=0.0, ge=0.0)`。
- `status`：`Literal['succeeded', 'failed', 'rejected_by_validation', 'budget_exhausted', 'unknow…`。
- `error_code`：`str | None`；默认 `None`。
- `warnings`：`list[str]`；默认 `Field(default_factory=list)`。
- `created_at`：`datetime`；默认 `Field(default_factory=lambda: datetime.now(UTC))`。

**内部成员**：此类未直接定义方法；字段/继承行为见源码。


---
