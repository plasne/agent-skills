---
description: End-to-end deployment and evaluation pipeline for GTC, AML Evaluation Runner, and Experiment Catalog
ms.date: 2026-03-17
---

# Evaluation Pipeline Deployment

Deploy GTC, AML Evaluation Runner, and Experiment Catalog to a shared resource group, populate ground truths, run a full evaluation pipeline, and output results to the catalog.

## Configuration

- Resource group: `pelasne-eval-06`
- Clone all repos fresh (even if they exist locally)
- Share Azure resources where possible (storage account, etc.)
- Use OIDC auth for GTC and Experiment Catalog
- 100 ground truths with 5 iterations each
- 25 metrics organized into `retrieval_`, `generation_`, and `metadata_` prefixes
- 1 baseline + 3 permutations of the experiment

## TODO Checklist

### Clone and setup

- [ ] Clone `andrewDoing/GroundTruthCurator` (HTTPS)
- [ ] Clone `commercial-software-engineering/aml-evaluation-runner` (SSH first, fallback HTTPS)
- [ ] Clone `plasne/experiment-catalog` (HTTPS)

### Azure resource group

- [ ] Create resource group `pelasne-eval-09` (ask for region preference)

### Shared Azure resources

- [ ] Create Storage Account (shared across AML runner, Experiment Catalog, and optionally GTC)
- [ ] Create Key Vault (used by AML workspace)
- [ ] Create Log Analytics workspace
- [ ] Create Application Insights (backed by Log Analytics)
- [ ] Assign yourself `Storage Blob Data Contributor`, `Storage Table Data Contributor`, and `Storage Queue Data Contributor` on the storage account

### GTC deployment

- [ ] Provision Cosmos DB
- [ ] Deploy GTC backend and frontend to Container Apps
- [ ] Configure OIDC / EasyAuth authentication on GTC
- [ ] Initialize Cosmos DB containers (gt-container, assignments-container, tags-container)

### AML Evaluation Runner deployment

> [!IMPORTANT]
> Do NOT use `SetupEnv.ps1` or the Bicep private-networking templates. Deploy via `az` CLI only.

- [ ] Create Azure Machine Learning workspace (Basic SKU, `system_datastores_auth_mode = identity`)
- [ ] Create Container Registry
- [ ] Create User-Assigned Managed Identity for the compute cluster
- [ ] Create AML Compute Cluster (Standard_D3_v2, 0–3 autoscale)
- [ ] Create `jobinput` datastore with identity-based auth (`credentialsType: None`, `serviceDataAccessAuthIdentity: WorkspaceSystemAssignedIdentity`)
- [ ] Create `joboutput` datastore with identity-based auth (same settings)
- [ ] Assign Blob, Table, and Queue Contributor roles to workspace system identity on the storage account
- [ ] Assign Blob, Table, and Queue Contributor roles to compute user-assigned managed identity on the storage account

### Experiment Catalog deployment

- [ ] Deploy catalog backend and Svelte UI to Azure (Container Apps)
- [ ] Enable Managed Identity on the hosting solution
- [ ] Assign `Storage Blob Data Contributor` to the managed identity on the shared storage account
- [ ] Configure OIDC authentication on the Experiment Catalog
- [ ] Set `INCLUDE_CREDENTIAL_TYPES=mi` and `AZURE_STORAGE_ACCOUNT_NAME` in catalog config

### Ground truth data

- [ ] Seed GTC with 100 ground truth items (varied questions, references, tags; all approved)
- [ ] Export 100 ground truths from GTC as v2 snapshot
- [ ] Split export into individual JSON files for the AML runner input datastore
- [ ] Upload 100 individual JSON files to the `jobinput` blob container at `AML_GROUND_TRUTHS_PATH` (use `--auth-mode login`)

### Fake inference module

Create at `aml-evaluation-runner/inference/demo-inference/`:

