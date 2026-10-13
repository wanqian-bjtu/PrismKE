#!/usr/bin/env bash
set -euo pipefail

source "$(dirname -- "${BASH_SOURCE[0]}")/service_profile.sh"
MINERU_ROOT="${PRISMKE_MINERU_ROOT:-${PRISMKE_RUNTIME_DIR}/mineru}"
MINERU_PORT="${PRISMKE_MINERU_PORT:-18020}"
PID_FILE="${MINERU_ROOT}/run/mineru.pid"
command -v curl >/dev/null 2>&1 || {
  echo "curl is required for MinerU health checks" >&2
  exit 1
}
if [[ ! -f "${PID_FILE}" ]] || ! kill -0 "$(cat "${PID_FILE}")" 2>/dev/null; then
  echo "MinerU: stopped"
  exit 1
fi
curl -fsS "http://127.0.0.1:${MINERU_PORT}/v1/health" >/dev/null || {
  echo "MinerU: process running but health check failed"
  exit 1
}
echo "MinerU: healthy (pid $(cat "${PID_FILE}"), loopback port ${MINERU_PORT})"
