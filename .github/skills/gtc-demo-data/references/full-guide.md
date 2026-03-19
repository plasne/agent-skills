---
name: gtc-demo-data
description: Generate realistic sample ground truth items for the Ground Truth Curator so SMEs can test the self-serve queue and "request more" workflow.
---

# Generate GTC Sample Data

Populate a running Ground Truth Curator instance with realistic ground truth items for development, testing, or demonstration. The script creates draft items across one or more datasets with varied questions, references, multi-turn conversations, and tags so the self-serve queue has items available for "request more."

## Execution Model

> [!IMPORTANT]
> **Do not execute tasks from this skill directly.** Every discrete task you
> derive from this skill must be delegated to its own sub-agent. Each sub-agent
> should be given this skill file's path so it can read the full instructions
> itself.
>
> For example, if the user asks to "add 100 approved and 100 draft ground
> truths," that is one task for a sub-agent. If there are other tasks (deploying
> GTC, running the pipeline), those are separate sub-agents.

When the user asks for a larger workflow that includes GTC data generation, do
not merge the data work into unrelated deployment or pipeline tasks. Keep data
generation/import as its own delegated phase.

Additional rules for avoiding main-context overflow:

- Keep the main thread in a coordinator role. Use sub-agents for execution,
  especially for generation scripts, API import loops, export preparation, and
  verification.
- Write or update concise artifacts in the session workspace when available
  (for example: generated JSON files, import summaries, dataset names, counts,
  and next-step notes). Prefer artifact handoff over repeating all state in the
  conversation.
- Successful bulk operations should be summarized briefly. Only surface full
  logs when a command fails or when specific output is required to make a
  decision.
- If the data task uncovers a new discrete task, delegate that follow-up as its
  own sub-agent instead of extending the current thread indefinitely.
- End the task with a checkpoint that records what was created, where it was
  stored, and how it was verified.

## Prerequisites

- Python 3.11 or later with `uv` installed.
- The GTC backend running locally (default `http://localhost:8000`).
- The `httpx` package (already in the GTC backend dependencies).

## Generating Ground Truths Directly (v2 Format)

When admin consent is unavailable or the GTC API is not accessible, generate ground truths directly in GTC v2 JSON format. Each file is a single JSON record:

```json
{
  "id": "gt-000",
  "datasetName": "demo",
  "bucket": 0,
  "status": "approved",
  "history": [
    { "role": "user", "msg": "What is Azure Machine Learning?" },
    {
      "role": "assistant",
      "msg": "Azure Machine Learning is a cloud service for training and deploying ML models."
    }
  ],
  "manualTags": { "source": "synthetic", "topic": "general" },
  "computedTags": { "question_length": "medium" }
}
```

The AML Evaluation Runner reads `question` and `answer` from the history (first user message and last assistant message). Multi-turn items have multiple user/assistant pairs.

Split files into individual JSON records and upload to the AML datastore:

```bash
az storage blob upload-batch \
  --auth-mode login \
  --account-name <storage-account> \
  --destination <container>/<AML_GROUND_TRUTHS_PATH> \
  --source <local-ground-truths-dir>
```

## Quick Start

Run from the GTC backend directory with defaults (100 draft items in dataset `demo`):

```bash
cd GroundTruthCurator/backend
uv run python scripts/generate_gtc_sample_data.py
```

Generate 200 items across two datasets:

```bash
uv run python scripts/generate_gtc_sample_data.py --count 200 --datasets demo,support-kb
```

Import items as pre-approved (useful for testing duplicate detection against new drafts):

```bash
uv run python scripts/generate_gtc_sample_data.py --dataset golden --count 50 --approve
```

## Parameters Reference

| Parameter      | Default                 | Description                                                       |
| -------------- | ----------------------- | ----------------------------------------------------------------- |
| `--base-url`   | `http://localhost:8000` | Base URL of the running GTC backend.                              |
| `--api-prefix` | `/v1`                   | API prefix path.                                                  |
| `--user`       | `seed-script`           | `X-User-Id` header for dev auth.                                  |
| `--dataset`    | `demo`                  | Single dataset name (ignored when `--datasets` is provided).      |
| `--datasets`   | —                       | Comma-separated list of dataset names to distribute items across. |
| `--count`      | `100`                   | Total number of ground truth items to create.                     |
| `--buckets`    | —                       | Number of sampling buckets (omit to let the server decide).       |
| `--approve`    | `false`                 | If set, mark all items as approved on import.                     |
| `--multi-turn` | `0.2`                   | Fraction of items that are multi-turn conversations (0.0 – 1.0).  |
| `--seed`       | —                       | Random seed for reproducible data generation.                     |

