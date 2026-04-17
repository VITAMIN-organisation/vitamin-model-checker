# VITAMIN Model Checker Docker
This directory contains the Docker configuration for the Model Checker core library.

## Usage
From this directory, you can build and run the model checker in a clean environment:

```bash
# Build the image
make build

# Run unit tests
make test
```

## Branch Independence
This Dockerfile assumes it is being built from the root of the `model-checker` repository or branch.
