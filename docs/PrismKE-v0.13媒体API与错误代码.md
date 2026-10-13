# PrismKE v0.13 媒体 API 与错误代码

## 1. 查询接口

| 方法 | 路径 | 用途 |
|---|---|---|
| GET | `/api/v1/media` | 按文档、实体、Claim、媒体类型或审核状态筛选 |
| GET | `/api/v1/media/{occurrence_id}` | 查看媒体内容、出现位置、关系和视觉断言 |
| GET | `/api/v1/entities/{entity_id}/media` | 查看实体关联图片 |
| GET | `/api/v1/claims/{claim_id}/media` | 查看 Claim 的图片证据 |
| GET | `/api/v1/runs/{run_id}/visual-reviews` | 查看候选与视觉审核任务 |
| POST | `/api/v1/runs/{run_id}/visual-reviews/{task_id}/decision` | 提交幂等视觉决定 |

列表查询参数：`document_id`、`entity_id`、`claim_id`、`media_type`、`review_status`。媒体内容读取继续使用受控证据接口，不在媒体元数据中返回磁盘路径。

## 2. 审核请求

```json
{
  "decision": "approve",
  "reviewer": "管理员",
  "reason": "区域证据与实体候选一致",
  "request_id": "review-request-001",
  "expected_version": 0
}
```

## 3. 稳定错误代码

| 代码或错误 | 含义 | 处理 |
|---|---|---|
| `VISUAL_REVIEW_REQUIRES_IDENTITY_REASON_REQUEST` | 缺少审核人、理由或请求号 | 补齐字段 |
| `VISUAL_REVIEW_REQUEST_CONFLICT` | 同一请求号对应不同任务或决定 | 使用原请求或新请求号 |
| `VISUAL_REVIEW_VERSION_CONFLICT` | 任务版本已变化 | 刷新任务后重试 |
| `VISUAL_REVIEW_ALREADY_RESOLVED` | 任务已完成 | 查看历史事件 |
| `VISUAL_REVIEW_TARGET_ENTITY_UNRESOLVED` | DEPICTS 尚未链接实体 | 先完成实体治理 |
| `VISUAL_REVIEW_SUBJECT_UNRESOLVED` | 视觉断言主体未解析 | 先完成实体治理 |
| `VISUAL_REVIEW_PENDING` | 仍有开放视觉任务 | 完成审核后恢复 |
| `media occurrence evidence is invalid` | 证据缺失或篡改 | 恢复证据并重新校验 |
| `DEPICTS review event does not approve relation` | 审核事件与候选不匹配 | 禁止提交，核对事件 |
| `SUPPORTS evidence does not support target claim` | Claim 未引用该图片证据 | 修正证据关联 |
| `visual assertion predicate is not in schema` | 视觉字段不在 Schema | 修改 Schema 或拒绝候选 |

## 4. 安全输出

API 不返回 Base64、服务器绝对路径、完整向量、API Key、Neo4j 密码或原始模型请求。`MediaContent` 的哈希和尺寸属于可查询元数据；二进制只能通过受控 EvidenceStore 路径读取。
