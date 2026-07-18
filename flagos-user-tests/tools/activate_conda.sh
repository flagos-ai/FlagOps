#!/bin/bash

# Copyright 2026 FlagOS Contributors
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# Activate a conda environment inside a container.
#
# Detects conda installation, initializes the shell, then activates the env.
# Must be sourced (not executed) so the activation persists in the caller's shell:
#   source tools/activate_conda.sh <env_name> [conda_path]
#
# Arguments:
#   env_name    — conda environment name (required)
#   conda_path  — path to conda installation (optional, auto-detected if omitted)

set -e

_activate_conda() {
    local env_name="${1:?Usage: source activate_conda.sh <env_name> [conda_path]}"
    local conda_path="${2:-}"

    # Auto-detect conda path if not provided
    if [ -z "$conda_path" ]; then
        if [ -n "$CONDA_DIR" ] && [ -d "$CONDA_DIR" ]; then
            conda_path="$CONDA_DIR"
        elif command -v conda &>/dev/null; then
            conda_path="$(conda info --base 2>/dev/null)"
        elif [ -d "$HOME/miniconda3" ]; then
            conda_path="$HOME/miniconda3"
        elif [ -d "$HOME/anaconda3" ]; then
            conda_path="$HOME/anaconda3"
        elif [ -d "/opt/conda" ]; then
            conda_path="/opt/conda"
        fi
    fi

    if [ -z "$conda_path" ]; then
        echo "[activate_conda] WARNING: conda not found, skipping activation"
        return 0
    fi

    local conda_sh="$conda_path/etc/profile.d/conda.sh"
    if [ ! -f "$conda_sh" ]; then
        echo "[activate_conda] ERROR: conda.sh not found at $conda_sh"
        return 1
    fi

    # Initialize conda for this shell
    echo "[activate_conda] Initializing conda from $conda_path"
    source "$conda_sh"

    # Activate the environment
    echo "[activate_conda] Activating environment: $env_name"
    conda activate "$env_name" || {
        echo "[activate_conda] ERROR: Failed to activate conda env '$env_name'"
        return 1
    }

    echo "[activate_conda] Active Python: $(which python) ($(python --version 2>&1))"
}

_activate_conda "$@"
