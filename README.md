# PrismKE

PrismKE 是一个面向通用多模态知识图谱构建的研究型项目，目标是实现模式引导、证据感知、可审核和可持续更新的知识抽取流程。

当前稳定版本为 `v0.12.0`。v0.8 将研究工作台重构为左侧导航与右侧主工作区；v0.9 新增不可变审核案例库、BGE-M3 案例检索和受预算约束的 Reflection；v0.9.2 增加历史测试事实的受控治理与 Neo4j 测试实例守卫；v0.10 建立三个语义 Agent，并完成研究工作台的视觉与配置收尾；v0.11 增加多文档批次与六种任务模式；v0.12 增加 PyMuPDF 与 MinerU 双层 PDF 解析和可审计的证据派生链。系统同时保留持久化任务管理、安全取消、审核纠正、统一校验、语义实体治理、Neo4j 与补偿回滚。软件版本与流程协议版本独立管理；旧运行继续使用对应发布版本处理，生产服务升级需单独执行。

`dev/v0.13` 正在开发媒体知识图层：媒体内容、文档出现位置、视觉关系和视觉断言保持独立边界，视觉独有知识经人工审核后才能写图。开发版软件版本为 `0.13.0.dev0`，流程协议为 `0.13.0`；v0.12 及更早运行只读保留。

`v0.12.0` 软件版本与流程协议均为 `0.12.0`。该版本增加 PyMuPDF 与 MinerU 双层 PDF 解析、可审计的解析路由、派生资产清单及人工降级机制；Git 发布不替换生产 v0.9.2 服务。

`v0.10.0` 包含三个有结构化交接与决策轨迹的语义 Agent：多模态抽取、实体与事实治理、知识融合与审核。LangGraph 仍是确定性协调器，GraphStore 仍执行硬校验和事务提交；灰区模型建议受显式开关和预算约束。研究工作台提供可调宽侧栏、Schema 文件/文本输入、会话级模型配置、OCR 自动设备选择和中英混合识别，具体边界见 [v0.10 前端视觉验收](docs/PrismKE-v0.10前端视觉验收.md)。本次 Git 发布不替换生产服务。职责、命令和边界见 [v0.10 三 Agent 架构说明](docs/PrismKE-v0.10三Agent架构与验收.md)。

`v0.6.0` 软件版本与流程协议均为 `0.6.0`。新增审核人/原因校验、暂缓、不可变候选与审核事件、可重放投影、纠正预览及精确补偿提交。使用边界见 [v0.6 审核纠正说明](docs/v0.6审核纠正说明.md)，快速检查问题保留在 [问题清单](docs/v0.6.0问题记录与改进清单.md)。旧运行不能由新流程纠正或恢复。

`v0.7.0` 软件版本与流程协议均为 `0.7.0`，发布分支保留为 `dev/v0.7`。提供持久化执行状态、单工作器互斥、安全取消、请求结果复用与安全重启恢复。见 [运行管理说明](docs/v0.7运行管理说明.md)、[隔离验收报告](docs/v0.7隔离验收报告.md) 和 [问题记录](docs/v0.7问题记录.md)。未知请求会安全阻断恢复，暂不支持页面人工解锁；不宣称跨数据库原子一致。v0.7 不接续旧检查点，旧运行用对应发布代码处理。

`v0.8.0` 软件版本与流程协议均为 `0.8.0`。工作台验收范围、浏览器视口和安全边界见 [v0.8 工作台与运行治理验收报告](docs/v0.8工作台与运行治理验收报告.md)。未知 Provider 请求只有经审计确认为未发送或未计费后才允许重试；页面不显示或编辑 API Key、Neo4j 密码。

