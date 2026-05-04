# Deployment Ports

`vitamin-model-checker` is a Python library and CLI package. It does not bind a
network port by default.

## Cross-Project Port Contract

| Project | Default port | Notes |
|---|---:|---|
| `vitamin-workbench` | `80` | User-facing web/API application, usually behind a reverse proxy. |
| `vitamin-module-integrator` | `8081` | Developer tool for bundle validation and integration. |
| `vitamin-model-checker` | none | Imported as a Python dependency or mounted into another service. |

## Local Development

Running tests, benchmarks, or scripts in this repository does not require a
reserved HTTP port.

Only allocate a port if you intentionally wrap this package in a service. If
you do that, document the wrapper in the owning project rather than treating it
as part of the core model-checker library.
