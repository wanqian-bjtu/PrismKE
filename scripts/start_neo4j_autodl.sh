#!/usr/bin/env bash
# Compatibility entrypoint for existing deployments.
exec bash "$(dirname -- "${BASH_SOURCE[0]}")/start_neo4j.sh" "$@"
