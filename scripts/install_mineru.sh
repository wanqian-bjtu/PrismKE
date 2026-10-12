#!/usr/bin/env bash
set -euo pipefail

source "$(dirname -- "${BASH_SOURCE[0]}")/service_profile.sh"
MINERU_ROOT="${PRISMKE_MINERU_ROOT:-${PRISMKE_RUNTIME_DIR}/mineru}"
MINERU_VENV="${PRISMKE_MINERU_VENV:-${MINERU_ROOT}/venv}"
MINERU_HOME="${PRISMKE_MINERU_HOME:-${MINERU_ROOT}/home}"
PYTHON_BIN="${PRISMKE_MINERU_PYTHON:-python3.11}"

mkdir -p "${PRISMKE_RUNTIME_DIR}"
available_kib="$(df -Pk "${PRISMKE_RUNTIME_DIR}" | awk 'NR==2 {print $4}')"
(( available_kib >= 10 * 1024 * 1024 )) || {
  echo "MinerU installation requires at least 10 GiB free in PRISMKE_RUNTIME_DIR" >&2
  exit 1
}

mkdir -p "${MINERU_ROOT}" "${MINERU_HOME}"
"${PYTHON_BIN}" -m venv "${MINERU_VENV}"
"${MINERU_VENV}/bin/python" -m pip install --upgrade pip
"${MINERU_VENV}/bin/python" -m pip install 'mineru[full]==4.0.12'
export MINERU_HOME MINERU_CONFIG="${MINERU_HOME}/config.yaml"
export DO_NOT_TRACK=1 HF_HUB_DISABLE_TELEMETRY=1
"${MINERU_VENV}/bin/mineru-kit" models download --tier standard

installed_kib="$(du -sk "${MINERU_ROOT}" | awk '{print $1}')"
(( installed_kib <= 8 * 1024 * 1024 )) || {
  echo "MinerU environment and models exceed the 8 GiB installation limit" >&2
  exit 1
}
available_kib="$(df -Pk "${PRISMKE_RUNTIME_DIR}" | awk 'NR==2 {print $4}')"
(( available_kib >= 5 * 1024 * 1024 )) || {
  echo "MinerU installation left less than 5 GiB free; do not start the service" >&2
  exit 1
}
echo "MinerU footprint: ${installed_kib} KiB (limit: 8388608 KiB)"
"${MINERU_VENV}/bin/mineru" version --json
