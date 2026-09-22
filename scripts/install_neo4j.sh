#!/usr/bin/env bash
set -euo pipefail

source "$(dirname -- "${BASH_SOURCE[0]}")/service_profile.sh"
NEO4J_VERSION="${NEO4J_VERSION:-5.26.30}"
INSTALL_BASE="${PRISMKE_PROJECT_DIR}/runtime/neo4j"
ARCHIVE="${INSTALL_BASE}/neo4j-community-${NEO4J_VERSION}-unix.tar.gz"
INSTALL_DIR="${INSTALL_BASE}/neo4j-community-${NEO4J_VERSION}"
CURRENT="${INSTALL_BASE}/current"

for command in java curl tar; do
  command -v "${command}" >/dev/null 2>&1 || {
    echo "Required command not found: ${command}; install it using your system package manager" >&2
    exit 1
  }
done
[[ ! -e "${CURRENT}" || -L "${CURRENT}" ]] || {
  echo "Refusing to replace a non-symlink Neo4j installation: ${CURRENT}" >&2
  exit 1
}
mkdir -p "${INSTALL_BASE}"
if [[ ! -d "${INSTALL_DIR}" ]]; then
  if [[ ! -f "${ARCHIVE}" ]]; then
    curl --fail --location --retry 3 \
      "https://dist.neo4j.org/neo4j-community-${NEO4J_VERSION}-unix.tar.gz" \
      --output "${ARCHIVE}"
  fi
  tar -xzf "${ARCHIVE}" -C "${INSTALL_BASE}"
fi
ln -sfn "${INSTALL_DIR}" "${CURRENT}"
echo "Neo4j ${NEO4J_VERSION} installed at ${CURRENT}"
echo "Run scripts/start_neo4j.sh to prepare the isolated instance configuration."
