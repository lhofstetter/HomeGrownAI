#!/usr/bin/env bash
set -Eeuo pipefail

PROJECT_ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
VENV="${UV_PROJECT_ENVIRONMENT:-${PROJECT_ROOT}/.venv}"
PYTHON="${VENV}/bin/python"

VLLM_VERSION="0.26.0"
VLLM_CORE_URL="https://github.com/vllm-project/vllm/releases/download/v${VLLM_VERSION}/vllm-${VLLM_VERSION}%2Bcpu-cp312-cp312-macosx_11_0_arm64.whl"

VLLM_METAL_RELEASE_API="https://api.github.com/repos/vllm-project/vllm-metal/releases/latest"

die() {
    printf 'error: %s\n' "$*" >&2
    exit 1
}

info() {
    printf '\n==> %s\n' "$*"
}

[[ "$(uname -s)" == "Darwin" ]] ||
    die "Metal bootstrap requires macOS."

[[ "$(uname -m)" == "arm64" ]] ||
    die "vllm-metal requires native Apple Silicon arm64, not Rosetta."

command -v uv >/dev/null 2>&1 ||
    die "uv is not installed or is not in PATH."

command -v curl >/dev/null 2>&1 ||
    die "curl is not installed or is not in PATH."

[[ -x "${PYTHON}" ]] ||
    die "Project environment does not exist. Run 'uv sync --python 3.12 --inexact' first."

PYTHON_VERSION="$("${PYTHON}" -c \
    'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')"

PYTHON_ARCH="$("${PYTHON}" -c 'import platform; print(platform.machine())')"

[[ "${PYTHON_VERSION}" == "3.12" ]] ||
    die "vllm-metal requires Python 3.12; found ${PYTHON_VERSION}."

[[ "${PYTHON_ARCH}" == "arm64" ]] ||
    die "The project Python is ${PYTHON_ARCH}, not native arm64."

info "Installing vLLM core ${VLLM_VERSION} for macOS arm64"

uv pip install \
    --python "${PYTHON}" \
    "${VLLM_CORE_URL}"

info "Finding the latest vllm-metal release wheel"

METAL_WHEEL_URL="$(
    curl -fsSL "${VLLM_METAL_RELEASE_API}" |
        "${PYTHON}" -c '
import json
import sys

release = json.load(sys.stdin)

wheels = [
    asset["browser_download_url"]
    for asset in release.get("assets", [])
    if asset.get("name", "").endswith(".whl")
]

if not wheels:
    raise SystemExit("No wheel was attached to the latest vllm-metal release")

# Current releases provide a single macOS arm64 wheel. Prefer an explicitly
# arm64-tagged wheel if multiple wheels are eventually published.
arm64 = [url for url in wheels if "arm64" in url]
print((arm64 or wheels)[0])
'
)" || die "Could not determine the latest vllm-metal wheel URL."

[[ -n "${METAL_WHEEL_URL}" ]] ||
    die "The vllm-metal wheel URL was empty."

info "Installing vllm-metal from ${METAL_WHEEL_URL}"

uv pip install \
    --python "${PYTHON}" \
    "${METAL_WHEEL_URL}"

info "Verifying Metal installation"

"${PYTHON}" <<'PY'
import platform
import sys

import vllm
import vllm_metal

print(f"Python:      {sys.version.split()[0]}")
print(f"Architecture:{platform.machine()}")
print(f"vLLM:        {vllm.__version__}")
print("vllm-metal: imported successfully")
PY

printf '\nMetal vLLM installation completed in %s\n' "${VENV}"
