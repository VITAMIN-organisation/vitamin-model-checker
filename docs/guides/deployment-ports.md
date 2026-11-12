# Deployment Ports

`vitamin-model-checker` is a Python library. It installs no command-line program
(`pyproject.toml` has no `[project.scripts]`) and binds no network port.

## Cross-Project Port Contract

The sibling projects that serve HTTP use these default ports. Each project's
own files are the source; the table names them.

| Project | Port | Notes |
|---|---:|---|
| `vitamin-workbench` API | `8000` | `docker/docker-compose.yml` (`BACKEND_PORT`), bound to `127.0.0.1`. |
| `vitamin-workbench` UI in Docker | `5173` | `docker/docker-compose.yml` host port (`FRONTEND_PORT`), bound to `127.0.0.1`. |
| `vitamin-workbench` UI outside Docker | `5174` | Vite dev server (`PORT`), `docs/operations/configuration-reference.md`. |
| `vitamin-workbench` Ollama | `11434` | `docker/docker-compose.yml` (`OLLAMA_PORT`), optional AI service. |
| `vitamin-workbench` on the server | `80`, `443` | nginx only (`deploy/nginx-vitamin.conf`): `80` redirects to HTTPS; `443` proxies to the API on `8000` and the UI on `5174`. |
| `vitamin-module-integrator` | `8081` | API and UI (`VMI_PORT`), `docs/dev/api-and-config.md`. |
| `vitamin-module-integrator` UI dev | `5180` | Vite dev server, proxies to `8081` (`docs/introduction.md`). |
| `vitamin-model-checker` | none | Imported as a Python dependency. |

## Local Development

Running tests or scripts in this repository does not require a reserved HTTP
port.

Only allocate a port if you intentionally wrap this package in a service. If
you do that, document the wrapper in the owning project rather than treating it
as part of the core model-checker library.
