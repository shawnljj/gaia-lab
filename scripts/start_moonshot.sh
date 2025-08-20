#!/usr/bin/env bash

# Unified launcher for Moonshot Web UI
# - Creates/uses .venv (Python 3.11)
# - Installs Python deps from requirements.txt
# - Installs Moonshot data + Web UI assets
# - Verifies Node.js >= 20.11.1 (required for Web UI)
# - Starts the Moonshot Web UI

set -euo pipefail

REQ_NODE_VER="20.11.1"
VENV_DIR=".venv"

log() { echo -e "[moonshot] $*"; }
err() { echo -e "[moonshot][error] $*" >&2; }

# Pick a Python executable
pick_python() {
  if command -v python3.11 >/dev/null 2>&1; then
    echo "python3.11"
    return
  fi
  if command -v python3 >/dev/null 2>&1; then
    echo "python3"
    return
  fi
  if command -v python >/dev/null 2>&1; then
    echo "python"
    return
  fi
  err "No Python found. Please install Python 3.11."
  exit 1
}

# Ensure Python version is 3.11.x
ensure_python_version() {
  local py
  py="$(pick_python)"
  local v
  v="$($py -c 'import sys; print("%d.%d"% (sys.version_info[0], sys.version_info[1]))' 2>/dev/null || true)"
  if [[ "$v" != "3.11" ]]; then
    if [[ "${MOONSHOT_RELAX:-}" == "1" ]]; then
      log "Warning: Detected Python $v via '$py'. Proceeding (MOONSHOT_RELAX=1)."
    else
      err "Detected Python $v via '$py'. Moonshot 0.7.3 requires Python 3.11."
      err "Set MOONSHOT_RELAX=1 to attempt anyway, or install Python 3.11."
      exit 1
    fi
  fi
}

# Create venv if missing
ensure_venv() {
  local py
  py="$(pick_python)"
  if [[ ! -d "$VENV_DIR" ]]; then
    log "Creating virtualenv at $VENV_DIR (Python 3.11)"
    "$py" -m venv "$VENV_DIR"
  fi
  # shellcheck disable=SC1091
  source "$VENV_DIR/bin/activate"
}

# Install Python deps
install_python_deps() {
  log "Upgrading pip/setuptools/wheel"
  python -m pip install --upgrade pip setuptools wheel >/dev/null
  log "Installing requirements.txt"
  python -m pip install -r requirements.txt
}

# Ensure .env exists
ensure_env_file() {
  if [[ ! -f .env && -f .env.example ]]; then
    cp .env.example .env
    log "Created .env from .env.example. Fill in API keys as needed."
  fi
}

# Verify Node.js version (for Web UI)
check_node() {
  if ! command -v node >/dev/null 2>&1; then
    if [[ "${MOONSHOT_RELAX:-}" == "1" ]]; then
      log "Warning: Node.js not found. Proceeding (MOONSHOT_RELAX=1). Web UI may fail."
      return
    fi
    err "Node.js not found. Install Node >= $REQ_NODE_VER for the Web UI."
    err "Download: https://nodejs.org/en (LTS)"
    exit 1
  fi
  local nv raw
  raw="$(node -v)"          # e.g., v20.11.1
  nv="${raw#v}"             # strip leading v
  # Compare versions with sort -V; if the smallest is not REQ_NODE_VER, it's too old
  if [[ "$(printf '%s\n' "$REQ_NODE_VER" "$nv" | sort -V | head -n1)" != "$REQ_NODE_VER" ]]; then
    if [[ "${MOONSHOT_RELAX:-}" == "1" ]]; then
      log "Warning: Node.js $nv detected (< $REQ_NODE_VER). Proceeding (MOONSHOT_RELAX=1)."
      return
    fi
    err "Node.js $nv detected. Require >= $REQ_NODE_VER."
    exit 1
  fi
}

# Install Moonshot data + UI assets (idempotent)
install_moonshot_assets() {
  log "Installing Moonshot data and UI assets (idempotent)"
  python -m moonshot -i moonshot-data -i moonshot-ui || {
    err "Failed to install Moonshot assets. Ensure network access and Git are available."
    exit 1
  }
}

# Start the Web UI
start_web() {
  local port
  port="${PORT:-3000}"
  log "Starting Moonshot Web UI on http://localhost:$port"
  # If Moonshot supports explicit port flags, it will honor PORT env or its own defaults.
  # Running in the foreground; use Ctrl+C to stop.
  exec python -m moonshot web
}

main() {
  ensure_python_version
  ensure_venv
  ensure_env_file
  install_python_deps
  check_node
  install_moonshot_assets
  start_web
}

main "$@"
