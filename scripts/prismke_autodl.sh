#!/usr/bin/env bash
# Compatibility entrypoint for existing deployments.
exec bash "$(dirname -- "${BASH_SOURCE[0]}")/prismke.sh" "$@"
