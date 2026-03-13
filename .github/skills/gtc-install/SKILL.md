````skill
---
name: gtc-install
description: Clone, build, and run the Ground Truth Curator (andrewDoing/GroundTruthCurator). Starts the Cosmos DB Emulator, initializes containers, builds the Python backend and React frontend, and runs in consolidated or development mode. Trigger phrases include "install GTC", "run ground truth curator", "GTC", "GTC dev setup".
---

# Ground Truth Curator Installation

The Ground Truth Curator is an open-source platform for subject-matter experts to create and maintain high-quality ground truth datasets for agent evaluation and model accuracy measurement. It provides a structured workflow for curating question-answer pairs, tagging, assignment management, and export.

This skill targets users who have never used the Ground Truth Curator. They may not know what resources are required, what those resources are used for, what configuration options are available, or how to run it once deployed. Provide clear and comprehensive guidance on these topics.

## Guidelines

- Never just stub things out in the configuration, provision everything the user asks for with the appropriate permissions and settings to make it work.

- Never assume you know what to name something or what settings to use. Always ask the user for preferences and guidance on naming, configuration options, and deployment choices.

## Source Code

The Ground Truth Curator is available on GitHub at: <https://github.com/andrewDoing/GroundTruthCurator>.

You can clone from that location. The folders of interest for installation are:

- `backend` — Python (FastAPI) API server
- `frontend` — React + Vite + TypeScript UI
- `infra` — Bicep templates and deployment scripts for Azure

Additional documentation can be found in the repo's `docs/` folder and the per-component READMEs. Those should be considered the most up-to-date and comprehensive source of information.

> **Authoritative source**: The repository README, `backend/README.md`, and `frontend/README.md` are the source of truth for configuration variables, defaults, and supported options. This skill provides a subset for quick guidance. Always fetch the repo docs for the latest details.

## Prerequisites

Before running the Ground Truth Curator, the following must be installed:

