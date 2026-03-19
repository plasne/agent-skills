---
name: aml-eval-runner-install
description: Clone, configure, and deploy the AML Evaluation Runner (commercial-software-engineering/aml-evaluation-runner). Provisions Azure Machine Learning workspace, Storage Account, and supporting resources. Builds the experiment image and runs evaluation pipelines. Trigger phrases include "install AML eval runner", "run AML evaluation runner", "AML eval runner", "experiment runner setup", "install evaluation runner", "deploy eval runner".
---

## Execution Model

> [!IMPORTANT]
> **Do not execute tasks from this skill directly.** Every discrete task you
> derive from this skill must be delegated to its own sub-agent. Each sub-agent
> should be given this skill file's path so it can read the full instructions
> itself.
>
> For example, if the user asks to "deploy the AML runner and run a pipeline,"
> that is two tasks — one sub-agent to deploy infrastructure, another to
> configure and run the pipeline. Break the work into logical tasks and run
> each in its own sub-agent.

When the user asks for a large end-to-end workflow, do not treat it as one
continuous execution stream. Split the work into explicit phases and delegate
each phase separately.

Recommended phases for long AML runner work:

1. discovery and plan
2. infrastructure and shared resource provisioning
3. authentication and RBAC
4. data staging and configuration
5. pipeline submission and monitoring
6. validation and handoff

Additional rules for avoiding main-context overflow:

- Keep the main thread in a coordinator role. Use sub-agents for execution,
  especially for builds, Azure provisioning, AML runs, log inspection, and
  retry/debug loops.
- After each phase, write or update concise artifacts in the session workspace
  when available (for example: env files, JSON summaries, app IDs, URLs, run
  IDs, failure notes, and next-step notes). Prefer artifact handoff over
  repeating all state in the conversation.
- Successful long-running commands should be summarized briefly. Only surface
  full logs when a command fails or when specific output is required to make a
  decision.
- If a phase uncovers a new discrete task, delegate that follow-up as its own
  sub-agent instead of extending the current thread indefinitely.
- Before moving to the next phase, checkpoint the current live state: resource
  names, important IDs, artifact paths, verified URLs, and any unresolved
  blockers.

# AML Evaluation Runner Installation

The AML Evaluation Runner is a reusable framework built on Azure Machine Learning for running inference, evaluation, and summarization experiments at scale. It uses AML parallel jobs for concurrency and retry, supports iteration-based evaluation for statistical significance, and is agnostic about inference and evaluation implementations. Users plug in their own inference and evaluation modules while the runner orchestrates the pipeline.

This skill targets users who have never used the AML Evaluation Runner. They may not know what Azure resources are required, what those resources are used for, what configuration options are available, or how to run experiments once deployed. Provide clear and comprehensive guidance on these topics.

## Guidelines

- Never stub things out in the configuration. Provision everything the user asks for with the appropriate permissions and settings to make it work.

- Never assume you know what to name something or what settings to use. Always ask the user for preferences and guidance on naming, configuration options, and deployment choices.

- The repository contains folders for demo-experiments, evaluation, inference, ingestion, and search. These are reference implementations and demo tooling. The runner itself lives in the `experiment` folder. Focus installation guidance on the `experiment` folder and `infra` folder only.

- Ask the user whether they want to use either of the available "actions" (catalog integration, mlflow logging). Actions are optional plug-ins that hook into the inference, evaluation, or summarization steps.

- Do not deploy VNets, Private Endpoints, Private DNS Zones, NSGs, or any network-isolation infrastructure unless the user explicitly requests it. The default deployment should use public endpoints with RBAC-based security. The `SetupEnv.ps1` Bicep templates deploy all of this extra infrastructure automatically — do not use them unless the user specifically asks for private networking or production hardening.

## Source Code

The AML Evaluation Runner is available on GitHub at: <https://github.com/commercial-software-engineering/aml-evaluation-runner>.

This is a **private repository** under the `commercial-software-engineering` GitHub organization. HTTPS clone will fail with "Repository not found" unless the user has a cached credential or `gh` CLI configured. **Always clone via SSH first.** Only fall back to HTTPS if the user specifically asks for it and has credentials configured.

The folders of interest for installation are:

- `experiment` — Python CLI that kicks off AML parallel job pipelines (inference, evaluation, summarization)
- `infra` — Bicep templates and PowerShell deployment script for Azure resources
- `actions` — Optional plug-in actions that hook into pipeline steps

