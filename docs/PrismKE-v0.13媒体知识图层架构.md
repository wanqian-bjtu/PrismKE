# PrismKE v0.13 媒体知识图层架构

## 1. 目标与边界

v0.13 将图片、图表、表格、公式和被实际引用的页面渲染纳入可查询、可审核、可版本化的图谱层。媒体对象与现实世界对象严格分开：

- `MediaContent` 表示内容寻址的媒体二进制，同一 SHA-256 只保存一个节点。
- `MediaOccurrence` 表示该内容在某一文档、页码和区域中的一次出现。
- `Entity` 表示图片中出现的人、组织、产品或设备等语义对象。
- `VisualAssertion` 表示经 Schema 约束的视觉属性、计数或空间关系。
- 原始 `VisualObservation` 是模型观察记录，不是正式图谱知识。

图片本体保存在 EvidenceStore。Neo4j、JSON GraphStore、Revision、API 和日志只保存内容哈希、证据 ID、定位信息和审核引用，不保存 Base64 或服务器绝对路径。

## 2. 建图资格

自动建立媒体内容与出现记录的对象包括：

1. 独立图片输入。
2. MinerU 识别出的表格、图表和公式。
3. 被 OCR、VLM、候选事实或证据实际引用的内嵌图片和页面渲染。

未使用的装饰图片不写图，运行警告记录 `media_excluded:<asset_id>:unused_or_decorative`。页面渲染只有被候选或证据引用时才进入媒体图层。

## 3. 稳定标识与去重

| 对象 | 稳定 ID 输入 |
|---|---|
| `MediaContent` | 图片二进制 SHA-256 |
| `MediaOccurrence` | 文档 ID、内容 ID、页码、bbox、Evidence ID |
| `GraphMediaRelation` | 出现记录、关系类型、目标、证据 |
| `VisualAssertion` | 主体、谓词、规范值、出现记录、证据 |

跨文档重复图片复用一个 `MediaContent`，但每个文档位置拥有独立 `MediaOccurrence`。提交预览会复用已存在的不可变内容对象，避免时间戳差异造成重复或误报。

## 4. Agent 协作

### 多模态抽取 Agent

- VLM 观察由系统补齐 `media_asset_id`、Evidence ID 和区域 bbox。
- 图片实体提及投影为 `CandidateMediaRelation(DEPICTS)`。
- 观察属性只有在匹配 Schema、区域证据有效且主体唯一链接时，才投影为 `CandidateVisualAssertion`。
- 普通描述、无法唯一确定主体的属性和不在 Schema 中的字段不转成正式知识。

### 实体与事实治理 Agent

- 图片提及沿用现有实体链接阈值、类型约束和 NIL 策略。
- 媒体按二进制哈希去重，出现位置按文档区分。
- 图文属性值不一致时记录 `cross_modal_attribute_conflict`，不得覆盖文本结论。

### 知识融合与审核 Agent

- 所有视觉独有 `DEPICTS`、视觉属性、计数和空间关系进入人工审核。
- 图文共同支持的已批准 Claim 可确定性生成 `SUPPORTS`。
- 审核事件必须与候选 ID、对象类型和 `approve` 决定完全匹配，不能复用其他任务的批准事件。

## 5. 图模型

```text
(:Document)-[:CONTAINS]->(:MediaOccurrence)
(:MediaOccurrence)-[:INSTANCE_OF]->(:MediaContent)
(:MediaOccurrence)-[:DEPICTS]->(:Entity)
(:MediaOccurrence)-[:SUPPORTS]->(:Claim)
(:MediaOccurrence)-[:HAS_ASSERTION]->(:VisualAssertion)
(:VisualAssertion)-[:ABOUT]->(:Entity)
```

`MediaRelation` 同时保留为可版本化关系对象，直接 `DEPICTS`/`SUPPORTS` 边用于查询。补偿回滚关闭出现记录、关系和视觉断言，并移除活动直接边；共享 `MediaContent` 与证据文件保留。

## 6. 原子提交与校验

媒体、实体、Claim 和 Revision 在同一 `GraphCommit` 中提交。提交前验证：

- 媒体 blob 存在，SHA-256 与 `MediaContent` 一致。
- EvidenceRef 可回读，页码、bbox 和画布合法。
- `DEPICTS` 目标实体存在，审核事件确实批准对应候选。
- `SUPPORTS` 目标 Claim 已批准且共享同一图片证据。
- 视觉断言谓词存在于 Schema，值类型和主体实体有效。
- 没有开放视觉审核或阻断问题。

任一条件失败时整个事务回滚，不产生半写入媒体节点。

## 7. 兼容性

旧 JSON 图缺少媒体集合时按空集合读取。v0.12 及更早运行只读展示，不使用 v0.13 检查点恢复。本版不迁移历史媒体、不实现图片向量检索，也不把普通文本属性和事件写入正式图模型。
