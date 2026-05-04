# Docker

This directory contains the Docker setup for the `vitamin-model-checker` core
library. Use it when you want a clean Python 3.11 environment for smoke tests or
CI-style checks.

## Build And Run

Run these commands from the `docker/` directory:

```bash
make build
make run
make test
```

What they do:

- `make build` builds the image using the repository root as the Docker build
  context,
- `make run` starts the image with the Dockerfile default command,
- `make test` runs the unit test suite inside the container.

The image installs the package in editable mode with development dependencies:

```bash
pip install -e ".[dev]"
```

## Direct Docker Commands

From the repository root:

```bash
docker build -t vitamin-model-checker -f docker/Dockerfile .
docker run --rm vitamin-model-checker
docker run --rm vitamin-model-checker pytest model_checker/tests/unit
```

## Notes

- This image is for the library package, not a web service.
- No HTTP port is exposed.
- CI uses the same idea: build the package image, then run a smoke test.
