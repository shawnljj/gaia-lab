"""
Programmatic runner for Moonshot suites.

Usage:
  python scripts/run_suite.py suites/quickcheck.yaml

This script attempts to:
  1) Read the suite YAML (connector, cookbooks, output_dir)
  2) Invoke Moonshot to run the suite (via Python API if available; otherwise CLI)
  3) Ensure the output directory exists and copy suite metadata
  4) Optionally generate a summary via export_report.py

Notes:
- Requires environment variables for provider keys (see .env.example)
- Keeps secrets out of git; reports are written under reports/<suite-name>
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path

import yaml


def read_yaml(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def write_json(path: Path, data: dict) -> None:
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def try_moonshot_python_api(suite_path: Path, output_dir: Path) -> bool:
    """Attempt to run via Moonshot's Python API, if available.

    Returns True if it appears to run, else False to fall back to CLI.
    """
    try:
        import moonshot  # type: ignore
    except Exception:
        return False

    # Try a few likely entry points defensively.
    # If none exist, fall back to the CLI path.
    try:
        if hasattr(moonshot, "run_suite"):
            moonshot.run_suite(str(suite_path), output_dir=str(output_dir))  # type: ignore[attr-defined]
            return True
        if hasattr(moonshot, "cli") and hasattr(moonshot.cli, "run_suite"):
            moonshot.cli.run_suite(str(suite_path), output_dir=str(output_dir))  # type: ignore[attr-defined]
            return True
    except Exception as e:  # noqa: BLE001
        print(f"Moonshot Python API attempt failed: {e}")
        return False

    return False


def try_moonshot_cli(suite_path: Path, output_dir: Path) -> None:
    """Attempt a few CLI invocation patterns to run a suite.
    Raises CalledProcessError if all options fail.
    """
    candidates = [
        [sys.executable, "-m", "moonshot", "cli", "run", str(suite_path)],
        [sys.executable, "-m", "moonshot", "run", str(suite_path)],
        ["moonshot", "run", str(suite_path)],
    ]
    env = os.environ.copy()
    env["MOONSHOT_OUTPUT_DIR"] = str(output_dir)

    last_err = None
    for cmd in candidates:
        try:
            print(f"Running: {' '.join(cmd)} (output -> {output_dir})")
            subprocess.run(cmd, check=True, env=env)
            return
        except subprocess.CalledProcessError as e:  # noqa: PERF203
            last_err = e
            print(f"Moonshot CLI attempt failed: {e}")
            continue

    if last_err is not None:
        raise last_err


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("suite", type=str, help="Path to suite YAML")
    args = parser.parse_args()

    suite_path = Path(args.suite).resolve()
    if not suite_path.exists():
        print(f"Suite file not found: {suite_path}")
        return 1

    suite_cfg = read_yaml(suite_path)
    out_dir = Path(suite_cfg.get("output_dir", "reports/output")).resolve()
    ensure_dir(out_dir)

    # Persist a little run metadata next to the Moonshot outputs
    metadata = {
        "suite": suite_cfg.get("name"),
        "connector": suite_cfg.get("connector"),
        "cookbooks": suite_cfg.get("cookbooks", []),
        "invoked_at": datetime.utcnow().isoformat() + "Z",
        "host": os.uname().nodename if hasattr(os, "uname") else "unknown",
    }
    write_json(out_dir / "run_metadata.json", metadata)

    # Try Python API, then fallback to CLI
    ran = try_moonshot_python_api(suite_path, out_dir)
    if not ran:
        try:
            try_moonshot_cli(suite_path, out_dir)
        except Exception as e:  # noqa: BLE001
            print("Could not invoke Moonshot. Ensure it is installed and accessible.")
            print("Install deps: pip install -r requirements.txt")
            print(f"Error: {e}")
            # Still write a minimal placeholder so export step can run
            write_json(out_dir / "placeholder_results.json", {"note": "Moonshot run failed/was skipped."})

    # Export a summary (best-effort)
    try:
        subprocess.run([sys.executable, "scripts/export_report.py", str(out_dir)], check=True)
    except Exception as e:  # noqa: BLE001
        print(f"Export summary failed: {e}")

    print(f"Done. Reports at: {out_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

