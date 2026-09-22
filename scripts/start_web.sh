#!/usr/bin/env bash
set -euo pipefail

source "$(dirname -- "${BASH_SOURCE[0]}")/service_profile.sh"
[[ "${PRISMKE_API_HOST:-127.0.0.1}" == "127.0.0.1" ]] || {
  echo "Web must listen on 127.0.0.1; use SSH forwarding to access it" >&2
  exit 1
}
[[ -f "${PRISMKE_PROJECT_DIR}/.env" ]] || {
  echo "Project .env is missing" >&2
  exit 1
}
export PRISMKE_API_HOST=127.0.0.1
export PRISMKE_GRAPH_STORE=neo4j
export PRISMKE_API_PORT="${PRISMKE_API_PORT:-8000}"
if [[ -d "${PRISMKE_PROJECT_DIR}/runtime/models/huggingface" ]]; then
  export PRISMKE_EMBEDDING_MODEL_CACHE="${PRISMKE_EMBEDDING_MODEL_CACHE:-${PRISMKE_PROJECT_DIR}/runtime/models/huggingface}"
fi
cd "${PRISMKE_PROJECT_DIR}"
exec "${PRISMKE_UV_BIN:-/root/miniconda3/envs/prismke/bin/uv}" run --no-sync prismke serve \
  --host 127.0.0.1 --port "${PRISMKE_API_PORT}"
