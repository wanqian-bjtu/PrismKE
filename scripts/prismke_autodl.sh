#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="${PRISMKE_PROJECT_DIR:-/root/autodl-tmp/PrismKE}"
UV_BIN="${PRISMKE_UV_BIN:-/root/miniconda3/envs/prismke/bin/uv}"
PYTHON_BIN="${PROJECT_DIR}/.venv/bin/python"
TMUX_SESSION="${PRISMKE_TMUX_SESSION:-prismke-web}"
LEGACY_TMUX_SESSION="prismke-v03"
START_TIMEOUT="${PRISMKE_START_TIMEOUT:-30}"

RUNTIME_DIR="${PRISMKE_RUNTIME_DIR:-${PROJECT_DIR}/runtime}"
if [[ "${RUNTIME_DIR}" != /* ]]; then
  RUNTIME_DIR="${PROJECT_DIR}/${RUNTIME_DIR}"
fi
NEO4J_HOME="${PRISMKE_NEO4J_HOME:-${RUNTIME_DIR}/neo4j/current}"
NEO4J_CONF="${PRISMKE_NEO4J_CONF:-${NEO4J_HOME}/conf}"
NEO4J_HTTP_PORT="${PRISMKE_NEO4J_HTTP_PORT:-7474}"
NEO4J_BOLT_PORT="${PRISMKE_NEO4J_BOLT_PORT:-7687}"
NEO4J_BIN="${NEO4J_HOME}/bin/neo4j"
LOG_DIR="${RUNTIME_DIR}/logs"
WEB_LOG="${LOG_DIR}/prismke-web.log"
NEO4J_LOG="${RUNTIME_DIR}/neo4j/logs/neo4j.log"
LOCK_FILE="${RUNTIME_DIR}/prismke-autodl.lock"
MAX_WEB_LOG_BYTES=$((10 * 1024 * 1024))
MANAGE_LEGACY_SESSION=0
if [[ "${TMUX_SESSION}" == "prismke-web" && "${RUNTIME_DIR}" == "${PROJECT_DIR}/runtime" ]]; then
  MANAGE_LEGACY_SESSION=1
fi
export PRISMKE_RUNTIME_DIR="${RUNTIME_DIR}"
export PRISMKE_NEO4J_HOME="${NEO4J_HOME}"
export PRISMKE_NEO4J_CONF="${NEO4J_CONF}"
export PRISMKE_NEO4J_HTTP_PORT="${NEO4J_HTTP_PORT}"
export PRISMKE_NEO4J_BOLT_PORT="${NEO4J_BOLT_PORT}"

usage() {
  cat <<'EOF'
Usage:
  bash scripts/prismke_autodl.sh start
  bash scripts/prismke_autodl.sh stop
  bash scripts/prismke_autodl.sh restart
  bash scripts/prismke_autodl.sh status
  bash scripts/prismke_autodl.sh health
  bash scripts/prismke_autodl.sh logs web [--lines N] [--follow]
  bash scripts/prismke_autodl.sh logs neo4j [--lines N] [--follow]

Instance overrides:
  PRISMKE_RUNTIME_DIR, PRISMKE_NEO4J_HOME, PRISMKE_NEO4J_CONF,
  PRISMKE_NEO4J_HTTP_PORT, PRISMKE_NEO4J_BOLT_PORT,
  PRISMKE_TMUX_SESSION, PRISMKE_HEALTH_URL
EOF
}

die() {
  echo "Error: $*" >&2
  exit 1
}

require_command() {
  command -v "$1" >/dev/null 2>&1 || die "required command not found: $1"
}

api_port() {
  (
    cd "${PROJECT_DIR}"
    "${PYTHON_BIN}" -c \
      'from prismke.core.settings import Settings; print(Settings().api_port)'
  )
}

preflight() {
  [[ -d "${PROJECT_DIR}" ]] || die "project directory not found: ${PROJECT_DIR}"
  [[ -f "${PROJECT_DIR}/.env" ]] || die ".env not found in project directory"
  [[ -x "${UV_BIN}" ]] || die "uv executable not found: ${UV_BIN}"
  [[ -x "${PYTHON_BIN}" ]] || die "project Python not found: ${PYTHON_BIN}"
  [[ -x "${NEO4J_BIN}" ]] || die "Neo4j is not installed: ${NEO4J_BIN}"
  [[ -d "${NEO4J_CONF}" ]] || die "Neo4j configuration directory not found: ${NEO4J_CONF}"
  [[ "${START_TIMEOUT}" =~ ^[1-9][0-9]*$ ]] || die "PRISMKE_START_TIMEOUT must be a positive integer"
  [[ "${NEO4J_HTTP_PORT}" =~ ^[1-9][0-9]*$ ]] || die "PRISMKE_NEO4J_HTTP_PORT must be a positive integer"
  [[ "${NEO4J_BOLT_PORT}" =~ ^[1-9][0-9]*$ ]] || die "PRISMKE_NEO4J_BOLT_PORT must be a positive integer"
  [[ "${NEO4J_HTTP_PORT}" != "${NEO4J_BOLT_PORT}" ]] || die "Neo4j HTTP and Bolt ports must differ"
  require_command curl
  require_command flock
  require_command tmux
  mkdir -p "${LOG_DIR}"
}

neo4j_running() {
  NEO4J_CONF="${NEO4J_CONF}" "${NEO4J_BIN}" status >/dev/null 2>&1
}

neo4j_command() {
  NEO4J_CONF="${NEO4J_CONF}" "${NEO4J_BIN}" "$@"
}

tmux_running() {
  tmux has-session -t "$1" >/dev/null 2>&1
}

health_url() {
  if [[ -n "${PRISMKE_HEALTH_URL:-}" ]]; then
    printf '%s\n' "${PRISMKE_HEALTH_URL}"
  else
    printf 'http://127.0.0.1:%s/api/v1/health\n' "$(api_port)"
  fi
}

health_payload() {
  curl --silent --show-error --max-time 3 "$(health_url)"
}

http_healthy() {
  local payload
  payload="$(health_payload 2>/dev/null || true)"
  [[ "${payload}" == *'"status":"ok"'* && "${payload}" == *'"healthy":true'* ]]
}

port_in_use() {
  local port="$1"
  "${PYTHON_BIN}" - "${port}" <<'PY'
import socket
import sys

with socket.socket() as probe:
    probe.settimeout(0.5)
    raise SystemExit(0 if probe.connect_ex(("127.0.0.1", int(sys.argv[1]))) == 0 else 1)
PY
}

assert_port_free() {
  local port="$1"
  local component="$2"
  if port_in_use "${port}"; then
    echo "Port ${port} is already in use while ${component} is not managed by PrismKE." >&2
    return 1
  fi
}

rotate_web_log() {
  local size=0
  if [[ -f "${WEB_LOG}" ]]; then
    size="$(stat -c '%s' "${WEB_LOG}")"
  fi
  if (( size < MAX_WEB_LOG_BYTES )); then
    return
  fi
  rm -f "${WEB_LOG}.5"
  local index
  for index in 4 3 2 1; do
    if [[ -f "${WEB_LOG}.${index}" ]]; then
      mv "${WEB_LOG}.${index}" "${WEB_LOG}.$((index + 1))"
    fi
  done
  mv "${WEB_LOG}" "${WEB_LOG}.1"
}

stop_tmux_session() {
  local session="$1"
  local attempt
  if ! tmux_running "${session}"; then
    return
  fi
  tmux send-keys -t "${session}" C-c >/dev/null 2>&1 || true
  for attempt in $(seq 1 10); do
    if ! tmux_running "${session}"; then
      return
    fi
    sleep 1
  done
  tmux kill-session -t "${session}" >/dev/null 2>&1 || true
}

start_web() {
  local command
  rotate_web_log
  printf -v command 'cd %q && exec env PRISMKE_RUNTIME_DIR=%q %q run prismke serve >>%q 2>&1' \
    "${PROJECT_DIR}" "${RUNTIME_DIR}" "${UV_BIN}" "${WEB_LOG}"
  tmux new-session -d -s "${TMUX_SESSION}" "${command}" 9>&-
}

wait_for_health() {
  local attempt
  for attempt in $(seq 1 "${START_TIMEOUT}"); do
    if http_healthy; then
      return 0
    fi
    if ! tmux_running "${TMUX_SESSION}"; then
      break
    fi
    sleep 1
  done
  return 1
}

start_all() {
  local started_neo4j=0
  local started_web=0
  local port

  if neo4j_running && tmux_running "${TMUX_SESSION}" && http_healthy; then
    echo "PrismKE services are already healthy."
    status_all
    return
  fi

  if tmux_running "${TMUX_SESSION}" && ! http_healthy; then
    echo "Restarting unhealthy Web session ${TMUX_SESSION}."
    stop_tmux_session "${TMUX_SESSION}"
  fi
  if (( MANAGE_LEGACY_SESSION )) && tmux_running "${LEGACY_TMUX_SESSION}"; then
    echo "Stopping legacy tmux session ${LEGACY_TMUX_SESSION}."
    stop_tmux_session "${LEGACY_TMUX_SESSION}"
  fi

  if ! tmux_running "${TMUX_SESSION}"; then
    port="$(api_port)"
    assert_port_free "${port}" "PrismKE Web"
  fi

  if ! neo4j_running; then
    assert_port_free "${NEO4J_HTTP_PORT}" "Neo4j"
    assert_port_free "${NEO4J_BOLT_PORT}" "Neo4j"
    PRISMKE_PROJECT_DIR="${PROJECT_DIR}" \
      PRISMKE_RUNTIME_DIR="${RUNTIME_DIR}" \
      PRISMKE_NEO4J_HOME="${NEO4J_HOME}" \
      PRISMKE_NEO4J_CONF="${NEO4J_CONF}" \
      PRISMKE_NEO4J_HTTP_PORT="${NEO4J_HTTP_PORT}" \
      PRISMKE_NEO4J_BOLT_PORT="${NEO4J_BOLT_PORT}" \
      bash "${PROJECT_DIR}/scripts/start_neo4j_autodl.sh" 9>&-
    started_neo4j=1
  fi

  if ! tmux_running "${TMUX_SESSION}"; then
    if ! start_web; then
      if (( started_neo4j )); then
        neo4j_command stop >/dev/null 2>&1 || true
      fi
      die "failed to create tmux session ${TMUX_SESSION}"
    fi
    started_web=1
  fi

  if ! wait_for_health; then
    echo "PrismKE health check did not become ready within ${START_TIMEOUT}s." >&2
    if [[ -f "${WEB_LOG}" ]]; then
      echo "Last 30 web log lines:" >&2
      tail -n 30 "${WEB_LOG}" >&2
    fi
    if (( started_web )); then
      stop_tmux_session "${TMUX_SESSION}"
    fi
    if (( started_neo4j )); then
      neo4j_command stop >/dev/null 2>&1 || true
    fi
    return 1
  fi

  echo "PrismKE services started successfully."
  status_all
}

stop_all() {
  local stopped=0
  if tmux_running "${TMUX_SESSION}"; then
    echo "Stopping PrismKE Web session ${TMUX_SESSION}."
    stop_tmux_session "${TMUX_SESSION}"
    stopped=1
  fi
  if (( MANAGE_LEGACY_SESSION )) && tmux_running "${LEGACY_TMUX_SESSION}"; then
    echo "Stopping legacy Web session ${LEGACY_TMUX_SESSION}."
    stop_tmux_session "${LEGACY_TMUX_SESSION}"
    stopped=1
  fi
  if neo4j_running; then
    echo "Stopping Neo4j."
    neo4j_command stop
    stopped=1
  fi
  if (( ! stopped )); then
    echo "PrismKE services are already stopped."
  else
    echo "PrismKE services stopped."
  fi
}

status_all() {
  local neo4j_status="stopped"
  local web_status="stopped"
  local http_status="unhealthy"
  local neo4j_pid="-"
  local web_pid="-"
  local healthy=0

  if neo4j_running; then
    neo4j_status="running"
    neo4j_pid="$(neo4j_command status 2>/dev/null | sed -n 's/.*pid \([0-9][0-9]*\).*/\1/p' | head -1)"
    neo4j_pid="${neo4j_pid:--}"
  fi
  if tmux_running "${TMUX_SESSION}"; then
    web_status="running"
    web_pid="$(tmux list-panes -t "${TMUX_SESSION}" -F '#{pane_pid}' 2>/dev/null | head -1)"
    web_pid="${web_pid:--}"
  elif (( MANAGE_LEGACY_SESSION )) && tmux_running "${LEGACY_TMUX_SESSION}"; then
    web_status="legacy-session"
    web_pid="$(tmux list-panes -t "${LEGACY_TMUX_SESSION}" -F '#{pane_pid}' 2>/dev/null | head -1)"
    web_pid="${web_pid:--}"
  fi
  if http_healthy; then
    http_status="healthy"
  fi

  printf '%-12s %-16s %s\n' "COMPONENT" "STATUS" "PID/DETAIL"
  printf '%-12s %-16s %s\n' "Neo4j" "${neo4j_status}" "${neo4j_pid}"
  printf '%-12s %-16s %s\n' "Web" "${web_status}" "${web_pid}"
  printf '%-12s %-16s %s\n' "HTTP" "${http_status}" "$(health_url)"
  printf '%-12s %-16s %s\n' "Web log" "path" "${WEB_LOG}"
  printf '%-12s %-16s %s\n' "Neo4j log" "path" "${NEO4J_LOG}"
  echo "Listeners:"
  local port
  for port in "${NEO4J_HTTP_PORT}" "${NEO4J_BOLT_PORT}" "$(api_port)"; do
    if port_in_use "${port}"; then
      printf '  127.0.0.1:%s listening\n' "${port}"
    else
      printf '  127.0.0.1:%s closed\n' "${port}"
    fi
  done

  if [[ "${neo4j_status}" == "running" && "${web_status}" == "running" && "${http_status}" == "healthy" ]]; then
    healthy=1
  fi
  (( healthy ))
}

show_health() {
  local payload
  if ! payload="$(health_payload)"; then
    echo "PrismKE health endpoint is unavailable: $(health_url)" >&2
    return 1
  fi
  printf '%s\n' "${payload}"
  [[ "${payload}" == *'"status":"ok"'* && "${payload}" == *'"healthy":true'* ]]
}

show_logs() {
  local component="${1:-}"
  shift || true
  local lines=100
  local follow=0
  local log_file

  case "${component}" in
    web) log_file="${WEB_LOG}" ;;
    neo4j) log_file="${NEO4J_LOG}" ;;
    *) die "logs requires component: web or neo4j" ;;
  esac

  while (($#)); do
    case "$1" in
      --follow) follow=1; shift ;;
      --lines)
        (($# >= 2)) || die "--lines requires a value"
        lines="$2"
        shift 2
        ;;
      *) die "unknown logs option: $1" ;;
    esac
  done
  [[ "${lines}" =~ ^[1-9][0-9]*$ ]] || die "--lines must be a positive integer"
  [[ -f "${log_file}" ]] || die "log file not found: ${log_file}"
  if (( follow )); then
    tail -n "${lines}" -F "${log_file}"
  else
    tail -n "${lines}" "${log_file}"
  fi
}

with_lock() {
  mkdir -p "${RUNTIME_DIR}"
  exec 9>"${LOCK_FILE}"
  flock -n 9 || die "another PrismKE service operation is in progress"
  "$@"
}

main() {
  local action="${1:-}"
  case "${action}" in
    -h|--help|help)
      usage
      ;;
    start)
      preflight
      with_lock start_all
      ;;
    stop)
      preflight
      with_lock stop_all
      ;;
    restart)
      preflight
      with_lock stop_all
      start_all
      ;;
    status)
      preflight
      status_all
      ;;
    health)
      preflight
      show_health
      ;;
    logs)
      preflight
      shift
      show_logs "$@"
      ;;
    *)
      usage >&2
      exit 2
      ;;
  esac
}

main "$@"
