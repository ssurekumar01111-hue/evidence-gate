# Evidence Gate — Setup Guide

## Environment

This project is configured to run inside **GitHub Codespaces** using Docker-in-Docker via `.devcontainer/devcontainer.json`. Codespaces was chosen deliberately — DataHub's full stack (GMS, OpenSearch, MySQL, Kafka, frontend) needs real memory headroom, and running it locally on a laptop without dedicated resources is a rough experience. If you're setting this up outside Codespaces, you'll need Docker with at least 8GB RAM available and the DataHub CLI installed.

## Quickstart Steps

### 1. Confirm Environment

```bash
docker --version
python --version
```

### 2. Start DataHub Local Instance

Run DataHub Docker Quickstart inside the Codespace terminal:

```bash
datahub docker quickstart
```

This starts DataHub containers (GMS, OpenSearch, MySQL, Kafka, DataHub Frontend/UI). First run pulls several GB of images and can take a few minutes; subsequent runs are faster.

### 3. Forwarded Ports & UI Access

Codespaces automatically forwards the following ports. The forwarded URL is specific to your own codespace instance — check the **Ports** tab in VS Code, or use `gh codespace ports forward <port>:<port> -c <your-codespace-name>` from your local machine if you're not using the browser-based editor.

- **Port 9002**: DataHub UI
  - **Local URL**: `http://localhost:9002`
  - **Credentials**: Username `datahub`, Password `datahub`
- **Port 8080**: DataHub GMS REST API (`http://localhost:8080`)
- **Port 8000**: Evidence Gate FastAPI service (`http://localhost:8000`)

### 4. Load Sample Data (`showcase-ecommerce`)

Ingest the `showcase-ecommerce` datapack into DataHub:

```bash
python scripts/load_showcase_ecommerce.py
```

Safe to re-run — it's idempotent against the same URNs.

### 5. Install Dependencies & Configure `.env`

```bash
pip install -r requirements.txt
cp .env.example .env
```

Then edit `.env` and set `DATAHUB_GMS_URL`, `DATAHUB_MCP_URL`, and `GEMINI_API_KEY` (get a key from [Google AI Studio](https://aistudio.google.com/apikey) — used only for turning the deterministic decision facts into readable rationale text, never for the approve/block decision itself).

### 6. Verify DataHub Connection

Run the verification script to retrieve datasets and lineage:

```bash
python scripts/verify_mcp_connection.py
```

### 7. Run the Full Demo Pipeline

```bash
python scripts/submit_change.py --fixture fixtures/net_revenue_rename.json
```

Then open the DataHub UI (port 9002) and search for `order_details` to see the written-back Decision Provenance on the affected asset.

## Teardown

When you're done working, or before switching to a fresh environment:

### Stop the DataHub stack (keep data)

```bash
docker compose -f /home/vscode/.datahub/quickstart/docker-compose.yml -p datahub stop
```

Or more simply, stop the individual containers:

```bash
docker stop datahub-frontend-quickstart-1 datahub-datahub-gms-quickstart-1 datahub-datahub-actions-quickstart-1 datahub-kafka-broker-1 datahub-opensearch-1 datahub-mysql-1
```

Data persists in Docker volumes, so `datahub docker quickstart` will bring everything back next session without re-ingesting.

### Full reset (removes all DataHub data, including any decisions you've written back)

```bash
datahub docker nuke
```

Use this if you want to start completely fresh, e.g. to reproduce the demo scenario from a clean slate. You'll need to re-run steps 4 and 7 above afterward.

### Free up disk space (if you hit "disk space below threshold" errors)

DataHub's images and old containers can accumulate quickly across repeated restarts. If `datahub docker quickstart` warns about insufficient disk space:

```bash
docker system df              # see what's using space
docker system prune -af --volumes   # only run this if you don't need to preserve
                                     # any currently-stopped container's data —
                                     # check `docker ps` first to confirm MySQL
                                     # (or whichever container holds your data)
                                     # is still Up before using --volumes
```

### Stop the codespace itself

From `github.com/codespaces`, or via `gh codespace stop -c <your-codespace-name>` — this pauses compute billing. A stopped codespace retains its filesystem (including any Docker volumes) and resumes from where you left off, so this is the normal way to pause work between sessions rather than deleting the codespace.

## Troubleshooting

See `docs/troubleshooting.md` for common DataHub/MCP connectivity issues, including GMS taking longer than expected to become healthy after a restart, and OpenSearch index staleness after a container recreation.