`v0.9.2` 软件版本对应流程协议 `0.9.0`，因此不改变 v0.9 Run ID 或检查点规则。案例只来源于 v0.9 中具有审核人、原因和可验证证据的最终决定；Reflection 默认关闭，不能新增 Schema、伪造证据、绕过硬校验或自动批准事实。使用方法见 [v0.9 案例检索与 Reflection 使用说明](docs/v0.9案例检索与Reflection使用说明.md)，真实模型验收结果见 [v0.9.0 评测与验收报告](docs/v0.9.0评测与验收报告.md)，并行部署与回退见 [v0.9.1 生产并行部署与回退](docs/PrismKE-v0.9.1生产并行部署与回退.md)。历史证据治理和当前部署状态见 [v0.9.2 治理验收](docs/v0.9.2历史证据治理与验收.md)。

## 当前能力

统一校验自 `v0.5.0` 引入，后续版本保留违规候选隔离、独立排除审计和存储提交硬校验。不同流程协议的检查点不可混用；旧审核工作区继续使用 v0.4.1。

统一校验操作、问题代码和迁移边界见 [v0.5 统一校验说明](docs/v0.5统一校验说明.md)，历史测试与完成边界见 [隔离验收报告](docs/v0.5隔离验收报告.md)。稳定版本的能力与开发版本的验收结果分开记录。

### 文档解析

- `dev/v0.11` 支持 TXT、Markdown、HTML、DOC、DOCX、PDF、普通 JSON、PrismKE DocumentIR JSON，以及 PNG、JPEG、WebP、TIFF、BMP 图片。
- 旧 DOC 先由 LibreOffice headless 在隔离配置目录中转换为 DOCX；原文件与派生文件分别记录哈希和工具版本。缺少转换器、转换超时或派生文件异常时明确失败。
- 普通 JSON 按 JSONPath 展开标量并保留数组顺序，Evidence 同时校验原文件哈希、JSONPath 和字段值哈希。
- Markdown、HTML 和 DOCX 中的图片会与邻近文字、alt 或图注一同进入 `DocumentIR`。
- v0.12 默认先由 PyMuPDF 只读预检 PDF。普通文本型 PDF 继续使用 PyMuPDF；扫描件、表格、绘图或多栏密集文档路由到本机 MinerU 4.0.12 Standard。请求模式、复杂度指标、路由原因、解析器版本和配置指纹均进入运行快照。
- MinerU Markdown 仅用于预览；页码、bbox、表格、图片、公式和派生关系从 MiddleJson 转换到 `DocumentIR`/`EvidenceRef`，并同时校验原 PDF 与派生产物哈希。MinerU 失败时自动模式进入阻断，只有具名操作者填写原因后才可降级到 PyMuPDF。
- PaddleOCR 3.x 将扫描页和图片文字转为带像素 bbox 的 OCR 文本块。
- 小于 `64×64` 的装饰图默认跳过；远程图片默认禁止下载。

### 模式引导抽取

- Schema 支持 YAML 和 JSON 格式。
- 支持实体类型、类型别名、关系、关系别名、domain、range、基数、对称关系、逆关系和严格模式。
- 提供可重复测试的 Mock Provider。
- 提供 OpenAI-compatible 文本模型接口。
- 提供独立的 OpenAI-compatible 多模态 VLM 接口，每次处理一个可追溯视觉资产。
- 只有显式选择 `mock` 才会使用 Mock Provider；真实模型配置缺失时直接报错。

### 多任务与批次

- Web、API 和 CLI 可选择实体抽取、关系抽取、Schema 信息抽取、端到端实体关系抽取、实体关系抽取与消歧、完整知识构建六种模式。
- 前五种模式只生成可审核、可导出的 `TaskExtractionResult`，不会创建 Graph Revision；提交请求返回 `TASK_MODE_NO_GRAPH_COMMIT`。
- 完整知识构建保持 v0.10 的默认行为，只有该模式允许跨文档治理和显式批次图提交。
- 一个批次默认最多 20 个文件、单文件 200 MiB、总计 500 MiB。每个文件拥有独立子运行、证据、Token、状态和失败原因。
- 同批次内容哈希相同的文件复用同一子运行。单个文件失败不会丢弃其他结果，但会阻断批次融合，直到重试成功或由操作者带原因排除。
- 批次提交会合并重复事实与多来源证据，并再次检查跨文档基数冲突。冲突不会写图，需先人工排除冲突来源。

