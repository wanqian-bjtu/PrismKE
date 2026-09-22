源码：[agents.py:1](../../../src/domain/agents.py#L1) | 基准：`dev/v0.10@f2f34d7` | 本文件符号数：6

**模块职责**：Structured contracts exchanged by PrismKE's three semantic agents.
**在系统中的位置**：文档、知识、Schema、运行、审核、校验、案例等结构化领域契约。
**直接依赖**：[src.domain.knowledge](knowledge.md)；外部/标准库：`__future__`、`datetime`、`pydantic`、`typing`。
**主要调用方（静态导入）**：[agents/trace.py](../agents/trace.md)、[domain/__init__.py](__init__.md)、[domain/workflow.py](workflow.md)。
**阅读提示**：下列流程根据当前源码控制流整理；`self`/接口对象的实际类型可能在运行时注入，未能静态解析的调用会明确标注。链接指向源码行或对应讲解文件。

---

# AgentHandoff ⭐⭐⭐

**位置与等级**：[agents.py:21](../../../src/domain/agents.py#L21)；关键支撑逻辑，影响候选、证据或接口的正确传递。

**职责**：Pydantic 领域/接口模型；实例创建时按字段类型和验证器约束数据。基类：`BaseModel`。

**字段与类级约束**：
- `id`：`str`。
- `run_id`：`str`。
- `agent`：`AgentRole`。
- `input_ids`：`list[str]`；默认 `Field(default_factory=list)`。
- `output_ids`：`list[str]`；默认 `Field(default_factory=list)`。
- `evidence_ids`：`list[str]`；默认 `Field(default_factory=list)`。
- `issue_ids`：`list[str]`；默认 `Field(default_factory=list)`。
- `review_task_ids`：`list[str]`；默认 `Field(default_factory=list)`。
- `next_action`：`Literal['continue', 'review', 'stop']`；默认 `'continue'`。

**内部成员**：此类未直接定义方法；字段/继承行为见源码。


---

# AgentTrace ⭐⭐⭐

**位置与等级**：[agents.py:33](../../../src/domain/agents.py#L33)；关键支撑逻辑，影响候选、证据或接口的正确传递。

**职责**：Pydantic 领域/接口模型；实例创建时按字段类型和验证器约束数据。基类：`BaseModel`。

**字段与类级约束**：
- `id`：`str`。
- `run_id`：`str`。
- `agent`：`AgentRole`。
- `step`：`str`。
- `selected_tools`：`list[str]`；默认 `Field(default_factory=list)`。
- `decision`：`str`。
- `reason_codes`：`list[str]`；默认 `Field(default_factory=list)`。
- `input_ids`：`list[str]`；默认 `Field(default_factory=list)`。
- `output_ids`：`list[str]`；默认 `Field(default_factory=list)`。
- `model_fingerprint`：`str | None`；默认 `None`。
- `token_usage`：`int | None`；默认 `Field(default=None, ge=0)`。
- `latency_ms`：`float | None`；默认 `Field(default=None, ge=0)`。
- `status`：`Literal['succeeded', 'failed', 'skipped']`；默认 `'succeeded'`。
- `created_at`：`datetime`；默认 `Field(default_factory=utc_now)`。

**内部成员**：此类未直接定义方法；字段/继承行为见源码。


---

# EntityAdviceRequest ⭐⭐⭐

**位置与等级**：[agents.py:50](../../../src/domain/agents.py#L50)；关键支撑逻辑，影响候选、证据或接口的正确传递。

**职责**：输入契约，集中表达调用前需要的字段与约束。基类：`BaseModel`。

**字段与类级约束**：
- `mention`：`EntityMention`。
- `candidates`：`list[EntityCandidate]`。
- `candidate_entities`：`list[CanonicalEntity]`。

**内部成员**：此类未直接定义方法；字段/继承行为见源码。


---

# EntityAdvice ⭐⭐⭐

**位置与等级**：[agents.py:56](../../../src/domain/agents.py#L56)；关键支撑逻辑，影响候选、证据或接口的正确传递。

**职责**：Pydantic 领域/接口模型；实例创建时按字段类型和验证器约束数据。基类：`BaseModel`。

**字段与类级约束**：
- `action`：`Literal['link', 'review', 'nil']`。
- `selected_entity_id`：`str | None`；默认 `None`。
- `reason_code`：`str`。

**内部成员**：此类未直接定义方法；字段/继承行为见源码。


---

# FusionAdviceRequest ⭐⭐⭐

**位置与等级**：[agents.py:62](../../../src/domain/agents.py#L62)；关键支撑逻辑，影响候选、证据或接口的正确传递。

**职责**：输入契约，集中表达调用前需要的字段与约束。基类：`BaseModel`。

**字段与类级约束**：
- `left`：`CandidateClaim`。
- `right`：`CandidateClaim`。

**内部成员**：此类未直接定义方法；字段/继承行为见源码。


---

# FusionAdvice ⭐⭐⭐

**位置与等级**：[agents.py:67](../../../src/domain/agents.py#L67)；关键支撑逻辑，影响候选、证据或接口的正确传递。

**职责**：Pydantic 领域/接口模型；实例创建时按字段类型和验证器约束数据。基类：`BaseModel`。

**字段与类级约束**：
- `decision`：`Literal['support', 'conflict', 'related', 'uncertain']`。
- `reason_code`：`str`。

**内部成员**：此类未直接定义方法；字段/继承行为见源码。


---
