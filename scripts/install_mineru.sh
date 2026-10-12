#!/usr/bin/env bash
set -euo pipefail

source "$(dirname -- "${BASH_SOURCE[0]}")/service_profile.sh"
MINERU_ROOT="${PRISMKE_MINERU_ROOT:-${PRISMKE_RUNTIME_DIR}/mineru}"
MINERU_VENV="${PRISMKE_MINERU_VENV:-${MINERU_ROOT}/venv}"
MINERU_HOME="${PRISMKE_MINERU_HOME:-${MINERU_ROOT}/home}"
PYTHON_BIN="${PRISMKE_MINERU_PYTHON:-python3.11}"
MINERU_SPEC="${PRISMKE_MINERU_INSTALL_SPEC:-mineru==4.0.12}"
SMALL_BACKEND="${PRISMKE_MINERU_SMALL_BACKEND:-onnx}"
VLM_ENGINE="${PRISMKE_MINERU_VLM_ENGINE:-llama-cpp}"
MODEL_SOURCE="${PRISMKE_MINERU_DOWNLOAD_SOURCE:-auto}"
MAX_INSTALL_GIB="${PRISMKE_MINERU_MAX_INSTALL_GIB:-10}"
MIN_FREE_GIB="${PRISMKE_MINERU_MIN_FREE_GIB:-5}"
MIN_INITIAL_FREE_GIB="${PRISMKE_MINERU_MIN_INITIAL_FREE_GIB:-10}"

[[ "${MAX_INSTALL_GIB}" =~ ^[1-9][0-9]*$ ]] || {
  echo "PRISMKE_MINERU_MAX_INSTALL_GIB must be a positive integer" >&2
  exit 1
}
[[ "${MIN_FREE_GIB}" =~ ^[1-9][0-9]*$ ]] || {
  echo "PRISMKE_MINERU_MIN_FREE_GIB must be a positive integer" >&2
  exit 1
}
[[ "${MIN_INITIAL_FREE_GIB}" =~ ^[1-9][0-9]*$ ]] || {
  echo "PRISMKE_MINERU_MIN_INITIAL_FREE_GIB must be a positive integer" >&2
  exit 1
}

mkdir -p "${PRISMKE_RUNTIME_DIR}"
available_kib="$(df -Pk "${PRISMKE_RUNTIME_DIR}" | awk 'NR==2 {print $4}')"
(( available_kib >= MIN_INITIAL_FREE_GIB * 1024 * 1024 )) || {
  echo "MinerU installation requires at least ${MIN_INITIAL_FREE_GIB} GiB free before installation" >&2
  exit 1
}

mkdir -p "${MINERU_ROOT}" "${MINERU_HOME}"
cat >"${MINERU_HOME}/config.yaml" <<EOF
model:
  source: auto
  base_dir: "${MINERU_HOME}/models"
  small_backend: ${SMALL_BACKEND}
  vlm:
    engine: ${VLM_ENGINE}
EOF
"${PYTHON_BIN}" -m venv "${MINERU_VENV}"
"${MINERU_VENV}/bin/python" -m pip install --upgrade pip
"${MINERU_VENV}/bin/python" -m pip install "${MINERU_SPEC}"
export MINERU_HOME MINERU_CONFIG="${MINERU_HOME}/config.yaml"
export DO_NOT_TRACK=1 HF_HUB_DISABLE_TELEMETRY=1
installed_kib="$(du -sk "${MINERU_ROOT}" | awk '{print $1}')"
(( installed_kib <= MAX_INSTALL_GIB * 1024 * 1024 )) || {
  echo "MinerU environment exceeds the ${MAX_INSTALL_GIB} GiB installation limit before model download" >&2
  exit 1
}
source_args=()
if [[ "${MODEL_SOURCE}" != "auto" ]]; then
  source_args=(--source "${MODEL_SOURCE}")
fi
"${MINERU_VENV}/bin/mineru-kit" models download \
  --tier standard \
  --small-backend "${SMALL_BACKEND}" \
  --vlm-engine "${VLM_ENGINE}" \
  "${source_args[@]}"
"${MINERU_VENV}/bin/mineru-kit" models verify \
  --tier standard \
  --small-backend "${SMALL_BACKEND}" \
  --vlm-engine "${VLM_ENGINE}"

cat >"${MINERU_HOME}/config.yaml" <<EOF
model:
  source: local
  base_dir: "${MINERU_HOME}/models"
  small_backend: ${SMALL_BACKEND}
  vlm:
    engine: ${VLM_ENGINE}
EOF

installed_kib="$(du -sk "${MINERU_ROOT}" | awk '{print $1}')"
(( installed_kib <= MAX_INSTALL_GIB * 1024 * 1024 )) || {
  echo "MinerU environment and models exceed the ${MAX_INSTALL_GIB} GiB installation limit" >&2
  exit 1
}
available_kib="$(df -Pk "${PRISMKE_RUNTIME_DIR}" | awk 'NR==2 {print $4}')"
(( available_kib >= MIN_FREE_GIB * 1024 * 1024 )) || {
  echo "MinerU installation left less than ${MIN_FREE_GIB} GiB free; do not start the service" >&2
  exit 1
}
echo "MinerU footprint: ${installed_kib} KiB (limit: $((MAX_INSTALL_GIB * 1024 * 1024)) KiB)"
echo "MinerU Standard runtime: ${SMALL_BACKEND} + ${VLM_ENGINE} (local models)"
"${MINERU_VENV}/bin/mineru" version --json
