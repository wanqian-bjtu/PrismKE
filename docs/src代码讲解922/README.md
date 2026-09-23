# PrismKE `src` 逐文件代码讲解

基准提交：`dev/v0.10@f2f34d7`。覆盖 `99` 个 `.py` 文件、`882` 个类/函数/方法定义（含嵌套路由）；仅对应此提交，不代表生产 v0.9.2 的运行代码。

## 阅读顺序

1. `domain` 与 `core`：先理解契约、设置、错误与标识。
2. `providers` 与 `parsing`：再看外部模型、OCR、输入文档及资产。
3. `agents` 与 `governance`：理解三 Agent、实体解析、事实治理及硬校验。
4. `workflow` 与 `persistence`：沿节点、审核、事务和版本追踪数据。
5. `api`、`evaluation`、`web`、`cli.py`：最后看入口、评测与兼容转发。

## 术语

- **DocumentIR**：解析后的文档与媒体定位结构，供模型和证据校验使用。
- **Candidate / Claim**：前者为带原始证据的抽取候选，后者为规范化事实；未经治理和校验的候选不是正式图谱事实。
- **EvidenceRef**：证据位置与引用；合法坐标或哈希不保证事实语义正确。
- **GraphCommit / Revision**：经校验的事务输入与不可删的版本记录；回滚产生补偿版本。
- **Agent / 协调器**：三个 Agent 管理语义工具和结构化决策，LangGraph 管状态、路由与恢复；GraphStore 执行确定性写入。

## 模块依赖示意

```text
CLI / FastAPI / frontend
          ↓
workflow/service → workflow/graph (LangGraph)
          ↓                 ↓
agents/extraction → agents/governance → agents/fusion_review
          ↓                 ↓
providers + parsing → domain + governance/validation
                            ↓
                    persistence (JSON / Neo4j / Evidence)
```

这是一张阅读路径图，不声称每条箭头都是源码中的静态导入；逐个调用点以文件文档和源码行链接为准。

## 星级约定

`⭐⭐⭐⭐⭐`：工作流/硬校验/事务关键边界；`⭐⭐⭐⭐`：主要 Agent、服务入口和审核执行；`⭐⭐⭐`：重要支撑逻辑；`⭐⭐`：局部辅助；`⭐`：适配或转发。每个符号标题后的正文给出评级理由。

## 完整文件索引

### `src` 根目录

- [__init__.py](__init__.md)
- [__main__.py](__main__.md)
- [cli.py](cli.md)

### [agents](agents/README.md)

- [__init__.py](agents/__init__.md)
- [budget.py](agents/budget.md)
- [entity_governance_agent.py](agents/entity_governance_agent.md)
- [fusion_review_agent.py](agents/fusion_review_agent.md)
- [multimodal_extraction_agent.py](agents/multimodal_extraction_agent.md)
- [trace.py](agents/trace.md)

### [api](api/README.md)

- [__init__.py](api/__init__.md)
- [app.py](api/app.md)
- [models.py](api/models.md)

### [core](core/README.md)

- [__init__.py](core/__init__.md)
- [errors.py](core/errors.md)
- [execution_control.py](core/execution_control.md)
- [ids.py](core/ids.md)
- [settings.py](core/settings.md)

### [domain](domain/README.md)

- [__init__.py](domain/__init__.md)
- [agents.py](domain/agents.md)
- [cases.py](domain/cases.md)
- [documents.py](domain/documents.md)
- [execution.py](domain/execution.md)
- [knowledge.py](domain/knowledge.md)
- [reviews.py](domain/reviews.md)
- [schema.py](domain/schema.md)
- [validation.py](domain/validation.md)
- [workflow.py](domain/workflow.md)

### [evaluation](evaluation/README.md)

- [__init__.py](evaluation/__init__.md)
- [annotations.py](evaluation/annotations.md)
- [baseline_report.py](evaluation/baseline_report.md)
- [document_review.py](evaluation/document_review.md)
- [document_validation.py](evaluation/document_validation.md)
- [entity_linking.py](evaluation/entity_linking.md)
- [models.py](evaluation/models.md)
- [reflection.py](evaluation/reflection.md)
- [request_budget.py](evaluation/request_budget.md)
- [runner.py](evaluation/runner.md)

### [governance](governance/README.md)

- [__init__.py](governance/__init__.md)
- [alignment.py](governance/alignment.md)
- [claim_normalization.py](governance/claim_normalization.md)
- [conflicts.py](governance/conflicts.md)
- [entity_index.py](governance/entity_index.md)
- [entity_operations.py](governance/entity_operations.md)
- [entity_resolution.py](governance/entity_resolution.md)
- [review_guards.py](governance/review_guards.md)
- [risk.py](governance/risk.md)
- [governance/validation](governance/validation/README.md)
- [__init__.py](governance/validation/__init__.md)
- [context.py](governance/validation/context.md)
- [service.py](governance/validation/service.md)

### [parsing](parsing/README.md)

- [__init__.py](parsing/__init__.md)
- [adapters.py](parsing/adapters.md)
- [base.py](parsing/base.md)
- [registry.py](parsing/registry.md)
- [visual_assets.py](parsing/visual_assets.md)

### [persistence](persistence/README.md)

- [__init__.py](persistence/__init__.md)
- [audit.py](persistence/audit.md)
- [base.py](persistence/base.md)
- [cases.py](persistence/cases.md)
- [checkpoints.py](persistence/checkpoints.md)
- [entity_governance.py](persistence/entity_governance.md)
- [execution.py](persistence/execution.md)
- [file_evidence.py](persistence/file_evidence.md)
- [json_graph.py](persistence/json_graph.md)
- [legacy_evidence.py](persistence/legacy_evidence.md)
- [migration.py](persistence/migration.md)
- [neo4j_graph.py](persistence/neo4j_graph.md)
- [reviews.py](persistence/reviews.md)
- [runs.py](persistence/runs.md)
- [runtime_config.py](persistence/runtime_config.md)

### [providers](providers/README.md)

- [__init__.py](providers/__init__.md)
- [base.py](providers/base.md)
- [common.py](providers/common.md)
- [embedding.py](providers/embedding.md)
- [http_client.py](providers/http_client.md)
- [mock.py](providers/mock.md)
- [ocr.py](providers/ocr.md)
- [openai_compatible.py](providers/openai_compatible.md)
- [pricing.py](providers/pricing.md)
- [reflection.py](providers/reflection.md)
- [semantic.py](providers/semantic.md)
- [validation.py](providers/validation.md)
- [vlm.py](providers/vlm.md)

### [web](web/README.md)

- [__init__.py](web/__init__.md)
- [app.py](web/app.md)
- [corrections.py](web/corrections.md)
- [execution.py](web/execution.md)
- [review.py](web/review.md)
- [validation.py](web/validation.md)

### [workflow](workflow/README.md)

- [__init__.py](workflow/__init__.md)
- [cases.py](workflow/cases.md)
- [corrections.py](workflow/corrections.md)
- [execution.py](workflow/execution.md)
- [graph.py](workflow/graph.md)
- [nodes.py](workflow/nodes.md)
- [reflection.py](workflow/reflection.md)
- [review_details.py](workflow/review_details.md)
- [review_workspace.py](workflow/review_workspace.md)
- [reviews.py](workflow/reviews.md)
- [service.py](workflow/service.md)

## 维护方式

源码变化后先核对符号清单、行号、调用边界及相对链接，再更新讲解。本文档不包含环境密钥、运行数据或完整模型请求。
