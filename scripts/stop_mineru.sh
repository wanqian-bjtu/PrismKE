#!/usr/bin/env bash
set -euo pipefail

source "$(dirname -- "${BASH_SOURCE[0]}")/service_profile.sh"
MINERU_ROOT="${PRISMKE_MINERU_ROOT:-${PRISMKE_RUNTIME_DIR}/mineru}"
PID_FILE="${MINERU_ROOT}/run/mineru.pid"
[[ -f "${PID_FILE}" ]] || { echo "MinerU is not running."; exit 0; }
pid="$(cat "${PID_FILE}")"
if ! kill -0 "${pid}" 2>/dev/null; then
  rm -f "${PID_FILE}"
  echo "Removed stale MinerU PID file."
  exit 0
fi
command_line="$(tr '\0' ' ' <"/proc/${pid}/cmdline")"
[[ "${command_line}" == *"mineru-kit api-server"* ]] || {
  echo "Refusing to stop PID ${pid}: it is not this MinerU service" >&2
  exit 1
}
kill "${pid}"
for _ in $(seq 1 30); do
  kill -0 "${pid}" 2>/dev/null || { rm -f "${PID_FILE}"; echo "MinerU stopped."; exit 0; }
  sleep 1
done
echo "MinerU did not stop within 30 seconds" >&2
exit 1
