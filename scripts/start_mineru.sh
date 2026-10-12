#!/usr/bin/env bash
set -euo pipefail

source "$(dirname -- "${BASH_SOURCE[0]}")/service_profile.sh"
MINERU_ROOT="${PRISMKE_MINERU_ROOT:-${PRISMKE_RUNTIME_DIR}/mineru}"
MINERU_VENV="${PRISMKE_MINERU_VENV:-${MINERU_ROOT}/venv}"
MINERU_HOME="${PRISMKE_MINERU_HOME:-${MINERU_ROOT}/home}"
MINERU_PORT="${PRISMKE_MINERU_PORT:-18020}"
PID_FILE="${MINERU_ROOT}/run/mineru.pid"
LOG_FILE="${MINERU_ROOT}/logs/mineru.log"
UPLOAD_DIR="${MINERU_ROOT}/uploads"
MINERU_BIN="${MINERU_VENV}/bin/mineru-kit"

[[ "${PRISMKE_MINERU_HOST:-127.0.0.1}" == "127.0.0.1" ]] || {
  echo "MinerU must listen on 127.0.0.1" >&2
  exit 1
}
[[ -x "${MINERU_BIN}" ]] || {
  echo "MinerU 4.0.12 is not installed; run scripts/install_mineru.sh" >&2
  exit 1
}
command -v curl >/dev/null 2>&1 || {
  echo "curl is required for MinerU health checks" >&2
  exit 1
}
mkdir -p "${MINERU_ROOT}/run" "${MINERU_ROOT}/logs" "${UPLOAD_DIR}" "${MINERU_HOME}"
if [[ -f "${PID_FILE}" ]] && kill -0 "$(cat "${PID_FILE}")" 2>/dev/null; then
  echo "MinerU is already running (pid $(cat "${PID_FILE}"))."
  exit 0
fi
if curl -fsS "http://127.0.0.1:${MINERU_PORT}/v1/health" >/dev/null 2>&1; then
  echo "Port ${MINERU_PORT} is owned by another MinerU service" >&2
  exit 1
fi
export MINERU_HOME MINERU_CONFIG="${MINERU_HOME}/config.yaml"
export DO_NOT_TRACK=1 HF_HUB_DISABLE_TELEMETRY=1
nohup "${MINERU_BIN}" api-server \
  --host 127.0.0.1 --port "${MINERU_PORT}" --tier standard \
  --concurrency 1 --upload-dir "${UPLOAD_DIR}" >"${LOG_FILE}" 2>&1 &
pid=$!
printf '%s\n' "${pid}" >"${PID_FILE}"
for _ in $(seq 1 120); do
  if curl -fsS "http://127.0.0.1:${MINERU_PORT}/v1/health" >/dev/null 2>&1; then
    echo "MinerU is healthy on http://127.0.0.1:${MINERU_PORT} (pid ${pid})."
    exit 0
  fi
  kill -0 "${pid}" 2>/dev/null || {
    echo "MinerU exited before becoming healthy; inspect ${LOG_FILE}" >&2
    rm -f "${PID_FILE}"
    exit 1
  }
  sleep 1
done
echo "MinerU did not become healthy within 120 seconds" >&2
exit 1
