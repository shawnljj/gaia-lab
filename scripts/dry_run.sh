#!/usr/bin/env bash
# Shell-only dry run to simulate a Moonshot suite run.
# Usage: bash scripts/dry_run.sh suites/quickcheck.yaml

set -euo pipefail

if [ "$#" -ne 1 ]; then
  echo "Usage: bash scripts/dry_run.sh <suite_yaml>" >&2
  exit 1
fi

SUITE_FILE="$1"
if [ ! -f "$SUITE_FILE" ]; then
  echo "Suite file not found: $SUITE_FILE" >&2
  exit 1
fi

SUITE_NAME=$(grep -E '^name:' "$SUITE_FILE" | head -n1 | awk '{print $2}')
OUTPUT_DIR=$(grep -E '^output_dir:' "$SUITE_FILE" | head -n1 | awk '{print $2}')
[ -z "${OUTPUT_DIR:-}" ] && OUTPUT_DIR="reports/${SUITE_NAME:-output}"

mkdir -p "$OUTPUT_DIR"

# Minimal run metadata
cat >"$OUTPUT_DIR/run_metadata.json" <<'JSON'
{
  "note": "This is a dry-run placeholder generated without Moonshot.",
  "suite": "DRY_RUN",
  "invoked_by": "scripts/dry_run.sh"
}
JSON

# Placeholder results to satisfy downstream tools
cat >"$OUTPUT_DIR/placeholder_results.json" <<'JSON'
{
  "cases": [
    {"recipe": "example", "status": "passed"},
    {"recipe": "example", "status": "failed"}
  ]
}
JSON

# Simple summaries
cat >"$OUTPUT_DIR/summary.csv" <<'CSV'
metric,value
total,2
passed,1
pass_rate,0.5

recipe,total,passed,pass_rate
example,2,1,0.5
CSV

cat >"$OUTPUT_DIR/summary.md" <<'MD'
# Suite Summary

- Total cases: 2
- Passed: 1
- Pass rate: 50.00%

## By Recipe
- example: 1/2 (50.00%)
MD

echo "Dry run complete. Reports at: $OUTPUT_DIR"

