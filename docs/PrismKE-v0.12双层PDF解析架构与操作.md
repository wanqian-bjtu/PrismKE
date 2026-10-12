# PrismKE v0.12 双层 PDF 解析架构与操作

## 1. 目标与边界

v0.12 在不改变六种任务模式、三个语义 Agent、审核和图事务边界的前提下，为 PDF 增加两级解析。普通文本型 PDF 继续由 PyMuPDF 快速处理；扫描件、复杂多栏、表格、公式或图表密集文档交给 MinerU 4.0.12 Standard。两条路径统一生成 `DocumentIR` 和 `EvidenceRef`，后续仍经过 OCR、VLM、候选校验、实体治理和人工审核。

MinerU 的 Markdown 只供人阅读，不能作为最终证据。可提交候选必须能回到原 PDF、MiddleJson 元素和相关派生资产，并通过全部哈希与坐标检查。

## 2. 自动路由

`pdf_parse_mode` 支持以下值：

| 模式 | 行为 |
|---|---|
| `auto` | 先做 PyMuPDF 只读预检，再按复杂度选择解析器；默认值 |
| `pymupdf` | 强制使用轻量解析，不自动升级 |
| `mineru` | 强制使用 MinerU；失败时不允许在原运行中降级 |

自动模式满足任一条件即选择 MinerU：

- 无原生文本页达到 `max(1, ceil(页数 × 15%))`；
- 原生文字少于 80 字的页面达到 `max(2, ceil(页数 × 30%))`；
- 表格候选页达到 `max(1, ceil(页数 × 10%))`；
- 每页绘图元素不少于 5 个的页面达到 `max(1, ceil(页数 × 20%))`；
- 多栏且阅读顺序不稳定页面达到 `max(1, ceil(页数 × 20%))`。

阈值来自服务端配置。`PDFParseDecision` 保存请求模式、实际解析器、原因代码、全部复杂度指标、解析器版本和配置指纹，并进入 Run ID 与检查点。

## 3. MinerU V1 生命周期

PrismKE 使用 MinerU 4.0 的 V1 分级解析接口：

1. 创建上传记录；
2. 流式上传 PDF；
3. 完成上传；
4. 创建 Standard tier 解析任务；
5. 查询原 job，直到完成或明确失败；
6. 下载 MiddleJson、结构化内容、Markdown 预览和资产包；
7. 校验并生成 SHA-256 清单。

发送前，逻辑请求编号、原文件哈希、MinerU 版本、tier 和配置指纹写入现有请求账本。检查点恢复优先查询已保存的 job id，不重复上传或新建任务。网络中断后无法确认结果的请求标记为未知并阻断，不能自动重发。

MinerU 服务进程内保存任务状态，因此服务重启后若原 job 无法查询，PrismKE 将其视为未知请求，不以重新解析伪装恢复成功。

## 4. 证据派生链

派生产物保存到：

```text
runtime/derived-documents/<source_hash>/<logical_request_id>/
```

目录包含原始 MiddleJson、可选结构化内容、Markdown 预览、资产包及 `manifest.json`。运行数据与模型不进入 Git。

转换规则如下：

- 文本块保留原 PDF 页码、PDF point bbox、画布尺寸和 MiddleJson locator；
- 表格保留结构化内容及原页区域，检索文本不能替代表格区域证据；
- 图片复制到 EvidenceStore，记录资产哈希、原页 bbox 和派生关系；
- 公式保留文本或 LaTeX、原页区域和派生来源；
- `EvidenceRef.source_hash` 始终指向原 PDF；
- `derivation_id`、解析器指纹和产物清单哈希连接原文与全部派生产物。

证据读取会同时验证原 PDF 哈希、页码、bbox、画布、MiddleJson schema/version、locator、派生文件哈希和资产哈希。任一不一致都会返回验证失败，并阻断候选提交。

## 5. 失败与人工降级

自动模式选择 MinerU 后，不会静默退回 PyMuPDF：

| 错误码 | 含义 |
|---|---|
| `MINERU_UNAVAILABLE` | 服务或传输不可用 |
| `MINERU_PARSE_FAILED` | MinerU 明确解析失败 |
| `MINERU_EVIDENCE_INVALID` | 输出结构、坐标或资产无法验证 |

运行进入 `parser_blocked`。操作者可在执行页查看实际解析器、路由原因、复杂度指标、job 状态和产物摘要。只有 `auto` 模式允许填写姓名与原因，确认以 PyMuPDF 重试。降级请求要求请求编号和预期执行版本；同一请求幂等返回，过期版本或请求编号复用返回 `409`。事件不可变保存。

强制 `mineru` 模式不能在原运行降级。需要轻量解析时必须新建 `pymupdf` 运行，从而让 Run ID 和审计语义保持准确。

## 6. 接口与命令

```text
GET  /api/v1/pdf-parsers/status
GET  /api/v1/runs/{run_id}/pdf-parse
POST /api/v1/runs/{run_id}/pdf-parser-fallback
```

运行命令可指定解析器：

```bash
prismke run INPUT SCHEMA --pdf-parser auto
prismke run-batch INPUTS... SCHEMA --pdf-parser mineru
prismke pdf-parser-fallback RUN_ID --operator 管理员 --reason "已核对后使用轻量解析"
```

MinerU 使用独立环境和运行目录：

```bash
bash scripts/install_mineru.sh
bash scripts/start_mineru.sh
bash scripts/status_mineru.sh
bash scripts/stop_mineru.sh
```

默认安装固定的 MinerU 4.0.12 基础包，并以 `ONNX + llama.cpp` 运行 Standard tier；
该组合是为了满足单独环境、默认总占用不超过 10GB 且安装后至少保留 5GB 空间的部署边界。模型下载并验证后，配置会切换为
`source: local`，服务启动时不会静默下载模型。需要自行选择其他后端时，可通过
`PRISMKE_MINERU_INSTALL_SPEC`、`PRISMKE_MINERU_SMALL_BACKEND` 和
`PRISMKE_MINERU_VLM_ENGINE` 覆盖。安装上限和保留空间也可分别通过
`PRISMKE_MINERU_MAX_INSTALL_GIB`、`PRISMKE_MINERU_MIN_FREE_GIB` 调整，安装前空间门槛可通过
`PRISMKE_MINERU_MIN_INITIAL_FREE_GIB` 调整，但仍必须通过空间与模型完整性检查。

脚本从自身位置推导项目根目录，不硬编码 AutoDL 路径。服务只能监听 `127.0.0.1`，默认端口 `18020`，并关闭遥测。安装前至少需要 10 GiB 可用空间，安装后必须保留 5 GiB。

## 7. 兼容性

- v0.11 及更早检查点只读保留，不由 v0.12 恢复；
- 普通文本型 PDF 的 PyMuPDF、OCR、VLM 和证据行为保持兼容；
- 两种解析器都不能绕过 Schema、证据和图提交硬校验；
- Windows 与 CI 不强制安装 MinerU，使用固定 MiddleJson 和 Mock V1 服务验收；
- 当前 v0.9.2 生产服务和生产图谱不替换、不迁移。
