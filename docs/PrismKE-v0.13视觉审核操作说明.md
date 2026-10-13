# PrismKE v0.13 视觉审核操作说明

## 1. 审核对象

视觉审核页处理两类候选：

- `media_relation`：图片出现位置描绘某个规范实体，即 `DEPICTS`。
- `visual_assertion`：图片中的属性、计数或空间关系。

审核详情同时显示原图或区域裁剪、出现位置、候选对象、规范实体、Schema 字段和 EvidenceRef。原始模型请求与密钥不会显示。

## 2. 决定契约

每次提交必须提供：

```text
decision: approve | reject | defer
reviewer: 非空审核人
reason: 非空理由
request_id: 幂等请求编号
expected_version: 当前任务版本
```

- `approve`：形成正式媒体关系或视觉断言。
- `reject`：保留候选和事件，不进入 GraphCommit。
- `defer`：任务继续阻断，版本递增，后续可再次决定。

相同 `request_id` 和相同决定返回原状态；同一编号携带不同决定返回冲突。版本过期返回 `VISUAL_REVIEW_VERSION_CONFLICT`。

## 3. Web 操作

1. 打开左侧“媒体知识 → 视觉审核”。
2. 选择运行并刷新队列。
3. 选择任务，核对区域证据、候选、实体映射和 Schema。
4. 选择决定，填写审核人与原因。
5. 提交后确认任务状态和版本变化。

所有视觉审核结束后，完整知识构建任务才可恢复到提交预览。非写图任务只更新可导出结果，不创建 Revision。

## 4. CLI

```bash
prismke list-visual-reviews RUN_ID
prismke review-visual RUN_ID TASK_ID \
  --decision approve \
  --reviewer 管理员 \
  --reason "区域证据与实体候选一致" \
  --expected-version 0
```

可通过 `--request-id` 指定稳定幂等编号；省略时 CLI 生成新编号。

## 5. 禁止行为

- 不得用其他候选的审核事件批准当前关系。
- 不得在图片缺失、哈希错误、bbox 越界或目标实体悬空时批准写图。
- 不得把视觉描述直接当作事实。
- 不得以视觉结果静默覆盖文本结论。
- 人物身份、图表数值、计数和空间关系始终需要人工确认。
