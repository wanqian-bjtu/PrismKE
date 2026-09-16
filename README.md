# PrismKE

PrismKE 是一个面向通用多模态知识图谱构建的研究型项目，目标是实现模式引导、证据感知、可审核和可持续更新的知识抽取流程。

当前稳定版本为 `v0.3.0`，已经接入 Neo4j、版本差异与补偿回滚、FastAPI、Gradio 研究工作台和 Docker Compose。

## 当前能力

### 文档解析

- 支持 TXT、Markdown、HTML、DOCX、PDF、PNG、JPEG 和 WebP。
- Markdown、HTML 和 DOCX 中的图片会与邻近文字、alt 或图注一同进入 `DocumentIR`。
- PDF 保留文本页码和 bbox，抽取内嵌光栅图片，并为扫描页或矢量较重页面生成页面图。
- PaddleOCR 3.x 将扫描页和图片文字转为带像素 bbox 的 OCR 文本块。
- 小于 `64×64` 的装饰图默认跳过；远程图片默认禁止下载。

### 模式引导抽取

- Schema 支持 YAML 和 JSON 格式。
- 支持实体类型、类型别名、关系、关系别名、domain、range、基数、对称关系、逆关系和严格模式。
- 提供可重复测试的 Mock Provider。
- 提供 OpenAI-compatible 文本模型接口。
- 提供独立的 OpenAI-compatible 多模态 VLM 接口，每次处理一个可追溯视觉资产。
- 只有显式选择 `mock` 才会使用 Mock Provider；真实模型配置缺失时直接报错。

### 实体与事实治理

- 实体名称规范化和别名精确匹配。
- 基于规范名称、实体类型和别名的基础跨文档去重。
- 无法链接到已知实体时生成稳定的 NIL 实体 ID。
- 将关系别名映射为 Schema 中的规范关系 ID。
- 执行关系 domain/range 类型约束检查。
- 相同 Claim 合并证据，功能关系或超出最大基数时形成 `ConflictSet`。
- 多值关系不会仅因宾语不同而误判为冲突；有效时间不重叠的事实可以共存。

### 风险审核

- 置信度不低于 `0.85` 且无冲突的 Claim 自动通过。
- 置信度位于 `0.55` 至 `0.85` 之间的 Claim 进入人工审核。
- 置信度低于 `0.55` 的 Claim 默认拒绝。
- 冲突 Claim 必须进入人工审核。
- 只有整图证据的视觉独有 Claim 必须进入人工审核。
- 审核决定保存后，可以从 LangGraph SQLite 检查点继续工作流。

### 图谱与版本

- 默认使用支持文件锁和原子替换的本地 JSON GraphStore。
- 实体、Claim、冲突集合和不可变 Revision 在一个事务中提交。
- 原始文件按 SHA-256 保存，Claim 的每个证据引用均可独立读取和校验。
- LangGraph SQLite Checkpointer 保存节点状态，失败恢复不会重复已经成功的节点。
- 可切换 JSON 或 Neo4j GraphStore，并提供版本差异和补偿回滚。
- 提供 `/api/v1` HTTP API 和挂载在 `/ui` 的 Gradio 研究工作台。

## 处理流程

```text
ingest
  -> parse_document
  -> materialize_visual_assets
  -> run_ocr
  -> persist_evidence
  -> load_schema
       |-> extract_text_claims ---|
       |-> extract_visual_claims -|-> align_modalities
  -> resolve_entities
  -> normalize_claims
  -> detect_conflicts
  -> route_by_risk
  -> prepare_graph_commit
  -> commit_graph
```

工作流由 LangGraph 组织。文本与视觉抽取并行执行并分别保存检查点；某一分支失败时，恢复任务不会重跑已完成分支。解析、治理和持久化等确定性步骤不调用大模型；只有需要语义判断的抽取 Provider 使用 LLM/VLM。

## 环境安装

推荐使用 Python 3.11。服务器已使用独立 Conda 环境：

