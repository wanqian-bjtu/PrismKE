# PrismKE v0.3 部署与操作

本文说明 `v0.3.0` 的 Neo4j、FastAPI、Gradio、迁移和版本回滚用法。v0.3 面向单用户研究与论文演示，服务器端口默认不暴露到公网。

## 一、组件关系

```text
CLI / Gradio / FastAPI
         |
         v
  PrismKEService
    |         |
    v         v
LangGraph   GraphStore
              |-- JSON
              `-- Neo4j
    |
    v
EvidenceStore + RunRepository + AuditLog
```

三种入口共享 `PrismKEService`。模型密钥只从服务器 `.env` 读取，浏览器只选择 Provider 名称。

## 二、AutoDL 原生部署

进入项目并安装开发、Neo4j Driver 和 Web 依赖：

```bash
cd /root/autodl-tmp/PrismKE
conda activate prismke
uv sync --extra dev --extra neo4j --extra web
```

安装 OpenJDK 17 和 Neo4j 5.26 LTS Community：

```bash
bash scripts/install_neo4j_autodl.sh
```

Neo4j 程序、数据和日志全部位于：

```text
/root/autodl-tmp/PrismKE/runtime/neo4j
```

在 `.env` 中增加以下配置。密码应使用独立随机值，不要复用 SSH 或百炼密钥：

```env
PRISMKE_GRAPH_STORE=neo4j
PRISMKE_NEO4J_URI=bolt://127.0.0.1:7687
PRISMKE_NEO4J_USER=neo4j
PRISMKE_NEO4J_PASSWORD=<填写独立密码>
PRISMKE_NEO4J_DATABASE=neo4j
PRISMKE_API_HOST=127.0.0.1
PRISMKE_API_PORT=8000
```

首次启动会使用 `.env` 中的密码初始化 Neo4j。推荐通过统一脚本同时管理 Neo4j 与 PrismKE Web：

```bash
bash scripts/prismke_autodl.sh start
```

查看服务状态与健康接口：

```bash
bash scripts/prismke_autodl.sh status
bash scripts/prismke_autodl.sh health
```

其他生命周期命令：

```bash
bash scripts/prismke_autodl.sh restart
bash scripts/prismke_autodl.sh stop
bash scripts/prismke_autodl.sh logs web --lines 100
bash scripts/prismke_autodl.sh logs web --follow
bash scripts/prismke_autodl.sh logs neo4j --lines 100
```

统一脚本具有以下行为：

- Web 使用稳定的 `prismke-web` tmux 会话，旧的 `prismke-v03` 会话会在启动时平滑替换。
- `start` 和 `stop` 可以重复执行，不会创建重复进程或因服务已停止而失败。
- 服务控制使用文件锁，拒绝同时执行两个启动或停止操作。
- 启动前检查 7474、7687 和 API 端口，端口被非受管进程占用时拒绝启动。
- Web 健康检查失败会回滚本次新启动的组件，并输出最后 30 行 Web 日志。
- `status` 仅在 Neo4j、tmux 和 HTTP 健康检查全部通过时返回退出码 `0`。

日志位置：

```text
runtime/logs/prismke-web.log
runtime/neo4j/logs/
```

Web 日志超过 10 MiB 时在下次启动前轮转，最多保留 5 份。脚本不会配置 AutoDL 平台级开机启动，实例开启后仍需手动执行一次 `start`。

故障排查时可以绕过统一脚本手工启动：

```bash
bash scripts/start_neo4j_autodl.sh
tmux new -s prismke-web
conda activate prismke
cd /root/autodl-tmp/PrismKE
prismke serve
```

按 `Ctrl+B`，再按 `D` 脱离手工创建的 tmux 会话。

## 三、本地访问服务器

在 Windows 本地终端建立端口转发：

```bash
ssh -p 41051 \
  -L 8000:127.0.0.1:8000 \
  -L 7474:127.0.0.1:7474 \
  root@connect.westc.seetacloud.com
```

随后访问：

- PrismKE 工作台：`http://127.0.0.1:8000/ui`
- API 文档：`http://127.0.0.1:8000/docs`
- Neo4j Browser：`http://127.0.0.1:7474`

不要在 AutoDL 安全组中直接开放 7474、7687 或 8000。

## 四、图谱迁移

先执行只读预检：

```bash
prismke migrate-graph \
  --from-json runtime/graph/graph.json \
  --to neo4j \
  --dry-run
```

确认文档、证据、实体、Claim、冲突和 Revision 数量后执行迁移：

```bash
prismke migrate-graph \
  --from-json runtime/graph/graph.json \
  --to neo4j
```

迁移以 Revision 为单位提交。相同 Revision 重复执行为幂等操作。v0.1/v0.2 的旧图文件没有图内 Evidence 时，迁移器会尝试从同级 `runtime/evidence` 恢复引用；无法恢复的证据会出现在预检警告中。

## 五、HTTP API

所有业务接口使用 `/api/v1` 前缀：

| 方法 | 路径 | 用途 |
|---|---|---|
| POST | `/runs` | 上传文档与 Schema，创建后台任务 |
| GET | `/runs/{run_id}` | 查询运行状态和节点轨迹 |
| POST | `/runs/{run_id}/resume` | 恢复失败或审核完成的任务 |
| GET | `/runs/{run_id}/claims` | 查询本次运行 Claim |
| GET | `/evidence/{evidence_id}` | 查询证据元数据 |
| GET | `/evidence/{evidence_id}/content` | 读取原文或裁剪区域 |
| POST | `/reviews/{task_id}` | 提交批准或拒绝决定 |
| GET | `/entities/{entity_id}/neighborhood` | 查询有限实体邻域 |
| GET | `/revisions` | 查询版本时间线 |
| GET | `/revisions/diff?from=...&to=...` | 比较两个版本 |
| POST | `/revisions/{revision_id}/rollback` | 创建补偿 Revision |
| GET | `/health` | 检查应用和图后端 |

当 `PRISMKE_API_HOST` 不是回环地址时，启动前必须配置 `PRISMKE_API_TOKEN`，请求使用：

```text
Authorization: Bearer <PRISMKE_API_TOKEN>
```

## 六、版本与回滚

新 Revision 保存每项实体、Claim 和 ConflictSet 变更的 `before` 与 `after` 快照。回滚不会删除历史：

- 新增 Claim 被关闭 `tx_to`。
- 更新资源恢复 `before` 快照。
- 新增 ConflictSet 标记为 `resolved`。
- 新增实体仅在没有活动 Claim 引用时标记为 `inactive`。
- 回滚本身产生新的不可变补偿 Revision。

旧 Revision 没有状态快照，只能比较涉及的资源 ID，不能执行自动回滚。

## 七、Docker Compose

普通 Linux 主机可使用：

```bash
cp .env.example .env
# 填写 Neo4j 密码、API Token 和所需模型配置
docker compose up --build -d
docker compose ps
```

Compose 仅将 7474、7687 和 8000 映射到宿主机回环地址。运行数据挂载到 `runtime/compose/`，`.env`、证据和模型不会写入镜像。

## 八、验收命令

```bash
uv run ruff check .
uv run mypy src
uv run pytest
bash scripts/prismke_autodl.sh status
bash scripts/prismke_autodl.sh health
```

验收全过程使用 Mock Provider，不消耗百炼额度。
