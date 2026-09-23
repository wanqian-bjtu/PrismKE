源码：[models.py:1](../../../src/evaluation/models.py#L1) | 基准：`dev/v0.10@f2f34d7` | 本文件符号数：5

**模块职责**：Evaluation manifest and report models.
**在系统中的位置**：离线评测、预算账本、标注导出及报告；不等于生产工作流。
**直接依赖**：无显式项目内模块导入；外部/标准库：`__future__`、`pydantic`。
**主要调用方（静态导入）**：[evaluation/runner.py](runner.md)。
**阅读提示**：下列流程根据当前源码控制流整理；`self`/接口对象的实际类型可能在运行时注入，未能静态解析的调用会明确标注。链接指向源码行或对应讲解文件。

---

# GoldClaim ⭐⭐⭐

**位置与等级**：[models.py:8](../../../src/evaluation/models.py#L8)；关键支撑逻辑，影响候选、证据或接口的正确传递。

**职责**：Pydantic 领域/接口模型；实例创建时按字段类型和验证器约束数据。基类：`BaseModel`。

**字段与类级约束**：
- `subject`：`str`。
- `relation`：`str`。
- `object`：`str`。

**内部成员**：此类未直接定义方法；字段/继承行为见源码。


---

# EvaluationCase ⭐⭐⭐

**位置与等级**：[models.py:14](../../../src/evaluation/models.py#L14)；关键支撑逻辑，影响候选、证据或接口的正确传递。

**职责**：Pydantic 领域/接口模型；实例创建时按字段类型和验证器约束数据。基类：`BaseModel`。

**字段与类级约束**：
- `id`：`str`。
- `input`：`str`。
- `language`：`str`。
- `scenarios`：`list[str]`；默认 `Field(default_factory=list)`。
- `claims`：`list[GoldClaim]`；默认 `Field(default_factory=list)`。
- `expected_alignment_decisions`：`list[str]`；默认 `Field(default_factory=list)`。
- `expected_localization_levels`：`list[str]`；默认 `Field(default_factory=list)`。

**内部成员**：此类未直接定义方法；字段/继承行为见源码。


---

# EvaluationManifest ⭐⭐⭐

**位置与等级**：[models.py:24](../../../src/evaluation/models.py#L24)；关键支撑逻辑，影响候选、证据或接口的正确传递。

**职责**：Pydantic 领域/接口模型；实例创建时按字段类型和验证器约束数据。基类：`BaseModel`。

**字段与类级约束**：
- `version`：`str`。
- `schema_path`：`str`。
- `cases`：`list[EvaluationCase]`；默认 `Field(min_length=1)`。

**内部成员**：此类未直接定义方法；字段/继承行为见源码。


---

# EvaluationCaseResult ⭐⭐⭐

**位置与等级**：[models.py:30](../../../src/evaluation/models.py#L30)；关键支撑逻辑，影响候选、证据或接口的正确传递。

**职责**：输出契约，供后续节点、API 或报告消费。基类：`BaseModel`。

**字段与类级约束**：
- `id`：`str`。
- `status`：`str`。
- `error`：`str | None`；默认 `None`。
- `claim_true_positive`：`int`；默认 `0`。
- `claim_false_positive`：`int`；默认 `0`。
- `claim_false_negative`：`int`；默认 `0`。
- `entity_true_positive`：`int`；默认 `0`。
- `entity_false_positive`：`int`；默认 `0`。
- `entity_false_negative`：`int`；默认 `0`。
- `evidence_claims`：`int`；默认 `0`。
- `total_claims`：`int`；默认 `0`。
- `valid_bboxes`：`int`；默认 `0`。
- `total_bboxes`：`int`；默认 `0`。
- `alignment_passed`：`bool`；默认 `False`。
- `localization_passed`：`bool`；默认 `False`。
- `provider_calls`：`int`；默认 `0`。
- `unknown_usage_calls`：`int`；默认 `0`。
- `input_tokens`：`int`；默认 `0`。
- `output_tokens`：`int`；默认 `0`。
- `latency_ms`：`float`；默认 `0.0`。
- `estimated_cost_cny`：`float`；默认 `0.0`。

**内部成员**：此类未直接定义方法；字段/继承行为见源码。


---

# EvaluationReport ⭐⭐⭐

**位置与等级**：[models.py:54](../../../src/evaluation/models.py#L54)；关键支撑逻辑，影响候选、证据或接口的正确传递。

**职责**：输出契约，供后续节点、API 或报告消费。基类：`BaseModel`。

**字段与类级约束**：
- `manifest_version`：`str`。
- `requested_model`：`str | None`；默认 `None`。
- `cases`：`list[EvaluationCaseResult]`。
- `completed_cases`：`int`。
- `failed_cases`：`int`。
- `claim_precision`：`float`。
- `claim_recall`：`float`。
- `claim_f1`：`float`。
- `entity_precision`：`float`。
- `entity_recall`：`float`。
- `entity_f1`：`float`。
- `evidence_coverage`：`float`。
- `bbox_validity`：`float`。
- `scenario_pass_rate`：`float`。
- `provider_calls`：`int`。
- `unknown_usage_calls`：`int`；默认 `0`。
- `input_tokens`：`int`。
- `output_tokens`：`int`。
- `latency_ms`：`float`。
- `estimated_cost_cny`：`float`。
- `pricing_note`：`str`；默认 `<字符串常量>`。

**内部成员**：此类未直接定义方法；字段/继承行为见源码。


---
