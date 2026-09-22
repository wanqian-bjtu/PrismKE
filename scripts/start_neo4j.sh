#!/usr/bin/env bash
set -euo pipefail

source "$(dirname -- "${BASH_SOURCE[0]}")/service_profile.sh"
prepare_neo4j_config
if [[ "${1:-}" == "--prepare" ]]; then
  exit 0
fi
[[ $# -eq 0 ]] || { echo "Usage: bash scripts/start_neo4j.sh [--prepare]" >&2; exit 2; }
PYTHON_BIN="${PRISMKE_PYTHON_BIN:-${PRISMKE_PROJECT_DIR}/.venv/bin/python}"
[[ -x "${PYTHON_BIN}" ]] || {
  echo "Project Python is not installed; set PRISMKE_PYTHON_BIN" >&2
  exit 1
}
NEO4J_BIN="${PRISMKE_NEO4J_HOME}/bin/neo4j"
[[ -x "${NEO4J_BIN}" ]] || {
  echo "Neo4j is not installed; set PRISMKE_NEO4J_HOME" >&2
  exit 1
}
neo4j_command() {
  NEO4J_CONF="${PRISMKE_NEO4J_CONF}" "${NEO4J_BIN}" "$@"
}
if neo4j_command status >/dev/null 2>&1; then
  echo "Neo4j is already running."
  neo4j_command status
  exit 0
fi
for port in "${PRISMKE_NEO4J_HTTP_PORT}" "${PRISMKE_NEO4J_BOLT_PORT}"; do
  if "${PYTHON_BIN}" - "${port}" <<'PY'
import socket
import sys

with socket.socket() as probe:
    probe.settimeout(0.5)
    raise SystemExit(0 if probe.connect_ex(("127.0.0.1", int(sys.argv[1]))) == 0 else 1)
PY
  then
    echo "Port ${port} is already in use by another Neo4j instance" >&2
    exit 1
  fi
done
cd "${PRISMKE_PROJECT_DIR}"
PASSWORD="$("${PYTHON_BIN}" - <<'PY'
from src.core.settings import Settings

print(Settings().neo4j_password or "")
PY
)"
[[ -n "${PASSWORD}" ]] || {
  echo "PRISMKE_NEO4J_PASSWORD is missing from .env" >&2
  exit 1
}
AUTH_FILE="${PRISMKE_RUNTIME_DIR}/neo4j/data/dbms/auth"
if [[ ! -f "${AUTH_FILE}" ]]; then
  NEO4J_CONF="${PRISMKE_NEO4J_CONF}" \
    "${PRISMKE_NEO4J_HOME}/bin/neo4j-admin" dbms set-initial-password "${PASSWORD}" >/dev/null
fi
echo "Starting Neo4j on loopback HTTP ${PRISMKE_NEO4J_HTTP_PORT} and Bolt ${PRISMKE_NEO4J_BOLT_PORT}."
neo4j_command start
neo4j_command status