- [ ] Create `inference.py` with `InferenceService` that reads `question`/`answer` (supports `editedQuestion`/`synthQuestion` aliases) and returns a deterministic, slightly perturbed echo
- [ ] Emit standard result dict: `response`, `usage`, `function_calls`, timing fields
- [ ] Export `EventBus` and `GroundTruth` stubs in `__all__`
- [ ] Create `Models/__init__.py`
- [ ] Create `Models/ground_truth.py` with stub `GroundTruth` dataclass

### Fake evaluation module (25 metrics)

Create at `aml-evaluation-runner/evaluation/demo-evaluation/`:

- [ ] Create `eval.py` with `run_eval` function producing all 25 metrics below
- [ ] All metrics must be deterministic, stdlib-only, and produce non-trivial scores

**Retrieval metrics (10):**

- [ ] `retrieval_accuracy` — correctness of retrieved documents (0–1)
- [ ] `retrieval_precision` — fraction of retrieved docs that are relevant (0–1)
- [ ] `retrieval_recall` — fraction of relevant docs that were retrieved (0–1)
- [ ] `retrieval_f1` — harmonic mean of precision and recall (0–1)
- [ ] `retrieval_mrr` — mean reciprocal rank of first relevant result (0–1)
- [ ] `retrieval_ndcg` — normalized discounted cumulative gain (0–1)
- [ ] `retrieval_map` — mean average precision (0–1)
- [ ] `retrieval_hit_rate` — fraction of queries with at least one relevant result (0 or 1)
- [ ] `retrieval_context_relevance` — relevance of retrieved context to the question (0–1)
- [ ] `retrieval_chunk_utilization` — fraction of retrieved chunks actually used (0–1)

**Generation metrics (10):**

- [ ] `generation_correctness` — factual correctness of the answer (0–1)
- [ ] `generation_faithfulness` — answer grounded in provided context (0–1)
- [ ] `generation_completeness` — coverage of all expected answer points (0–1)
- [ ] `generation_coherence` — logical flow and readability (0–1)
- [ ] `generation_relevance` — answer relevance to the question (0–1)
- [ ] `generation_conciseness` — absence of unnecessary verbosity (0–1)
- [ ] `generation_fluency` — grammatical quality and naturalness (0–1)
- [ ] `generation_toxicity` — absence of harmful content (0–1, higher is better)
- [ ] `generation_answer_similarity` — SequenceMatcher ratio between expected and actual (0–1)
- [ ] `generation_word_overlap_f1` — token-level F1 score (0–1)

**Metadata metrics (5):**

- [ ] `metadata_inference_time_ms` — inference latency in milliseconds (≥ 0)
- [ ] `metadata_prompt_tokens` — input token count (≥ 0)
- [ ] `metadata_completion_tokens` — output token count (≥ 0)
- [ ] `metadata_answer_length_ratio` — ratio of actual to expected answer length (0–2)
- [ ] `metadata_has_answer` — did inference produce a non-empty response (0 or 1)

### Experiment configuration

- [ ] Configure `.exp.env` with 1 baseline permutation (default parameters)
- [ ] Configure 3 additional permutations (varied parameters: temperature, top-k, prompt strategy, etc.)
- [ ] Set 5 iterations per permutation
- [ ] Set `ENABLED_ACTIONS=catalog` to output results to the Experiment Catalog
- [ ] Set `AML_INF_MODULE_DIR=../inference/demo-inference`
- [ ] Set `AML_EVAL_MODULE_DIR=../evaluation/demo-evaluation`

### Experiment Catalog pre-creation

- [ ] Create a project in the catalog (with Bearer token auth)
- [ ] Create the experiment under that project (both `name` and `hypothesis` required; name must match `AML_EXPERIMENT_NAME`)
- [ ] Create metric definitions for all 25 metrics with appropriate ranges, aggregates, and display order
- [ ] Set the baseline permutation

### Build and run

