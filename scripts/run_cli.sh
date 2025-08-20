#!/usr/bin/env bash
# Simple wrapper to launch Moonshot interactive CLI.
# Make executable: chmod +x scripts/run_cli.sh

set -euo pipefail

python -m moonshot cli interactive "$@"

