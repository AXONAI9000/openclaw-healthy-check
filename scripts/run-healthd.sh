#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd -- "${SCRIPT_DIR}/.." && pwd)"

export PATH="/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin:${PATH:-}"
export PYTHONPATH="${ROOT_DIR}/src"

CONFIG_PATH="${OPENCLAW_HEALTHD_CONFIG:-${ROOT_DIR}/config.toml}"

exec /usr/bin/python3 -m oc_healthd.main --config "${CONFIG_PATH}" "$@"

