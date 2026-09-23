源码：[conflicts.py:1](../../../src/governance/conflicts.py#L1) | 基准：`dev/v0.10@f2f34d7` | 本文件符号数：6

**模块职责**：Cardinality-aware and time-aware claim conflict detection.
**在系统中的位置**：实体解析、事实规范化、冲突、风险、审核及实体操作的确定性规则。
**直接依赖**：[src.core.ids](../core/ids.md)、[src.domain](../domain/__init__.md)；外部/标准库：`__future__`、`collections`。
**主要调用方（静态导入）**：[governance/__init__.py](__init__.md)。
**阅读提示**：下列流程根据当前源码控制流整理；`self`/接口对象的实际类型可能在运行时注入，未能静态解析的调用会明确标注。链接指向源码行或对应讲解文件。

---

# _overlaps ⭐⭐

**位置与等级**：[conflicts.py:11](../../../src/governance/conflicts.py#L11)；局部辅助逻辑，需理解其调用条件与失败传播。

**签名**：`def _overlaps(left: Claim, right: Claim) -> bool`。

**作用**：内部辅助步骤；将参数转换为本模块所需的中间对象或操作结果。

**输入与输出**：
- 输入：`left`（Claim）；`right`（Claim）。
- 输出类型：`bool`；具体返回路径见流程步骤。

**处理流程**：
1. 更新 `(left_start, left_end)`，值来自 `(left.valid_from, left.valid_to)`。
2. 更新 `(right_start, right_end)`，值来自 `(right.valid_from, right.valid_to)`。
3. 检查 `left_end is not None and right_start is not None and (left_end <= right_start)`；按条件分流，else 分支不存在。
4. 返回 `not (right_end is not None and left_start is not None and (right_end <= left_start))`。

**关键条件与保护**：
- [conflicts.py:14](../../../src/governance/conflicts.py#L14)：`left_end is not None and right_start is not None and (left_end <= right_start)`，不满足时跳过本分支。

**调用与被调用**：
- 无显式函数调用，或仅声明协议/常量。
- 静态可定位的调用方：[_violating_claims](conflicts.md)。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：未见 `raise`；下游异常可能继续上抛。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。


---

# _scope_key ⭐⭐

**位置与等级**：[conflicts.py:19](../../../src/governance/conflicts.py#L19)；局部辅助逻辑，需理解其调用条件与失败传播。

**签名**：`def _scope_key(claim: Claim) -> str`。

**作用**：内部辅助步骤；将参数转换为本模块所需的中间对象或操作结果。

**输入与输出**：
- 输入：`claim`（Claim；规范化事实及其证据引用）。
- 输出类型：`str`；具体返回路径见流程步骤。

**处理流程**：
1. 返回 `repr(sorted(claim.qualifiers.items()))`。

**调用与被调用**：
- `repr`（[conflicts.py:20](../../../src/governance/conflicts.py#L20)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `sorted`（[conflicts.py:20](../../../src/governance/conflicts.py#L20)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `claim.qualifiers.items`（[conflicts.py:20](../../../src/governance/conflicts.py#L20)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- 静态可定位的调用方：[detect_conflicts](conflicts.md)。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：未见 `raise`；下游异常可能继续上抛。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。


---

# _object_key ⭐⭐

**位置与等级**：[conflicts.py:23](../../../src/governance/conflicts.py#L23)；局部辅助逻辑，需理解其调用条件与失败传播。

**签名**：`def _object_key(claim: Claim) -> str`。

**作用**：内部辅助步骤；将参数转换为本模块所需的中间对象或操作结果。

**输入与输出**：
- 输入：`claim`（Claim；规范化事实及其证据引用）。
- 输出类型：`str`；具体返回路径见流程步骤。

**处理流程**：
1. 返回 `claim.object_entity_id or f<字符串常量>`。

**调用与被调用**：
- 无显式函数调用，或仅声明协议/常量。
- 静态可定位的调用方：[_oriented_claims](conflicts.md)。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：未见 `raise`；下游异常可能继续上抛。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。


---

# _oriented_claims ⭐⭐

**位置与等级**：[conflicts.py:27](../../../src/governance/conflicts.py#L27)；局部辅助逻辑，需理解其调用条件与失败传播。

**签名**：`def _oriented_claims(claim: Claim, schema: SchemaIndex) -> list[tuple[str, str, str, Claim]]`。

**作用**：内部辅助步骤；将参数转换为本模块所需的中间对象或操作结果。

**输入与输出**：
- 输入：`claim`（Claim；规范化事实及其证据引用）；`schema`（SchemaIndex；当前任务的 Schema 或索引，约束实体与关系）。
- 输出类型：`list[tuple[str, str, str, Claim]]`；具体返回路径见流程步骤。

**处理流程**：
1. 更新 `result`，值来自 `[(claim.subject_id, claim.relation_id, _object_key(claim), claim)]`。
2. 更新 `relation`，值来自 `schema.relation_by_id(claim.relation_id)`。
3. 检查 `relation and relation.inverse_relation and claim.object_entity_id`；按条件分流，else 分支不存在。
4. 返回 `result`。

**关键条件与保护**：
- [conflicts.py:30](../../../src/governance/conflicts.py#L30)：`relation and relation.inverse_relation and claim.object_entity_id`，不满足时跳过本分支。

**调用与被调用**：
- `_object_key`（调用点 [conflicts.py:28](../../../src/governance/conflicts.py#L28)）→ [_object_key](conflicts.md)，静态可定位。
- `schema.relation_by_id`（[conflicts.py:29](../../../src/governance/conflicts.py#L29)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `result.append`（[conflicts.py:31](../../../src/governance/conflicts.py#L31)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- 静态可定位的调用方：[detect_conflicts](conflicts.md)。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：未见 `raise`；下游异常可能继续上抛。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。


---

# _violating_claims ⭐⭐

**位置与等级**：[conflicts.py:35](../../../src/governance/conflicts.py#L35)；局部辅助逻辑，需理解其调用条件与失败传播。

**签名**：`def _violating_claims(claims: list[tuple[str, Claim]], maximum: int) -> set[str]`。

**作用**：内部辅助步骤；将参数转换为本模块所需的中间对象或操作结果。

**输入与输出**：
- 输入：`claims`（list[tuple[str, Claim]]；待处理的规范事实集合）；`maximum`（int）。
- 输出类型：`set[str]`；具体返回路径见流程步骤。

**处理流程**：
1. 更新 `violating`，值来自 `set()`。
2. 遍历 `claims`，逐项处理 `(_, anchor)`。
3. 返回 `violating`。

**关键条件与保护**：
- [conflicts.py:39](../../../src/governance/conflicts.py#L39)：`len({value for value, _ in active}) > maximum`，不满足时跳过本分支。

**调用与被调用**：
- `set`（[conflicts.py:36](../../../src/governance/conflicts.py#L36)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `_overlaps`（调用点 [conflicts.py:38](../../../src/governance/conflicts.py#L38)）→ [_overlaps](conflicts.md)，静态可定位。
- `len`（[conflicts.py:39](../../../src/governance/conflicts.py#L39)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `violating.update`（[conflicts.py:40](../../../src/governance/conflicts.py#L40)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- 静态可定位的调用方：[detect_conflicts](conflicts.md)。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：未见 `raise`；下游异常可能继续上抛。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。


---

# detect_conflicts ⭐⭐⭐⭐

**位置与等级**：[conflicts.py:44](../../../src/governance/conflicts.py#L44)；承担主要 Agent、应用服务或审核/执行入口，跨模块影响显著。

**签名**：`def detect_conflicts(new_claims: list[Claim], existing_claims: list[Claim], schema: SchemaIndex) -> list[ConflictSet]`。

**作用**：对规范事实做支持/冲突识别，不由冲突分数直接替代人工审核。

**输入与输出**：
- 输入：`new_claims`（list[Claim]）；`existing_claims`（list[Claim]）；`schema`（SchemaIndex；当前任务的 Schema 或索引，约束实体与关系）。
- 输出类型：`list[ConflictSet]`；具体返回路径见流程步骤。

**处理流程**：
1. 更新 `groups`，值来自 `defaultdict(list)`。
2. 遍历 `[*existing_claims, *new_claims]`，逐项处理 `claim`。
3. 更新 `conflicts`，值来自 `{}`。
4. 遍历 `groups.items()`，逐项处理 `(group_key, group)`。
5. 返回 `list(conflicts.values())`。

**关键条件与保护**：
- [conflicts.py:56](../../../src/governance/conflicts.py#L56)：`maximum is None`，不满足时跳过本分支。
- [conflicts.py:59](../../../src/governance/conflicts.py#L59)：`len(claim_ids) < 2`，不满足时跳过本分支。

**调用与被调用**：
- `defaultdict`（[conflicts.py:47](../../../src/governance/conflicts.py#L47)）：来自 `collections.defaultdict`；具体实现可能由依赖注入或运行时分派决定。
- `_oriented_claims`（调用点 [conflicts.py:49](../../../src/governance/conflicts.py#L49)）→ [_oriented_claims](conflicts.md)，静态可定位。
- `groups[subject_id, relation_id, _scope_key(claim)].append`（[conflicts.py:50](../../../src/governance/conflicts.py#L50)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `_scope_key`（调用点 [conflicts.py:50](../../../src/governance/conflicts.py#L50)）→ [_scope_key](conflicts.md)，静态可定位。
- `groups.items`（[conflicts.py:53](../../../src/governance/conflicts.py#L53)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `schema.relation_by_id`（[conflicts.py:54](../../../src/governance/conflicts.py#L54)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `sorted`（[conflicts.py:58](../../../src/governance/conflicts.py#L58)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `_violating_claims`（调用点 [conflicts.py:58](../../../src/governance/conflicts.py#L58)）→ [_violating_claims](conflicts.md)，静态可定位。
- `len`（[conflicts.py:59](../../../src/governance/conflicts.py#L59)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `ConflictSet`（[conflicts.py:61](../../../src/governance/conflicts.py#L61)）：来自 `src.domain.ConflictSet`；具体实现可能由依赖注入或运行时分派决定。
- `stable_id`（调用点 [conflicts.py:62](../../../src/governance/conflicts.py#L62)）→ [stable_id](../core/ids.md)，静态可定位。
- `list`（[conflicts.py:71](../../../src/governance/conflicts.py#L71)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `conflicts.values`（[conflicts.py:71](../../../src/governance/conflicts.py#L71)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- 静态扫描未定位直接调用方；可能通过路由注册、LangGraph 节点、协议方法或依赖注入动态调用，不据此判断为死代码。

**状态、副作用与异常**：
- 显式状态/容器赋值：`conflicts[conflict.id]`。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：未见 `raise`；下游异常可能继续上抛。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。


---
