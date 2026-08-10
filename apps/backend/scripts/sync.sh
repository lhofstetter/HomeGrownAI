#!/usr/bin/env bash
set -Eeuo pipefail

PROJECT_ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${PROJECT_ROOT}"

OS="$(uname -s)"
ARCH="$(uname -m)"

case "${OS}:${ARCH}" in
    Darwin:arm64)
        PYTHON_VERSION="3.12"
        BOOTSTRAP="./scripts/bootstrap-metal.sh"
        ;;

    Linux:x86_64)
        PYTHON_VERSION="3.14"
        BOOTSTRAP="./scripts/bootstrap-rocm.sh"
        ;;

    *)
        printf 'error: unsupported platform: %s/%s\n' "${OS}" "${ARCH}" >&2
        exit 1
        ;;
esac

command -v uv >/dev/null 2>&1 || {
    printf 'error: uv is not installed or is not in PATH\n' >&2
    exit 1
}

printf '\n==> Syncing project with Python %s\n' "${PYTHON_VERSION}"

uv python install "${PYTHON_VERSION}"

# Important: the accelerator packages are installed separately with uv pip.
# --inexact prevents uv sync from deleting those packages as extraneous.
uv sync \
    --python "${PYTHON_VERSION}" \
    --inexact

"${BOOTSTRAP}"
