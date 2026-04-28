# Deployment Ports

Use this page as the port contract for the model-checker project.

## Default behavior

The model-checker is a Python library and CLI package. It does not bind a network port by default.

## Cross-project deployment contract

- `vitamin-workbench` serves users on port `80` (public via reverse proxy)
- `vitamin-module-integrator` serves developers on port `8081`
- `vitamin-model-checker` stays internal (imported as a dependency or mounted into another service)

## Local development note

If you run standalone scripts or tests in this repository, no HTTP port allocation is required.
Only allocate a port if you explicitly add a wrapper service around this library.
