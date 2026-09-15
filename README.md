# PrismKE

PrismKE is an early research implementation of a schema-guided and evidence-aware
pipeline for general multimodal knowledge graph construction.

Version `0.1` implements a small but complete vertical slice:

- TXT, Markdown, text PDF, and image ingestion
- page, character-span, bounding-box, and image-level evidence
- YAML/JSON schema constraints
- mock and OpenAI-compatible text extraction providers
- deterministic entity resolution, claim normalization, conflict detection, and risk routing
- an idempotent local JSON graph store, SQLite workflow checkpoints, and revisions

Image files are represented as evidence assets in this version. Real OCR, visual fact
extraction, Neo4j, API, and web UI integrations are intentionally deferred.

## Install

```bash
conda create -n prismke python=3.11 -y
conda activate prismke
python -m pip install uv
uv sync --extra dev
```

## Quick Start

```bash
uv run prismke validate-schema configs/schemas/example.yaml
uv run prismke run examples/sample.md \
  --schema configs/schemas/example.yaml \
  --provider mock
```

The command prints a run ID. Inspect it with:

```bash
uv run prismke show-run RUN_ID
```

Review and resume a claim when a run is waiting for human review:

```bash
uv run prismke review RUN_ID --claim-id CLAIM_ID --decision approve
uv run prismke resume RUN_ID
```

## Mock Input Format

For deterministic examples and tests, the mock provider recognizes one claim per line:

```text
subject | relation | object | subject_type | object_type | confidence
```

It is a testing protocol, not the final extraction format.

## Runtime Data

Runtime files are written below `runtime/` and are excluded from Git:

- `runtime/runs`: serialized workflow runs
- `runtime/graph`: entities, claims, conflicts, and revisions
- `runtime/checkpoints.sqlite3`: node-level workflow snapshots

See [the construction plan](docs/PrismKE%E4%BB%8E%E9%9B%B6%E6%9E%84%E5%BB%BA%E8%AE%A1%E5%88%92.md)
for the research roadmap.