```bash
conda create -n prismke python=3.11 -y
conda activate prismke
python -m pip install uv
uv sync --extra dev
```

需要真实 OCR 时安装可选依赖：

```bash
uv sync --extra dev --extra ocr
```

开发 v0.3 图谱与 Web 服务时安装：

```bash
uv sync --extra dev --extra neo4j --extra web
```

在当前 AutoDL 服务器上，环境路径为：

```text
/root/miniconda3/envs/prismke
```

## 快速开始

进入项目目录并激活环境：

```bash
cd /root/autodl-tmp/PrismKE
conda activate prismke
```

验证示例 Schema：

```bash
prismke validate-schema configs/schemas/example.yaml
```

使用 Mock Provider 运行完整流程：

```bash
prismke run examples/sample.md \
  --schema configs/schemas/example.yaml \
  --provider mock
```

命令会输出 `run_id`。可以使用以下命令查看完整运行状态：

```bash
prismke show-run RUN_ID
```

对等待审核的 Claim 作出决定：

```bash
prismke review RUN_ID --claim-id CLAIM_ID --decision approve
prismke review RUN_ID --claim-id CLAIM_ID --decision reject
```

审核完成后恢复工作流：

```bash
prismke resume RUN_ID
```

## Mock 输入格式

Mock Provider 用于开发和自动化测试。它识别以下管道符分隔格式，每行表示一个候选事实：

```text
主语 | 关系 | 宾语 | 主语类型 | 宾语类型 | 置信度
```

示例：

```text
PrismKE | developed_by | OpenAI | Software | Organization | 0.92
```

该格式仅用于稳定测试，不是 PrismKE 最终的数据标注协议。

## OpenAI-compatible 配置

复制 `.env.example` 中的配置项并通过环境变量或本地 `.env` 提供：

```text
PRISMKE_LLM_BASE_URL=https://<WorkspaceId>.cn-beijing.maas.aliyuncs.com/compatible-mode/v1
PRISMKE_LLM_API_KEY=
PRISMKE_LLM_MODEL=qwen3.7-flash
PRISMKE_RUNTIME_DIR=runtime
PRISMKE_REQUEST_TIMEOUT=120
```

`.env` 已被 Git 忽略，禁止将 API Key 提交到仓库。

配置完成后使用：

```bash
prismke run INPUT \
  --schema configs/schemas/example.yaml \
  --provider openai-compatible
```

## OCR 与视觉抽取

OCR 默认使用 CPU、中文模型（兼容常见中英混排）：

```text
PRISMKE_OCR_DEVICE=cpu
PRISMKE_OCR_LANG=ch
PRISMKE_OCR_MODEL=PP-OCRv5
```

VLM 使用与文本模型相互独立的配置，缺少配置时不会静默回退 Mock：

```text
PRISMKE_VLM_BASE_URL=https://<WorkspaceId>.cn-beijing.maas.aliyuncs.com/compatible-mode/v1
PRISMKE_VLM_API_KEY=
PRISMKE_VLM_MODEL=qwen3.7-flash
PRISMKE_VLM_TIMEOUT=120
```

北京地域推荐使用百炼业务空间专属 API Host。`<WorkspaceId>` 可在 API Key 创建结果或
业务空间管理页面中查看。服务器上的真实配置应写入
`/root/autodl-tmp/PrismKE/.env`：先复制 `.env.example`，再将同一个 API Key 分别填入
`PRISMKE_LLM_API_KEY` 和 `PRISMKE_VLM_API_KEY`。`.env` 已被 Git 忽略，禁止将密钥
写入 `.env.example`、命令行参数、日志或运行结果。

真实多模态运行：

```bash
prismke run INPUT \
  --schema configs/schemas/example.yaml \
  --provider openai-compatible \
  --ocr-provider paddle \
  --vlm-provider openai-compatible
```

不调用真实 API 的结构测试可以使用 `--ocr-provider mock --vlm-provider mock`。HTML 与 Markdown 远程图片只有显式添加 `--allow-remote-assets` 才会下载。

