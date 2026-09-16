# PrismKE v0.4 实体链接与跨文档治理

## 目标

v0.4 在现有 Schema、证据、Claim 和 Revision 基础上增加语义实体解析。系统先执行确定性的名称、别名和类型匹配，再使用 BGE-M3 召回候选，最后根据置信度与候选差距选择自动链接、人工审核或创建 NIL 实体。

```text
EntityMention
  -> 精确名称与别名匹配
  -> 类型硬过滤
  -> BGE-M3 Dense Top-K
  -> 名称、上下文和邻域重排
  -> 自动链接 / EntityReviewTask / NIL
  -> Claim 规范化
```

## 决策规则

默认检索 `Top-K=10`。精确别名且类型相同的实体直接链接。语义候选最高分不低于 `0.88`、领先第二名至少 `0.08` 且不存在硬冲突时自动链接。最高分不低于 `0.65` 的模糊候选进入审核，其余提及创建稳定 NIL 实体。

不同类型的同名实体属于硬冲突。同名同类型但存在多个候选时也不会直接取最后一个精确命中，而是继续使用上下文和邻域消歧。系统保留候选与证据并暂停工作流，不会通过降低阈值绕过审核。Embedding Provider 或 Neo4j 向量索引不可用时只保留唯一精确匹配，其他模糊结果进入审核。

## 向量数据

实体向量文本由规范名称、别名、实体类型、稳定属性和限制长度的上下文摘要组成。首版使用 BGE-M3 的 1024 维 Dense Embedding；Sparse、ColBERT 和额外 Reranker 不在 v0.4 范围内。

JSON GraphStore 在进程内计算余弦相似度。Neo4j 使用 `entity_embedding_bge_m3` Vector Index。向量连同模型指纹和实体文本哈希保存，但不进入 Revision 的 before/after 快照，也不写入运行结果、检查点或日志。

## 合并与拆分

已经拥有不同稳定 ID 的规范实体不会自动合并。系统只创建 `EntityOperation` 和 `EntityReviewTask`，审核批准后才提交图事务。

合并选定一个保留实体，转移别名、属性和证据，将其他实体标记为 inactive 并建立 `MERGED_INTO`。活跃 Claim 在同一事务中改指向保留实体。

拆分要求审核者提供新实体及 Claim 到新实体的分配。每个被分配 Claim 必须具有证据。原实体仍有未迁移的活跃 Claim 时继续保留，否则标记为 inactive。

两类操作都保存实体和 Claim 的前后快照。回滚创建补偿 Revision，不删除原治理 Revision。

## 运维步骤

```bash
uv sync --extra dev --extra neo4j --extra web --extra embedding
prismke prepare-model --embedding BAAI/bge-m3
prismke rebuild-entity-index --backend neo4j --dry-run
prismke rebuild-entity-index --backend neo4j
prismke evaluate-entities examples/entity_resolution_v0_4/manifest.json \
  --embedding-provider bge-m3 \
  --output runtime/evaluation/entity-resolution-v0.4.json
bash scripts/prismke_autodl.sh restart
```

自动测试使用 Mock Embedding，不下载模型，也不调用百炼 API。真实 BGE-M3 验收只在 AutoDL GPU 服务器执行。
