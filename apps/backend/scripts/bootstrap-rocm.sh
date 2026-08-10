#!/usr/bin/env bash
set -Eeuo pipefail

PROJECT_ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
VENV="${UV_PROJECT_ENVIRONMENT:-${PROJECT_ROOT}/.venv}"
PYTHON="${VENV}/bin/python"

ROCM_VERSION="7.14.0"
PYTORCH_VERSION="2.11.0"
TORCHVISION_VERSION="0.26.0"
TORCHAUDIO_VERSION="2.11.0"
GPU_ARCH="${ROCM_GPU_ARCH:-gfx1201}"

AMD_INDEX="https://repo.amd.com/rocm/whl-multi-arch/"

FLASH_ATTN_URL="https://rocm.frameworks.amd.com/whl-multi-arch/vllm-rdna/flash-attn/flash_attn-2.8.3-py3-none-any.whl"

VLLM_URL="https://rocm.frameworks.amd.com/whl-multi-arch/vllm-rdna/vllm/vllm-0.23.1.dev1%2Brocm7.14.0.g9ddef7117.d20260715-cp314-cp314-linux_x86_64.whl"

die() {
    printf 'error: %s\n' "$*" >&2
    exit 1
}

info() {
    printf '\n==> %s\n' "$*"
}

[[ "$(uname -s)" == "Linux" ]] ||
    die "ROCm bootstrap requires Linux."

[[ "$(uname -m)" == "x86_64" ]] ||
    die "ROCm bootstrap requires x86_64 Linux."

command -v uv >/dev/null 2>&1 ||
    die "uv is not installed or is not in PATH."

[[ -x "${PYTHON}" ]] ||
    die "Project environment does not exist. Run 'uv sync --python 3.14 --inexact' first."

PYTHON_VERSION="$("${PYTHON}" -c \
    'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')"

[[ "${PYTHON_VERSION}" == "3.14" ]] ||
    die "AMD's selected vLLM wheel requires Python 3.14; found ${PYTHON_VERSION}."

[[ -e /dev/kfd ]] ||
    die "/dev/kfd does not exist. Verify that the AMD GPU driver and ROCm are installed."

[[ -d /dev/dri ]] ||
    die "/dev/dri does not exist. Verify that the AMD GPU driver is loaded."

if command -v rocminfo >/dev/null 2>&1; then
    if ! rocminfo 2>/dev/null | grep -q "${GPU_ARCH}"; then
        die "rocminfo did not report ${GPU_ARCH}. Set ROCM_GPU_ARCH if this is intentional."
    fi
else
    printf 'warning: rocminfo is unavailable; GPU architecture could not be verified.\n' >&2
fi

info "Installing AMD PyTorch ${PYTORCH_VERSION} for ${GPU_ARCH}"

uv pip install \
    --python "${PYTHON}" \
    --index-url "${AMD_INDEX}" \
    "torch[device-${GPU_ARCH}]==${PYTORCH_VERSION}+rocm${ROCM_VERSION}" \
    "torchvision[device-${GPU_ARCH}]==${TORCHVISION_VERSION}+rocm${ROCM_VERSION}" \
    "torchaudio==${TORCHAUDIO_VERSION}+rocm${ROCM_VERSION}"

info "Installing AMD RDNA Flash Attention"

uv pip install \
    --python "${PYTHON}" \
    "${FLASH_ATTN_URL}"

info "Installing AMD ROCm vLLM"

uv pip install \
    --python "${PYTHON}" \
    "${VLLM_URL}"

info "Verifying ROCm installation"

"${PYTHON}" <<'PY'
import sys

import torch
import vllm
import flash_attn

print(f"Python:          {sys.version.split()[0]}")
print(f"PyTorch:         {torch.__version__}")
print(f"vLLM:            {vllm.__version__}")
print(f"Flash Attention: {flash_attn.__version__}")
print(f"CUDA/HIP API:    {torch.cuda.is_available()}")

if not torch.cuda.is_available():
    raise SystemExit(
        "PyTorch installed, but torch.cuda.is_available() is false. "
        "Check /dev/kfd permissions, ROCm installation, and GPU support."
    )

print(f"Device count:    {torch.cuda.device_count()}")
print(f"Device name:     {torch.cuda.get_device_name(0)}")
PY

cat <<EOF

ROCm vLLM installation completed.

Before starting vLLM, export:

    source "${VENV}/bin/activate"
    export PYTHONPATH="${VENV}/lib/python3.14/site-packages/_rocm_sdk_core/share/amd_smi\${PYTHONPATH:+:\$PYTHONPATH}"
    export FLASH_ATTENTION_TRITON_AMD_ENABLE=TRUE

You may place those exports in a project environment script.
EOF
