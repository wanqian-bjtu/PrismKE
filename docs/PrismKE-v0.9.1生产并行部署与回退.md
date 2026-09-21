# PrismKE v0.9.1 生产并行部署与回退

## 1. 目的与边界

v0.9.1 只加固 AutoDL 多实例部署，不改变 v0.9.0 的流程协议、抽取逻辑、实体阈值、案例检索或 Reflection 规则。生产 v0.7 与 v0.9.1 灰度实例使用独立端口、运行目录、锁、日志、PID、Neo4j 数据和应用数据库。

旧运行和检查点不迁移。最终切换只克隆现有 Neo4j 图谱，v0.9.1 的运行、检查点、审核和案例库从空目录开始。

## 2. 实例布局

| 项目 | v0.7 生产 | v0.9.1 灰度 |
|---|---|---|
| 代码目录 | `/root/autodl-tmp/PrismKE` | `/root/autodl-tmp/PrismKE-v09` |
| 运行目录 | `runtime` | `runtime/canary-v091` |
| Web | `127.0.0.1:8000` | `127.0.0.1:18009` |
| Neo4j HTTP | `127.0.0.1:7474` | `127.0.0.1:17474` |
| Neo4j Bolt | `127.0.0.1:7687` | `127.0.0.1:17687` |
| tmux | `prismke-web` | `prismke-v091-canary` |

端口不得直接开放到公网。灰度页面通过 SSH 转发访问：

```bash
ssh -p 41051 -L 18009:127.0.0.1:18009 root@connect.westc.seetacloud.com
```

## 3. 多实例控制变量

统一控制脚本支持以下实例级覆盖：

```text
PRISMKE_PROJECT_DIR
PRISMKE_RUNTIME_DIR
PRISMKE_NEO4J_HOME
PRISMKE_NEO4J_CONF
PRISMKE_NEO4J_HTTP_PORT
PRISMKE_NEO4J_BOLT_PORT
PRISMKE_TMUX_SESSION
PRISMKE_HEALTH_URL
PRISMKE_START_TIMEOUT
```

未设置时继续使用单实例默认值 `8000/7474/7687`。只有默认目录和 `prismke-web` 会话会兼容清理历史会话 `prismke-v03`，灰度实例不会操作它。

## 4. 灰度环境配置

灰度 `.env` 在服务器端由生产配置派生，只替换下列键，不输出文件内容：

```env
PRISMKE_RUNTIME_DIR=/root/autodl-tmp/PrismKE-v09/runtime/canary-v091
PRISMKE_API_HOST=127.0.0.1
PRISMKE_API_PORT=18009
PRISMKE_NEO4J_URI=bolt://127.0.0.1:17687
PRISMKE_EMBEDDING_MODEL_CACHE=/root/autodl-tmp/PrismKE/runtime/models/huggingface
```

文件权限必须为 `600`。API Key、Neo4j 密码和 Base URL 不进入命令输出、Git、日志或验收报告。

灰度 Neo4j 配置目录为：

```text
/root/autodl-tmp/PrismKE-v09/runtime/canary-v091/neo4j/conf
```

配置必须显式设置回环监听、独立数据/日志/run/import 目录，以及 `17474/17687` 端口。Neo4j 程序可复用生产安装目录，但不得共享数据、日志或 PID 目录。

## 5. 一致性备份和克隆

备份目录：

```text
/root/autodl-tmp/prismke-backups/v0.9.1/<UTC时间>/
```

Neo4j Community 不支持对运行中的已挂载数据库执行 dump。备份步骤必须是：停止生产 Web 和 Neo4j、执行 dump、检查 dump 信息与 SHA-256、立即恢复生产服务。维护窗口内不接受写入。

除 Neo4j dump 外，备份以下可变状态：

```text
runtime/graph
runtime/evidence
runtime/runs
runtime/review*
runtime/execution*
runtime/cases*
runtime/audit*
runtime/checkpoints.sqlite3
runtime/entity-governance.json
```

不复制模型、评测材料、日志和缓存。生成 `SHA256SUMS`，并使用以下命令验证归档：

```bash
neo4j-admin database load --info --from-path=<dump目录> neo4j
```

灰度恢复必须指定独立 `NEO4J_CONF`，并在 Neo4j 未运行时执行：

```bash
NEO4J_CONF=<灰度配置目录> neo4j-admin database load \
  --from-path=<dump目录> --overwrite-destination=true neo4j
```

## 6. 灰度启动与验收

通过实例环境变量调用统一脚本：

```bash
PRISMKE_PROJECT_DIR=/root/autodl-tmp/PrismKE-v09 \
PRISMKE_RUNTIME_DIR=/root/autodl-tmp/PrismKE-v09/runtime/canary-v091 \
PRISMKE_NEO4J_HOME=/root/autodl-tmp/PrismKE/runtime/neo4j/current \
PRISMKE_NEO4J_CONF=/root/autodl-tmp/PrismKE-v09/runtime/canary-v091/neo4j/conf \
PRISMKE_NEO4J_HTTP_PORT=17474 \
PRISMKE_NEO4J_BOLT_PORT=17687 \
PRISMKE_TMUX_SESSION=prismke-v091-canary \
PRISMKE_HEALTH_URL=http://127.0.0.1:18009/api/v1/health \
bash scripts/prismke_autodl.sh start
```

验收包括：

1. 生产与灰度健康接口同时为 `ok`。
2. 两套服务只监听回环地址。
3. Entity、Claim、Evidence、ConflictSet、Revision 数量和最新 Revision 一致。
4. Mock 完成案例检索、Reflection、校验、审核、提交、纠正和补偿回滚。
5. 真实 `qwen3.7-flash` 只运行 `test-valid-zh`、`test-relation-en`、`test-evidence-zh`；30,000 Token 上限，27,000 停止新增调用，不启用 VLM/OCR。
6. 未知用量、未知请求、鉴权失败或额度不足立即停止。

灰度图谱可包含验收数据，但正式切换时必须丢弃，并从切换时的最新生产 dump 重新创建。

## 7. 正式切换

1. 停止 v0.7，生成并验证最终 dump。
2. 停止灰度 v0.9.1，清理灰度 Neo4j 测试数据。
3. 将最终 dump 恢复到干净的 v0.9.1 生产 Neo4j 目录。
4. 使用默认端口 `8000/7474/7687` 启动 v0.9.1。
5. 核对健康状态、图谱数量、最新 Revision、证据读取和案例索引状态。
6. 完成不写图的 Mock 冒烟后再开放正常使用。

原 v0.7 目录、`.env` 和运行目录保持冻结，不删除或改写。

## 8. 回退

在 v0.9.1 尚无新图谱写入时，停止 v0.9.1 并按原配置启动 v0.7 即可。若 v0.9.1 已产生新 Revision，必须先停止服务、额外 dump v0.9.1 图谱并列出新增 Revision，不执行自动覆盖回退。

v0.9.1 的 Revision 不直接写回 v0.7。需要回退时，新增事实由人工决定后续迁移方式。

## 9. 完成标准

- 代码、服务器和 GitHub 的 `v0.9.1` 标签指向同一发布提交。
- 生产图谱备份可读且哈希可核验。
- 多实例启停互不影响，日志、锁和端口完全隔离。
- 灰度及真实三样例满足验收要求。
- 正式切换后默认端口运行 v0.9.1，v0.7 保留可回退状态。
