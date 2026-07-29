# Evidence Gate — Setup Guide

## Environment
This project is configured to run inside **GitHub Codespaces** using Docker-in-Docker via `.devcontainer/devcontainer.json`.

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
This starts DataHub containers (GMS, OpenSearch, MySQL, Kafka, DataHub Frontend/UI).

### 3. Forwarded Ports & UI Access
Codespaces automatically forwards the following ports:
- **Port 9002**: DataHub UI
  - **Forwarded URL**: `https://symmetrical-cod-q7g9jgrw4p64c9554-9002.app.github.dev`
  - **Local URL**: `http://localhost:9002`
  - **Credentials**: Username `datahub`, Password `datahub`
- **Port 8080**: DataHub GMS REST API (`http://localhost:8080`)
- **Port 8000**: Evidence Gate FastAPI service (`http://localhost:8000`)

### 4. Load Sample Data (`showcase-ecommerce`)
Ingest the `showcase-ecommerce` datapack into DataHub:
```bash
python scripts/load_showcase_ecommerce.py
```

### 5. Install Dependencies & Configure `.env`
```bash
pip install -r requirements.txt
cp .env.example .env
```

### 6. Verify DataHub Connection
Run the verification script to retrieve datasets and lineage:
```bash
python scripts/verify_mcp_connection.py
```
