# PrismKE v0.11 多任务与多文档说明

## 版本边界

`dev/v0.11` 使用软件版本 `0.11.0.dev0` 和流程协议 `0.11.0`。它从已发布的 `v0.10.0` 创建，尚未合并 `main`、未创建发布标签，也未替换生产 v0.9.2。v0.10 及更早运行可只读查看，不能由 v0.11 检查点恢复。

## 六种任务模式

| 模式 | 输出 | 实体消歧 | 跨文档治理 | 写图 |
|---|---|---:|---:|---:|
| `entity_extraction` | 实体提及、类型、置信度、证据 | 否 | 否 | 否 |
| `relation_extraction` | 关系候选与证据 | 否 | 否 | 否 |
| `schema_information_extraction` | 实体、关系、属性、事件 | 否 | 否 | 否 |
| `joint_entity_relation_extraction` | 端到端实体与关系 | 否 | 否 | 否 |
| `joint_entity_relation_disambiguation` | 实体、关系、规范实体及映射 | 是 | 否 | 否 |
| `knowledge_graph_construction` | 完整治理、审核、融合和 Revision | 是 | 是 | 是 |

Web 和兼容接口默认使用 `knowledge_graph_construction`。前五种模式在生成 `TaskExtractionResult` 后停止；它们可以查看、审核和导出结果，但提交接口稳定返回 `TASK_MODE_NO_GRAPH_COMMIT`。

关系抽取支持 `auto` 与 `provided` 两种实体来源。`provided` 实体清单是 JSON 数组，每项包含 `name`、`entity_type`，可选 `char_start` 与 `char_end`。未给范围时，系统会先在文本块中定位名称；找不到时在模型请求前以 `PROVIDED_ENTITY_NOT_FOUND` 阻断，多处匹配时进入待确认状态。给定范围与原文不一致时返回 `PROVIDED_ENTITY_SPAN_INVALID`。模型只能输出给定实体之间的关系，服务端会再次过滤越界实体。

## 多文件批次

Web、API 和 `run-batch` 使用一个 `BatchRun` 管理多个 `BatchItem`。每个非重复文件对应独立子运行，分别保存解析、证据、Provider 请求账本、Token、状态和错误。相同内容哈希复用第一个子运行，不重复调用模型。

默认限制如下：

- 每批最多 20 个文件。
- 单文件最多 200 MiB。
- 每批总计最多 500 MiB。
- 上传按 1 MiB 数据块流式写入，不把完整文件留在请求内存。

一个子运行失败不会删除其他结果。批次会进入 `blocked`，失败项必须重试成功或由操作者填写原因后排除。完整知识构建批次只有在所有活动子运行完成审核后才进入 `awaiting_commit`。

提交时再次合并相同事实的来源运行、候选和证据，并检测跨文档功能关系冲突。发现冲突时不写图，批次记录稳定冲突 ID；操作者可以排除冲突来源后重新提交。一次成功批次只创建一个原子 Revision。

## 文件与证据

支持的输入为：

- TXT、Markdown、HTML。
- PDF、DOC、DOCX。
- 普通 JSON、PrismKE DocumentIR JSON。
- PNG、JPEG、WebP、TIFF、BMP。

XLS/XLSX、PPT/PPTX 和未知格式不在本版范围内。

普通 JSON 递归展开标量，数组保持原始顺序。每个字段 Evidence 保存 JSONPath、字段值哈希和原文件哈希；证据读取会重新解析原文件并验证路径和值，不把整个 JSON 直接拼接为模型输入。

旧 DOC 通过 LibreOffice Writer/headless 转成 DOCX。转换使用独立临时用户配置目录、参数数组调用和默认 120 秒超时，保存原文件哈希、派生 DOCX 哈希、工具版本与派生路径。缺少 LibreOffice、超时、转换失败或派生文件被改动都会阻断运行。

Linux 安装示例：

```bash
sudo apt-get update
sudo apt-get install -y libreoffice-writer
```

可用 `PRISMKE_LIBREOFFICE_BIN` 指定 `soffice`，留空时从 `PATH` 查找。

## API 与 CLI

批次接口：

```text
POST /api/v1/batches
GET  /api/v1/batches/{batch_id}
GET  /api/v1/batches/{batch_id}/results
POST /api/v1/batches/{batch_id}/items/{item_id}/retry
POST /api/v1/batches/{batch_id}/items/{item_id}/exclude
POST /api/v1/batches/{batch_id}/confirm-commit
GET  /api/v1/runs/{run_id}/results
```

单文件接口和 `prismke run` 保持兼容。示例：

```bash
prismke run-batch a.pdf b.docx c.json \
  --schema configs/schemas/example.yaml \
  --provider mock \
  --task-mode schema_information_extraction \
  --output runtime/results/batch.json
```

## 安全边界

- 通用启动脚本默认使用新的 `runtime/services/v011`；v0.10 及更早运行目录只读保留，不作为 v0.11 的恢复来源。
- 只有完整知识构建允许写图。
- 所有图提交继续经过证据、Schema、引用和父 Revision 硬校验。
- 属性和事件本版只进入抽取结果、校验、审核和导出，不写入正式图模型。
- 批次排除保留操作者和原因，不删除原文件、子运行或失败记录。
- API Key、Neo4j 密码、原始模型请求和完整向量不进入批次结果。
- 本版自动测试使用 Mock，不调用百炼、不修改生产图谱。