### 实体与事实治理

- 实体名称规范化和别名精确匹配。
- v0.4 可选使用本地 BGE-M3 Dense Embedding 与 Neo4j Vector Index 召回实体。
- 候选实体结合名称、类型、上下文和图邻域信号进行可审计重排。
- 高置信实体自动链接，模糊实体、同名异型实体进入独立人工审核。
- 跨文档重复实体可生成合并建议，已有不同稳定 ID 不会被自动合并。
- 实体合并与拆分以原子 Revision 提交，保留历史并支持补偿回滚。
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
- `dev/v0.4` 增加可选择的实体/事实审核队列、证据预览及隔离评测运行接续；导入运行不会重新调用模型，写图前必须单独确认。
- 真实材料的三条任务及访问步骤见 [隔离审核操作说明](docs/隔离审核操作说明.md)。人工确认前不宣称真实审核后闭环已经验收。

### 案例检索与 Reflection

- v0.9 将符合资格的实体和事实审核决定投影为不可变 Good/Bad Case；纠正会生成新案例并停用被替代案例，不覆盖历史。
- 案例按任务类型、Schema 指纹和语言过滤，再使用 BGE-M3 Dense Embedding 进行 Top-K 召回。
- 每个运行冻结案例快照、检索策略和 Embedding 指纹，案例库后续变化不会改变该运行的恢复结果。
- Reflection 仅处理结构、Schema、引用和证据问题，单候选最多两次，并受独立 Token 与时间预算约束。
- 修复后的候选必须再次通过统一校验；失败、问题增加、未知用量或不确定请求均保留原候选并转人工处理。
- 案例只作为不可信的结构化示例进入 Prompt，不作为指令，也不会直接批准候选。

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
  -> validate_candidates
  -> retrieve_cases
  -> bounded_reflection
  -> validate_candidates
  -> resolve_entities
       |-> route_entity_reviews -> 人工链接或创建 NIL -> resume
  -> normalize_claims
  -> detect_conflicts
  -> route_by_risk
  -> prepare_graph_commit
  -> commit_graph
```

工作流由 LangGraph 组织。文本与视觉抽取并行执行并分别保存检查点；某一分支失败时，恢复任务不会重跑已完成分支。v0.10 将现有节点委托给三个语义 Agent；仅显式启用时在实体灰区和复杂事实组调用文本模型，最终校验、审核与写图仍由原有硬边界负责。v0.11 在 `align_modalities` 后按任务模式路由：抽取模式直接生成结果，联合消歧模式在实体规范化后停止，只有完整知识构建继续进入事实融合和图提交。

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

开发 v0.4 本地语义实体链接时安装：

```bash
uv sync --extra dev --extra neo4j --extra web --extra embedding
```

### MinerU 高精度 PDF 解析

MinerU 不安装进 PrismKE 主环境。Linux 服务器先确认数据盘至少有 10 GiB 可用，再执行：

```bash
bash scripts/install_mineru.sh
bash scripts/start_mineru.sh
bash scripts/status_mineru.sh
```

服务固定监听 `127.0.0.1:18020`，默认单工作器、单并发。停止命令为：

```bash
bash scripts/stop_mineru.sh
```

Windows 和 CI 无需安装 MinerU，使用 Mock V1 服务测试。完整路由、证据和人工降级边界见 [v0.12 双层 PDF 解析说明](docs/PrismKE-v0.12双层PDF解析架构与操作.md)。

`uv sync` 在项目内创建 `.venv`。启动脚本优先使用该环境中的 `python` 和
`prismke`；其它安装方式可设置 `PRISMKE_PYTHON_BIN` 与 `PRISMKE_CLI_BIN`。

`v0.10` 及后续版本的 Python 源码直接放在根目录 `src/`，导入路径为 `src.*`；
命令行入口仍是 `prismke`。旧的 `prismke.*` 导入不再适用于此开发分支，
安装或拉取更新后需重新安装项目依赖。历史运行仍由对应发布版本接续。

## 快速开始

进入实际检出的项目目录并激活环境：

```bash
cd /path/to/PrismKE
source .venv/bin/activate
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

