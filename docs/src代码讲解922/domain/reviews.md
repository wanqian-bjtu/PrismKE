源码：[reviews.py:1](../../../src/domain/reviews.py#L1) | 基准：`dev/v0.10@f2f34d7` | 本文件符号数：3

**模块职责**：Immutable review history and optimistic correction contracts.
**在系统中的位置**：文档、知识、Schema、运行、审核、校验、案例等结构化领域契约。
**直接依赖**：无显式项目内模块导入；外部/标准库：`datetime`、`pydantic`、`typing`。
**主要调用方（静态导入）**：[domain/__init__.py](__init__.md)、[domain/knowledge.py](knowledge.md)、[persistence/reviews.py](../persistence/reviews.md)、[workflow/corrections.py](../workflow/corrections.md)、[workflow/reviews.py](../workflow/reviews.md)。
**阅读提示**：下列流程根据当前源码控制流整理；`self`/接口对象的实际类型可能在运行时注入，未能静态解析的调用会明确标注。链接指向源码行或对应讲解文件。

---

# ReviewEvent ⭐⭐⭐⭐

**位置与等级**：[reviews.py:9](../../../src/domain/reviews.py#L9)；承担主要 Agent、应用服务或审核/执行入口，跨模块影响显著。

**职责**：Pydantic 领域/接口模型；实例创建时按字段类型和验证器约束数据。基类：`BaseModel`。

**字段与类级约束**：
- `model_config`：类级默认或常量，取值由 `ConfigDict(frozen=True)` 决定。
- `id`：`str`。
- `request_id`：`str`。
- `run_id`：`str`。
- `task_id`：`str`。
- `kind`：`Literal['entity', 'claim']`。
- `action`：`Literal['link', 'create', 'approve', 'reject', 'defer', 'commit_correction']`。
- `version`：`int`；默认 `Field(ge=1)`。
- `reviewer`：`str`；默认 `Field(min_length=1)`。
- `reason`：`str`；默认 `''`。
- `before`：`dict[str, Any]`。
- `after`：`dict[str, Any]`。
- `supersedes_event_id`：`str | None`；默认 `None`。
- `correction_id`：`str | None`；默认 `None`。
- `created_at`：`datetime`；默认 `Field(default_factory=lambda: datetime.now(UTC))`。

**内部成员**：此类未直接定义方法；字段/继承行为见源码。


---

# CorrectionGuard ⭐⭐⭐

**位置与等级**：[reviews.py:27](../../../src/domain/reviews.py#L27)；关键支撑逻辑，影响候选、证据或接口的正确传递。

**职责**：Pydantic 领域/接口模型；实例创建时按字段类型和验证器约束数据。基类：`BaseModel`。

**字段与类级约束**：
- `source_event_id`：`str`。
- `reviewer`：`str`；默认 `Field(min_length=1)`。
- `reason`：`str`；默认 `Field(min_length=1)`。
- `expected_resources`：`dict[str, str | None]`。

**内部成员**：此类未直接定义方法；字段/继承行为见源码。


---

# ReviewCorrection ⭐⭐⭐⭐

**位置与等级**：[reviews.py:34](../../../src/domain/reviews.py#L34)；承担主要 Agent、应用服务或审核/执行入口，跨模块影响显著。

**职责**：Pydantic 领域/接口模型；实例创建时按字段类型和验证器约束数据。基类：`BaseModel`。

**字段与类级约束**：
- `id`：`str`。
- `run_id`：`str`。
- `source_event_id`：`str`。
- `task_id`：`str`。
- `kind`：`Literal['entity', 'claim']`。
- `action`：`Literal['link', 'create', 'approve', 'reject']`。
- `selected_entity_id`：`str | None`；默认 `None`。
- `expected_version`：`int`。
- `reviewer`：`str`；默认 `Field(min_length=1)`。
- `reason`：`str`；默认 `Field(min_length=1)`。
- `parent_revision_id`：`str | None`。
- `affected_claim_ids`：`list[str]`；默认 `Field(default_factory=list)`。
- `blocked_reasons`：`list[str]`；默认 `Field(default_factory=list)`。
- `preview`：`dict[str, Any]`；默认 `Field(default_factory=dict)`。
- `created_at`：`datetime`；默认 `Field(default_factory=lambda: datetime.now(UTC))`。

**内部成员**：此类未直接定义方法；字段/继承行为见源码。


---
