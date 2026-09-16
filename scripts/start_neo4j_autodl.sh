#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="${PRISMKE_PROJECT_DIR:-/root/autodl-tmp/PrismKE}"
NEO4J_HOME="${PROJECT_DIR}/runtime/neo4j/current"
cd "${PROJECT_DIR}"

if "${NEO4J_HOME}/bin/neo4j" status >/dev/null 2>&1; then
  echo "Neo4j is already running."
  "${NEO4J_HOME}/bin/neo4j" status
  exit 0
fi

PASSWORD="$(${PROJECT_DIR}/.venv/bin/python - <<'PY'
from prismke.core.settings import Settings
print(Settings().neo4j_password or "")
PY
)"
if [[ -z "${PASSWORD}" ]]; then
  echo "PRISMKE_NEO4J_PASSWORD is missing from .env" >&2
  exit 1
fi

AUTH_FILE="${PROJECT_DIR}/runtime/neo4j/data/dbms/auth"
if [[ ! -f "${AUTH_FILE}" ]]; then
  "${NEO4J_HOME}/bin/neo4j-admin" dbms set-initial-password "${PASSWORD}" >/dev/null
fi
"${NEO4J_HOME}/bin/neo4j" start
"${NEO4J_HOME}/bin/neo4j" status
