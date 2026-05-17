#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "Offline Project Launch Assistant E2E User Test"
echo "Project root: ${ROOT_DIR}"
echo

python3 -B "${ROOT_DIR}/main.py" e2e-check
