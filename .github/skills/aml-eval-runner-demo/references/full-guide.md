---
name: aml-eval-runner-demo
description: Deploy demo inference and evaluation modules for the AML Evaluation Runner. Provides a zero-dependency end-to-end pipeline using GTC v2 ground truth exports with lightweight string-similarity metrics.
---

# AML Evaluation Runner Demo

Deploy a pair of demo plug-in modules — inference and evaluation — that let you run the AML Evaluation Runner pipeline end-to-end without any API keys, model endpoints, or heavy dependencies. The demo modules accept ground truth records in the GTC v2 snapshot format and produce deterministic metrics using only the Python standard library.

## Execution Model

> [!IMPORTANT]
> **Do not execute tasks from this skill directly.** Every discrete task you
> derive from this skill must be delegated to its own sub-agent. Each sub-agent
> should be given this skill file's path so it can read the full instructions
> itself.
>
> For example, if the user asks to "set up demo modules and run ground truths
> through the pipeline," that is two tasks — one sub-agent to set up the demo
> modules, another to run the pipeline. Break the work into logical tasks and
> run each in its own sub-agent.

When the user asks for a large end-to-end workflow, do not treat it as one
continuous execution stream. Split the work into explicit phases and delegate
each phase separately.

Recommended phases for long demo runs:

1. inspect runner prerequisites and current deployment state
2. install or copy demo modules
3. prepare or export sample data
4. stage data and configure the experiment
5. submit and monitor the AML run
6. validate outputs and publish a concise handoff

Additional rules for avoiding main-context overflow:

- Keep the main thread in a coordinator role. Use sub-agents for execution,
  especially for Docker builds, AML job retries, log analysis, and result
  verification.
- After each phase, write or update concise artifacts in the session workspace
  when available (for example: staged data paths, config files, run summaries,
  catalog summaries, and next-step notes). Prefer artifact handoff over
  repeating all state in the conversation.
- Successful long-running commands should be summarized briefly. Only surface
  full logs when a command fails or when specific output is required to make a
  decision.
- If a phase uncovers a new discrete task, delegate that follow-up as its own
  sub-agent instead of extending the current thread indefinitely.
- Before moving to the next phase, checkpoint the current live state: run IDs,
  image tags, data paths, artifact paths, verified outputs, and unresolved
  blockers.

## Prerequisites

