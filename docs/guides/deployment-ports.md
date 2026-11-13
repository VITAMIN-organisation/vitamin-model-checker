# Deployment ports

This page lists the default network ports of the sibling projects, for anyone
running them next to this library. `vitamin-model-checker` itself is a Python
library: it installs no command-line program (`pyproject.toml` has no
`[project.scripts]`) and binds no network port, so running its tests or scripts
needs no free port. A service that wraps it documents its port in its own
project.

## Default ports

The sibling projects that serve HTTP use the default ports in Table 1. Each
project's own files are the source; the table names them, and each path is in
that project's repository.

**Table 1: Default ports of the sibling projects.**

| Project | Port | Notes |
| :--- | :---: | :--- |
| `vitamin-workbench` API in Docker | `8000` | `docker/docker-compose.yml` (`BACKEND_PORT`), bound to `127.0.0.1`. |
| `vitamin-workbench` API outside Docker | `8001` | `make backend` (`VWB_PORT`) with `env.example`; `env.server.example` sets `8000`. Both in `docs/operations/configuration-reference.md`. |
| `vitamin-workbench` UI in Docker | `5173` | `docker/docker-compose.yml` host port (`FRONTEND_PORT`), bound to `127.0.0.1`. |
| `vitamin-workbench` UI outside Docker | `5174` | Vite dev server (`PORT`), `docs/operations/configuration-reference.md`. |
| `vitamin-workbench` Ollama | `11434` | `docker/docker-compose.yml` (`OLLAMA_PORT`), optional AI service. |
| `vitamin-workbench` on the server | `80`, `443` | nginx only (`deploy/nginx-vitamin.conf`): `80` redirects to HTTPS; `443` proxies to the API on `8000` and the UI on `5174`. |
| `vitamin-module-integrator` | `8081` | API and UI (`VMI_PORT`), `docs/dev/api-and-config.md`. |
| `vitamin-module-integrator` UI dev | `5180` | Vite dev server, proxies to `8081` (`docs/introduction.md`). |
| `vitamin-benchmark-model-checker` API | `8082` | `apps/api/config.py` (`vbench_port`). |
| `vitamin-benchmark-model-checker` UI dev | `5181` | Vite dev server, proxies `/api` to `8082` (`apps/web/vite.config.ts`). |
