#!/usr/bin/env bash
set -euo pipefail

NEO4J_VERSION="${NEO4J_VERSION:-5.26.0}"
PROJECT_DIR="${PRISMKE_PROJECT_DIR:-/root/autodl-tmp/PrismKE}"
RUNTIME_DIR="${PROJECT_DIR}/runtime/neo4j"
ARCHIVE="${RUNTIME_DIR}/neo4j-community-${NEO4J_VERSION}-unix.tar.gz"
INSTALL_DIR="${RUNTIME_DIR}/neo4j-community-${NEO4J_VERSION}"

if ! command -v java >/dev/null 2>&1; then
  apt-get update
  DEBIAN_FRONTEND=noninteractive apt-get install -y openjdk-17-jre-headless curl
  apt-get clean
fi

mkdir -p "${RUNTIME_DIR}"
if [[ ! -d "${INSTALL_DIR}" ]]; then
  curl --fail --location --retry 3 \
    "https://dist.neo4j.org/neo4j-community-${NEO4J_VERSION}-unix.tar.gz" \
    --output "${ARCHIVE}"
  tar -xzf "${ARCHIVE}" -C "${RUNTIME_DIR}"
fi
ln -sfn "${INSTALL_DIR}" "${RUNTIME_DIR}/current"

CONFIG="${INSTALL_DIR}/conf/neo4j.conf"
if ! grep -q "PrismKE native configuration" "${CONFIG}"; then
  cat >>"${CONFIG}" <<EOF

# PrismKE native configuration
server.default_listen_address=127.0.0.1
server.bolt.listen_address=127.0.0.1:7687
server.http.listen_address=127.0.0.1:7474
server.directories.data=${RUNTIME_DIR}/data
server.directories.logs=${RUNTIME_DIR}/logs
server.memory.heap.initial_size=512m
server.memory.heap.max_size=1g
server.memory.pagecache.size=1g
EOF
fi

echo "Neo4j ${NEO4J_VERSION} installed at ${RUNTIME_DIR}/current"