## What Gets Created

### Ground Truth Items

Each item includes:

- A unique ID such as `demo-q0042`.
- A synthetic question with varied phrasing and domains.
- One to three references with realistic URLs, titles, and key excerpts.
- Manual tags drawn from the configured tag schema (source, answerability, topic, intent, expertise, difficulty).
- Computed tags are applied automatically by the server (question_length, reference_type, retrieval_behavior, turns).

### Multi-turn Items

A configurable fraction of items (default 20%) include multi-turn conversation history with:

- Two to four turns alternating user and assistant roles.
- Assistant turns with embedded references.
- Expected behavior annotations (`tool:search`, `generation:answer`).

### Tag Distribution

Tags are randomized with realistic distributions:

| Tag Group       | Values                                                 | Distribution        |
| --------------- | ------------------------------------------------------ | ------------------- |
| `source`        | synthetic, sme, user                                   | 60 / 25 / 15 %      |
| `answerability` | answerable, not_answerable, should_not_answer          | 75 / 15 / 10 %      |
| `topic`         | general, compatibility, install, performance, security | ~20 % each          |
| `intent`        | informational, action, clarification, feedback         | 40 / 30 / 20 / 10 % |
| `expertise`     | novice, expert                                         | 65 / 35 %           |
| `difficulty`    | easy, medium, hard                                     | 40 / 40 / 20 %      |

### Using the Self-Serve Queue

After importing draft items, open the GTC frontend and click **Request More** to pull items from the queue:

1. Run the seed script to populate draft items.
2. Open the GTC UI (default `http://localhost:5173` for Vite dev server or `http://localhost:8000` if serving from backend).
3. Click **Request More** — this calls `POST /v1/assignments/self-serve` with `{ "limit": 10 }`.
4. Draft items are assigned to you and appear in your queue for curation.

## Authentication for Deployed Instances

> [!IMPORTANT]
> Never disable EasyAuth or set `GTC_AUTH_MODE=dev` on a deployed GTC instance to work around 401 errors. Always use Bearer tokens for programmatic access.

When running against a deployed GTC instance with EasyAuth enabled, the seed script must authenticate. Acquire a token and pass it via the `--header` flag or set the `GTC_BEARER_TOKEN` environment variable (if supported by the script):

```bash
TOKEN=$(az account get-access-token --resource api://<appId> --query accessToken -o tsv)

cd GroundTruthCurator/backend
uv run python scripts/generate_gtc_sample_data.py \
  --base-url "https://<gtc-fqdn>" \
  --header "Authorization: Bearer $TOKEN"
```

If the script does not support a `--header` flag, use `curl` or `httpx` directly with the Bearer token to POST ground truth items to the `/v1/ground-truths/import` endpoint.

The `api://<appId>` value is the Application ID URI of the GTC app registration. See the **gtc-install** skill for complete Entra ID app registration setup.

## Troubleshooting

| Symptom                      | Fix                                                                                                                                                                                                                                                                                                               |
| ---------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `ConnectionError`            | Confirm the GTC backend is running at the base URL.                                                                                                                                                                                                                                                               |
| `401 Unauthorized`           | If running locally without auth, ensure `GTC_AUTH_MODE=dev`. For deployed instances with EasyAuth, acquire a Bearer token: `TOKEN=$(az account get-access-token --resource api://<appId> --query accessToken -o tsv)` and pass `--header "Authorization: Bearer $TOKEN"`. Never disable EasyAuth as a workaround. |
| `400 Bad Request`            | Items may have invalid tags. Check the tag schema via `GET /v1/tags/schema`.                                                                                                                                                                                                                                      |
| Items not appearing in queue | Verify items are in `draft` status and unassigned (`assignedTo` is null).                                                                                                                                                                                                                                         |
| `httpx` not found            | Run from the GTC backend directory with `uv run` to use project dependencies.                                                                                                                                                                                                                                     |
| Admin consent unavailable    | When admin consent cannot be granted (common in non-production tenants), generate ground truths directly in GTC v2 JSON format and upload to the AML datastore, bypassing the GTC API export. Browser-based EasyAuth login still works for interactive users.                                                     |

> Brought to you by att/GroundTruthCurator
