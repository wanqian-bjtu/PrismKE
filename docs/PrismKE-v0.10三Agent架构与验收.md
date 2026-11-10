# PrismKE v0.10 三 Agent 架构与验收

## 定位

v0.10 把已存在的抽取、实体解析、融合和审核能力组织为三个有明确工具边界的语义 Agent，而不把每个解析器、OCR 或数据库适配器都称作 Agent。该版本的软件与流程协议为 `0.10.0`。

```text
LangGraph 协调器：状态、调度、并行、暂停与恢复
  → 多模态抽取 Agent：OCR、文本/视觉抽取、初步图文对齐
  → 知识融合与审核 Agent：候选问题的有界 Reflection
  → 实体与事实治理 Agent：证据与 Schema 校验、实体解析、事实规范化
  → 知识融合与审核 Agent：冲突检测、风险路由、人工审核任务
  → 确定性图谱更新：再次硬校验、EvidenceStore、JSON/Neo4j 原子事务
```

协调器不调用模型。图谱更新不接受模型自由生成的 Cypher。每个 Agent 只能调用白名单中的工具，并用结构化 `AgentHandoff` 交接候选、实体、事实、证据、问题和审核任务 ID。`AgentTrace` 只保存决定、理由代码、工具、模型指纹、Token 与耗时，不保存原始 Prompt、图片 Base64、密钥或完整向量。轨迹随运行状态持久化，同一步骤重复执行按稳定 ID 更新记录。

## 三个 Agent 的决定范围

- **多模态抽取**依据 `DocumentIR` 和 Schema 选择文本与视觉工具。文本和视觉分支保留原 LangGraph 检查点；可确认的单模态结构化响应错误会明确标记为失败，另一模态结果可保留。鉴权、网络、未知请求和证据存储故障不降级为成功。
- **实体与事实治理**沿用精确匹配、BGE-M3 召回、类型约束、上下文和邻域评分。仅待审核且具有同类型候选的灰区提及可请求语义建议。建议只能引用现有候选；不能单凭建议自动链接、创建已确认实体或绕过阈值。规范化后仍逐项校验证据与 Schema。
- **知识融合与审核**保留候选级有界 Reflection、规则冲突检测和风险路由。对已标记 `related` 的同主体、同关系事实组，可请求一次结构化语义判断；模型建议冲突或不确定时进入人工审核，不能自动批准。规则明确的硬冲突不会被模型覆盖。

## 启用与查看

旧命令保持可用，默认 `--semantic-advisor disabled`，不会新增治理与融合的模型调用。显式启用 Mock 或真实建议：

```bash
prismke run examples/sample.md --schema configs/schemas/example.yaml --provider mock \
  --semantic-advisor mock --agent-token-budget 20000

prismke run examples/sample.md --schema configs/schemas/example.yaml \
  --provider openai-compatible --semantic-advisor openai-compatible \
  --agent-token-budget 20000
```

真实建议复用已经配置的 `PRISMKE_LLM_BASE_URL`、`PRISMKE_LLM_API_KEY` 和 `PRISMKE_LLM_MODEL`，但只有显式选择时才调用。请求发送前预留预算；返回缺少可核实 Token 用量时停止新增调用。Prompt、Provider、预算及 Agent 策略进入 Run ID。可使用 `prismke agent-traces RUN_ID`、`GET /api/v1/runs/{run_id}/agent-traces` 或工作台“Agent 协作”查看脱敏轨迹。

旧流程检查点不能由 v0.10 恢复；旧运行仍可只读查看，继续处理须使用对应发布代码。

小规模真实联调使用独立的 JSON 图谱和持久化请求账本，不通过普通 `run` 命令绕过总预算：

```bash
python scripts/validate_three_agents.py \
  --output runtime/agent-validation/<新的运行目录> \
  --env-file /path/to/isolated-validation.env
```

脚本依次运行中文、英文和图文公开样例，再进行一条不写图的语义建议探针。每次使用新的输出目录；失败或未知用量后不要重发未结算请求。`report.json` 仅保存状态、计数、哈希及用量，详细运行状态和请求账本只留在被 Git 忽略的 `runtime/`。

## 验收边界

- Mock 测试覆盖工具白名单、交接幂等、灰区建议不越权、复杂事实进审核、失败模态可见、未知用量阻断和无额外调用的默认路径。
- 全量 Ruff、Mypy、pytest 以及隔离 JSON/Neo4j、桌面与移动浏览器验证必须通过；不得使用共享或生产图谱。
- 真实联调只使用隔离目录及公开中英文、图文小样例；全部模型调用合计最多 30,000 Token，达到 27,000 停止新增调用。额度、鉴权、未知请求或未记账用量异常时立即停止，不充值。
- 只有自动与真实验收都完成后才讨论 `v0.10.0` 发布。当前版本不能宣称具有结构化表格或图表解析能力，这部分留待后续版本独立实现和评测。