- [Python 3.11](https://www.python.org/downloads/) — required for the backend.
- [uv](https://docs.astral.sh/uv) — Python virtualenv and package manager used by the backend.
- [Node.js 18+](https://nodejs.org/) (LTS recommended) with npm 9+ — required for the frontend.
- [Docker Desktop](https://www.docker.com/) — required to run the Azure Cosmos DB Emulator locally.

For Azure deployment, the user also needs the [Azure CLI](https://learn.microsoft.com/cli/azure/install-azure-cli).

## Local Deployment

When running the Ground Truth Curator locally, the following components are required:

- **Azure Cosmos DB Emulator** (Docker) — stores ground truth items, assignments, and tags.

### Step 1 — Start the Cosmos DB Emulator

Run the emulator interactively so logs stream to the console. Unless the user explicitly requests a detached container, use `create_and_run_task` in VS Code so the emulator runs in a visible terminal:

```bash
docker run --rm --name cosmos-emulator -p 8081:8081 \
  mcr.microsoft.com/cosmosdb/linux/azure-cosmos-emulator:vnext-preview
```

Do **not** pass `-d` (detached mode) by default. Running interactively lets the user see emulator startup logs and diagnose issues directly. If the user prefers to run detached, add `-d` and use `docker logs -f cosmos-emulator` to tail output.

The emulator can take a few seconds to become ready after starting. The repository's environment files are already configured to use the emulator over HTTP at `http://localhost:8081`. No HTTPS or certificate setup is required.

### Step 2 — Install Backend Dependencies

From the `backend/` directory:

```bash
cd backend
uv sync
```

This creates a local `.venv` and installs all dependencies.

### Step 3 — Initialize Cosmos DB Containers

Before running the application for the first time, create the required Cosmos DB containers:

```bash
uv run python scripts/cosmos_container_manager.py \
  --endpoint http://localhost:8081 \
  --key "<EMULATOR_KEY>" \
  --no-verify \
  --db gt-curator \
  --gt-container --assignments-container --tags-container
```

Replace `<EMULATOR_KEY>` with the well-known Cosmos DB Emulator primary key. You can find it in the [Azure Cosmos DB Emulator documentation](https://learn.microsoft.com/azure/cosmos-db/emulator#authentication) or by running `environments/sample.env` in the repository, which contains the key as `GTC_COSMOS_KEY`. The script is idempotent and safe to run repeatedly.

### Step 4 — Configure Environment

The backend uses `pydantic-settings` with the `GTC_` prefix. By default it auto-loads `environments/.dev.env`. This file does not exist initially; create it from the provided sample:

```bash
cp environments/sample.env environments/.dev.env
```

You can overlay additional env files:

```bash
export GTC_ENV_FILE="environments/.dev.env,environments/local.env"
```

Key values provided by the default dev env:

| Variable | Value | Purpose |
|---|---|---|
| `GTC_REPO_BACKEND` | `cosmos` | Use Cosmos DB as the data store |
| `GTC_COSMOS_ENDPOINT` | `http://localhost:8081` | Emulator endpoint |
| `GTC_COSMOS_KEY` | *(emulator well-known key)* | Authentication key |
| `GTC_COSMOS_CONNECTION_VERIFY` | `false` | Skip TLS verification for emulator |
| `GTC_USE_COSMOS_EMULATOR` | `true` | Enable emulator mode |
| `GTC_COSMOS_DISABLE_UNICODE_ESCAPE` | `true` | Workaround for emulator Unicode bug |

If you need secrets or developer-specific overrides, create `environments/local.env` (git-ignored):

```bash
# API keys and tokens (do not commit real values)
GTC_AZ_FOUNDRY_KEY=<your-azure-ai-foundry-key>
GTC_AZ_SEARCH_KEY=<your-azure-ai-search-key>
```

### Step 5 — Run the Backend

```bash
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Verify health:

```bash
curl http://localhost:8000/healthz
```

Expected response:

```json
{
  "status": "ok",
  "repoBackend": "CosmosGroundTruthRepo",
  "cosmos": {
    "endpoint": "http://localhost:8081",
    "db": "gt-curator",
    "container": "ground_truth"
  }
}
```

### Step 6 — Install Frontend Dependencies

From the `frontend/` directory:

```bash
cd frontend
npm install
```

Optionally copy `.env.example` to `.env.local` and adjust:

| Variable | Default | Purpose |
|---|---|---|
| `VITE_API_BASE_URL` | `http://localhost:8000` | Backend base URL |
| `VITE_OPENAPI_URL` | *(derived from API base)* | OpenAPI spec URL for type generation |
| `VITE_DEV_USER_ID` | *(none)* | Optional dev-only user id sent as `X-User-Id` |
| `VITE_SELF_SERVE_LIMIT` | *(none)* | Optional default for self-serve assignments |

### Step 7 — Run the Frontend

```bash
npm run dev
```

Visit <http://localhost:5173>. The Vite dev server proxies `/v1/...` requests to the backend at `VITE_API_BASE_URL`.

Use VS Code tasks (`create_and_run_task`) so that each process (emulator, backend, frontend) runs in a visible, interactive terminal the user can monitor. Do **not** use background terminals (`isBackground` on `run_in_terminal`), because the user cannot see or interact with those.

### Optional — Seed Sample Data

```bash
cd backend
uv run python scripts/init_seed_data.py --dataset demo --count 50
```

Do **not** pass `--approve`. Demo items should remain in "draft" status so they are eligible for self-serve assignment. Approved items cannot be assigned and will not appear in the queue.

## Azure Deployment

When deploying the Ground Truth Curator to Azure, the following resources are needed:

- **Azure Cosmos DB** (NoSQL API) — stores ground truth items, assignments, and tags
- A container hosting solution:
  - Azure Container Apps (default if user has no preference)
  - Azure Kubernetes Service
  - Azure App Service for Containers

The `infra/` directory in the repository contains Bicep templates (`main.bicep`) and a deployment script (`deploy-demo-infra.sh`) that can provision these resources. These templates are a useful reference and may do exactly what you need, but using them is not required. If the user already has infrastructure provisioned, prefers a different IaC tool (Terraform, Pulumi, ARM templates), or wants to provision resources manually through the portal or CLI, that is perfectly fine. Adapt the deployment approach to match the user's environment and preferences.

### Container Initialization for Azure Cosmos DB

Use Azure AD authentication instead of keys:

```bash
uv run python scripts/cosmos_container_manager.py \
  --endpoint https://<your-account>.documents.azure.com:443/ \
  --use-aad \
  --db gt-curator \
  --gt-container --assignments-container --tags-container
```

If the Cosmos DB account uses **serverless** capacity mode, do **not** pass `--max-throughput`. Serverless accounts do not support provisioned or autoscale throughput, and the SDK raises a `TypeError` if the parameter is present.

The user running the script needs the **Cosmos DB Built-in Data Contributor** role (definition ID `00000000-0000-0000-0000-000000000002`) on the Cosmos DB account. Assign it with:

```bash
az cosmosdb sql role assignment create \
  --account-name <cosmos-account> \
  --resource-group <resource-group> \
  --role-definition-id 00000000-0000-0000-0000-000000000002 \
  --principal-id <user-or-identity-object-id> \
  --scope /
```

Also assign this role to the Container App's managed identity so the application can read and write data at runtime.

### Environment Configuration for Azure

```bash
GTC_REPO_BACKEND=cosmos
GTC_COSMOS_ENDPOINT=https://<your-account>.documents.azure.com:443/
```

Use managed identity for authentication. Assign only the minimum required RBAC roles. Avoid storing connection strings or account keys; if keys are unavoidable, store them in Azure Key Vault.

### Deploy Env Vars to Azure Container Apps

```bash
cd backend
scripts/aca-push-env.sh \
  --resource-group <rg-name> \
  --name <container-app-name> \
  --yes
```

Options: `--env-file PATH`, `--prefix REGEX`, `--container NAME`, `--dry-run`.

This sets plain env vars. Keep real secrets in Key Vault and wire them via `az containerapp secret set` + `secretref:` envs.

## Docker / Container Image

The backend includes a multi-stage Dockerfile that builds both the frontend and backend into a single image. The build context must be the **repository root** (not `backend/`), because the first stage copies and builds the `frontend/` directory:

```bash
docker build --rm -t gtc-backend:latest -f backend/Dockerfile .
```

When building on Apple Silicon (arm64) for deployment to Azure (amd64), use `--platform linux/amd64`:

```bash
docker build --rm --platform linux/amd64 -t gtc-backend:latest -f backend/Dockerfile .
```

Inside the container, use `http://host.docker.internal:8081` to reach the host's Cosmos DB Emulator.

## Ports

| Service | Default Port | Purpose |
|---|---|---|
| Backend (FastAPI) | 8000 | API server |
| Frontend (Vite dev) | 5173 | Development UI server |
| Cosmos DB Emulator | 8081 | Local database |

## What Resources Are Used For

- **Azure Cosmos DB**: Stores all ground truth items, SME assignments, and tag definitions. Uses the NoSQL API with hierarchical partition keys.
- **Container hosting solution**: Runs the backend API which provides the REST endpoints for the frontend and any integrations.

## Authentication

The backend supports:

- **Anonymous / Dev mode** (default): No authentication required. Uses the `X-User-Id` header if provided, otherwise `anonymous`. Appropriate for local development and testing.
- **EasyAuth**: When hosted in Azure App Service or Container Apps, EasyAuth can be configured with the Microsoft identity provider. Set `GTC_EZAUTH_ENABLED=true`. The app derives user identity from the principal's `email`, then `oid`, then `name`.
- See `infra/easy-auth-setup.md` in the repository for configuration steps.

## Telemetry

### Backend

The backend emits structured logs to stdout. Optionally enable OpenTelemetry export to Azure Monitor / Application Insights:

```bash
GTC_AZ_MONITOR_CONNECTION_STRING=<your-connection-string>
```

Optional controls:

| Variable | Default | Purpose |
|---|---|---|
| `GTC_AZ_MONITOR_ENABLED` | `true` | Toggle telemetry wiring |
| `GTC_SERVICE_NAME` | `gtc-backend` | `service.name` resource attribute |

When no connection string is provided, telemetry is a no-op.

### Frontend

Client telemetry is configured via Vite env vars:

| Variable | Default | Purpose |
|---|---|---|
| `VITE_TELEMETRY_BACKEND` | `otlp` | `otlp`, `appinsights`, or `none` |
| `VITE_OTLP_EXPORTER_URL` | *(none)* | OTLP HTTP collector endpoint |
| `VITE_APPINSIGHTS_CONNECTION_STRING` | *(none)* | Azure App Insights connection string |
| `VITE_ENVIRONMENT` | *(none)* | Environment label |
| `VITE_BUILD_SHA` | *(none)* | Short commit SHA |

Telemetry automatically no-ops in demo mode or when config is missing.

## Running Tests

### Backend

```bash
# Unit tests
cd backend
uv run pytest -q tests/unit

# Integration tests (with emulator)
GTC_ENV_FILE="environments/integration-tests.env,environments/local.env" \
  uv run pytest -q tests/integration

# Container smoke test
GTC_RUN_DOCKER_TESTS=1 uv run pytest -vv \
  tests/integration/test_container_smoke.py::test_healthz_ok_in_containerized_env
```

### Frontend

```bash
cd frontend
npm test -- --run
```

## Troubleshooting

- **Emulator not ready**: It can take a few seconds after `docker run` before it accepts connections. Retry.
- **Connection issues**: Verify the container is running (`docker ps`) and port `8081` is mapped.
- **Self-signed TLS**: Keep `GTC_COSMOS_CONNECTION_VERIFY=false` (already set in the dev env files).
- **Endpoint mismatch in containers**: Inside Docker, use `http://host.docker.internal:8081` to reach the host emulator.
- **Wrong env files**: Verify `GTC_ENV_FILE` or rely on the default auto-load.
- **Missing `.dev.env`**: The backend returns 500 at startup if `environments/.dev.env` is missing. Create it from `sample.env`: `cp environments/sample.env environments/.dev.env`.
- **API requests 404/CORS in dev**: Use relative paths like `/v1/...` and confirm the Vite proxy is active via `npm run dev`.
- **Unicode errors with emulator**: Set `GTC_COSMOS_DISABLE_UNICODE_ESCAPE=true` in your local env.
- **macOS SSL errors with `--use-aad`**: When running `cosmos_container_manager.py --use-aad` on macOS, Python may fail with `SSL: CERTIFICATE_VERIFY_FAILED`. Set the cert bundle from certifi before running:

  ```bash
  export SSL_CERT_FILE=$(python -c "import certifi; print(certifi.where())")
  export REQUESTS_CA_BUNDLE="$SSL_CERT_FILE"
  ```

- **Serverless Cosmos and `--max-throughput`**: Do not pass `--max-throughput` when the Cosmos DB account uses serverless capacity mode. The SDK raises `TypeError` because serverless does not support provisioned throughput.
- **Cosmos DB RBAC Forbidden (403)**: When using `--use-aad`, the caller needs the Cosmos DB Built-in Data Contributor role. See the Container Initialization for Azure Cosmos DB section for the assignment command.
- **Easy Auth returns 401 in browser**: See `infra/easy-auth-setup.md` in the repository. Common causes: missing client secret on the Container App, missing token store configuration, or the Container App's system-assigned identity lacking `Storage Blob Data Contributor` on the token store storage account.

## Cleanup

Delete all emulator databases to reset local state:

```bash
cd backend
uv run python scripts/delete_cosmos_emulator_dbs.py
```

## Support Documents

For additional reference on hardening and production security, see [references/hardening.md](references/hardening.md).
````