选择独立任务或运行多文件批次：

```bash
prismke run examples/sample.md \
  --schema configs/schemas/example.yaml \
  --provider mock \
  --task-mode entity_extraction \
  --output runtime/results/entities.json

prismke run-batch examples/a.pdf examples/b.docx examples/c.json \
  --schema configs/schemas/example.yaml \
  --provider mock \
  --task-mode joint_entity_relation_extraction \
  --output runtime/results/batch.json
```

关系抽取可通过 `--entity-source provided --entities entities.json` 使用给定实体；未指定时先自动识别实体。Web 页面提供相同任务选择，并按文件显示批次状态和统一抽取结果。

对等待审核的 Claim 作出决定：

```bash
prismke review RUN_ID --claim-id CLAIM_ID --decision approve
prismke review RUN_ID --claim-id CLAIM_ID --decision reject
```

审核完成后恢复工作流：

```bash
prismke resume RUN_ID
```

启用案例检索与 Reflection 时，需要显式选择模式、Provider 和预算：

```bash
prismke run examples/sample.md \
  --schema configs/schemas/example.yaml \
  --provider mock \
  --cases good_bad \
  --reflection \
  --reflection-provider mock \
  --reflection-max-attempts 2 \
  --reflection-token-budget 20000 \
  --reflection-time-budget 180
```

案例库维护命令不会物理删除历史案例：

```bash
prismke list-cases --type good --task-type claim
prismke disable-case CASE_ID --operator researcher --reason "已被纠正事件替代"
prismke rebuild-case-index --dry-run
prismke rebuild-case-index
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
PRISMKE_LIBREOFFICE_BIN=
PRISMKE_DOCUMENT_CONVERSION_TIMEOUT_SECONDS=120
PRISMKE_MAX_BATCH_FILES=20
PRISMKE_MAX_FILE_BYTES=209715200
PRISMKE_MAX_BATCH_BYTES=524288000
```

`.env` 已被 Git 忽略，禁止将 API Key 提交到仓库。

配置完成后使用：

```bash
prismke run INPUT \
  --schema configs/schemas/example.yaml \
  --provider openai-compatible
```

## OCR 与视觉抽取

OCR 默认自动检测 Paddle 可用设备，无卡或 CPU 版 Paddle 会安全使用 CPU；中英混排和中文均使用保留英文内容的 `ch` 引擎：

```text
PRISMKE_OCR_DEVICE=auto
PRISMKE_OCR_LANG=mixed
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
业务空间管理页面中查看。真实配置应写入项目根目录的 `.env`：先复制
`.env.example`，再将同一个 API Key 分别填入
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

## BGE-M3 与实体向量索引

Embedding 依赖固定为官方 `torch 2.6.0 + CUDA 12.4`，与当前 AutoDL 驱动及 Transformers 权重加载要求兼容。普通 Python 包使用阿里云 HTTPS 镜像，Torch 使用 PyTorch 官方 CUDA 12.4 索引。

在服务器 `.env` 中启用本地 Embedding：

```text
PRISMKE_EMBEDDING_PROVIDER=bge-m3
PRISMKE_EMBEDDING_MODEL=BAAI/bge-m3
PRISMKE_EMBEDDING_MODEL_REVISION=5617a9f61b028005a4858fdac845db406aefb181
PRISMKE_EMBEDDING_DEVICE=cuda:0
PRISMKE_EMBEDDING_USE_FP16=true
PRISMKE_EMBEDDING_BATCH_SIZE=32
PRISMKE_EMBEDDING_MODEL_CACHE=runtime/models/huggingface
PRISMKE_ENTITY_TOP_K=10
PRISMKE_ENTITY_AUTO_LINK_THRESHOLD=0.88
PRISMKE_ENTITY_REVIEW_THRESHOLD=0.65
PRISMKE_ENTITY_MIN_MARGIN=0.08
```

首次使用先显式下载并验证模型，Web 请求不会临时下载模型：

```bash
prismke prepare-model --embedding BAAI/bge-m3
```

检查并重建已有实体索引：

```bash
prismke rebuild-entity-index --backend neo4j --batch-size 32 --dry-run
prismke rebuild-entity-index --backend neo4j --batch-size 32
```

运行仓库内 60 组可重复生成的实体链接与治理评测：

```bash
prismke evaluate-entities examples/entity_resolution_v0_4/manifest.json \
  --embedding-provider bge-m3 \
  --output runtime/evaluation/entity-resolution-v0.4.json
