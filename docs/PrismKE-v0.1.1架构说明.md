# PrismKE v0.1.1 架构说明

## 1. 版本目标

v0.1.1 在 v0.1 纵向闭环基础上解决四类可靠性问题：代码职责平铺、证据只存在于运行结果、图谱逐条写入，以及恢复时重新遍历整张工作流。该版本不增加真实 OCR、VLM 或 Neo4j，而是先稳定后续能力共同依赖的领域协议和持久化边界。

## 2. 分层结构

```text
CLI
 └─ workflow       应用服务、LangGraph编排和节点
     ├─ parsing    文档到DocumentIR
     ├─ providers  LLM/VLM调用
     ├─ governance 实体、Claim、冲突和风险治理
     ├─ persistence 图、证据、检查点和运行记录
     ├─ domain     公共数据契约和Schema
     └─ core       配置、ID和异常
```

依赖方向固定从外层指向 `domain` 和 `core`。`domain` 不允许导入 Provider、存储实现、CLI 或工作流，以便未来的 FastAPI、Gradio、Neo4j 和本地模型复用同一套契约。

## 3. 可信处理流程

```text
ingest
  -> parse_document
  -> persist_evidence
  -> load_schema
  -> extract_claims
  -> resolve_entities
  -> normalize_claims
  -> detect_conflicts
  -> route_by_risk
  -> prepare_graph_commit
  -> commit_graph
```

解析完成后，原始文件与 `EvidenceRef` 先进入不可变 EvidenceStore。只有通过审核且全部证据验证成功的 Claim 才能进入 `GraphCommit`。实体、Claim、可持久化冲突和 Revision 经过一次文件锁保护的原子替换写入 `graph.json`。

## 4. 证据存储

原始文件按 SHA-256 存放在 `runtime/evidence/blobs/<前两位>/<哈希>`。每个证据引用在 `runtime/evidence/refs` 中保存为带校验和的 JSON。证据引用记录文档、来源哈希、模态、页码、字符范围、bbox 或图片资产 ID。

EvidenceStore 是先于图事务的不可变存储。写图失败时可能留下尚未被 Claim 引用的证据，但不会产生引用不存在证据的正式 Claim。未引用证据的回收不属于本版本。

## 5. 图事务

`GraphCommit` 是唯一写图入口，包含实体、正式 Claim、冲突集合和 Revision。提交时检查父版本、实体引用、Claim 引用、冲突引用及 Revision 引用，然后通过临时文件、`fsync` 和原子替换更新图文件。

相同 Revision 和相同内容的重复提交视为成功；相同 Revision ID 对应不同内容、过期父版本或缺失引用时拒绝提交。并发写入通过跨平台文件锁串行化，过期父版本必须由调用方重新读取后重建事务。

## 6. 冲突语义

关系默认是非功能、多值关系。只有 `functional: true`、`max_cardinality: 1` 或显式有限最大基数时，多个同时有效对象才可能形成冲突。`valid_to` 按右开区间处理，因此前一事实结束时间等于后一事实开始时间时不冲突。

对称关系通过无方向事实标识合并支持证据；互为逆关系的两种表达映射为同一事实标识。Schema 在加载时校验逆关系必须双向声明，避免单边配置造成不确定解释。

## 7. 运行标识与恢复

Run ID 由输入内容哈希、规范化 Schema 哈希、Schema 版本、Provider 指纹和流程版本共同生成，不包含文件路径、修改时间或 API Key。同一配置和内容重复运行会返回已有状态。

工作流使用 LangGraph `AsyncSqliteSaver`，以 Run ID 作为 `thread_id`。节点失败后，`resume` 使用同一线程和空输入恢复，已经成功并写入检查点的节点不会重新执行。v0.1 的自定义快照只支持查看，不进行隐式迁移；旧任务需要重新运行才能获得 v0.1.1 检查点。

## 8. Provider 规则

Mock Provider 必须通过 `--provider mock` 显式选择。选择 `openai-compatible` 时必须同时提供 `PRISMKE_LLM_API_KEY` 和 `PRISMKE_LLM_MODEL`，否则在创建运行记录前报错。Provider 指纹包含名称、模型、标准化服务地址、Prompt 版本、协议版本和实现版本，但不包含密钥。
