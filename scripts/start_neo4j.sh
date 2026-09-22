#!/usr/bin/env bash
set -euo pipefail

source "$(dirname -- "${BASH_SOURCE[0]}")/service_profile.sh"
prepare_neo4j_config
if [[ "${1:-}" == "--prepare" ]]; then
  exit 0
fi
[[ $# -eq 0 ]] || { echo "Usage: bash scripts/start_neo4j.sh [--prepare]" >&2; exit 2; }
if ! NEO4J_CONF="${PRISMKE_NEO4J_CONF}" "${PRISMKE_NEO4J_HOME}/bin/neo4j" status >/dev/null 2>&1; then
  for port in "${PRISMKE_NEO4J_HTTP_PORT}" "${PRISMKE_NEO4J_BOLT_PORT}"; do
    if "${PRISMKE_PROJECT_DIR}/.venv/bin/python" - "${port}" <<'PY'
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
fi
cd "${PRISMKE_PROJECT_DIR}"
exec bash "${PRISMKE_PROJECT_DIR}/scripts/start_neo4j_autodl.sh"
