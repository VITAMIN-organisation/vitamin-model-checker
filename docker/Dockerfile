# VITAMIN Model Checker - Core Library Build
# This image is used specifically for running tests and benchmarks in an isolated environment.

FROM python:3.11-slim

WORKDIR /app

# Copy configuration and metadata first
COPY pyproject.toml .
COPY README.md .

# Copy the source package and the test suite
COPY model_checker/ ./model_checker/

# Install the library in editable mode so changes are reflected during development/testing
RUN pip install --no-cache-dir -e ".[dev]"

# By default, trigger the unit test suite on container start
CMD ["pytest", "model_checker/tests/unit"]
