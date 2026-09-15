# PrismKE

PrismKE 是一个面向通用多模态知识图谱构建的研究型项目，目标是实现模式引导、证据感知、可审核和可持续更新的知识抽取流程。

当前代码位于 `dev/v0.1` 分支。v0.1 是第一版可运行纵向闭环，重点验证从文档输入到实体与事实治理、风险审核、图谱持久化和版本登记的完整流程。

## 当前能力

### 文档解析

- 支持 TXT 和 Markdown 文档，并保留字符级证据范围。
- 支持文本型 PDF，并保留页码和边界框坐标（bbox）。
- 支持 PNG、JPEG 和 WebP 图片，生成 `MediaAsset` 与图片级证据。
- 扫描型 PDF 暂不执行真实 OCR，而是为无文本页面记录 `ocr_required` 警告。

### 模式引导抽取

- Schema 支持 YAML 和 JSON 格式。
- 支持实体类型、类型别名、关系、关系别名、domain、range 和严格模式。
- 提供可重复测试的 Mock Provider。
- 提供 OpenAI-compatible 文本模型接口。
- 未配置模型密钥和模型名称时，不会在日志中打印密钥，并回退到 Mock Provider。

### 实体与事实治理

- 实体名称规范化和别名精确匹配。
- 基于规范名称、实体类型和别名的基础跨文档去重。
- 无法链接到已知实体时生成稳定的 NIL 实体 ID。
- 将关系别名映射为 Schema 中的规范关系 ID。
- 执行关系 domain/range 类型约束检查。
- 相同 Claim 合并证据，不同对象值形成 `ConflictSet`，冲突事实不会相互覆盖。

### 风险审核

- 置信度不低于 `0.85` 且无冲突的 Claim 自动通过。
- 置信度位于 `0.55` 至 `0.85` 之间的 Claim 进入人工审核。
- 置信度低于 `0.55` 的 Claim 默认拒绝。
- 冲突 Claim 必须进入人工审核。
- 审核决定保存后，可以从 SQLite 检查点恢复工作流。

### 图谱与版本

- 默认使用幂等的本地 JSON GraphStore。
- 保存实体、Claim、冲突集合和不可变 Revision。
- 每条正式 Claim 必须关联至少一个证据引用。
- SQLite 保存节点级工作流快照，用于失败重试与恢复。

## 处理流程

```text
ingest
  -> parse_document
  -> load_schema
  -> extract_claims
  -> resolve_entities
  -> normalize_claims
  -> detect_conflicts
  -> route_by_risk
  -> persist_graph
  -> commit_revision
```

工作流由 LangGraph 组织。解析、治理和持久化等确定性步骤不调用大模型；只有需要语义判断的抽取 Provider 使用 LLM。

## 环境安装

推荐使用 Python 3.11。服务器已使用独立 Conda 环境：

```bash
conda create -n prismke python=3.11 -y
conda activate prismke
python -m pip install uv
uv sync --extra dev
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
PRISMKE_LLM_BASE_URL=https://api.openai.com/v1
PRISMKE_LLM_API_KEY=
PRISMKE_LLM_MODEL=
PRISMKE_RUNTIME_DIR=runtime
PRISMKE_REQUEST_TIMEOUT=60
```

`.env` 已被 Git 忽略，禁止将 API Key 提交到仓库。

配置完成后使用：

```bash
prismke run INPUT \
  --schema configs/schemas/example.yaml \
  --provider openai-compatible
```

## 运行产物

运行数据默认写入 `runtime/`，该目录不会提交到 Git：

```text
runtime/
├── checkpoints.sqlite3  # 节点级工作流快照
├── graph/
│   └── graph.json       # 实体、Claim、冲突和 Revision
└── runs/
    └── RUN_ID.json      # 完整运行状态与中间结果
```

## 开发检查

```bash
ruff check .
mypy src/prismke
pytest
```

当前服务器验证结果：

```text
Ruff:  All checks passed
Mypy:  Success, 16 source files
Pytest: 16 passed
```

## 当前边界

v0.1 尚未实现以下能力：

- 真实 OCR 推理。
- 真实 VLM 图片事实抽取与图文对齐。
- Neo4j 正式写入。
- FastAPI 和 Gradio 页面。
- Docker Compose 部署。
- 表格和图表语义解析。
- 向量召回、复杂实体消歧和 MSPT 式持续学习。

图片在当前版本中作为证据资产，而不是默认作为领域实体。后续视觉抽取模块会从图片区域生成 `VisualObservation`，再将其中识别出的真实领域对象链接到 `CanonicalEntity`。

详细研究设计与后续路线见 [`docs/PrismKE从零构建计划.md`](docs/PrismKE从零构建计划.md)。
