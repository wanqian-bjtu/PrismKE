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

唯一精确命中仍会检查可用的实体上下文：归一化上下文相似度低于 `0.65` 时视为强冲突并进入审核。该边界是保守启发式，需要在真实文档上继续校准。

实体向量文本由规范名称、别名、实体类型、稳定属性和限制长度的上下文摘要组成。首版使用 BGE-M3 的 1024 维 Dense Embedding；Sparse、ColBERT 和额外 Reranker 不在 v0.4 范围内。

默认模型快照固定为 `5617a9f61b028005a4858fdac845db406aefb181`，可通过 `PRISMKE_EMBEDDING_MODEL_REVISION` 显式修改。模型文件保存在数据盘的 `runtime/models/huggingface`，正常 Web 请求只允许读取已准备的本地快照。

JSON GraphStore 在进程内计算余弦相似度。Neo4j 使用 `entity_embedding_bge_m3` Vector Index。向量连同模型指纹和实体文本哈希保存，但不进入 Revision 的 before/after 快照，也不写入运行结果、检查点或日志。

## 合并与拆分

已经拥有不同稳定 ID 的规范实体不会自动合并。系统只创建 `EntityOperation` 和 `EntityReviewTask`，审核批准后才提交图事务。

合并选定一个保留实体，转移别名、属性和证据，将其他实体标记为 inactive 并建立 `MERGED_INTO`。活跃 Claim 在同一事务中改指向保留实体。

拆分要求审核者提供新实体及 Claim 到新实体的分配。每个被分配 Claim 必须具有证据。原实体仍有未迁移的活跃 Claim 时继续保留，否则标记为 inactive。

两类操作都保存实体和 Claim 的前后快照。回滚创建补偿 Revision，不删除原治理 Revision。

拆分目标必须使用新的实体 ID，不能覆盖已有实体。审批前会重新校验建议中的实体和 Claim 快照，过期建议必须重新创建。实体内容更新或回滚后，旧向量在同一事务中失效；再执行 `rebuild-entity-index` 补齐派生索引。

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

## AutoDL 验证记录（2026-09-16）

服务器使用 Python 3.11、RTX 4090D 24 GB、PyTorch `2.6.0+cu124`。BGE-M3 模型已显式下载到数据盘，并完成真实 FP16 Dense 编码。固定 CUDA 12.4 构建是为了适配当前服务器驱动，避免安装不兼容的最新 CUDA 构建。

公开合成基线包含 60 个实体提及，以及五组合并、五组拆分治理场景。真实 BGE-M3 实体评测结果如下：

| 指标 | 本次结果 |
|---|---:|
| 已知实体 Top-10 候选召回率 | 1.00 |
| 已知实体 Top-1 候选准确率 | 1.00 |
| NIL F1 | 1.00 |
| 跨文档聚类 B-Cubed F1 | 1.00 |
| 进入人工审核的提及比例 | 25% |
| 错误自动链接率（自动链接为分母，含 NIL 误链接） | 0% |

Top-1 指标包含待审核任务的首位候选，不代表所有提及均被自动提交。合成材料中的不少名称和别名可以精确命中，因此这些指标只证明回归基线通过，不能作为开放域真实文档的最终论文结果。

首次加载模型并建索引约 7.64 秒，60 个提及消歧约 2.04 秒，GPU 峰值已分配显存约 1110 MiB。缓存复测总耗时约 1.37 秒；缓存吞吐不能当作 GPU 新文本编码吞吐。

模型预热后另测 32 条未缓存短文本：批量编码及缓存落盘约 0.118 秒，约 271 条/秒，GPU 峰值已分配显存约 1126 MiB。该结果只适用于本次短文本批次，不代表 512 Token 长文本的吞吐。

Neo4j 真实索引状态为 `ONLINE`。首次重建写入 13 个已有活跃实体，重复重建写入 0 个。对同一批实体、向量和查询，JSON 与 Neo4j 的候选及原始余弦分数一致；Neo4j ANN 在更大图谱上仍需单独测试召回率，不承诺与穷举检索永远相同。合并、拆分、补偿回滚已在真实 Neo4j 集成测试中执行。

完整结果保存在服务器 `runtime/evaluation/entity-resolution-v0.4-bge-m3-final.json`，不提交运行产物、模型或密钥。实体评测和治理测试未调用百炼 API。

发布回归通过 Ruff、Mypy 与 107 项测试（包含真实 Neo4j 测试）。浏览器验证了实体候选检索与治理历史查询，1366×900 桌面及 390×844 手机视口无横向溢出。原生 Neo4j 与 Web 服务重启后健康，7474、7687、8000 只监听回环地址。Docker Compose 本轮未重新进行实机启动验证。
