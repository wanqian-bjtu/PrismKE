# 变更日志

本项目遵循语义化版本管理。

## 未发布 - v0.3.0

### 新增

- JSON 与 Neo4j 可配置 GraphStore，以及 JSON 到 Neo4j 的幂等迁移命令。
- `GraphDocument`、`GraphChange`、Revision diff 和补偿回滚协议。
- FastAPI 任务、证据、审核、邻域、版本和健康检查接口。
- Gradio 文档构建、Claim 审核、证据定位、图谱与版本工作台。
- AutoDL 原生 Neo4j 安装脚本、Dockerfile 和 Docker Compose。

### 安全

- 非本机 API 监听强制要求 Bearer Token。
- 图数据库不保存服务器绝对路径，页面不接收或展示模型 API Key。
- 审核和回滚操作写入追加式审计日志。

## v0.2.1 - 2026-09-16

### 新增

- 支持独立图片、扫描 PDF、PDF 内嵌图片、Markdown、HTML 和 DOCX 图片进入统一 `DocumentIR`。
- 接入 PaddleOCR 3.x，保留 OCR 文本、置信度、页码和像素 bbox。
- 接入 OpenAI-compatible 多模态 VLM，输出视觉观察、候选 Claim 和区域证据。
- 增加文本、OCR 和图像候选的跨模态支持、冲突、相关和独立判定。
- 增加 12 份可复现的公开多模态评测样例及真实联调报告。

### 修复

- 修正实体别名、关系别名、逆关系和对称关系的评测等价判断。
- 修正 HTML 图片继承过宽正文上下文导致的视觉事实偏置。
- 视觉 Prompt 明确图片和 OCR 为主要证据，邻近正文仅作为辅助上下文。
- 增加 `context_only_visual_claim` 风险标记，阻止缺少视觉依据的候选自动写图。
- 避免 OCR 与图片对同一可见文字重复增强置信度。
- 运行记录文件名改为跨平台安全格式，并兼容旧服务器记录。

### 验证

- 12 份公开样例全部完成，Claim Micro-F1 为 0.9630，Entity Micro-F1 为 0.9804。
- 英文图文冲突样例修复后真实复测通过，正确生成两条 Claim 和一个 `ConflictSet`。
- 正式 Claim 证据覆盖率和 bbox 合法率均为 100%。

## v0.2.0 - 2026-09-15

- 建立 v0.2 多模态数据模型、解析器、OCR/VLM Provider、跨模态工作流和公开评测框架。

## v0.1.1 - 2026-09-10

- 完成分层目录重构、内容寻址证据存储、原子 JSON GraphStore、稳定运行 ID 和 LangGraph SQLite 检查点恢复。
