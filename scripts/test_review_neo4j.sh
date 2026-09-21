#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_DIR"
HOME_DIR="${PRISMKE_TEST_NEO4J_HOME:-$PROJECT_DIR/runtime/neo4j/current}"
WORKSPACE="$PROJECT_DIR/runtime/review-neo4j-test"
mkdir -p "$WORKSPACE/conf" "$WORKSPACE/run" "$WORKSPACE/logs" "$WORKSPACE/data"
sed "s|__WORKSPACE__|$WORKSPACE|g" configs/neo4j/review-test.conf > "$WORKSPACE/conf/neo4j.conf"
export NEO4J_CONF="$WORKSPACE/conf"

if "$HOME_DIR/bin/neo4j" status >/dev/null 2>&1; then
    echo "Dedicated review test instance already running; refusing shared use" >&2
    exit 1
fi
# Stable test IDs make stale data look like a concurrent graph update. Start every
# isolated run from an empty database after confirming that no test instance owns it.
rm -rf "$WORKSPACE/data" "$WORKSPACE/run" "$WORKSPACE/logs"
mkdir -p "$WORKSPACE/run" "$WORKSPACE/logs" "$WORKSPACE/data"
"$HOME_DIR/bin/neo4j" start
trap '"$HOME_DIR/bin/neo4j" stop >/dev/null 2>&1 || true' EXIT
export PRISMKE_TEST_NEO4J=1
export PRISMKE_NEO4J_URI=bolt://127.0.0.1:17687
export PRISMKE_NEO4J_PASSWORD=review-local-unused
"$PROJECT_DIR/.venv/bin/python" - <<'PY'
import socket
import time
for _ in range(90):
    with socket.socket() as connection:
        if connection.connect_ex(('127.0.0.1', 17687)) == 0:
            break
    time.sleep(1)
else:
    raise SystemExit('dedicated Neo4j readiness timeout')
PY
"$PROJECT_DIR/.venv/bin/python" -m pytest tests/test_neo4j_integration.py tests/test_review_workspace.py tests/test_validation.py tests/test_reviews_v06.py tests/test_execution_v07.py -ra
