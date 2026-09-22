源码：[models.py:1](../../../src/api/models.py#L1) | 基准：`dev/v0.10@f2f34d7` | 本文件符号数：14

**模块职责**：Public HTTP request and response models.
**在系统中的位置**：FastAPI 路由和请求/响应模型；负责参数解析、调用应用服务与 HTTP 错误映射。
**直接依赖**：[src.domain](../domain/__init__.md)、[src.domain.execution](../domain/execution.md)；外部/标准库：`__future__`、`pydantic`、`typing`。
**主要调用方（静态导入）**：[api/app.py](app.md)。
**阅读提示**：下列流程根据当前源码控制流整理；`self`/接口对象的实际类型可能在运行时注入，未能静态解析的调用会明确标注。链接指向源码行或对应讲解文件。

---

# RunAccepted ⭐⭐⭐⭐

**位置与等级**：[models.py:13](../../../src/api/models.py#L13)；承担主要 Agent、应用服务或审核/执行入口，跨模块影响显著。

**职责**：Pydantic 领域/接口模型；实例创建时按字段类型和验证器约束数据。基类：`BaseModel`。

**字段与类级约束**：
- `run_id`：`str`。
- `status`：`str`。
- `created`：`bool`。
- `execution`：`dict[str, object] | None`；默认 `None`。

**内部成员**：此类未直接定义方法；字段/继承行为见源码。


---

# CancelRequest ⭐⭐⭐

**位置与等级**：[models.py:20](../../../src/api/models.py#L20)；关键支撑逻辑，影响候选、证据或接口的正确传递。

**职责**：输入契约，集中表达调用前需要的字段与约束。基类：`BaseModel`。

**字段与类级约束**：
- `operator`：`str`；默认 `Field(min_length=1)`。
- `reason`：`str`；默认 `Field(min_length=1)`。
- `request_id`：`str`；默认 `Field(min_length=1)`。
- `expected_version`：`int`；默认 `Field(ge=0)`。

**内部成员**：此类未直接定义方法；字段/继承行为见源码。


---

# ResumeRequest ⭐⭐⭐⭐

**位置与等级**：[models.py:27](../../../src/api/models.py#L27)；承担主要 Agent、应用服务或审核/执行入口，跨模块影响显著。

**职责**：输入契约，集中表达调用前需要的字段与约束。基类：`BaseModel`。

**字段与类级约束**：
- `expected_version`：`int | None`；默认 `Field(default=None, ge=0)`。

**内部成员**：此类未直接定义方法；字段/继承行为见源码。


---

# ReviewRequest ⭐⭐⭐⭐

**位置与等级**：[models.py:31](../../../src/api/models.py#L31)；承担主要 Agent、应用服务或审核/执行入口，跨模块影响显著。

**职责**：输入契约，集中表达调用前需要的字段与约束。基类：`BaseModel`。

**字段与类级约束**：
- `decision`：`ReviewDecision`。
- `reviewer`：`str | None`；默认 `None`。
- `comment`：`str | None`；默认 `None`。
- `expected_version`：`int | None`；默认 `Field(default=None, ge=0)`。
- `request_id`：`str | None`；默认 `None`。

**内部成员**：此类未直接定义方法；字段/继承行为见源码。


---

# RollbackRequest ⭐⭐⭐

**位置与等级**：[models.py:39](../../../src/api/models.py#L39)；关键支撑逻辑，影响候选、证据或接口的正确传递。

**职责**：输入契约，集中表达调用前需要的字段与约束。基类：`BaseModel`。

**字段与类级约束**：
- `confirm`：`Literal[True]`。

**内部成员**：此类未直接定义方法；字段/继承行为见源码。


---

# ValidationExcludeRequest ⭐⭐⭐

**位置与等级**：[models.py:43](../../../src/api/models.py#L43)；关键支撑逻辑，影响候选、证据或接口的正确传递。

**职责**：输入契约，集中表达调用前需要的字段与约束。基类：`BaseModel`。

**字段与类级约束**：
- `reviewer`：`str`；默认 `Field(min_length=1)`。
- `comment`：`str`；默认 `''`。

**内部成员**：此类未直接定义方法；字段/继承行为见源码。


---

# EntityReviewRequest ⭐⭐⭐⭐

**位置与等级**：[models.py:48](../../../src/api/models.py#L48)；承担主要 Agent、应用服务或审核/执行入口，跨模块影响显著。

**职责**：输入契约，集中表达调用前需要的字段与约束。基类：`BaseModel`。

**字段与类级约束**：
- `action`：`Literal['link', 'create', 'approve', 'reject', 'defer']`。
- `run_id`：`str | None`；默认 `None`。
- `selected_entity_id`：`str | None`；默认 `None`。
- `reviewer`：`str | None`；默认 `None`。
- `comment`：`str | None`；默认 `None`。
- `expected_version`：`int | None`；默认 `Field(default=None, ge=0)`。
- `request_id`：`str | None`；默认 `None`。

**内部成员**：此类未直接定义方法；字段/继承行为见源码。


---

# CorrectionRequest ⭐⭐⭐

**位置与等级**：[models.py:58](../../../src/api/models.py#L58)；关键支撑逻辑，影响候选、证据或接口的正确传递。

**职责**：输入契约，集中表达调用前需要的字段与约束。基类：`BaseModel`。

**字段与类级约束**：
- `source_event_id`：`str`。
- `action`：`Literal['link', 'create', 'approve', 'reject']`。
- `selected_entity_id`：`str | None`；默认 `None`。
- `expected_version`：`int`；默认 `Field(ge=1)`。
- `reviewer`：`str`；默认 `Field(min_length=1)`。
- `reason`：`str`；默认 `Field(min_length=1)`。
- `request_id`：`str`；默认 `Field(min_length=1)`。

**内部成员**：此类未直接定义方法；字段/继承行为见源码。


---

# MergeProposalRequest ⭐⭐⭐

**位置与等级**：[models.py:68](../../../src/api/models.py#L68)；关键支撑逻辑，影响候选、证据或接口的正确传递。

**职责**：输入契约，集中表达调用前需要的字段与约束。基类：`BaseModel`。

**字段与类级约束**：
- `source_entity_ids`：`list[str]`。
- `target_entity_id`：`str`。
- `reasons`：`list[str]`；默认 `Field(default_factory=list)`。

**内部成员**：此类未直接定义方法；字段/继承行为见源码。


---

# SplitProposalRequest ⭐⭐⭐

**位置与等级**：[models.py:74](../../../src/api/models.py#L74)；关键支撑逻辑，影响候选、证据或接口的正确传递。

**职责**：输入契约，集中表达调用前需要的字段与约束。基类：`BaseModel`。

**字段与类级约束**：
- `target_entities`：`list[CanonicalEntity]`。
- `claim_assignments`：`dict[str, str]`。
- `reasons`：`list[str]`；默认 `Field(default_factory=list)`。

**内部成员**：此类未直接定义方法；字段/继承行为见源码。


---

# RequestReconciliationRequest ⭐⭐⭐

**位置与等级**：[models.py:80](../../../src/api/models.py#L80)；关键支撑逻辑，影响候选、证据或接口的正确传递。

**职责**：输入契约，集中表达调用前需要的字段与约束。基类：`RequestReconciliation`。

**字段与类级约束**：
- 类体未直接声明字段；实例状态请看 `__init__` 及方法中的赋值。

**内部成员**：此类未直接定义方法；字段/继承行为见源码。


---

# RuntimeSettingsUpdate ⭐⭐⭐⭐

**位置与等级**：[models.py:84](../../../src/api/models.py#L84)；承担主要 Agent、应用服务或审核/执行入口，跨模块影响显著。

**职责**：Pydantic 领域/接口模型；实例创建时按字段类型和验证器约束数据。基类：`BaseModel`。

**字段与类级约束**：
- `values`：`dict[str, Any]`；默认 `Field(default_factory=dict)`。
- `clear_secrets`：`list[Literal[<字符串常量>, <字符串常量>, <字符串常量>]]`；默认 `Field(default_factory=list)`。
- `operator`：`str`；默认 `Field(min_length=1)`。

**内部成员**：此类未直接定义方法；字段/继承行为见源码。


---

# CaseDisableRequest ⭐⭐⭐

**位置与等级**：[models.py:92](../../../src/api/models.py#L92)；关键支撑逻辑，影响候选、证据或接口的正确传递。

**职责**：输入契约，集中表达调用前需要的字段与约束。基类：`BaseModel`。

**字段与类级约束**：
- `operator`：`str`；默认 `Field(min_length=1)`。
- `reason`：`str`；默认 `Field(min_length=1)`。
- `request_id`：`str`；默认 `Field(min_length=1)`。

**内部成员**：此类未直接定义方法；字段/继承行为见源码。


---

# CaseIndexRequest ⭐⭐⭐

**位置与等级**：[models.py:98](../../../src/api/models.py#L98)；关键支撑逻辑，影响候选、证据或接口的正确传递。

**职责**：输入契约，集中表达调用前需要的字段与约束。基类：`BaseModel`。

**字段与类级约束**：
- `dry_run`：`bool`；默认 `False`。

**内部成员**：此类未直接定义方法；字段/继承行为见源码。


---