运行仓库内 12 份可复现的公开多模态样例并生成汇总报告：

```bash
prismke evaluate examples/eval_v0_2/manifest.json \
  --output runtime/evaluation/qwen3.7-flash-report.json \
  --provider openai-compatible \
  --ocr-provider paddle \
  --vlm-provider openai-compatible
```

报告包含 Claim 与实体指标、证据覆盖率、bbox 合法率、请求模型与响应模型、Token、延迟、重试次数及估算成本。费用只是按带日期的价格快照估算，最终以阿里云账单为准。

查看或导出 Claim 引用的证据：

```bash
prismke show-evidence EVIDENCE_ID
prismke export-evidence EVIDENCE_ID --output evidence.png
```

## Neo4j 与 Web 服务

在 `.env` 中设置图存储和本机监听参数：

```text
PRISMKE_GRAPH_STORE=neo4j
PRISMKE_NEO4J_URI=bolt://127.0.0.1:7687
PRISMKE_NEO4J_USER=neo4j
PRISMKE_NEO4J_PASSWORD=
PRISMKE_NEO4J_DATABASE=neo4j
PRISMKE_API_HOST=127.0.0.1
PRISMKE_API_PORT=8000
```

AutoDL 原生部署使用统一控制脚本启动 Neo4j 与 PrismKE Web：

```bash
bash scripts/prismke_autodl.sh start
bash scripts/prismke_autodl.sh status
```

API 位于 `http://127.0.0.1:8000/api/v1`，研究界面位于
`http://127.0.0.1:8000/ui`。服务器保持本机监听，通过 SSH 端口转发访问。若改为非本地监听，必须设置 `PRISMKE_API_TOKEN`。

常用运维命令：

```bash
bash scripts/prismke_autodl.sh stop
bash scripts/prismke_autodl.sh restart
bash scripts/prismke_autodl.sh health
bash scripts/prismke_autodl.sh logs web --lines 100
bash scripts/prismke_autodl.sh logs neo4j --follow
```

脚本不会配置平台级开机自启动。AutoDL 实例启动后执行一次 `start` 即可；重复启动和停止均为幂等操作。本地开发仍可直接执行 `prismke serve`。

JSON 图谱迁移预检与执行：

```bash
prismke migrate-graph --from-json runtime/graph/graph.json --to neo4j --dry-run
prismke migrate-graph --from-json runtime/graph/graph.json --to neo4j
```

AutoDL 原生安装、Docker Compose、接口和回滚操作详见
[`docs/PrismKE-v0.3-部署与操作.md`](docs/PrismKE-v0.3-部署与操作.md)。

## 运行产物

运行数据默认写入 `runtime/`，该目录不会提交到 Git：

```text
runtime/
├── checkpoints.sqlite3  # LangGraph持久化检查点
├── evidence/
│   ├── blobs/           # 按SHA-256寻址的原始文件
│   └── refs/            # 带完整性校验的EvidenceRef
├── assets/               # 解析阶段产生的内容寻址视觉资产
├── graph/
│   └── graph.json       # 原子提交的实体、Claim、冲突和Revision
└── runs/
    └── RUN_ID.json      # 完整运行状态与中间结果
```

## 开发检查

```bash
ruff check .
mypy src/prismke
pytest
```

发布前必须在 Python 3.11 环境中通过以上三项检查。

## 当前边界

当前尚未实现以下能力：

- 表格和图表语义解析。
- 向量召回、复杂实体消歧和 MSPT 式持续学习。
- 本地 VLM 与结构化表格/图表数值解析。
- 多租户、细粒度权限和面向公网的生产级任务队列。

图片作为证据资产，而不是默认作为领域实体。VLM 从整图或图片区域生成 `VisualObservation`，其中识别出的真实领域对象才会链接到 `CanonicalEntity`。区域定位不可用时会保留整图证据并降低自动提交权限。

详细研究设计与后续路线见 [`docs/PrismKE从零构建计划.md`](docs/PrismKE从零构建计划.md)。
