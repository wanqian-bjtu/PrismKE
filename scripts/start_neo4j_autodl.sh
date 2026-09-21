#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="${PRISMKE_PROJECT_DIR:-/root/autodl-tmp/PrismKE}"
RUNTIME_DIR="${PRISMKE_RUNTIME_DIR:-${PROJECT_DIR}/runtime}"
if [[ "${RUNTIME_DIR}" != /* ]]; then
  RUNTIME_DIR="${PROJECT_DIR}/${RUNTIME_DIR}"
fi
NEO4J_HOME="${PRISMKE_NEO4J_HOME:-${RUNTIME_DIR}/neo4j/current}"
NEO4J_CONF="${PRISMKE_NEO4J_CONF:-${NEO4J_HOME}/conf}"
NEO4J_HTTP_PORT="${PRISMKE_NEO4J_HTTP_PORT:-7474}"
NEO4J_BOLT_PORT="${PRISMKE_NEO4J_BOLT_PORT:-7687}"
cd "${PROJECT_DIR}"

[[ -d "${NEO4J_CONF}" ]] || {
  echo "Neo4j configuration directory not found: ${NEO4J_CONF}" >&2
  exit 1
}

neo4j_command() {
  NEO4J_CONF="${NEO4J_CONF}" "${NEO4J_HOME}/bin/neo4j" "$@"
}

if neo4j_command status >/dev/null 2>&1; then
  echo "Neo4j is already running."
  neo4j_command status
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

AUTH_FILE="${RUNTIME_DIR}/neo4j/data/dbms/auth"
if [[ ! -f "${AUTH_FILE}" ]]; then
  NEO4J_CONF="${NEO4J_CONF}" \
    "${NEO4J_HOME}/bin/neo4j-admin" dbms set-initial-password "${PASSWORD}" >/dev/null
fi
echo "Starting Neo4j on loopback HTTP ${NEO4J_HTTP_PORT} and Bolt ${NEO4J_BOLT_PORT}."
neo4j_command start
neo4j_command status
