# PrismKE Deployment and Operations

This guide covers the supported v0.14 deployment paths: Docker Compose and a native
Linux/WSL installation. All services bind to loopback by default. Use SSH forwarding or
a properly secured reverse proxy for remote access.

## 1. Prerequisites

- Python 3.11 (`>=3.11,<3.12`) and `uv`
- Git
- Docker with Compose, or Linux/WSL with Java 21, `curl`, `flock`, `tar`, and `tmux`
- Optional NVIDIA GPU only for local embedding, OCR, or MinerU workloads

Clone the repository and create the local configuration file:

```bash
git clone https://github.com/wanqian-bjtu/PrismKE.git
cd PrismKE
cp .env.example .env
```

Set unique values for at least `PRISMKE_NEO4J_PASSWORD` and `PRISMKE_API_TOKEN` in
`.env`. Keep `.env`, model caches, runtime data, and generated reports out of Git.

## 2. Docker Compose

Docker Compose starts PrismKE and Neo4j with persistent named volumes:

```bash
docker compose up --build -d
docker compose ps
docker compose logs -f prismke
```

The default host bindings are loopback-only:

- PrismKE UI: <http://127.0.0.1:8000/ui>
- PrismKE API: <http://127.0.0.1:8000/api/v1>
- Neo4j Browser: <http://127.0.0.1:7474>
- Neo4j Bolt: `bolt://127.0.0.1:7687`

Stop the stack without removing data:

```bash
docker compose down
```

Do not add `-v` unless you intentionally want to remove the Compose volumes.

## 3. Native Linux or WSL

Install the project and the Web/Neo4j dependencies:

```bash
python -m pip install uv
uv sync --extra web --extra neo4j
cp .env.example .env
```

Install the pinned Neo4j Community distribution into `runtime/neo4j` and prepare its
isolated configuration:

```bash
bash scripts/install_neo4j.sh
bash scripts/start_neo4j.sh --prepare
```

The unified service script manages Neo4j and the Web process:

```bash
bash scripts/prismke.sh start
bash scripts/prismke.sh status
bash scripts/prismke.sh health
```

Common operations:

```bash
bash scripts/prismke.sh restart
bash scripts/prismke.sh stop
bash scripts/prismke.sh logs web --lines 100
bash scripts/prismke.sh logs web --follow
bash scripts/prismke.sh logs neo4j --lines 100
```

For foreground development without the service manager:

```bash
uv run prismke serve --host 127.0.0.1 --port 8000
```

`scripts/service_profile.sh` derives paths from the repository by default. Multiple
isolated instances can override `PRISMKE_PROJECT_DIR`, `PRISMKE_RUNTIME_DIR`,
`PRISMKE_NEO4J_HOME`, `PRISMKE_NEO4J_CONF`, `PRISMKE_NEO4J_HTTP_PORT`,
`PRISMKE_NEO4J_BOLT_PORT`, and `PRISMKE_TMUX_SESSION`.

## 4. Remote Access

Keep the services on loopback and forward only the ports you need:

```bash
ssh -N \
  -L 8000:127.0.0.1:8000 \
  -L 7474:127.0.0.1:7474 \
  -L 7687:127.0.0.1:7687 \
  user@server.example
```

Then open <http://127.0.0.1:8000/ui> locally. For shared deployments, terminate TLS and
enforce authentication at a maintained reverse proxy. Do not expose ports 7474, 7687,
or 8000 directly to the public internet.

## 5. Health and Data Migration

Check the HTTP health endpoint:

```bash
curl --fail http://127.0.0.1:8000/api/v1/health
```

Migrate a local JSON graph to Neo4j only after a successful dry run:

```bash
uv run prismke migrate-graph \
  --from-json runtime/graph/graph.json \
  --to neo4j \
  --dry-run

uv run prismke migrate-graph \
  --from-json runtime/graph/graph.json \
  --to neo4j
```

Back up `runtime/` or the corresponding Compose volumes before upgrades. Workflow
checkpoints are protocol-versioned; resume old runs with the release that created them.

## 6. Security Checklist

- Replace all example passwords and tokens before starting services.
- Keep `.env`, `runtime/`, logs, model caches, and uploaded source documents untracked.
- Bind application and database ports to `127.0.0.1`.
- Use SSH forwarding or an authenticated TLS reverse proxy for remote access.
- Run PrismKE as an unprivileged user and restrict filesystem permissions.
- Review logs and exported artifacts before sharing; they may contain source evidence.
- Never reuse a production graph or credential file for validation scripts.