- Python 3.10 or later.
- An existing [aml-evaluation-runner](https://github.com/commercial-software-engineering/aml-evaluation-runner) clone in the workspace (typically at `aml-evaluation-runner/`).
- (Optional) A GTC snapshot export for real ground truth data. Sample data is included.

### Infrastructure Prerequisites

The AML Evaluation Runner requires a deployed Azure ML workspace with associated infrastructure. Deploy using the Bicep templates in `aml-evaluation-runner/infra/`:

```bash
cd aml-evaluation-runner/infra
pwsh -Command './SetupEnv.ps1 -Prefix "eval" -ResourceGroupName "<rg-name>" -Location "<region>" -EnableAML'
```

Ensure these infrastructure components are correctly configured before running the pipeline:

- **Workspace auth mode**: The workspace `system_datastores_auth_mode` must be `identity`. If the storage account has key-based auth disabled (`KeyBasedAuthenticationNotPermitted`), setting this to `accesskey` causes all datastore access to fail silently with "Unsupported datastore authentication." Verify and fix with:

```bash
az ml workspace show --name <workspace> --resource-group <rg> \
    --query system_datastores_auth_mode -o tsv

az ml workspace update --name <workspace> --resource-group <rg> \
    --system-datastores-auth-mode identity
```

- **Datastore configuration**: Both `jobinput` and `joboutput` datastores must have `credentialsType: None` and `serviceDataAccessAuthIdentity: WorkspaceSystemAssignedIdentity`. The Bicep templates set this correctly, but if datastores were created manually or reconfigured, verify via the Azure ML Studio portal or ARM REST API.

- **Storage account key access**: When storage account key-based auth is disabled (recommended for security), all access must go through identity-based RBAC. This affects the AML workspace, compute cluster, and log retrieval tooling.
- **Image strategy for demo runs**: If AML image builds or Conda resolution are unreliable, prefer a prebuilt custom image pushed to ACR and point `AML_IMAGE_NAME` at that image. This is often more reliable than rebuilding from the AML environment definition on every run.

### RBAC Requirements

AML parallel run jobs use three storage services: blobs (data I/O), tables (state tracking), and queues (work distribution). Two identities need access to the storage account hosting the datastores:

| Identity                                       | Required Roles                                                                                      |
| ---------------------------------------------- | --------------------------------------------------------------------------------------------------- |
| Workspace system-assigned managed identity     | `Storage Blob Data Contributor`, `Storage Table Data Contributor`, `Storage Queue Data Contributor` |
| Compute cluster user-assigned managed identity | `Storage Blob Data Contributor`, `Storage Table Data Contributor`, `Storage Queue Data Contributor` |
| Your user account (for log retrieval)          | `Storage Blob Data Contributor` (on the `azureml` default storage and the app storage)              |

Grant roles with:

```bash
# Find principal IDs
az ml workspace show --name <workspace> --resource-group <rg> \
    --query identity.principal_id -o tsv           # workspace system identity

az ml compute show --name <cluster> --resource-group <rg> \
    --workspace-name <workspace> \
    --query identity.user_assigned_identities -o json  # compute user-assigned identity

# Assign roles (repeat for each identity)
STORAGE_ID=$(az storage account show --name <storage> --resource-group <rg> --query id -o tsv)

az role assignment create --assignee <principal-id> \
    --role "Storage Blob Data Contributor" --scope "$STORAGE_ID"
az role assignment create --assignee <principal-id> \
    --role "Storage Table Data Contributor" --scope "$STORAGE_ID"
az role assignment create --assignee <principal-id> \
    --role "Storage Queue Data Contributor" --scope "$STORAGE_ID"
```

> [!IMPORTANT]
> Allow 60–90 seconds after creating RBAC role assignments for propagation before submitting a pipeline run.

> [!IMPORTANT]
> If the datastores point to the application storage account instead of the AML
> default storage account, both the workspace system identity and the compute
> identity need blob, table, and queue roles on that storage account.

The Bicep `rbac.bicep` template assigns blob, table, and queue roles to the compute managed identity on the AML storage account, and blob-only to the workspace system identity on the app storage account. If the datastores point to the app storage account (the default configuration), you must manually add table and queue roles for both the workspace system identity and the compute identity on that account.

## Quick Start

Run the setup script from the workspace root:

```bash
python .github/skills/aml-eval-runner-demo/scripts/setup_demo.py
```

The script copies the modules into the runner tree and prints the `.exp.env` lines to add:

```dotenv
AML_INF_MODULE_DIR=../inference/demo-inference
AML_EVAL_MODULE_DIR=../evaluation/demo-evaluation
```

Then run the experiment as usual:

```bash
cd aml-evaluation-runner/experiment
uv run python run.py
```

> [!IMPORTANT]
> When the catalog action is enabled (`ENABLED_ACTIONS=catalog`), the target experiment must already exist in the experiment catalog before submitting the pipeline. The catalog action only POSTs individual results; it does not create experiments. If the experiment does not exist, every result POST returns `404: experiment not found` and no data reaches the catalog. Create the experiment via the catalog API or UI before running `run.py`. See the Catalog Action Pre-Creation section for details.

## Parameters Reference

| Parameter       | Default                                           | Description                                  |
| --------------- | ------------------------------------------------- | -------------------------------------------- |
| `--runner-root` | `../../aml-evaluation-runner` (relative to skill) | Path to the aml-evaluation-runner directory. |
| `--gt-output`   | `<runner-root>/experiment/ground-truths`          | Directory for individual ground-truth files. |

## What Gets Deployed

### demo-inference

Folder: `aml-evaluation-runner/inference/demo-inference/`

A single `inference.py` with an `InferenceService` class that:

1. Reads the `question` and `answer` fields from GTC v2 ground truth records (supports `editedQuestion` / `synthQuestion` aliases).
2. Returns a deterministic, slightly perturbed echo of the expected answer so evaluation metrics produce non-trivial scores.
3. Emits a standard inference result dict with `response`, `usage`, `function_calls`, and timing fields.
4. Exports `EventBus` and `GroundTruth` stubs required by the runner's hard-coded imports (`from inference.inference import EventBus, GroundTruth`).

A `Models/ground_truth.py` dataclass stub satisfies the runner's `from inference.Models.ground_truth import GroundTruth` import. Neither stub is used at runtime — the runner passes plain dicts — but both must exist for the imports to resolve.

No network calls. No API keys. No pip packages beyond the standard library.

### demo-evaluation

Folder: `aml-evaluation-runner/evaluation/demo-evaluation/`

A single `eval.py` with a `run_eval` function that computes 25 metrics organized by prefix:

**Retrieval metrics (10):**

| Metric                        | Range  | Description                                     |
| ----------------------------- | ------ | ----------------------------------------------- |
| `retrieval_accuracy`          | 0 – 1  | Correctness of retrieved documents.             |
| `retrieval_precision`         | 0 – 1  | Fraction of retrieved docs that are relevant.   |
| `retrieval_recall`            | 0 – 1  | Fraction of relevant docs that were retrieved.  |
| `retrieval_f1`                | 0 – 1  | Harmonic mean of precision and recall.          |
| `retrieval_mrr`               | 0 – 1  | Mean reciprocal rank of first relevant result.  |
| `retrieval_ndcg`              | 0 – 1  | Normalized discounted cumulative gain.          |
| `retrieval_map`               | 0 – 1  | Mean average precision.                         |
| `retrieval_hit_rate`          | 0 or 1 | Did at least one relevant result appear?        |
| `retrieval_context_relevance` | 0 – 1  | Relevance of retrieved context to the question. |
| `retrieval_chunk_utilization` | 0 – 1  | Fraction of retrieved chunks actually used.     |

**Generation metrics (10):**

| Metric                         | Range | Description                                                |
| ------------------------------ | ----- | ---------------------------------------------------------- |
| `generation_correctness`       | 0 – 1 | Factual correctness of the answer.                         |
| `generation_faithfulness`      | 0 – 1 | Answer grounded in provided context.                       |
| `generation_completeness`      | 0 – 1 | Coverage of all expected answer points.                    |
| `generation_coherence`         | 0 – 1 | Logical flow and readability.                              |
| `generation_relevance`         | 0 – 1 | Answer relevance to the question.                          |
| `generation_conciseness`       | 0 – 1 | Absence of unnecessary verbosity.                          |
| `generation_fluency`           | 0 – 1 | Grammatical quality and naturalness.                       |
| `generation_toxicity`          | 0 – 1 | Absence of harmful content (higher is better).             |
| `generation_answer_similarity` | 0 – 1 | SequenceMatcher ratio between expected and actual answers. |
| `generation_word_overlap_f1`   | 0 – 1 | Token-level F1 score (precision × recall harmonic mean).   |

**Metadata metrics (5):**

| Metric                         | Range  | Description                                             |
| ------------------------------ | ------ | ------------------------------------------------------- |
| `metadata_inference_time_ms`   | ≥ 0    | Inference latency in milliseconds.                      |
| `metadata_prompt_tokens`       | ≥ 0    | Input token count from inference usage.                 |
| `metadata_completion_tokens`   | ≥ 0    | Output token count from inference usage.                |
| `metadata_answer_length_ratio` | 0 – 2  | Ratio of actual to expected answer length (word count). |
| `metadata_has_answer`          | 0 or 1 | Did inference produce a non-empty response?             |

No network calls. No API keys. No pip packages beyond the standard library.

### Sample Ground Truths

Five example records in `assets/sample-ground-truths.json` covering Azure ML, security, data architecture, Kubernetes, and identity topics. The setup script splits them into individual files for the runner's input datastore.

## Using Your Own Ground Truths

Export a GTC snapshot and split it into individual files:

```bash
python .github/skills/aml-eval-runner-demo/scripts/setup_demo.py \
    --gt-output path/to/your/ground-truths
```

Or point `AML_GROUND_TRUTHS_PATH` in `.exp.env` to an existing directory of per-record JSON files.

## Catalog Action Pre-Creation

The catalog action (enabled via `ENABLED_ACTIONS=catalog`) posts evaluation results to the experiment catalog during the summarization step. The action calls `POST /projects/{project}/experiments/{experiment}/results` for each evaluated ground truth. This endpoint requires the experiment to exist beforehand.

Before submitting the AML pipeline, create the experiment:

```bash
curl -X POST "<CATALOG_URL>/projects/<PROJECT>/experiments" \
  -H "Content-Type: application/json" \
  -d '{"name": "<EXPERIMENT_NAME>", "hypothesis": "<DESCRIPTION>"}'
```

Both `name` and `hypothesis` are required fields. The `name` value must match the `AML_EXPERIMENT_NAME` in your `.exp.env` file (this becomes the `CATALOG_EXPERIMENT_NAME` at runtime).

### Metric Definitions

Create metric definitions in the catalog before submitting the pipeline so results display correctly. Each definition specifies the metric name, value range, aggregation function, and display order:

```bash
TOKEN=$(az account get-access-token --resource api://<catalog-appId> --query accessToken -o tsv)

curl -X POST "<CATALOG_URL>/api/projects/<PROJECT>/metric-definitions" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"name": "retrieval_accuracy", "range": "0-1", "aggregate": "Average", "order": 100}'
```

Repeat for each metric. Use `Average` aggregate for all continuous float metrics. Use sequential `order` values to control column display order (for example, `retrieval_` metrics at 100–190, `generation_` at 200–290, `metadata_` at 300–340). See the Metric Definition Aggregation Functions section for aggregate function guidance.

### Setting the Baseline

After the first permutation's pipeline run completes, set it as the baseline so the catalog can compute deltas for subsequent permutations:

```bash
curl -X PUT "<CATALOG_URL>/api/projects/<PROJECT>/experiments/<EXPERIMENT>/baseline" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"set": "<TIMESTAMP>"}'
```

The `<TIMESTAMP>` is the set ID from the first pipeline run (for example, `20260317143738`).

## Running Multiple Permutations

To compare different configurations, run the pipeline once per permutation with different parameters. The typical workflow:

1. Create a separate `.env` file for each permutation (for example, `.baseline.env`, `.temp07.env`, `.topk10.env`, `.prompt-v2.env`).
2. Each file shares the same base configuration but overrides specific parameters via `INF_OVERRIDE_*` or `EVAL_OVERRIDE_*` variables.
3. Use a different `AML_CONFIG_TAG_NAME` in each file to distinguish runs in AML Studio.
4. Submit the pipeline once per permutation:

   ```bash
   cd aml-evaluation-runner/experiment
   uv run python run.py --env_path .baseline.env
   # Wait for completion, then:
   uv run python run.py --env_path .temp07.env
   # Repeat for each permutation
   ```

5. The catalog action creates a new set (identified by timestamp) for each submission.
6. After the first permutation completes, set it as the baseline (see Setting the Baseline above).
7. Post annotations to each set to identify its configuration (see Set Annotations below).

If you ran a pipeline before creating the experiment, the eval output files are still available in the `joboutput` storage container at `<experiment>/<timestamp>/eval/`. You can replay them without re-running the pipeline by downloading each eval JSON and POSTing its `$metrics` to the catalog.

## Authentication for GTC and Catalog

> [!IMPORTANT]
> Never disable authentication on GTC or the experiment catalog to work around 401 errors during seeding or pipeline runs. Always acquire Bearer tokens for programmatic access. Disabling auth — even temporarily — bypasses security controls and masks integration issues that must be resolved before production use.

### Seeding GTC with Auth Enabled

When the GTC instance has EasyAuth enabled, acquire a Bearer token before seeding ground truths:

```bash
TOKEN=$(az account get-access-token --resource api://<gtc-appId> --query accessToken -o tsv)
curl -H "Authorization: Bearer $TOKEN" "https://<gtc-fqdn>/v1/stats"
```

Use this token when calling the GTC API to export ground truths or verify data.

### Catalog Action Authentication

When the experiment catalog has OIDC or EasyAuth enabled, the catalog action in the AML pipeline must authenticate. Set these env vars in `.exp.env`:

```dotenv
EVAL_SET_CATALOG_URL=https://<catalog-fqdn>/api
EVAL_SET_CATALOG_PROJECT=<project-name>
EVAL_SET_CATALOG_API_APP_ID_URI=api://<catalog-appId>
```

The `CATALOG_API_APP_ID_URI` setting tells the catalog action to acquire a token for the specified audience using the compute cluster's managed identity. The managed identity must be able to obtain a token for the catalog's app registration.

For managed identity access to work:

1. The catalog app registration must have an **Application-type app role** (delegated scopes are not sufficient for the client credentials flow).
2. The managed identity's service principal must be assigned that app role via the Graph API.
3. The catalog's `OIDC_AUDIENCES` must include both the raw `appId` and the `api://` URI format.

#### Creating an App Role and Assigning It to the Compute MI

Create an application-scoped app role on the catalog registration:

```bash
# Get the catalog app's object ID (not appId)
APP_OBJECT_ID=$(az ad app show --id <catalog-appId> --query id -o tsv)

# Add an Application-type app role
az rest --method PATCH \
  --url "https://graph.microsoft.com/v1.0/applications/$APP_OBJECT_ID" \
  --body '{
    "appRoles": [{
      "id": "<generate-a-guid>",
      "allowedMemberTypes": ["Application"],
      "displayName": "Catalog.ReadWrite.All",
      "description": "Read and write catalog data",
      "value": "Catalog.ReadWrite.All",
      "isEnabled": true
    }]
  }'
```

Assign the app role to the compute managed identity's service principal:

```bash
# Get the catalog's service principal object ID
CATALOG_SP_ID=$(az ad sp show --id <catalog-appId> --query id -o tsv)

# Get the compute MI's service principal object ID
COMPUTE_MI_SP_ID=$(az ad sp show --id <compute-mi-client-id> --query id -o tsv)

# Assign the app role
az rest --method POST \
  --url "https://graph.microsoft.com/v1.0/servicePrincipals/$COMPUTE_MI_SP_ID/appRoleAssignments" \
  --body "{
    \"principalId\": \"$COMPUTE_MI_SP_ID\",
    \"resourceId\": \"$CATALOG_SP_ID\",
    \"appRoleId\": \"<the-role-id-from-above>\"
  }"
```

### Pre-Creating Experiments with Auth

When creating the project and experiment before the pipeline run, include the Bearer token:

```bash
TOKEN=$(az account get-access-token --resource api://<catalog-appId> --query accessToken -o tsv)

curl -X POST "https://<catalog-fqdn>/api/projects" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"name": "<PROJECT_NAME>"}'

curl -X POST "https://<catalog-fqdn>/api/projects/<PROJECT_NAME>/experiments" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"name": "<EXPERIMENT_NAME>", "hypothesis": "<DESCRIPTION>"}'
```

### Troubleshooting Auth Errors

| Error                                                      | Cause                                                                                         | Fix                                                                                                                         |
| ---------------------------------------------------------- | --------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------- |
| `AADSTS50011` redirect URI mismatch                        | The catalog's OIDC callback URL is not registered in the app registration.                    | Add `https://<catalog-fqdn>/auth/callback` to the app's web redirect URIs via `az ad app update --web-redirect-uris`.       |
| `AADSTS7000218` client_assertion or client_secret required | The OIDC authorization code flow requires a client secret for the token exchange.             | Create a client secret via `az rest --method POST --url .../addPassword` and set `OIDC_CLIENT_SECRET` on the container app. |
| `AADSTS7000215` invalid client secret                      | Wrong secret value — ensure you use `secretText`, not `keyId`.                                | Verify the env var contains the actual secret string returned by the addPassword call.                                      |
| 401 from catalog when posting pipeline results             | `EVAL_SET_CATALOG_API_APP_ID_URI` is not set, or the compute MI lacks an app role assignment. | Set the env var and create the app role + assignment per the steps above.                                                   |

## Result Ref Format

The catalog action in `run_evaluation.py` constructs a `ref` field for each result posted to the catalog. The ref identifies which ground truth item a result belongs to.

> [!IMPORTANT]
> All iterations of the same ground truth item must share the same `ref`. For example, if ground truth `gt-000` is evaluated across 5 iterations, all 5 results must use `ref: "gt-000"` — not `gt-000_0`, `gt-000_1`, etc. The catalog uses the ref to group iterations and compute aggregated statistics (mean, standard deviation). Appending the iteration index creates unique refs that prevent aggregation.

The `ref` is constructed in `code/actions/catalog.py`:

```python
# Correct — use the ground truth ID as the ref without iteration suffix
id = job_details.get("ground_truth_ref")
```

Do not append the iteration index to the ref. The catalog tracks iterations implicitly through multiple results sharing the same ref within a set.

## Set Annotations

Each permutation (set) in the catalog is identified by its timestamp (for example, `20260317143738`). Without additional context, it is difficult to determine which configuration produced which set. Use annotations to label sets with their permutation details.

Post an annotation-only result to the catalog after submitting each pipeline run:

```bash
TOKEN=$(az account get-access-token --resource api://<catalog-appId> --query accessToken -o tsv)

curl -X POST "https://<catalog-fqdn>/api/projects/<PROJECT>/experiments/<EXPERIMENT>/results" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "set": "<TIMESTAMP>",
    "annotations": [
      {"text": "config: baseline"},
      {"text": "perturbation_level: 1"},
      {"text": "description: Default parameters with minimal perturbation"}
    ]
  }'
```

The catalog accepts results with only `set` and `annotations` (no ref or metrics required). This attaches descriptive metadata to the set visible in the catalog UI.

Consider automating this in the pipeline submission script or as a post-pipeline step. The `AML_CONFIG_TAG_NAME` value from `.exp.env` is a natural source for the annotation text.

## Tags for Data Subsetting

The catalog supports project-level tags that map tag names to lists of result refs. Tags enable filtering results by subsets (for example, by question type, difficulty, or domain) in compare and analysis views.

Create tags after the pipeline completes:

```bash
TOKEN=$(az account get-access-token --resource api://<catalog-appId> --query accessToken -o tsv)

# Create each tag individually — PUT /tags accepts a single Tag object, not an array
curl -X PUT "https://<catalog-fqdn>/api/projects/<PROJECT>/tags" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"name": "single-turn", "refs": ["gt-000", "gt-001", "gt-002"]}'

curl -X PUT "https://<catalog-fqdn>/api/projects/<PROJECT>/tags" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"name": "multi-turn", "refs": ["gt-050", "gt-051"]}'

curl -X PUT "https://<catalog-fqdn>/api/projects/<PROJECT>/tags" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"name": "retrieval", "refs": ["gt-000", "gt-010", "gt-020"]}'
```

Tags can be derived from the ground truth metadata. GTC v2 ground truths include `manualTags` and `computedTags` fields that can be mapped to catalog tags. For example, build a tag mapping script that:

1. Reads each ground truth file from the jobinput container.
2. Extracts the `id` (used as the catalog ref) and `manualTags` / `computedTags`.
3. Groups refs by tag value.
4. PUTs each tag individually to the catalog (the API accepts a single Tag object per request, not an array).

Filtering by tags is available on the compare endpoint:

```text
GET /api/projects/<PROJECT>/experiments/<EXPERIMENT>/compare?include-tags=single-turn&exclude-tags=multi-turn
```

## Metric Definition Aggregation Functions

When creating metric definitions in the catalog, choose the correct `aggregate_function` for each metric type:

| Aggregate Function | Use When                                       | Values Expected                |
| ------------------ | ---------------------------------------------- | ------------------------------ |
| `Average`          | Continuous float metrics (most common)         | Floats in a defined range      |
| `Count`            | Counting occurrences                           | Integers ≥ 0                   |
| `Accuracy`         | Classification accuracy from confusion matrix  | `t+`, `t-`, `f+`, `f-` strings |
| `Precision`        | Classification precision from confusion matrix | `t+`, `t-`, `f+`, `f-` strings |
| `Recall`           | Classification recall from confusion matrix    | `t+`, `t-`, `f+`, `f-` strings |

> [!IMPORTANT]
> Do not use `Accuracy`, `Precision`, or `Recall` aggregation for continuous float metrics. These functions expect classification outcomes (`t+`, `t-`, `f+`, `f-`) and silently produce zeros when given floats. Use `Average` for any metric that produces a continuous value in a range like 0–1.

## Troubleshooting

### Common Errors

| Symptom                                                                              | Cause                                                                                        | Fix                                                                                                                                                                                  |
| ------------------------------------------------------------------------------------ | -------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | --- | --------------------------------------------------------- | -------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------- |
| `ModuleNotFoundError: inference`                                                     | `AML_INF_MODULE_DIR` in `.exp.env` is wrong.                                                 | Set to `../inference/demo-inference`.                                                                                                                                                |
| `ModuleNotFoundError: evaluation`                                                    | `AML_EVAL_MODULE_DIR` in `.exp.env` is wrong.                                                | Set to `../evaluation/demo-evaluation`.                                                                                                                                              |
| `ImportError: cannot import name 'EventBus' from 'inference'`                        | Runner hard-codes `from inference.inference import EventBus, GroundTruth`.                   | Ensure `inference.py` exports `EventBus` and `GroundTruth` stub classes in `__all__`.                                                                                                |
| `ImportError: cannot import name 'GroundTruth' from 'inference.Models.ground_truth'` | Runner imports `from inference.Models.ground_truth import GroundTruth`.                      | Ensure `Models/__init__.py` and `Models/ground_truth.py` exist with a stub `GroundTruth` dataclass.                                                                                  |
| `Unsupported datastore authentication`                                               | Workspace `system_datastores_auth_mode` is `accesskey` but storage key access is disabled.   | Run `az ml workspace update --system-datastores-auth-mode identity`. Also verify datastores have `serviceDataAccessAuthIdentity: WorkspaceSystemAssignedIdentity`.                   |
| `AccessError: Failed to create table ... authorization failure`                      | Workspace or compute identity lacks `Storage Table Data Contributor` on the storage account. | Add `Storage Table Data Contributor` and `Storage Queue Data Contributor` roles for both the workspace system identity and compute user-assigned managed identity. See RBAC section. |
| `AccessError: Failed to create queue ... authorization failure`                      | Same root cause as table authorization failure.                                              | Same fix as table authorization.                                                                                                                                                     |
| All `answer_similarity` scores are 0                                                 | Ground truth records have no `answer` field.                                                 | Add expected answers or use the included sample data.                                                                                                                                |
| `FileNotFoundError` on ground truths                                                 | Ground truth files not uploaded to the datastore.                                            | Run `setup_demo.py` first, or upload files with `az storage blob upload-batch --auth-mode login`.                                                                                    |
| Runner root not found                                                                | Setup script cannot locate the runner directory.                                             | Pass `--runner-root` explicitly to the setup script.                                                                                                                                 |     | `404: experiment not found` in eval or summarization logs | Catalog action tried to POST results but the experiment does not exist in the catalog. | Create the experiment in the catalog before submitting the pipeline. See the Catalog Action Pre-Creation section. |
| Catalog action silently skips all results (no errors, no data in catalog)            | `CATALOG_URL` or `CATALOG_PROJECT` env var is missing or empty.                              | Verify `EVAL_SET_CATALOG_URL` and `EVAL_SET_CATALOG_PROJECT` are set in your `.exp.env`. The `EVAL_SET_` prefix is stripped at runtime.                                              |     | `az ml job download` fails with auth error                | Storage account has key-based auth disabled; the CLI falls back to keys by default.    | Use `az storage blob download --auth-mode login` instead (see Log Retrieval section).                             |

### Ground Truth Upload

When using the AML datastore (not local files), ground truth JSON files must be uploaded to the blob container referenced by `AML_JOB_INPUT_DATASTORE`. Upload with identity-based auth:

```bash
az storage blob upload-batch \
    --auth-mode login \
    --account-name <storage-account> \
    --destination <container>/<AML_GROUND_TRUTHS_PATH> \
    --source <local-ground-truths-dir>
```

## Pipeline Monitoring

### Submitting a Run

```bash
cd aml-evaluation-runner/experiment
uv run python run.py --env_path .exp.env
```

The script prints a pipeline name (for example, `lucid_curtain_9v6drgd42d`) and an Azure ML Studio URL.

### Checking Pipeline Status

```bash
az ml job show \
    --name <pipeline-name> \
    --resource-group <rg> --workspace-name <workspace> \
    --query "{status:status, display_name:display_name}" -o json
```

### Checking Child Job Status

The pipeline has three sequential steps: `batch_inference`, `batch_eval`, and `batch_summarization`. List their statuses with:

```bash
az ml job list \
    --parent-job-name <pipeline-name> \
    --resource-group <rg> --workspace-name <workspace> \
    --query "[].{name:name, display_name:display_name, status:status}" -o json
```

A typical healthy progression is: Queued (waiting for compute scale-up, 1–3 min) then Running then Completed for each step in sequence.

## Log Retrieval

When a child job fails, the pipeline-level status shows `Failed` but gives no detail. You must retrieve logs from the individual child job that failed.

### Important Constraint

When the storage account has key-based auth disabled, `az ml job download` does not work. It falls back to storage account keys and fails with an authorization error. Use `az storage blob download --auth-mode login` instead.

### Log File Locations

All logs are in the `azureml` container on the workspace's default storage account (not the app storage). The path structure is:

| Log File                | Blob Path                                                   | Contains                                                      |
| ----------------------- | ----------------------------------------------------------- | ------------------------------------------------------------- |
| Job result summary      | `ExperimentRun/dcid.<child-job-id>/logs/job_result.txt`     | High-level success/failure message with error details.        |
| Job error (per process) | `ExperimentRun/dcid.<child-job-id>/logs/job_error.<n>.txt`  | Stack traces and detailed error messages per worker process.  |
| User log (primary)      | `ExperimentRun/dcid.<child-job-id>/user_logs/std_log_0.txt` | Application-level stdout from the module code.                |
| System logs             | `ExperimentRun/dcid.<child-job-id>/system_logs/`            | AML framework logs (compute provisioning, environment setup). |

### Step-by-Step Log Retrieval

1. Get the child job ID for the failed step:

```bash
az ml job list \
    --parent-job-name <pipeline-name> \
    --resource-group <rg> --workspace-name <workspace> \
    --query "[?status=='Failed'].{name:name, display_name:display_name}" -o json
```

2. Find the workspace default storage account name:

```bash
az ml workspace show --name <workspace> --resource-group <rg> \
    --query storage_account -o tsv
# Returns a resource ID — extract the account name from the last segment.
```

3. Download the `job_result.txt` (start here for error diagnosis):

```bash
az storage blob download \
    --auth-mode login \
    --account-name <default-storage-account> \
    --container-name azureml \
    --name "ExperimentRun/dcid.<child-job-id>/logs/job_result.txt" \
    --file /tmp/job_result.txt

cat /tmp/job_result.txt
```

4. If more detail is needed, download the user log:

```bash
az storage blob download \
    --auth-mode login \
    --account-name <default-storage-account> \
    --container-name azureml \
    --name "ExperimentRun/dcid.<child-job-id>/user_logs/std_log_0.txt" \
    --file /tmp/std_log_0.txt

cat /tmp/std_log_0.txt
```

5. To list all available log files for a child job:

```bash
az storage blob list \
    --auth-mode login \
    --account-name <default-storage-account> \
    --container-name azureml \
    --prefix "ExperimentRun/dcid.<child-job-id>/" \
    --query "[].name" -o tsv | grep -E 'logs/|user_logs/'
```

### Diagnostic Sequence

When a run fails, follow this sequence to diagnose efficiently:

1. Check which child step failed (`az ml job list --parent-job-name ...`).
2. Download `logs/job_result.txt` for the failed child job — this usually contains the root cause.
3. If `job_result.txt` shows an `AccessError` or authorization failure, check RBAC roles (see RBAC Requirements section).
4. If `job_result.txt` shows an application error, download `user_logs/std_log_0.txt` for the full stack trace.
5. If the error is an `ImportError` or `ModuleNotFoundError`, the demo module files have a missing export or file (see Common Errors table).

> Brought to you by microsoft/aml-evaluation-runner
