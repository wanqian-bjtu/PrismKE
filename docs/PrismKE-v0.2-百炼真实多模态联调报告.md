# PrismKE v0.2 百炼真实多模态联调报告

## 1. 联调结论

PrismKE v0.2 已使用阿里云百炼 OpenAI-compatible API 和 `qwen3.7-flash` 完成文本、OCR、图像及图文联合抽取联调。公开评测集共 12 个合成样例，全部正常完成，无未捕获异常。

在修正评测器对实体别名、关系别名和逆关系的等价判断后，最终 Claim Micro-F1 为 **0.9630**，实体 Micro-F1 为 **0.9804**，超过本轮 `0.75` 的目标。所有正式 Claim 均有关联证据，所有 bbox 均合法。

本次报告基于已缓存的真实 API 运行结果重新计分。复算没有重新调用百炼 API，调用数和 Token 总量与首次运行完全一致。

## 2. 联调配置

| 项目 | 配置 |
|---|---|
| 分支 | `dev/v0.2` |
| Python | 3.11 |
| 文本模型 | `qwen3.7-flash` |
| 视觉模型 | `qwen3.7-flash` |
| API 协议 | OpenAI-compatible Chat Completions |
| OCR | PaddleOCR 3.x，CPU |
| 图存储 | 原子 JSON GraphStore |
| 评测集 | `examples/eval_v0_2/manifest.json` |
| 样例数量 | 12 |

真实 API Key 和业务空间专属 Host 只保存在服务器 `.env` 中，没有写入仓库、日志、运行结果或本报告。

## 3. 冒烟测试

### 3.1 文本调用

最小中文文本调用成功，模型返回结构化候选事实：

```text
北辰实验室 --develops--> AuroraGraph
```

经过逆关系规范化后，正式 Claim 表示为：

```text
AuroraGraph --developed_by--> Northstar Labs
```

本次调用共使用 2,031 Token，耗时约 15.26 秒，无重试，估算费用约为人民币 0.00132 元。

### 3.2 图像调用

独立公开图片调用成功，模型识别出 `VisionDesk developed_by Northstar Labs`，并产生 3 个合法视觉区域。由于该次模型结果没有把 Claim 显式关联到 Observation，Claim 使用整图级证据并进入人工审核，这是预期的安全降级行为。

本次调用共使用 1,675 Token，耗时约 6.23 秒，无重试，估算费用约为人民币 0.00080 元。

## 4. 总体指标

| 指标 | 结果 |
|---|---:|
| 完成样例 | 12/12 |
| 失败样例 | 0 |
| Claim Precision | 1.0000 |
| Claim Recall | 0.9286 |
| Claim Micro-F1 | 0.9630 |
| Entity Precision | 1.0000 |
| Entity Recall | 0.9615 |
| Entity Micro-F1 | 0.9804 |
| 证据覆盖率 | 1.0000 |
| bbox 合法率 | 1.0000 |
| 场景通过率 | 0.9167 |
| Provider 调用数 | 22 |
| 输入 Token | 21,614 |
| 输出 Token | 30,792 |
| Token 总量 | 52,406 |
| API 累计耗时 | 272.74 秒 |
| 估算费用 | 人民币 0.02896 元 |

费用为 PrismKE 按价格快照计算的实验估算值，最终以阿里云账单为准。

## 5. 分场景结果

| 样例 | 主要场景 | Claim 结果 | 场景结果 | 运行状态 |
|---|---|---:|---|---|
| `support-zh-md` | 中文图文支持 | 1 TP | 通过 | completed |
| `support-en-html` | 英文 HTML 图文支持 | 1 TP | 通过 | completed |
| `conflict-zh-md` | 中文图文冲突 | 2 TP | 通过 | awaiting_review |
| `conflict-en-html` | 英文 HTML 图文冲突 | 1 TP、1 FN | 未通过 | completed |
| `image-only-png` | PNG 图片独有事实 | 1 TP | 通过 | completed |
| `image-only-jpeg` | JPEG 图片独有事实 | 1 TP | 通过 | completed |
| `scanned-pdf-zh` | 中文扫描 PDF 与 OCR | 1 TP | 通过 | completed |
| `scanned-pdf-en` | 英文扫描 PDF 与 OCR | 1 TP | 通过 | completed |
| `pdf-text-image-duplicate` | PDF 文本层与 OCR 去重 | 1 TP | 通过 | completed |
| `pdf-image-coarse-fallback` | 整图证据降级 | 1 TP | 通过 | awaiting_review |
| `alias-zh` | 中文别名与逆关系 | 1 TP | 通过 | completed |
| `alias-en` | 英文别名与逆关系 | 1 TP | 通过 | completed |

`awaiting_review` 不是执行失败。冲突事实和只有粗粒度视觉证据的事实按风险规则进入人工审核，说明风险路由正常工作。

## 6. 已发现问题

### 6.1 英文图文冲突漏检

`conflict-en-html` 的正文声明 `AtlasFlow` 由 `Harbor Research` 开发，图片声明开发者为 `Contoso AI`。真实 VLM 结果却把图片也抽取为 `Harbor Research`，系统因此将两条候选判为 `support`，没有生成预期的 `ConflictSet`。

检查中间结果后确认：文本抽取、对齐和冲突规则没有丢弃候选；根因是 VLM 受 HTML 邻近文本影响，忽略了图片中的冲突文字。这是视觉抽取阶段的语义偏置。

后续应在视觉 Prompt 中明确区分：

1. 图片自身可见内容是视觉事实的首要依据。
2. `alt`、图注和邻近文本只能作为辅助上下文。
3. 当图片内容与上下文不一致时，必须分别输出并标记冲突，不得用上下文覆盖视觉内容。
4. 对 OCR 可读区域，先要求模型逐项复述可见文本，再生成 Claim。

### 6.2 区域证据关联仍可加强

VLM 可以返回合法 Observation bbox，但部分 Claim 没有携带 `observation_index`，只能降级使用整图证据。当前风险路由会阻止这类视觉独有 Claim 自动写图，因此不会破坏正式图谱，但会增加审核量。

下一步应强化输出 Schema，要求视觉 Claim 必须引用至少一个 Observation；无法定位时才允许显式返回 `whole_image`。

## 7. 本轮修正

- Provider Prompt 要求使用原文中的实体表面形式，并遵循关系方向。
- 当模型返回关系方向与 Schema 相反时，使用声明的逆关系安全规范化。
- 评测器将实体别名、关系别名、逆关系和对称关系视为语义等价事实。
- OCR 与图片可去重合并，但不把同一图片中的 OCR 文字误算为独立模态支持。
- Windows 运行记录文件名改为可移植编码，同时兼容服务器旧记录。
- 无可分析视觉资产时不初始化 PaddleOCR；批量评测复用同一个 OCR 引擎。
- 文档没有文本块时跳过文本 API 调用，避免无效费用。

## 8. 当前判断与后续建议

v0.2 的真实多模态纵向闭环已经成立：文档解析、OCR、文本和视觉抽取、实体规范化、跨模态对齐、冲突路由、证据验证及写图流程均可运行。当前指标已经达到发布门槛。

建议在发布 `v0.2.0` 前只完成一轮小范围修正：强化视觉 Prompt 的“图片优先、上下文辅助”原则，新增 `conflict-en-html` 的离线回归测试，并使用单个失败样例做一次真实复测。无需重新运行全部 12 个样例；若该样例能够正确输出双方 Claim 和 `ConflictSet`，再执行 Mock 全量测试、合并 `main` 并创建标签。
