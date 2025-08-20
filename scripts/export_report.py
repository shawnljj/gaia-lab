"""
Export Moonshot report summaries to CSV and Markdown.

Usage:
  python scripts/export_report.py reports/quickcheck

Reads a Moonshot output directory and writes:
  - summary.csv (overall totals, pass rate; by-recipe breakdown)
  - summary.md  (human-readable summary)

This is best-effort and tolerant of unknown Moonshot formats.
"""

from __future__ import annotations

import csv
import json
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, List, Tuple


def find_result_files(root: Path) -> List[Path]:
    # Look for common result file shapes
    patterns = ["*.jsonl", "*.json", "*.ndjson", "*.csv"]
    files: List[Path] = []
    for pat in patterns:
        files.extend(root.rglob(pat))
    return [f for f in files if f.name not in {"summary.json", "run_metadata.json", "placeholder_results.json"}]


def load_jsonl(path: Path) -> List[Dict[str, Any]]:
    rows = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except Exception:
                # Non-JSON line; skip
                continue
    return rows


def summarize(root: Path) -> Tuple[Dict[str, Any], List[Dict[str, Any]]]:
    files = find_result_files(root)
    total = 0
    passed = 0
    by_recipe = defaultdict(lambda: {"total": 0, "passed": 0})

    for f in files:
        if f.suffix == ".jsonl":
            rows = load_jsonl(f)
        elif f.suffix in {".json", ".ndjson"}:
            try:
                rows = json.loads(f.read_text(encoding="utf-8"))
                if isinstance(rows, dict):
                    rows = rows.get("cases", [])  # common shape
            except Exception:
                rows = []
        elif f.suffix == ".csv":
            rows = []
            # Treat CSV as opaque for now
        else:
            rows = []

        # Heuristics for pass/fail counting
        recipe_name = f.stem
        for r in rows or []:
            total += 1
            by_recipe[recipe_name]["total"] += 1
            status = (r.get("status") or r.get("passed") or r.get("score"))
            passed_flag = False
            if isinstance(status, bool):
                passed_flag = status
            elif isinstance(status, (int, float)):
                passed_flag = bool(status)
            elif isinstance(status, str):
                passed_flag = status.lower() in {"pass", "passed", "ok", "true"}
            if passed_flag:
                passed += 1
                by_recipe[recipe_name]["passed"] += 1

    overall = {
        "total": total,
        "passed": passed,
        "pass_rate": (passed / total) if total else 0.0,
    }

    by_recipe_rows = [
        {
            "recipe": k,
            "total": v["total"],
            "passed": v["passed"],
            "pass_rate": (v["passed"] / v["total"]) if v["total"] else 0.0,
        }
        for k, v in sorted(by_recipe.items())
    ]
    return overall, by_recipe_rows


def write_csv(path: Path, overall: Dict[str, Any], rows: List[Dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["metric", "value"])
        writer.writerow(["total", overall["total"]])
        writer.writerow(["passed", overall["passed"]])
        writer.writerow(["pass_rate", overall["pass_rate"]])
        writer.writerow([])
        writer.writerow(["recipe", "total", "passed", "pass_rate"])
        for r in rows:
            writer.writerow([r["recipe"], r["total"], r["passed"], r["pass_rate"]])


def write_md(path: Path, overall: Dict[str, Any], rows: List[Dict[str, Any]]) -> None:
    lines = []
    lines.append("# Suite Summary\n")
    lines.append(f"- Total cases: {overall['total']}")
    lines.append(f"- Passed: {overall['passed']}")
    lines.append(f"- Pass rate: {overall['pass_rate']:.2%}\n")
    lines.append("## By Recipe")
    for r in rows:
        lines.append(
            f"- {r['recipe']}: {r['passed']}/{r['total']} ({(r['pass_rate']):.2%})"
        )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    if len(sys.argv) != 2:
        print("Usage: python scripts/export_report.py <output_dir>")
        return 1
    out = Path(sys.argv[1]).resolve()
    out.mkdir(parents=True, exist_ok=True)

    overall, rows = summarize(out)
    write_csv(out / "summary.csv", overall, rows)
    write_md(out / "summary.md", overall, rows)
    print(f"Wrote summary to {out}/summary.csv and summary.md")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