Ignore these folders during installation (they are reference implementations and demo tooling):

- `demo-experiments`
- `evaluation`
- `inference`
- `ingestion`
- `search`
- `agent`

Additional documentation can be found in the repo's `docs/` folder and per-component READMEs. Those should be considered the most up-to-date and comprehensive source of information.

> **Authoritative source**: The repository README, `experiment/README.md`, `infra/README.md`, and `actions/README.md` are the source of truth for configuration variables, defaults, and supported options. This skill provides a subset for quick guidance. Always fetch the repo docs for the latest details.

## Prerequisites

Before using the AML Evaluation Runner, the following must be installed:

- [Python 3.10+](https://www.python.org/downloads/) — required for the experiment CLI and AML jobs.
- [uv](https://docs.astral.sh/uv) (version 0.8.9+) — Python virtualenv and package manager.
- [Azure CLI](https://learn.microsoft.com/cli/azure/install-azure-cli) — required for authentication and resource provisioning. Also install the `ml` and `application-insights` extensions:

  ```bash
  az extension add --name ml
  az extension add --name application-insights
  ```

- [Docker Desktop](https://www.docker.com/) — required for building AML container images.
- [PowerShell](https://learn.microsoft.com/powershell/scripting/install/installing-powershell) — optional, only needed if using `SetupEnv.ps1` for Bicep-based deployment. On macOS: `brew install powershell/tap/powershell`.
- [DevTunnel](https://learn.microsoft.com/azure/developer/dev-tunnels/get-started) — optional, required only for running inference locally against a remote AML job.

## Azure Resources Required

The runner requires these Azure resources. When deploying alongside the Experiment Catalog, the Storage Account, Key Vault, Log Analytics, and Application Insights can be shared between both systems to reduce cost and complexity.

- **Azure Machine Learning workspace** (Basic SKU) — orchestrates parallel job pipelines for inference, evaluation, and summarization.
- **Storage Account** (for AML) — stores ground truth inputs, inference outputs, evaluation results, and summarization artifacts via AML datastores.
- **Key Vault** — required by the AML workspace as a platform dependency. The runner itself does not directly access Key Vault, but AML needs it for workspace operations and secret storage (such as the Application Insights connection string).
- **Container Registry** — stores the custom Docker image used by AML parallel jobs.
- **Application Insights** — collects telemetry and logging from AML jobs.
- **Log Analytics workspace** — backing store for Application Insights.
- **AML Compute Cluster** — executes the parallel jobs. Default SKU is Standard_D3_v2 with 0–3 node autoscale.
- **User-Assigned Managed Identity** — used by the AML compute cluster to access the storage account and other resources.

Resources that the infra scripts can also deploy but are **not required** for the runner itself (ask the user before deploying these):

- Azure Cosmos DB (for ground truth curation, not the runner)
- Azure AI Search (for search indexing, not the runner)
- Azure AI Foundry (for agent development, not the runner)
- Container App Environment (for hosting services, not the runner)
- App Configuration (for centralized config, not the runner)
- Catalog Storage Account (for experiment catalog, not the runner)

## Infrastructure Deployment

### Preferred Method: Azure CLI

Deploy only the resources listed in the "Azure Resources Required" section above using `az` CLI commands. This is the **recommended approach** because it deploys exactly what is needed, gives clear per-resource feedback, and does not require PowerShell.

> [!IMPORTANT]
> The `infra/` directory contains Bicep templates and a `SetupEnv.ps1` script, but even with `-EnableAML`, these templates deploy significant additional infrastructure (VNet, subnets, NSGs, Private DNS Zones, Private Endpoints for every resource) that is **not required** for the runner to function. **Do not use the Bicep templates or `SetupEnv.ps1` unless the user explicitly asks for private networking or production hardening.** Default to the `az` CLI approach below, which deploys only what is needed with public endpoints and RBAC.

All `az` commands below should be run in a visible terminal so the user can see progress. For long-running commands (deployment group create, etc.), prefer `create_and_run_task` over background terminals so output streams in the VS Code terminal panel.

Ask the user for a **resource naming prefix** and the **resource group** (which may already exist).

> **Naming constraints**: Azure resource names have global uniqueness and character restrictions. Storage Account and ACR names cannot contain hyphens and must be globally unique (3–24 lowercase alphanumeric characters). Key Vault names must be globally unique (3–24 alphanumeric characters and hyphens). When the prefix alone is too short or collides, append a disambiguator (for example, `evalacr03`, `evalstorage03`, `eval-kv-03`). Ask the user for guidance if a name collision occurs.

Then deploy these resources in order:

#### Step 1 — Resource Group

```bash
az group create --name <rg-name> --location <location>
```

Skip if the resource group already exists.

#### Step 2 — User-Assigned Managed Identity

```bash
az identity create --name <prefix>-identity --resource-group <rg-name> --location <location>
```

Capture the `clientId` and `principalId` from the output.

#### Step 3 — Log Analytics Workspace

```bash
az monitor log-analytics workspace create \
  --resource-group <rg-name> \
  --workspace-name <prefix>-logs \
  --location <location>
```

#### Step 4 — Application Insights

```bash
az monitor app-insights component create \
  --app <prefix>-appinsights \
  --location <location> \
  --resource-group <rg-name> \
  --workspace <prefix>-logs \
  --kind web \
  --application-type web
```

Capture the `connectionString` from the output.

#### Step 5 — Key Vault

```bash
az keyvault create \
  --name <prefix>-kv \
  --resource-group <rg-name> \
  --location <location> \
  --enable-rbac-authorization true
```

Store the App Insights connection string as a secret:

```bash
az keyvault secret set \
  --vault-name <prefix>-kv \
  --name app-insights-connection-string \
  --value "<connection-string>"
```

Grant the current user "Key Vault Secrets Officer" and the managed identity "Key Vault Secrets User":

```bash
az role assignment create \
  --assignee <current-user-object-id> \
  --role "Key Vault Secrets Officer" \
  --scope $(az keyvault show --name <prefix>-kv --resource-group <rg-name> --query id -o tsv)

az role assignment create \
  --assignee <managed-identity-principal-id> \
  --role "Key Vault Secrets User" \
  --scope $(az keyvault show --name <prefix>-kv --resource-group <rg-name> --query id -o tsv)
```

#### Step 6 — Container Registry

```bash
az acr create \
  --name <prefix>acr \
  --resource-group <rg-name> \
  --location <location> \
  --sku Basic \
  --admin-enabled false
```

Grant the managed identity AcrPull:

```bash
az role assignment create \
  --assignee <managed-identity-principal-id> \
  --role AcrPull \
  --scope $(az acr show --name <prefix>acr --resource-group <rg-name> --query id -o tsv)
```

#### Step 7 — Storage Account

```bash
az storage account create \
  --name <prefix>storage \
  --resource-group <rg-name> \
  --location <location> \
  --sku Standard_LRS \
  --kind StorageV2
```

Create the required blob containers:

```bash
az storage container create --account-name <prefix>storage --name groundtruths --auth-mode login
az storage container create --account-name <prefix>storage --name joboutput --auth-mode login
```

Grant the managed identity and the current user "Storage Blob Data Contributor":

```bash
STORAGE_ID=$(az storage account show --name <prefix>storage --resource-group <rg-name> --query id -o tsv)

az role assignment create \
  --assignee <managed-identity-principal-id> \
  --role "Storage Blob Data Contributor" \
  --scope $STORAGE_ID

az role assignment create \
  --assignee <current-user-object-id> \
  --role "Storage Blob Data Contributor" \
  --scope $STORAGE_ID
```

#### Step 8 — AML Workspace

Requires the `ml` extension: `az extension add --name ml`.

The `az ml workspace create` command requires **full ARM resource IDs** for linked resources, not simple names. Passing a short name (for example, `evalstorage03`) fails with "ARM string is not formatted correctly." Resolve the IDs first:

```bash
STORAGE_ID=$(az storage account show --name <prefix>storage --resource-group <rg-name> --query id -o tsv)
KV_ID=$(az keyvault show --name <prefix>-kv --resource-group <rg-name> --query id -o tsv)
ACR_ID=$(az acr show --name <prefix>acr --resource-group <rg-name> --query id -o tsv)
AI_ID=$(az monitor app-insights component show --app <prefix>-appinsights --resource-group <rg-name> --query id -o tsv)

az ml workspace create \
  --name <prefix>-aml \
  --resource-group <rg-name> \
  --location <location> \
  --storage-account "$STORAGE_ID" \
  --key-vault "$KV_ID" \
  --container-registry "$ACR_ID" \
  --application-insights "$AI_ID"
```

#### Step 9 — AML Datastores

Create two datastores — one for job inputs and one for outputs. The `az ml datastore create` command requires a YAML specification file via `--file`; inline parameters like `--name` and `--type` are not supported.

Create `jobinput-datastore.yml`:

```yaml
$schema: https://azuremlschemas.azureedge.net/latest/azureBlob.schema.json
name: jobinput
type: azure_blob
account_name: <prefix>storage
container_name: groundtruths
```

Create `joboutput-datastore.yml`:

```yaml
$schema: https://azuremlschemas.azureedge.net/latest/azureBlob.schema.json
name: joboutput
type: azure_blob
account_name: <prefix>storage
container_name: joboutput
```

Then apply them:

```bash
az ml datastore create --file jobinput-datastore.yml \
  --resource-group <rg-name> --workspace-name <prefix>-aml

az ml datastore create --file joboutput-datastore.yml \
  --resource-group <rg-name> --workspace-name <prefix>-aml
```

#### Step 10 — AML Compute Cluster

The `az ml compute create` command requires a YAML specification file for user-assigned identity configuration. Inline identity flags are not supported by the CLI v2.

Get the managed identity resource ID first:

```bash
az identity show --name <prefix>-identity --resource-group <rg-name> --query id -o tsv
```

Create `compute.yml` with the managed identity resource ID:

```yaml
$schema: https://azuremlschemas.azureedge.net/latest/amlCompute.schema.json
name: <prefix>-cluster
type: amlcompute
size: Standard_D3_v2
min_instances: 0
max_instances: 3
identity:
  type: user_assigned
  user_assigned_identities:
    - resource_id: <managed-identity-resource-id>
```

Then create the cluster:

```bash
az ml compute create --file compute.yml \
  --resource-group <rg-name> --workspace-name <prefix>-aml
```

#### Step 11 — Configure Image Build Compute

```bash
az ml workspace update \
  --name <prefix>-aml \
  --resource-group <rg-name> \
  --image-build-compute <prefix>-cluster
```

### Alternative: SetupEnv.ps1 (Bicep)

> [!WARNING]
> **Do not use `SetupEnv.ps1` unless the user explicitly requests private networking or production hardening.** It deploys VNet, subnets, NSGs, Private DNS Zones, and Private Endpoints for every resource — infrastructure that is not required for the runner to function. It also takes 15–30 minutes to deploy and produces verbose Bicep compilation warnings that obscure progress. The `az` CLI approach above is the default.

```powershell
cd infra
.\SetupEnv.ps1 -Prefix "<your-prefix>" -ResourceGroupName "<rg-name>" -EnableAML
```

If no feature switches are specified, `-EnableAll` is set automatically, which deploys resources not required by the runner. Always pass `-EnableAML` explicitly.

### Post-Deployment Checklist

Regardless of deployment method, verify:

1. The AML workspace has a linked Storage Account, Key Vault, Container Registry, and Application Insights.
2. Two AML datastores exist: one for job inputs (ground truths) and one for job outputs.
3. An AML compute cluster exists with a user-assigned managed identity.
4. The managed identity has **Storage Blob Data Contributor** on the storage account.
5. The AML workspace is configured to use the compute cluster for image builds.

## Setting Up the Experiment Environment

### Step 1 — Clone the Repository

The repository is private. Clone via SSH (preferred):

```bash
git clone git@github.com:commercial-software-engineering/aml-evaluation-runner.git
cd aml-evaluation-runner
```

HTTPS clone will fail with "Repository not found" unless the user has `gh` CLI configured or cached credentials. Only use HTTPS if the user explicitly requests it:

```bash
git clone https://github.com/commercial-software-engineering/aml-evaluation-runner.git
```

### Step 2 — Install Python Dependencies

From the `experiment/` directory:

```bash
cd experiment
uv sync
```

This creates a local `.venv` and installs all dependencies.

### Step 3 — Authenticate with Azure

```bash
az login --tenant <your-tenant-id>
```

### Step 4 — Configure the Environment File

If you used `SetupEnv.ps1`, it generates `experiment/.test.env` automatically. Otherwise, create an `.env` file with the required configuration. There are three standard configurations:

- `.smoke.env` — functional testing when changing inference or evaluation code
- `.exp.env` — running experiment evaluations against validation ground truths
- `.baseline.env` — full evaluation against test and validation ground truths for baselines

#### Required Environment Variables

| Variable                             | Description                                                                                   |
| ------------------------------------ | --------------------------------------------------------------------------------------------- |
| `AML_SUBSCRIPTION_ID`                | Azure subscription ID                                                                         |
| `AML_RESOURCE_GROUP_NAME`            | Resource group name                                                                           |
| `AML_WORKSPACE_NAME`                 | AML workspace name                                                                            |
| `AML_COMPUTE_NAME`                   | AML compute cluster name                                                                      |
| `AML_EXPERIMENT_NAME`                | Experiment name (spaces converted to underscores, lowercased)                                 |
| `AML_IMAGE_NAME`                     | Docker image for AML jobs (for example, `mcr.microsoft.com/azureml/openmpi4.1.0-ubuntu22.04`) |
| `AML_JOB_INSTANCE_COUNT`             | Number of compute instances                                                                   |
| `AML_JOB_INPUT_DATASTORE`            | Input datastore name                                                                          |
| `AML_JOB_OUTPUT_DATASTORE`           | Output datastore name                                                                         |
| `AML_GROUND_TRUTHS_PATH`             | Path to ground truths in the input datastore                                                  |
| `JOB_MANAGED_IDENTITY_ID`            | Managed identity client ID used by compute                                                    |
| `AML_APP_INSIGHTS_CONNECTION_STRING` | Application Insights connection string (can be a Key Vault secret URL)                        |
| `AML_INF_MODULE_DIR`                 | Path to the inference module directory                                                        |
| `AML_EVAL_MODULE_DIR`                | Path to the evaluation module directory                                                       |

#### Optional Environment Variables

| Variable                             | Default   | Description                                                        |
| ------------------------------------ | --------- | ------------------------------------------------------------------ |
| `AML_LOG_LEVEL`                      | `INFO`    | Logging level                                                      |
| `AML_CONFIG_TAG_NAME`                | `NOT-SET` | Config tag name for experiment tracking                            |
| `AML_INFERENCE_CONCURRENCY`          | `1`       | Inference parallelism per instance                                 |
| `AML_EVAL_CONCURRENCY`               | `1`       | Evaluation parallelism per instance                                |
| `AML_ITERATION_COUNT`                | `0`       | Iteration count (0 skips the iteration step)                       |
| `AML_INF_TIMEOUT_SECONDS`            | `360`     | Inference timeout in seconds (minimum 30)                          |
| `AML_EVAL_TIMEOUT_SECONDS`           | `120`     | Evaluation timeout in seconds (minimum 30)                         |
| `AML_SUMMARY_TIMEOUT_SECONDS`        | `300`     | Summarization timeout in seconds (minimum 30)                      |
| `AML_INF_ENV_PATH`                   | —         | Path to the inference `.env` file                                  |
| `AML_EVAL_ENV_PATH`                  | —         | Path to the evaluation `.env` file                                 |
| `INF_INFERENCE_SERVICE_URL`          | —         | Remote inference service URL (for DevTunnel-based local inference) |
| `INF_INFERENCE_SERVICE_TUNNEL_TOKEN` | —         | DevTunnel token for remote inference                               |
| `EVAL_SERVICE_URL`                   | —         | Remote evaluation service URL                                      |
| `GROUND_TRUTH_INCLUDE_TAGS`          | —         | Comma-delimited tag filter for ground truths                       |
| `ENABLED_ACTIONS`                    | —         | Comma-delimited action names to enable                             |

#### Override Variables

You can override specific inference or evaluation environment variables using prefixed overrides:

```text
INF_OVERRIDE_<VARIABLE_NAME>=<value>
EVAL_OVERRIDE_<VARIABLE_NAME>=<value>
```

For example:

```text
EVAL_OVERRIDE_AI_SEARCH_ENDPOINT=https://contoso-search.search.windows.net
INF_OVERRIDE_AI_SEARCH_KEY=https://contoso.vault.azure.net/secrets/EVAL-AI-SEARCH-KEY
```

## Running an Experiment

### Basic Usage

```bash
cd experiment
uv run python run.py --env_path .exp.env --annotations key1=value1,key2=value2
```

### With a Hypothesis

```bash
uv run python run.py --env_path .exp.env \
  --hypothesis "adding context to the prompt yields higher accuracy" \
  --annotations model=gpt4,topk=10
```

### Resume a Failed Evaluation

```bash
uv run python run.py --env_path .exp.env --resume_evaluation_timestamp <job_timestamp>
```

### Resume Summarization Only

```bash
uv run python run.py --env_path .exp.env --resume_summary_timestamp <job_timestamp>
```

Once an experiment run is created, a link to Azure ML Studio is printed. Use it to monitor pipeline progress in real time.

## Pipeline Structure

The AML pipeline consists of up to four steps:

1. **Create Iterations** (optional, when `AML_ITERATION_COUNT > 0`) — replicates ground truth files for multiple iterations.
2. **Inference** — runs the user-provided inference module in parallel across ground truth items.
3. **Evaluation** — runs the user-provided evaluation module in parallel against inference outputs.
4. **Summarization** — aggregates evaluation results into a summary (single instance, no concurrency).

When `AML_ITERATION_COUNT` is 0 (default), the iteration step is skipped.

## Building Custom Images

Python dependencies for AML jobs are defined in `experiment/environments/parallel.yml` (a Conda environment file). When you add new dependencies for your inference or evaluation modules, update this file.

To build and push a custom image to your Azure Container Registry:

```powershell
cd experiment
.\BuildImage.ps1 -ResourceGroupName <your-resource-group>
```

This script finds the ACR in your resource group, builds the image from `experiment/aml.Dockerfile`, and pushes it. After building, update `AML_IMAGE_NAME` in your `.env` file with the new image tag.

If AML-managed image builds are unreliable or too slow for a demo, it is valid
to build and push a custom image locally and point `AML_IMAGE_NAME` directly to
that prebuilt image instead of relying on the workspace build path.

## Actions (Optional Plug-ins)

The runner is extensible via actions that hook into pipeline steps. Ask the user if they want to use any of these before configuring them.

### Catalog Action

Integrates with the Experiment Catalog to track and compare experiment runs visually.

Required environment variables:

```text
ENABLED_ACTIONS=catalog
EVAL_SET_CATALOG_URL=<catalog-api-base-url>/api
EVAL_SET_CATALOG_PROJECT=<project-name>
```

Optional environment variables:

```text
EVAL_SET_CATALOG_API_APP_ID_URI=<app-id-uri>
```

When `CATALOG_API_APP_ID_URI` is set, the action acquires a bearer token via `DefaultAzureCredential` and sends it in the `Authorization` header. When omitted, the action posts without authentication. Omit this variable when the catalog API does not require auth.

> [!NOTE]
> The managed identity uses the **client credentials flow** to acquire tokens. This requires an **Application-type app role** on the catalog's app registration — a delegated scope alone is not sufficient. The app role must have `allowedMemberTypes: ["Application"]`, and the MI's service principal must be assigned that role via the MS Graph API (`/servicePrincipals/<catalog-sp-id>/appRoleAssignedTo`). See the experiment-catalog-install skill's "OIDC Setup for Microsoft Entra ID" section for the full procedure.
>
> The `CATALOG_API_APP_ID_URI` value should be the identifier URI of the catalog app registration (for example, `api://<appId>`).

> [!IMPORTANT]
> The experiment and project must already exist in the catalog before submitting the pipeline. The catalog action only POSTs individual results to `/projects/{project}/experiments/{experiment}/results`; it does not create experiments or projects. If the experiment is missing, every result POST returns `404: experiment not found` and no data reaches the catalog.
>
> Create the experiment before running the pipeline:
>
> ```bash
> curl -X POST "<CATALOG_URL>/projects/<PROJECT>/experiments" \
>   -H "Content-Type: application/json" \
>   -d '{"name": "<EXPERIMENT_NAME>", "hypothesis": "<DESCRIPTION>"}'
> ```
>
> Both `name` and `hypothesis` are required fields. The experiment `name` must match `AML_EXPERIMENT_NAME` (which is propagated as `CATALOG_EXPERIMENT_NAME` at runtime).

> [!IMPORTANT]
> The catalog URL must include the `/api` path suffix. The action appends `/projects/{project}/experiments/{experiment}/results` to this base, so omitting `/api` produces 404 errors.

### MLflow Log Action

Logs metrics to MLflow during the summarization step for integration with AML's native experiment tracking.

```text
ENABLED_ACTIONS=mlflowlog
```

Multiple actions can be enabled by comma-separating them:

```text
ENABLED_ACTIONS=catalog,mlflowlog
```

### Custom Actions

Users can create custom actions by implementing a class that extends `BaseAction` in `experiment/code/actions/`. The action manager scans that directory for implementations. Custom action environment variables use the `EVAL_SET_` prefix:

```text
EVAL_SET_<MY_ENV_VAR>=<value>
```

## Inference and Evaluation Modules

The runner is agnostic about inference and evaluation implementations. Users point the runner at their own modules via `AML_INF_MODULE_DIR` and `AML_EVAL_MODULE_DIR`. The repository includes reference implementations in `inference/` and `evaluation/` that can serve as starting points, but these are not required.

Two integration modes are supported:

1. **Module-based** — the runner invokes `inference.py` and `eval.py` files directly, calling a known function interface.
2. **HTTP endpoint-based** — the runner calls remote HTTP services for inference and/or evaluation.

For remote services, configure:

```text
INF_INFERENCE_SERVICE_URL=<your-inference-url>
EVAL_SERVICE_URL=<your-evaluation-url>
```

See `inference/README.md` and `evaluation/README.md` in the repository for integration details.

## Running with Local Inference (DevTunnel)

To run inference locally while the AML pipeline runs in the cloud:

1. Start your inference service locally.
2. Log in to DevTunnel: `devtunnel user login`
3. Host a tunnel: `devtunnel host -p <port>`
4. Set the tunnel URL in your `.env`:

```text
INF_INFERENCE_SERVICE_URL=<devtunnel-url>
INF_INFERENCE_SERVICE_TUNNEL_TOKEN=<devtunnel-token>
```

Generate the token with: `devtunnel token --scopes connect <tunnel-id>`

## Utilities

### Download Experiment Outputs

The `experiment/utilities/download_outputs.py` script downloads artifacts from Azure Storage.

```bash
# List experiments
uv run python utilities/download_outputs.py --env_path .test.env --list_experiments

# List jobs for an experiment
uv run python utilities/download_outputs.py --env_path .test.env \
  --experiment_name <name> --list_jobs

# Download a specific job
uv run python utilities/download_outputs.py --env_path .test.env \
  --experiment_name <name> --job_id <timestamp>
```

## Deployment Options

Based on the user's input, your recommendations, or asking for guidance, you may deploy resources using:

- **Azure CLI commands** (recommended — deploys only what is needed, clear per-step feedback)
- PowerShell with the provided `SetupEnv.ps1` script (deploys extra networking/hardening infrastructure)
- Bicep templates directly
- Terraform
- ARM templates
- Azure Portal

For development and initial setup, use `az` CLI. For production or customer environments where network isolation is required, consider the Bicep templates or a desired-state-configuration approach (Bicep, Terraform).

## Hardening

When deploying for production or within a customer environment, consider defense-in-depth principles to protect the runner and its data. Detailed hardening recommendations (network isolation, managed identity, Key Vault, logging) are in [references/hardening.md](references/hardening.md). Ask the user before applying these measures.

## Telemetry

The runner supports Application Insights integration via the `AML_APP_INSIGHTS_CONNECTION_STRING` variable. This can be a direct connection string or a Key Vault secret URL. The `SetupEnv.ps1` script stores the connection string in Key Vault and references it by URL.

## Troubleshooting

| Issue                                                                                | Cause                                                                                                           | Solution                                                                                                                                                                              |
| ------------------------------------------------------------------------------------ | --------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `az: command not found`                                                              | Azure CLI missing                                                                                               | Install from <https://learn.microsoft.com/cli/azure/install-azure-cli>                                                                                                                |
| `az monitor app-insights` prompts to install extension                               | `application-insights` extension not pre-installed                                                              | Run `az extension add --name application-insights` before deploying. Also run `az config set extension.use_dynamic_install=yes_without_prompt` to prevent future interactive prompts. |
| `uv: command not found`                                                              | uv missing                                                                                                      | Install from <https://docs.astral.sh/uv>                                                                                                                                              |
| `pwsh: command not found`                                                            | PowerShell missing                                                                                              | Install from <https://learn.microsoft.com/powershell/scripting/install/installing-powershell>                                                                                         |
| `docker: command not found`                                                          | Docker missing                                                                                                  | Install from <https://www.docker.com/>                                                                                                                                                |
| Bicep deployment fails                                                               | Missing permissions                                                                                             | Ensure you are an Owner or Contributor on the target subscription                                                                                                                     |
| Bicep deployment hangs                                                               | Large template with VNet/Private Endpoints takes 15–30 min                                                      | Use `az` CLI for individual resources instead; or be patient and monitor via `az deployment group list`                                                                               |
| HTTPS clone fails with "Repository not found"                                        | Private repo, no cached credential                                                                              | Clone via SSH: `git clone git@github.com:commercial-software-engineering/aml-evaluation-runner.git`                                                                                   |
| `403 Forbidden` on storage                                                           | Missing RBAC role                                                                                               | Assign **Storage Blob Data Contributor** to the managed identity on the storage account                                                                                               |
| `403` or network error from storage after workspace creation                         | AML workspace creation or Bicep templates may set `publicNetworkAccess: Disabled` on the linked storage account | Run `az storage account update --name <name> --resource-group <rg> --public-network-access Enabled`                                                                                   |
| AML job fails to start                                                               | Image build not configured                                                                                      | Run `az ml workspace update --name <ws> --resource-group <rg> --image-build-compute <compute>`                                                                                        |
| `az ml workspace create` fails with "ARM string is not formatted correctly"          | Simple resource names passed instead of full ARM resource IDs                                                   | Use `az storage account show --query id -o tsv` (and equivalent for Key Vault, ACR, App Insights) to get full ARM IDs before passing them to `az ml workspace create`                 |
| `az ml datastore create` fails with "arguments are required: --file/-f"              | Inline parameters not supported by CLI v2                                                                       | Create a YAML specification file and pass it via `--file`. See Step 9 for the schema.                                                                                                 |
| AML job fails with "Unsupported datastore authentication"                            | Workspace system datastores auth mode is not `identity`                                                         | Run `az ml workspace update --name <ws> --resource-group <rg> --system-datastores-auth-mode identity` and verify the datastores use workspace identity access.                         |
| AML parallel job fails despite blob access working                                   | Missing table or queue RBAC on the datastore storage account                                                    | Grant **Storage Table Data Contributor** and **Storage Queue Data Contributor** to both the workspace system identity and the compute identity on the storage account.                   |
| AML job times out                                                                    | Timeout too short                                                                                               | Increase `AML_INF_TIMEOUT_SECONDS`, `AML_EVAL_TIMEOUT_SECONDS`, or `AML_SUMMARY_TIMEOUT_SECONDS`                                                                                      |
| `EnableAML` not passed                                                               | All resources deployed                                                                                          | Pass `-EnableAML` explicitly to `SetupEnv.ps1` to deploy only runner resources                                                                                                        |
| ACR login fails                                                                      | Not authenticated                                                                                               | Run `az acr login --name <acr-name>`                                                                                                                                                  |
| Image build fails on Apple Silicon                                                   | Wrong platform                                                                                                  | Build with `docker build --platform linux/amd64`                                                                                                                                      |
| AML job starts but Python imports fail in the custom image                           | Base image dependency drift or incompatible package versions                                                    | Prebuild and verify the custom image locally before submission. In particular, `azureml-core` may require `setuptools<75`; pin it explicitly if `pkg_resources` import errors appear. |
| AML job fails after adding OpenTelemetry or MLflow-related dependencies              | Transitive dependency mismatch in the custom image                                                              | Build incrementally and verify imports locally before pushing. Prefer a known-good prebuilt image tag once the dependency set is stable.                                               |
| DevTunnel token expired                                                              | Token needs refresh                                                                                             | Regenerate with `devtunnel token --scopes connect <id>`                                                                                                                               |
| Ground truths not found                                                              | Wrong path or tag filter                                                                                        | Verify `AML_GROUND_TRUTHS_PATH` and `GROUND_TRUTH_INCLUDE_TAGS` in your `.env`                                                                                                        |
| `404: experiment not found` from catalog action                                      | The experiment does not exist in the catalog                                                                    | Create the experiment in the catalog before submitting the pipeline. The catalog action only POSTs results, it does not create experiments.                                           |
| Catalog action posts succeed (200) but no results visible in catalog experiment list | Results are stored per-set, not shown in the experiment summary                                                 | Query a specific set: `GET /api/projects/{project}/experiments/{experiment}/sets/{set_id}` to see the results. The experiment list endpoint does not inline results.                  |
| `EVAL_SET_` prefixed variables not reaching the action                               | Prefix stripping misconfiguration                                                                               | The `EVAL_SET_` prefix is stripped at runtime so `EVAL_SET_CATALOG_URL` becomes `CATALOG_URL`. Verify the full prefixed name in `.exp.env`.                                           |
