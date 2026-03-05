#!/usr/bin/env bash
set -euo pipefail

WORKSPACE=${WORKSPACE:-/workspace}
BLUEPRINT_DIR=${BLUEPRINT_DIR:-"$WORKSPACE/blueprints/sdk-python-benchmark"}
SDK_PYTHON_DIR=${SDK_PYTHON_DIR:-"$WORKSPACE/sdk/sdk-python"}
SDK_CORE_DIR=${SDK_CORE_DIR:-"$WORKSPACE/sdk/sdk-core"}
VENV_PATH=${UV_VENV_PATH:-"$WORKSPACE/.venv"}

export PYTHONUNBUFFERED=1
export CARGO_TERM_COLOR=always

echo "🔍 Checking virtual environment at: $VENV_PATH"

if [ ! -d "$VENV_PATH" ]; then
  echo "📦 Creating virtual environment..."
  mkdir -p "$(dirname "$VENV_PATH")"
  echo "🔨 Running: uv venv $VENV_PATH"
  uv venv "$VENV_PATH" || {
    echo "❌ uv venv command failed with exit code $?"
    echo "🔍 Checking if uv is installed..."
    which uv && uv --version || echo "uv not found in PATH"
    exit 1
  }

  if [ ! -d "$VENV_PATH" ]; then
    echo "❌ Failed to create virtual environment"
    exit 1
  fi
  echo "✅ Virtual environment created successfully"
else
  echo "✅ Virtual environment directory already exists"
  # Check if it's actually a valid venv (maybe it's just an empty directory)
  if [ ! -f "$VENV_PATH/bin/activate" ]; then
    echo "🔧 Existing venv appears invalid, cleaning and recreating..."
    # Since this is a Docker volume, we can't remove the directory but we can empty it
    find "$VENV_PATH" -mindepth 1 -delete 2>/dev/null || true
    echo "🔨 Running: uv venv $VENV_PATH"
    uv venv "$VENV_PATH" || {
      echo "❌ uv venv command failed with exit code $?"
      echo "🔍 Checking if uv is installed..."
      which uv && uv --version || echo "uv not found in PATH"
      exit 1
    }
  fi
fi

if [ ! -f "$VENV_PATH/bin/activate" ]; then
  echo "❌ Virtual environment activation script not found at $VENV_PATH/bin/activate"
  ls -la "$VENV_PATH" || echo "Directory does not exist"
  ls -la "$VENV_PATH/bin" || echo "bin directory does not exist"
  exit 1
fi

echo "🚀 Activating virtual environment..."
# shellcheck source=/dev/null
source "$VENV_PATH/bin/activate"

uv pip install --upgrade maturin
uv pip install --editable "$SDK_PYTHON_DIR"
uv pip install --editable "$BLUEPRINT_DIR"

cd "$SDK_PYTHON_DIR"
maturin develop
cd - >/dev/null

export BLUEPRINT_DIR
export SDK_PYTHON_DIR
export SDK_CORE_DIR

watchexec --restart \
  --watch "$BLUEPRINT_DIR/app.py" \
  --watch "$BLUEPRINT_DIR/src" \
  --watch "$SDK_PYTHON_DIR/src" \
  --watch "$SDK_PYTHON_DIR/rust-src" \
  --watch "$SDK_CORE_DIR/src" \
  --watch "$SDK_CORE_DIR/Cargo.toml" \
  --ignore "$SDK_PYTHON_DIR/target" \
  --ignore "$SDK_CORE_DIR/target" \
  --ignore "$BLUEPRINT_DIR/.venv" \
  --ignore "$WORKSPACE/.venv" \
  --ignore "*.pyc" \
  --ignore "__pycache__" \
  --ignore "*.so" \
  -- bash -c '
    set -euo pipefail
    cd "$SDK_PYTHON_DIR"
    maturin develop
    cd "$BLUEPRINT_DIR"
    python app.py
  '
