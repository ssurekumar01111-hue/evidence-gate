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

### 5. Second Demo Run Produces Different / Missing Evidence (Glossary Term Gone)

The staleness simulation in Step 7 of `scripts/run_demo_timeline.py` deliberately removes
the `Revenue by Customer Class` glossary term from the live `ORDER_DETAILS` asset — that
removal is exactly what triggers the stale-flip the demo is showing. The step **does not
restore the term afterward** (restoration would undo the point).

If you run the demo pipeline more than once without reloading, the second run's Step 1
evidence bundle will already be missing that glossary term, making the staleness detection
in Step 7 a no-op and the output misleading.

**Fix: reload the showcase data before each demo run:**

```bash
python scripts/load_showcase_ecommerce.py
```

This resets the asset back to its pre-demo state (glossary term present, no provenance
properties written) so the full pipeline produces the expected output from a clean slate.
