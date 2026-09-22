源码：[risk.py:1](../../../src/governance/risk.py#L1) | 基准：`dev/v0.10@f2f34d7` | 本文件符号数：1

**模块职责**：Confidence and conflict-based review routing.
**在系统中的位置**：实体解析、事实规范化、冲突、风险、审核及实体操作的确定性规则。
**直接依赖**：[src.core.ids](../core/ids.md)、[src.domain](../domain/__init__.md)；外部/标准库：无。
**主要调用方（静态导入）**：[governance/__init__.py](__init__.md)。
**阅读提示**：下列流程根据当前源码控制流整理；`self`/接口对象的实际类型可能在运行时注入，未能静态解析的调用会明确标注。链接指向源码行或对应讲解文件。

---

# route_by_risk ⭐⭐

**位置与等级**：[risk.py:7](../../../src/governance/risk.py#L7)；局部辅助逻辑，需理解其调用条件与失败传播。

**签名**：`def route_by_risk(run_id: str, claims: list[Claim], conflicts: list[ConflictSet]) -> tuple[list[Claim], list[ReviewTask]]`。

**作用**：按风险规则决定后续审核或提交路径，不直接更改原始证据。

**输入与输出**：
- 输入：`run_id`（str；目标运行的稳定标识）；`claims`（list[Claim]；待处理的规范事实集合）；`conflicts`（list[ConflictSet]）。
- 输出类型：`tuple[list[Claim], list[ReviewTask]]`；具体返回路径见流程步骤。

**处理流程**：
1. 更新 `conflict_claims`，值来自 `{claim_id for conflict in conflicts for claim_id in conflict.claim_ids}`。
2. 更新 `reviews`，值来自 `[]`。
3. 遍历 `claims`，逐项处理 `claim`。
4. 返回 `(claims, reviews)`。

**关键条件与保护**：
- [risk.py:15](../../../src/governance/risk.py#L15)：`claim.status in {ClaimStatus.APPROVED, ClaimStatus.REJECTED}`，不满足时跳过本分支。
- [risk.py:18](../../../src/governance/risk.py#L18)：`claim.id in conflict_claims`，不满足时跳过本分支。
- [risk.py:20](../../../src/governance/risk.py#L20)：`claim.coarse_visual_evidence and (not claim.cross_modal_support)`，不满足时跳过本分支。
- [risk.py:22](../../../src/governance/risk.py#L22)：`claim.context_only_visual_claim`，不满足时跳过本分支。
- [risk.py:24](../../../src/governance/risk.py#L24)：`claim.uncalibrated_visual_confidence`，不满足时跳过本分支。
- [risk.py:26](../../../src/governance/risk.py#L26)：`claim.confidence < 0.55`，不满足时有 else 分支。
- [risk.py:28](../../../src/governance/risk.py#L28)：`claim.confidence < 0.85`，不满足时有 else 分支。
- [risk.py:31](../../../src/governance/risk.py#L31)：`reasons`，不满足时有 else 分支。
- [risk.py:35](../../../src/governance/risk.py#L35)：`claim.status == ClaimStatus.REVIEW_REQUIRED`，不满足时跳过本分支。

**调用与被调用**：
- `reasons.append`（[risk.py:19](../../../src/governance/risk.py#L19)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `reviews.append`（[risk.py:36](../../../src/governance/risk.py#L36)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `ReviewTask`（[risk.py:37](../../../src/governance/risk.py#L37)）：来自 `src.domain.ReviewTask`；具体实现可能由依赖注入或运行时分派决定。
- `stable_id`（调用点 [risk.py:38](../../../src/governance/risk.py#L38)）→ [stable_id](../core/ids.md)，静态可定位。
- 静态扫描未定位直接调用方；可能通过路由注册、LangGraph 节点、协议方法或依赖注入动态调用，不据此判断为死代码。

**状态、副作用与异常**：
- 显式状态/容器赋值：`claim.status`。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：未见 `raise`；下游异常可能继续上抛。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。


---
