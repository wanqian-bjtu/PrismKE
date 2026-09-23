#!/usr/bin/env bash
# Project-relative defaults. Override paths and ports for another installation.
SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
export PRISMKE_PROJECT_DIR="${PRISMKE_PROJECT_DIR:-$(cd -- "${SCRIPT_DIR}/.." && pwd)}"
export PRISMKE_RUNTIME_DIR="${PRISMKE_RUNTIME_DIR:-${PRISMKE_PROJECT_DIR}/runtime/services/v011}"
if [[ "${PRISMKE_RUNTIME_DIR}" != /* ]]; then
  export PRISMKE_RUNTIME_DIR="${PRISMKE_PROJECT_DIR}/${PRISMKE_RUNTIME_DIR}"
fi
export PRISMKE_NEO4J_HOME="${PRISMKE_NEO4J_HOME:-${NEO4J_HOME:-${PRISMKE_PROJECT_DIR}/runtime/neo4j/current}}"
export PRISMKE_NEO4J_CONF="${PRISMKE_NEO4J_CONF:-${PRISMKE_RUNTIME_DIR}/neo4j/conf}"
export PRISMKE_NEO4J_HTTP_PORT="${PRISMKE_NEO4J_HTTP_PORT:-7474}"
export PRISMKE_NEO4J_BOLT_PORT="${PRISMKE_NEO4J_BOLT_PORT:-7687}"
export PRISMKE_NEO4J_URI="${PRISMKE_NEO4J_URI:-bolt://127.0.0.1:${PRISMKE_NEO4J_BOLT_PORT}}"

prepare_neo4j_config() {
  local config="${PRISMKE_NEO4J_CONF}/neo4j.conf"
  local isolated="${PRISMKE_RUNTIME_DIR}"
  if [[ "${PRISMKE_NEO4J_CONF}" != "${isolated}/neo4j/conf" ]]; then
    [[ -d "${PRISMKE_NEO4J_CONF}" ]] || {
      echo "Neo4j instance config directory not found: ${PRISMKE_NEO4J_CONF}" >&2
      return 1
    }
    return
  fi
  for path in "${isolated}" "${isolated}/neo4j" "${isolated}/neo4j/data" "${isolated}/neo4j/conf" "${isolated}/neo4j/run"; do
    [[ "$(realpath -m "${path}")" == "${path}" ]] || {
      echo "Isolated Neo4j paths must not redirect through symlinks" >&2
      return 1
    }
  done
  mkdir -p "${PRISMKE_NEO4J_CONF}" "${isolated}/neo4j/data" "${isolated}/neo4j/logs" "${isolated}/neo4j/run"
  if [[ ! -f "${config}" ]]; then
    cat >"${config}" <<EOF
# PrismKE v0.11 isolated instance
server.default_listen_address=127.0.0.1
server.bolt.listen_address=127.0.0.1:${PRISMKE_NEO4J_BOLT_PORT}
server.http.listen_address=127.0.0.1:${PRISMKE_NEO4J_HTTP_PORT}
server.directories.data=${isolated}/neo4j/data
server.directories.logs=${isolated}/neo4j/logs
server.directories.run=${isolated}/neo4j/run
server.memory.heap.initial_size=512m
server.memory.heap.max_size=1g
server.memory.pagecache.size=1g
EOF
  fi
  grep -Fxq "server.directories.data=${isolated}/neo4j/data" "${config}" &&
    grep -Fxq "server.directories.logs=${isolated}/neo4j/logs" "${config}" &&
    grep -Fxq "server.directories.run=${isolated}/neo4j/run" "${config}" &&
    grep -Fxq "server.default_listen_address=127.0.0.1" "${config}" &&
    grep -Fxq "server.http.listen_address=127.0.0.1:${PRISMKE_NEO4J_HTTP_PORT}" "${config}" &&
    grep -Fxq "server.bolt.listen_address=127.0.0.1:${PRISMKE_NEO4J_BOLT_PORT}" "${config}" &&
    [[ "$(grep -c '^server.directories.data=' "${config}")" == 1 ]] &&
    [[ "$(grep -c '^server.directories.logs=' "${config}")" == 1 ]] &&
    [[ "$(grep -c '^server.directories.run=' "${config}")" == 1 ]] || {
    echo "Neo4j configuration does not point to the selected runtime directory" >&2
    return 1
  }
}
