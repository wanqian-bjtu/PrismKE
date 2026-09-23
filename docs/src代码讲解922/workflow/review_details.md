源码：[review_details.py:1](../../../src/workflow/review_details.py#L1) | 基准：`dev/v0.10@f2f34d7` | 本文件符号数：5

**模块职责**：Source-backed review views; risk flags are prompts, never automatic verdicts.
**在系统中的位置**：应用服务、LangGraph 编排、执行状态、审核接续、图提交及纠正流程。
**直接依赖**：[src.domain](../domain/__init__.md)；外部/标准库：`__future__`、`re`、`typing`。
**主要调用方（静态导入）**：未见静态直接导入；可能由包入口、框架注册或动态加载。
**阅读提示**：下列流程根据当前源码控制流整理；`self`/接口对象的实际类型可能在运行时注入，未能静态解析的调用会明确标注。链接指向源码行或对应讲解文件。

---

# candidate_mentions ⭐⭐

**位置与等级**：[review_details.py:11](../../../src/workflow/review_details.py#L11)；局部辅助逻辑，需理解其调用条件与失败传播。

**签名**：`def candidate_mentions(candidate: CandidateClaim) -> list[EntityMention]`。

**作用**：处理 `candidate_mentions` 对应步骤；下列步骤依据函数体的实际控制流和调用点整理。

**输入与输出**：
- 输入：`candidate`（CandidateClaim；尚未成为正式 Claim 的候选）。
- 输出类型：`list[EntityMention]`；具体返回路径见流程步骤。

**处理流程**：
1. 返回 `[candidate.subject, *([candidate.object] if isinstance(candidate.object, EntityMention) else [])]`。

**调用与被调用**：
- `isinstance`（[review_details.py:14](../../../src/workflow/review_details.py#L14)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- 静态可定位的调用方：[entity_task_base](review_details.md)。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：未见 `raise`；下游异常可能继续上抛。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。
- 恢复/幂等性：仅在代码有检查点、事务、请求编号或显式去重时才成立；此函数不能单凭名称视为可安全重试。


---

# risk_flags ⭐⭐

**位置与等级**：[review_details.py:18](../../../src/workflow/review_details.py#L18)；局部辅助逻辑，需理解其调用条件与失败传播。

**签名**：`def risk_flags(names: list[str], relations: list[str], reasons: list[str]) -> list[str]`。

**作用**：处理 `risk_flags` 对应步骤；下列步骤依据函数体的实际控制流和调用点整理。

**输入与输出**：
- 输入：`names`（list[str]）；`relations`（list[str]）；`reasons`（list[str]）。
- 输出类型：`list[str]`；具体返回路径见流程步骤。

**处理流程**：
1. 更新 `flags`，值来自 `[]`。
2. 检查 `any((re.fullmatch(<字符串常量>, name.strip(), re.IGNORECASE) for name in names))`；按条件分流，else 分支不存在。
3. 检查 `any(('cross_language' in reason or 'cross-lingual' in reason for reason in reasons))`；按条件分流，else 分支不存在。
4. 检查 `any((relation in {'authored_by', 'developed_by', 'author', 'developer'} for relation in relations))`；按条件分流，else 分支不存在。
5. 返回 `flags`。

**关键条件与保护**：
- [review_details.py:20](../../../src/workflow/review_details.py#L20)：`any((re.fullmatch(<字符串常量>, name.strip(), re.IGNORECASE) for name in names))`，不满足时跳过本分支。
- [review_details.py:22](../../../src/workflow/review_details.py#L22)：`any(('cross_language' in reason or 'cross-lingual' in reason for reason in reasons))`，不满足时跳过本分支。
- [review_details.py:24](../../../src/workflow/review_details.py#L24)：`any((relation in {'authored_by', 'developed_by', 'author', 'developer'} for relation in relations))`，不满足时跳过本分支。

**调用与被调用**：
- `any`（[review_details.py:20](../../../src/workflow/review_details.py#L20)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `re.fullmatch`（[review_details.py:20](../../../src/workflow/review_details.py#L20)）：来自 `re`；具体实现可能由依赖注入或运行时分派决定。
- `name.strip`（[review_details.py:20](../../../src/workflow/review_details.py#L20)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `flags.append`（[review_details.py:21](../../../src/workflow/review_details.py#L21)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- 静态可定位的调用方：[entity_task_base](review_details.md)、[claim_task_detail.describe](review_details.md)。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：未见 `raise`；下游异常可能继续上抛。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。
- 恢复/幂等性：仅在代码有检查点、事务、请求编号或显式去重时才成立；此函数不能单凭名称视为可安全重试。


---

# entity_task_base ⭐⭐

**位置与等级**：[review_details.py:31](../../../src/workflow/review_details.py#L31)；局部辅助逻辑，需理解其调用条件与失败传播。

**签名**：`def entity_task_base(state: WorkflowState, task_id: str) -> dict[str, Any]`。

**作用**：处理 `entity_task_base` 对应步骤；下列步骤依据函数体的实际控制流和调用点整理。

**输入与输出**：
- 输入：`state`（WorkflowState；跨节点 WorkflowState；调用方须保持证据与状态一致）；`task_id`（str；待处理审核任务标识）。
- 输出类型：`dict[str, Any]`；具体返回路径见流程步骤。

**处理流程**：
1. 更新 `task`，值来自 `next((item for item in state.entity_review_tasks if item.id == task_id), None)`。
2. 检查 `task is None`；按条件分流，else 分支不存在。
3. 更新 `all_candidates`，值来自 `{item.id: item for item in [*state.text_candidates, *state.visual_candidates, *state.candidates, *s…`。
4. 更新 `related`，值来自 `[item for item in all_candidates.values() if task.mention_id in {mention.id for mention in candidat…`。
5. 更新 `mention`，值来自 `next((mention for item in related for mention in candidate_mentions(item) if mention.id == task.men…`。
6. 返回 `{'run_id': state.run_id, 'task': task.model_dump(mode='json'), 'mention': mention.model_dump(mode='json'…`。

**关键条件与保护**：
- [review_details.py:33](../../../src/workflow/review_details.py#L33)：`task is None`，不满足时跳过本分支。

**调用与被调用**：
- `next`（[review_details.py:32](../../../src/workflow/review_details.py#L32)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `KeyError`（[review_details.py:34](../../../src/workflow/review_details.py#L34)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `all_candidates.values`（[review_details.py:46](../../../src/workflow/review_details.py#L46)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `candidate_mentions`（调用点 [review_details.py:47](../../../src/workflow/review_details.py#L47)）→ [candidate_mentions](review_details.md)，静态可定位。
- `task.model_dump`（[review_details.py:60](../../../src/workflow/review_details.py#L60)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `mention.model_dump`（[review_details.py:61](../../../src/workflow/review_details.py#L61)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `isinstance`（[review_details.py:68](../../../src/workflow/review_details.py#L68)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `risk_flags`（调用点 [review_details.py:75](../../../src/workflow/review_details.py#L75)）→ [risk_flags](review_details.md)，静态可定位。
- `list`（[review_details.py:80](../../../src/workflow/review_details.py#L80)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `dict.fromkeys`（[review_details.py:80](../../../src/workflow/review_details.py#L80)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- 静态可定位的调用方：[PrismKEService.entity_review_detail](service.md)。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：`KeyError(<字符串常量>)`。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。
- 恢复/幂等性：仅在代码有检查点、事务、请求编号或显式去重时才成立；此函数不能单凭名称视为可安全重试。


---

# claim_task_detail ⭐⭐

**位置与等级**：[review_details.py:84](../../../src/workflow/review_details.py#L84)；局部辅助逻辑，需理解其调用条件与失败传播。

**签名**：`def claim_task_detail(state: WorkflowState, task_id: str) -> dict[str, Any]`。

**作用**：处理 `claim_task_detail` 对应步骤；下列步骤依据函数体的实际控制流和调用点整理。

**输入与输出**：
- 输入：`state`（WorkflowState；跨节点 WorkflowState；调用方须保持证据与状态一致）；`task_id`（str；待处理审核任务标识）。
- 输出类型：`dict[str, Any]`；具体返回路径见流程步骤。

**处理流程**：
1. 更新 `task`，值来自 `next((item for item in state.review_tasks if item.id == task_id), None)`。
2. 检查 `task is None`；按条件分流，else 分支不存在。
3. 检查 `task.claim_id in state.normalization_issues`；按条件分流，else 分支不存在。
4. 更新 `entities`，值来自 `{item.id: item for item in state.entities}`。
5. 更新 `claim`，值来自 `next((item for item in state.claims if item.id == task.claim_id))`。
6. 更新 `conflicts`，值来自 `[item for item in state.conflicts if claim.id in item.claim_ids]`。
7. 更新 `peer_ids`，值来自 `{cid for item in conflicts for cid in item.claim_ids} - {claim.id}`。
8. 返回 `{'run_id': state.run_id, 'task': task.model_dump(mode='json'), 'claim': describe(claim), 'risk_flags': d…`。

**关键条件与保护**：
- [review_details.py:86](../../../src/workflow/review_details.py#L86)：`task is None`，不满足时跳过本分支。
- [review_details.py:88](../../../src/workflow/review_details.py#L88)：`task.claim_id in state.normalization_issues`，不满足时跳过本分支。

**调用与被调用**：
- `next`（[review_details.py:85](../../../src/workflow/review_details.py#L85)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `KeyError`（[review_details.py:87](../../../src/workflow/review_details.py#L87)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `task.model_dump`（[review_details.py:92](../../../src/workflow/review_details.py#L92)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `isinstance`（[review_details.py:97](../../../src/workflow/review_details.py#L97)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `describe`（[review_details.py:134](../../../src/workflow/review_details.py#L134)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `item.model_dump`（[review_details.py:136](../../../src/workflow/review_details.py#L136)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- 静态可定位的调用方：[PrismKEService.claim_review_detail](service.md)。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：`KeyError(<字符串常量>)`。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。
- 恢复/幂等性：仅在代码有检查点、事务、请求编号或显式去重时才成立；此函数不能单凭名称视为可安全重试。


---

# claim_task_detail.describe ⭐⭐

**位置与等级**：[review_details.py:115](../../../src/workflow/review_details.py#L115)；局部辅助逻辑，需理解其调用条件与失败传播。

**签名**：`def describe(claim: Any) -> dict[str, Any]`。

**作用**：处理 `describe` 对应步骤；下列步骤依据函数体的实际控制流和调用点整理。

**输入与输出**：
- 输入：`claim`（Any；规范化事实及其证据引用）。
- 输出类型：`dict[str, Any]`；具体返回路径见流程步骤。

**处理流程**：
1. 更新 `names`，值来自 `[entities[eid].name if eid in entities else eid for eid in (claim.subject_id, claim.object_entity_i…`。
2. 返回 `{**claim.model_dump(mode='json'), 'subject_name': names[0], 'object_name': names[1] if len(names) > 1 el…`。

**调用与被调用**：
- `claim.model_dump`（[review_details.py:122](../../../src/workflow/review_details.py#L122)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `len`（[review_details.py:124](../../../src/workflow/review_details.py#L124)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `risk_flags`（调用点 [review_details.py:125](../../../src/workflow/review_details.py#L125)）→ [risk_flags](review_details.md)，静态可定位。
- 静态扫描未定位直接调用方；可能通过路由注册、LangGraph 节点、协议方法或依赖注入动态调用，不据此判断为死代码。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：未见 `raise`；下游异常可能继续上抛。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。
- 恢复/幂等性：仅在代码有检查点、事务、请求编号或显式去重时才成立；此函数不能单凭名称视为可安全重试。


---