- [ ] Build the Docker image for AML parallel jobs
- [ ] Push image to the Container Registry
- [ ] Submit the AML pipeline run (`uv run python run.py --env_path .exp.env`)
- [ ] Monitor pipeline until all 3 steps complete (batch_inference, batch_eval, batch_summarization)
- [ ] If any step fails, retrieve logs via `az storage blob download --auth-mode login` (not `az ml job download`)

## Validation Checklist

### Resource group and shared resources

- [ ] `pelasne-eval-09` exists and contains all expected resources
- [ ] Only one Storage Account is used across AML runner and Experiment Catalog
- [ ] Key Vault and Log Analytics workspace are shared where applicable

### GTC

- [ ] GTC backend responds (`GET /v1/stats` → 200)
- [ ] Unauthenticated requests return 401 (OIDC / EasyAuth is active)
- [ ] Cosmos DB containers exist: gt-container, assignments-container, tags-container
- [ ] 100 approved ground truth items exist in GTC and are exportable

### AML workspace

- [ ] `system_datastores_auth_mode` is `identity` (not `accesskey`)
- [ ] `jobinput` datastore has `credentialsType: None`
- [ ] `joboutput` datastore has `credentialsType: None`
- [ ] Compute cluster exists and can scale (0–3 nodes)

### RBAC roles on storage account

- [ ] Workspace system identity has `Storage Blob Data Contributor`
- [ ] Workspace system identity has `Storage Table Data Contributor`
- [ ] Workspace system identity has `Storage Queue Data Contributor`
- [ ] Compute user-assigned identity has `Storage Blob Data Contributor`
- [ ] Compute user-assigned identity has `Storage Table Data Contributor`
- [ ] Compute user-assigned identity has `Storage Queue Data Contributor`
- [ ] Your user account has `Storage Blob Data Contributor`

### Experiment Catalog

- [ ] Catalog backend responds (`GET /api/projects` → 200)
- [ ] Unauthenticated requests return 401 (OIDC is active)
- [ ] Managed Identity has `Storage Blob Data Contributor` on the storage account

### Demo inference module

- [ ] `inference.py` exists at `aml-evaluation-runner/inference/demo-inference/`
- [ ] `EventBus` and `GroundTruth` stubs are exported
- [ ] `Models/ground_truth.py` and `Models/__init__.py` exist
- [ ] Module accepts GTC v2 format and returns proper inference result structure

### Demo evaluation module

- [ ] `eval.py` exists at `aml-evaluation-runner/evaluation/demo-evaluation/`
- [ ] Produces exactly 25 metrics (10 retrieval, 10 generation, 5 metadata)
- [ ] All metric values are in their documented ranges
- [ ] No external dependencies beyond the Python standard library

### Experiment structure

- [ ] Catalog contains the project and experiment
- [ ] All 25 metric definitions are created with correct ranges, aggregates, and order
- [ ] Experiment has exactly 4 permutations (1 baseline + 3)
- [ ] Baseline permutation is correctly flagged

### Ground truth upload

- [ ] 100 individual JSON files exist in the `jobinput` blob container at `AML_GROUND_TRUTHS_PATH`

### Pipeline execution

- [ ] Pipeline overall status is `Completed`
- [ ] `batch_inference` child job status is `Completed`
- [ ] `batch_eval` child job status is `Completed`
- [ ] `batch_summarization` child job status is `Completed`
- [ ] No errors in `job_result.txt` for any child job
- [ ] No errors in `std_log_0.txt` for any child job

### Results in catalog

- [ ] Each of the 4 permutations has results in the catalog
- [ ] Each result contains all 25 metrics
- [ ] 5 iterations were executed per permutation
- [ ] Total result records: 4 permutations × 5 iterations × 100 ground truths = 2,000
- [ ] Results are viewable in the catalog UI
- [ ] Metric values vary across permutations (not all 0 or all 1)
