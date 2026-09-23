源码：[validation.py:1](../../../src/domain/validation.py#L1) | 基准：`dev/v0.10@f2f34d7` | 本文件符号数：4

**模块职责**：Portable validation reports, exclusion audit and commit provenance.
**在系统中的位置**：文档、知识、Schema、运行、审核、校验、案例等结构化领域契约。
**直接依赖**：[src.domain.schema](schema.md)；外部/标准库：`datetime`、`pydantic`、`typing`。
**主要调用方（静态导入）**：[domain/__init__.py](__init__.md)、[domain/cases.py](cases.md)、[domain/knowledge.py](knowledge.md)、[domain/workflow.py](workflow.md)。
**阅读提示**：下列流程根据当前源码控制流整理；`self`/接口对象的实际类型可能在运行时注入，未能静态解析的调用会明确标注。链接指向源码行或对应讲解文件。

---

# ValidationIssue ⭐⭐⭐

**位置与等级**：[validation.py:13](../../../src/domain/validation.py#L13)；关键支撑逻辑，影响候选、证据或接口的正确传递。

**职责**：Pydantic 领域/接口模型；实例创建时按字段类型和验证器约束数据。基类：`BaseModel`。

**字段与类级约束**：
- `id`：`str`。
- `code`：`str`。
- `stage`：`Literal['structure', 'schema', 'reference', 'evidence', 'commit']`。
- `target_type`：`Literal['candidate', 'observation', 'claim', 'document', 'conflict']`。
- `target_id`：`str`。
- `field_path`：`str`。
- `severity`：`Literal['warning', 'blocking']`；默认 `'blocking'`。
- `message`：`str`。
- `evidence_ids`：`list[str]`；默认 `Field(default_factory=list)`。
- `allowed_actions`：`list[Literal['exclude']]`；默认 `Field(default=['exclude'])`。
- `candidate_summary`：`dict[str, Any]`；默认 `Field(default_factory=dict)`。
- `status`：`Literal['open', 'excluded', 'repaired']`；默认 `'open'`。

**内部成员**：此类未直接定义方法；字段/继承行为见源码。


---

# ValidationReviewDecision ⭐⭐⭐⭐

**位置与等级**：[validation.py:28](../../../src/domain/validation.py#L28)；承担主要 Agent、应用服务或审核/执行入口，跨模块影响显著。

**职责**：Pydantic 领域/接口模型；实例创建时按字段类型和验证器约束数据。基类：`BaseModel`。

**字段与类级约束**：
- `issue_id`：`str`。
- `action`：`Literal['exclude']`；默认 `'exclude'`。
- `reviewer`：`str`；默认 `Field(min_length=1)`。
- `comment`：`str`；默认 `''`。
- `reviewed_at`：`datetime`；默认 `Field(default_factory=lambda: datetime.now(UTC))`。

**内部成员**：此类未直接定义方法；字段/继承行为见源码。


---

# ValidationResult ⭐⭐⭐

**位置与等级**：[validation.py:36](../../../src/domain/validation.py#L36)；关键支撑逻辑，影响候选、证据或接口的正确传递。

**职责**：输出契约，供后续节点、API 或报告消费。基类：`BaseModel`。

**字段与类级约束**：
- `policy_version`：`str`；默认 `VALIDATION_POLICY_VERSION`。
- `input_fingerprint`：`str`；默认 `''`。
- `issues`：`list[ValidationIssue]`；默认 `Field(default_factory=list)`。
- `passed_count`：`int`；默认 `0`。
- `blocking_count`：`int`；默认 `0`。

**内部成员**：此类未直接定义方法；字段/继承行为见源码。


---

# CommitValidationContext ⭐⭐⭐

**位置与等级**：[validation.py:44](../../../src/domain/validation.py#L44)；关键支撑逻辑，影响候选、证据或接口的正确传递。

**职责**：Pydantic 领域/接口模型；实例创建时按字段类型和验证器约束数据。基类：`BaseModel`。

**字段与类级约束**：
- `policy_version`：`str`；默认 `VALIDATION_POLICY_VERSION`。
- `schemas`：`dict[str, OutputSchema]`；默认 `Field(default_factory=dict)`。
- `claim_schema_ids`：`dict[str, str]`；默认 `Field(default_factory=dict)`。
- `document_asset_ids`：`dict[str, list[str]]`；默认 `Field(default_factory=dict)`。

**内部成员**：此类未直接定义方法；字段/继承行为见源码。


---
