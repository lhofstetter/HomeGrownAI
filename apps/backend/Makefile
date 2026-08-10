# vLLM 0.26.0 requires bitsandbytes>=0.48.1, while the ROCm build
# requires >=0.49.2. Version 0.50.0 supports ROCm 7.14 and Apple Silicon MPS.
BITSANDBYTES_VERSION ?= 0.50.0
PROJECT_PYTHON = "$${UV_PROJECT_ENVIRONMENT:-.venv}/bin/python"
INSTALL_BITSANDBYTES = uv pip install --python $(PROJECT_PYTHON) "bitsandbytes==$(BITSANDBYTES_VERSION)"

.PHONY: sync sync-metal sync-rocm bitsandbytes verify

sync:
	./scripts/sync.sh
	$(INSTALL_BITSANDBYTES)

sync-metal:
	uv python install 3.12
	uv sync --python 3.12 --inexact
	./scripts/bootstrap-metal.sh
	$(INSTALL_BITSANDBYTES)

sync-rocm:
	uv python install 3.14
	uv sync --python 3.14 --inexact
	./scripts/bootstrap-rocm.sh
	$(INSTALL_BITSANDBYTES)

bitsandbytes:
	$(INSTALL_BITSANDBYTES)

verify:
	uv run python -c 'import sys, bitsandbytes, torch, vllm; print(sys.version); print(torch.__version__); print(vllm.__version__); print(bitsandbytes.__version__)'
