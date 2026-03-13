---
name: aml-eval-runner-demo
description: Deploy demo inference and evaluation modules for the AML Evaluation Runner. Provides a zero-dependency end-to-end pipeline using GTC v2 ground truth exports with lightweight string-similarity metrics.
---

# AML Evaluation Runner Demo

Deploy a pair of demo plug-in modules — inference and evaluation — that let you run the AML Evaluation Runner pipeline end-to-end without any API keys, model endpoints, or heavy dependencies. The demo modules accept ground truth records in the GTC v2 snapshot format and produce deterministic metrics using only the Python standard library.

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

A single `eval.py` with a `run_eval` function that computes:

| Metric                   | Range  | Description                                                |
| ------------------------ | ------ | ---------------------------------------------------------- |
| `answer_similarity`      | 0 – 1  | SequenceMatcher ratio between expected and actual answers. |
| `word_overlap_f1`        | 0 – 1  | Token-level F1 score (precision × recall harmonic mean).   |
| `answer_length_ratio`    | 0 – 2  | Ratio of actual to expected answer length (word count).    |
| `has_answer`             | 0 or 1 | Binary flag: did inference produce a non-empty response?   |
| `meta_inference_time_ms` | ≥ 0    | Inference latency from the inference step.                 |
| `meta_prompt_tokens`     | ≥ 0    | Input token count from inference usage.                    |
| `meta_completion_tokens` | ≥ 0    | Output token count from inference usage.                   |

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

## Troubleshooting

### Common Errors

| Symptom                                                                              | Cause                                                                                        | Fix                                                                                                                                                                                  |
| ------------------------------------------------------------------------------------ | -------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `ModuleNotFoundError: inference`                                                     | `AML_INF_MODULE_DIR` in `.exp.env` is wrong.                                                 | Set to `../inference/demo-inference`.                                                                                                                                                |
| `ModuleNotFoundError: evaluation`                                                    | `AML_EVAL_MODULE_DIR` in `.exp.env` is wrong.                                                | Set to `../evaluation/demo-evaluation`.                                                                                                                                              |
| `ImportError: cannot import name 'EventBus' from 'inference'`                        | Runner hard-codes `from inference.inference import EventBus, GroundTruth`.                   | Ensure `inference.py` exports `EventBus` and `GroundTruth` stub classes in `__all__`.                                                                                                |
| `ImportError: cannot import name 'GroundTruth' from 'inference.Models.ground_truth'` | Runner imports `from inference.Models.ground_truth import GroundTruth`.                      | Ensure `Models/__init__.py` and `Models/ground_truth.py` exist with a stub `GroundTruth` dataclass.                                                                                  |
| `Unsupported datastore authentication`                                               | Workspace `system_datastores_auth_mode` is `accesskey` but storage key access is disabled.   | Run `az ml workspace update --system-datastores-auth-mode identity`. Also verify datastores have `serviceDataAccessAuthIdentity: WorkspaceSystemAssignedIdentity`.                   |
| `AccessError: Failed to create table ... authorization failure`                      | Workspace or compute identity lacks `Storage Table Data Contributor` on the storage account. | Add `Storage Table Data Contributor` and `Storage Queue Data Contributor` roles for both the workspace system identity and compute user-assigned managed identity. See RBAC section. |
| `AccessError: Failed to create queue ... authorization failure`                      | Same root cause as table authorization failure.                                              | Same fix as table authorization.                                                                                                                                                     |
| All `answer_similarity` scores are 0                                                 | Ground truth records have no `answer` field.                                                 | Add expected answers or use the included sample data.                                                                                                                                |
| `FileNotFoundError` on ground truths                                                 | Ground truth files not uploaded to the datastore.                                            | Run `setup_demo.py` first, or upload files with `az storage blob upload-batch --auth-mode login`.                                                                                    |
| Runner root not found                                                                | Setup script cannot locate the runner directory.                                             | Pass `--runner-root` explicitly to the setup script.                                                                                                                                 |
| `az ml job download` fails with auth error                                           | Storage account has key-based auth disabled; the CLI falls back to keys by default.          | Use `az storage blob download --auth-mode login` instead (see Log Retrieval section).                                                                                                |

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
