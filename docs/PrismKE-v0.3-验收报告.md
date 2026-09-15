# PrismKE v0.3 验收报告

## 一、验收范围

本报告记录 PrismKE `v0.3.0` 图谱服务化版本的发布前验收。模型抽取能力沿用 v0.2，本轮验收不调用真实百炼 API，重点验证图存储、证据、审核、版本、Web 服务和部署。

验收环境：

| 项目 | 结果 |
|---|---|
| 操作系统 | Ubuntu 22.04（AutoDL） |
| Python | 3.11，独立 Conda 环境 `prismke` |
| Java | OpenJDK 17.0.20 |
| Neo4j | 5.26.30 Community |
| 图后端 | JSON 与 Neo4j |
| Web | FastAPI + Gradio |

## 二、自动化检查

服务器执行：

```bash
uv run --all-extras ruff check .
uv run --all-extras mypy src
uv run --all-extras pytest -q
PRISMKE_TEST_NEO4J=1 uv run --all-extras pytest -q tests/test_neo4j_integration.py
```

结果：

- Ruff 通过。
- Mypy 严格模式检查 53 个源码文件，无问题。
- 自动测试共 75 项；默认运行 74 项通过，真实 Neo4j 测试按设计跳过。
- 在专用 Neo4j 数据库启用集成标志后，真实 Neo4j 测试通过。
- 测试过程中没有调用真实 LLM、VLM 或 OCR 云服务。

## 三、图谱与版本验收

已验证：

- `GraphCommit` 将 Document、Evidence、Entity、Claim、ConflictSet 和 Revision 放入单个 Neo4j managed transaction。
- 唯一约束、父版本检查和 `GraphHead` 写锁阻止重复资源与并发父版本覆盖。
- 相同 Revision 重复提交保持幂等。
- 事务失败不会留下可查询的半写入图谱。
- Claim 可追溯到 Evidence，Evidence 可追溯到不含服务器绝对路径的 GraphDocument。
- JSON 与 Neo4j 均支持有限实体邻域、版本列表和 Revision diff。
- 补偿回滚关闭新增 Claim、恢复更新前快照，并保留原 Revision 和补偿 Revision。
- 旧版无快照 Revision 只允许 ID 级差异查询，回滚返回明确冲突错误。

## 四、迁移与接口验收

JSON 到 Neo4j 迁移已在真实数据库验证：

- `--dry-run` 只报告迁移内容，不写数据库。
- 首次迁移成功写入 Document、Evidence、Entity、Claim 和 Revision。
- 重复迁移不会生成重复 Revision 或图节点。
- v0.2 图中缺失的 Evidence 可从内容寻址 EvidenceStore 恢复。

FastAPI 已验证以下闭环：

```text
上传文档与 Schema
-> 后台执行 Mock 工作流
-> 查询运行和 Claim
-> 提交人工审核
-> 使用同一 run_id 恢复
-> 查询 Revision 与 diff
-> 创建补偿回滚 Revision
```

API 对未知资源返回 `404`，无快照回滚等图完整性冲突返回 `409`，非法版本顺序返回 `422`。非回环地址监听时未配置 `PRISMKE_API_TOKEN` 会拒绝启动。

## 五、界面与部署验收

Gradio 工作台已经在桌面 `1440x900` 和移动 `390x844` 视口检查：

- 文档上传、运行状态、审核、证据、图谱、版本和健康页可访问。
- 实体邻域使用 NetworkX 布局和 Plotly 呈现，查询结果不是一次加载整图。
- 页面无横向溢出和内容遮挡。
- 浏览器不接收或显示服务器模型 API Key。
- 回滚操作要求显式确认。

AutoDL 原生部署已验证：

- Neo4j 和 PrismKE Web 只监听服务器回环地址。
- `/api/v1/health` 返回 Neo4j 后端健康。
- `/ui` 返回 HTTP 200。
- Windows 可通过 SSH 端口转发访问工作台和 Neo4j Browser。

Docker Compose 因 AutoDL 主机未安装 Docker，未在该服务器启动容器；`docker-compose.yml` 已完成静态 YAML 校验，并配置健康检查、依赖顺序、回环端口映射与持久化卷。容器运行验证保留为普通 Linux Docker 主机的部署验收项，不影响 AutoDL 原生部署。

## 六、安全检查

- `.env`、百炼 API Key、Neo4j 密码、运行结果和模型缓存未加入 Git。
- API Key、Neo4j 密码、Authorization 和图片 Base64 不写入日志与运行状态。
- 上传文件使用随机服务器文件名并限制为 64 MiB。
- 审核与回滚写入只追加审计日志。
- Neo4j Browser、Bolt 和 PrismKE API 均不直接暴露公网。

## 七、结论

v0.3 的核心目标已经完成：PrismKE 具备 JSON/Neo4j 双后端、可追溯证据、可审核工作流、可查询图谱、不可变版本、补偿回滚、HTTP API、研究界面和两种部署方案。除 Docker 容器实机启动需在具备 Docker 的普通 Linux 主机补验外，本版本达到发布条件。