```

Embedding 是可重建的派生数据，不写入 Revision 快照、运行结果或检查点。模型指纹或实体文本变化后，重建命令只更新缺失或过期向量，不修改实体、Claim 和历史版本。

v0.4 新增 API：

```text
GET  /api/v1/entities/search
GET  /api/v1/entity-reviews
POST /api/v1/entity-reviews/{task_id}
POST /api/v1/entities/merge-proposals
POST /api/v1/entities/{entity_id}/split-proposals
GET  /api/v1/entities/{entity_id}/history
```

Gradio `/ui` 中的“实体治理”页面可以检查 Top-K 候选和评分、处理实体链接审核、创建合并/拆分建议并查看治理结果。合并和拆分始终需要人工批准。

Linux/WSL 部署使用项目内的统一控制脚本启动 Neo4j 与 PrismKE Web，不依赖
AutoDL 路径或 Conda。需先安装 Java、Neo4j、tmux、curl、flock 和项目虚拟环境；
`scripts/install_neo4j.sh` 可将 Neo4j 安装到项目的 `runtime/neo4j/current`。
开发服务默认使用显式指定的隔离运行目录，不会读取
旧的 `runtime/neo4j/data`；可用 `PRISMKE_RUNTIME_DIR` 指定另一实例目录：

```bash
bash scripts/prismke.sh start
bash scripts/prismke.sh status
```

也可以分别启动：`bash scripts/start_neo4j.sh` 启动本机 Neo4j daemon，
`bash scripts/start_web.sh` 在当前终端前台启动 Web（`Ctrl+C` 停止 Web）。
实际 Gradio 页面代码位于根目录 `frontend/`，FastAPI 仍由 `prismke serve`
启动并在 `/ui/` 挂载页面。独立实例、旧版服务回退及端口转发见
[v0.10 前端目录与服务切换说明](docs/v0.10前端目录与服务切换说明.md)。

API 位于 `http://127.0.0.1:8000/api/v1`，研究界面位于
`http://127.0.0.1:8000/ui`。服务器保持本机监听，通过 SSH 端口转发访问。若改为非本地监听，必须设置 `PRISMKE_API_TOKEN`。

常用运维命令：

```bash
bash scripts/prismke.sh stop
bash scripts/prismke.sh restart
bash scripts/prismke.sh health
bash scripts/prismke.sh logs web --lines 100
bash scripts/prismke.sh logs neo4j --follow
```

脚本从自身位置定位项目，不要求当前工作目录固定，也不配置平台级开机自启动。
机器重启后执行一次 `start` 即可；重复启动和停止均为幂等操作。本地开发仍可
直接执行 `prismke serve`。原 `_autodl.sh` 文件仅作为旧命令兼容入口。

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
mypy src
pytest
```

发布前必须在 Python 3.11 环境中通过以上三项检查。

## 当前边界

当前尚未实现以下能力：

- 表格和图表语义解析。
- MSPT 式持续学习。BGE-M3 向量召回与实体消歧已在 v0.4 实现。
- 本地 VLM 与结构化表格/图表数值解析。
- 多租户、细粒度权限和面向公网的生产级任务队列。

图片作为证据资产，而不是默认作为领域实体。VLM 从整图或图片区域生成 `VisualObservation`，其中识别出的真实领域对象才会链接到 `CanonicalEntity`。区域定位不可用时会保留整图证据并降低自动提交权限。

详细研究设计与后续路线见 [`docs/PrismKE从零构建计划.md`](docs/PrismKE从零构建计划.md)。
