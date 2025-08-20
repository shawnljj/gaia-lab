<!--
  gaia-lab: A neutral, Moonshot-first lab for evaluating LLMs
  Focus: reusable recipes & cookbooks; easy local run; minimal and clear.
-->

# gaia-lab

A lab for evaluating LLMs using Moonshot with reusable recipes & cookbooks.

## Quick Start

- Create a virtualenv and install dependencies:
  - `python -m venv .venv && source .venv/bin/activate`
  - `pip install -r requirements.txt`
- Copy env template and set keys:
  - `cp .env.example .env` (fill `OPENAI_API_KEY`, `TOGETHER_API_KEY`)
- Run Moonshot interactively or execute a suite:
  - `python -m moonshot cli interactive`
  - or `python scripts/run_suite.py suites/quickcheck.yaml`

## Start The App

- Start: `bash scripts/start_moonshot.sh`
- Open: `http://localhost:3000`
- Stop: `pkill -f "python -m moonshot web"`

## What is inside

- `connectors/`: Provider connector configs (OpenAI, Together Llama-Guard)
- `datasets/`: Small example datasets (e.g., `enterprise/sg_facts.jsonl`)
- `metrics/`: Custom metrics (e.g., JSON validity)
- `recipes/`: Atomic tests (quality/safety/robustness)
- `cookbooks/`: Grouped recipes aligned to common risk themes
- `suites/`: Higher-level orchestration that binds connectors + cookbooks
- `scripts/`: CLI wrapper, suite runner, and report exporter
- `reports/`: Output artifacts (kept out of git; artifacts uploaded in CI)

## Moonshot-first workflow

1) Connectors → 2) Recipes → 3) Cookbooks → 4) Suites → 5) Reports

- Start by configuring a connector under `connectors/` (e.g., OpenAI)
- Author a recipe under `recipes/` using a dataset and metric
- Group related recipes into a cookbook under `cookbooks/`
- Define one or more suites under `suites/` that pick a connector and cookbooks, and set an output directory under `reports/`
- Run the suite locally or in CI; reports are exported to CSV/Markdown

## Add a new recipe or cookbook

Add a recipe:
- Place a dataset (JSONL) under `datasets/` with fields (e.g., `prompt`, `expected`)
- Create a recipe JSON under `recipes/<category>/` with fields:
  - `name`
  - `dataset`: `{ "type": "jsonl", "path": "datasets/...", "input_field": "prompt", "reference_field": "expected" }`
  - `prompt_template`: e.g., `"{prompt}"`
  - `metric`: either a built-in metric or a custom one with `module: metrics/json_validity.py`

Add a cookbook:
- Create a JSON under `cookbooks/` with fields:
  - `name`, `description`, `recipes: ["recipes/...json", ...]`

Then include your cookbook in a suite under `suites/` and run it.

## Safety & data notes

- Do not commit secrets. Use `.env` and environment variables only.
- Use only non-sensitive, public datasets in this repository.
- This project is neutral and non-branded; bring your own model/provider keys.

## Local run examples

- Interactive: `python -m moonshot cli interactive`
- Quick check suite: `python scripts/run_suite.py suites/quickcheck.yaml`
- Export reports again: `python scripts/export_report.py reports/quickcheck`

## CI quickcheck

On pull requests to `main`, GitHub Actions runs `suites/quickcheck.yaml` and uploads `reports/quickcheck` as an artifact. Nightly safety runs use Llama-Guard.
