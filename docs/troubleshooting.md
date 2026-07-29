# Evidence Gate — Troubleshooting Guide

## Common Issues & Solutions

### 1. Docker Daemon Not Running
If `docker --version` or `docker ps` fails inside Codespaces:
- Ensure the devcontainer was rebuilt with the `ghcr.io/devcontainers/features/docker-in-docker:2` feature enabled.
- Rebuild the devcontainer: Open Command Palette (`Ctrl+Shift+P` / `Cmd+Shift+P`) -> `Codespaces: Rebuild Container`.

### 2. DataHub Quickstart Fails or Times Out
- Verify memory allocation: Codespaces free tier provides 8GB RAM, which is sufficient for `datahub docker quickstart`.
- Run `docker ps` to verify containers `datahub-gms`, `datahub-frontend-react`, `opensearch`, `mysql` are healthy.

### 3. Port Forwarding / UI Unreachable
- Check the VS Code / Codespaces **Ports** tab.
- Confirm port 9002 is listed as Forwarded and Visibility is set to Public/Private.

### 4. `datahub datapack load showcase-ecommerce` Failure
- Confirm `DATAHUB_GMS_URL` points to `http://localhost:8080`.
- Verify GMS health endpoint: `curl http://localhost:8080/health`.
