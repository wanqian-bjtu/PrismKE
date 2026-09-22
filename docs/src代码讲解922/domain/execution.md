源码：[execution.py:1](../../../src/domain/execution.py#L1) | 基准：`dev/v0.10@f2f34d7` | 本文件符号数：6

**模块职责**：Execution metadata is separate from knowledge and review state.
**在系统中的位置**：文档、知识、Schema、运行、审核、校验、案例等结构化领域契约。
**直接依赖**：无显式项目内模块导入；外部/标准库：`datetime`、`pydantic`、`typing`。
**主要调用方（静态导入）**：[api/models.py](../api/models.md)、[domain/__init__.py](__init__.md)、[persistence/execution.py](../persistence/execution.md)、[workflow/execution.py](../workflow/execution.md)。
**阅读提示**：下列流程根据当前源码控制流整理；`self`/接口对象的实际类型可能在运行时注入，未能静态解析的调用会明确标注。链接指向源码行或对应讲解文件。

---

# ExecutionTask ⭐⭐⭐

**位置与等级**：[execution.py:21](../../../src/domain/execution.py#L21)；关键支撑逻辑，影响候选、证据或接口的正确传递。

**职责**：Pydantic 领域/接口模型；实例创建时按字段类型和验证器约束数据。基类：`BaseModel`。

**字段与类级约束**：
- `run_id`：`str`。
- `operation`：`Literal['execute', 'resume', 'confirm']`；默认 `'execute'`。
- `status`：`ExecutionStatus`；默认 `'queued'`。
- `version`：`int`；默认 `0`。
- `attempt`：`int`；默认 `0`。
- `node`：`str`；默认 `'ingest'`。
- `input_hash`：`str`。
- `schema_hash`：`str`。
- `cancel_requested`：`bool`；默认 `False`。
- `operator`：`str | None`；默认 `None`。
- `reason`：`str | None`；默认 `None`。
- `error_code`：`str | None`；默认 `None`。
- `reviewer`：`str | None`；默认 `None`。
- `commit_revision_id`：`str | None`；默认 `None`。
- `commit_applied`：`bool`；默认 `False`。
- `created_at`：`datetime`；默认 `Field(default_factory=lambda: datetime.now(UTC))`。
- `updated_at`：`datetime`；默认 `Field(default_factory=lambda: datetime.now(UTC))`。

**内部成员**：此类未直接定义方法；字段/继承行为见源码。


---

# ExecutionEvent ⭐⭐⭐

**位置与等级**：[execution.py:41](../../../src/domain/execution.py#L41)；关键支撑逻辑，影响候选、证据或接口的正确传递。

**职责**：Pydantic 领域/接口模型；实例创建时按字段类型和验证器约束数据。基类：`BaseModel`。

**字段与类级约束**：
- `sequence`：`int`。
- `run_id`：`str`。
- `version`：`int`。
- `status`：`ExecutionStatus`。
- `node`：`str`。
- `reason`：`str | None`。
- `created_at`：`datetime`。

**内部成员**：此类未直接定义方法；字段/继承行为见源码。


---

# BranchProgress ⭐⭐⭐

**位置与等级**：[execution.py:51](../../../src/domain/execution.py#L51)；关键支撑逻辑，影响候选、证据或接口的正确传递。

**职责**：Pydantic 领域/接口模型；实例创建时按字段类型和验证器约束数据。基类：`BaseModel`。

**字段与类级约束**：
- `branch`：`Literal['text', 'visual', 'ocr', 'commit']`。
- `status`：`Literal['disabled', 'pending', 'running', 'completed', 'failed']`。
- `completed`：`int`；默认 `Field(ge=0)`。
- `total`：`int | None`；默认 `Field(default=None, ge=0)`。
- `current_asset`：`str | None`；默认 `None`。
- `updated_at`：`datetime`。

**内部成员**：此类未直接定义方法；字段/继承行为见源码。


---

# WorkspaceSummary ⭐⭐⭐

**位置与等级**：[execution.py:60](../../../src/domain/execution.py#L60)；关键支撑逻辑，影响候选、证据或接口的正确传递。

**职责**：输出契约，供后续节点、API 或报告消费。基类：`BaseModel`。

**字段与类级约束**：
- `run_counts`：`dict[str, int]`；默认 `Field(default_factory=dict)`。
- `pending_reviews`：`int`；默认 `Field(ge=0)`。
- `blocking_issues`：`int`；默认 `Field(ge=0)`。
- `worker_status`：`str`。
- `graph_health`：`dict[str, Any]`。

**内部成员**：此类未直接定义方法；字段/继承行为见源码。


---

# RequestReconciliation ⭐⭐⭐

**位置与等级**：[execution.py:68](../../../src/domain/execution.py#L68)；关键支撑逻辑，影响候选、证据或接口的正确传递。

**职责**：Pydantic 领域/接口模型；实例创建时按字段类型和验证器约束数据。基类：`BaseModel`。

**字段与类级约束**：
- `request_id`：`str`。
- `outcome`：`Literal['confirmed_not_sent', 'confirmed_not_billed', 'possibly_billed']`。
- `operator`：`str`；默认 `Field(min_length=1)`。
- `reason`：`str`；默认 `Field(min_length=1)`。
- `expected_execution_version`：`int`；默认 `Field(ge=0)`。

**内部成员**：此类未直接定义方法；字段/继承行为见源码。


---

# RequestReconciliationEvent ⭐⭐⭐

**位置与等级**：[execution.py:76](../../../src/domain/execution.py#L76)；关键支撑逻辑，影响候选、证据或接口的正确传递。

**职责**：本模块的对象实现或数据契约；具体语义由字段、基类和方法共同决定。基类：`RequestReconciliation`。

**字段与类级约束**：
- `sequence`：`int`。
- `run_id`：`str`。
- `created_at`：`datetime`。

**内部成员**：此类未直接定义方法；字段/继承行为见源码。


---
