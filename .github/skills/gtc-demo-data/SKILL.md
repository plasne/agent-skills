````skill
---
name: generate-gtc-data
description: Generate realistic sample ground truth items for the Ground Truth Curator so SMEs can test the self-serve queue and "request more" workflow.
---

# Generate GTC Sample Data

Populate a running Ground Truth Curator instance with realistic ground truth items for development, testing, or demonstration. The script creates draft items across one or more datasets with varied questions, references, multi-turn conversations, and tags so the self-serve queue has items available for "request more."

## Prerequisites

- Python 3.11 or later with `uv` installed.
- The GTC backend running locally (default `http://localhost:8000`).
- The `httpx` package (already in the GTC backend dependencies).

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

| Parameter      | Default                 | Description                                                         |
| -------------- | ----------------------- | ------------------------------------------------------------------- |
| `--base-url`   | `http://localhost:8000` | Base URL of the running GTC backend.                                |
| `--api-prefix` | `/v1`                   | API prefix path.                                                    |
| `--user`       | `seed-script`           | `X-User-Id` header for dev auth.                                    |
| `--dataset`    | `demo`                  | Single dataset name (ignored when `--datasets` is provided).        |
| `--datasets`   | —                       | Comma-separated list of dataset names to distribute items across.   |
| `--count`      | `100`                   | Total number of ground truth items to create.                       |
| `--buckets`    | —                       | Number of sampling buckets (omit to let the server decide).         |
| `--approve`    | `false`                 | If set, mark all items as approved on import.                       |
| `--multi-turn` | `0.2`                   | Fraction of items that are multi-turn conversations (0.0 – 1.0).   |
| `--seed`       | —                       | Random seed for reproducible data generation.                       |

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

| Tag Group      | Values                                               | Distribution     |
| -------------- | ---------------------------------------------------- | ---------------- |
| `source`       | synthetic, sme, user                                 | 60 / 25 / 15 %  |
| `answerability`| answerable, not_answerable, should_not_answer         | 75 / 15 / 10 %  |
| `topic`        | general, compatibility, install, performance, security | ~20 % each       |
| `intent`       | informational, action, clarification, feedback        | 40 / 30 / 20 / 10 % |
| `expertise`    | novice, expert                                       | 65 / 35 %       |
| `difficulty`   | easy, medium, hard                                   | 40 / 40 / 20 %  |

### Using the Self-Serve Queue

After importing draft items, open the GTC frontend and click **Request More** to pull items from the queue:

1. Run the seed script to populate draft items.
2. Open the GTC UI (default `http://localhost:5173` for Vite dev server or `http://localhost:8000` if serving from backend).
3. Click **Request More** — this calls `POST /v1/assignments/self-serve` with `{ "limit": 10 }`.
4. Draft items are assigned to you and appear in your queue for curation.

## Troubleshooting

| Symptom                    | Fix                                                                           |
| -------------------------- | ----------------------------------------------------------------------------- |
| `ConnectionError`          | Confirm the GTC backend is running at the base URL.                           |
| `401 Unauthorized`         | Ensure `AUTH_MODE=dev` or pass a valid `X-User-Id` header.                    |
| `400 Bad Request`          | Items may have invalid tags. Check the tag schema via `GET /v1/tags/schema`.  |
| Items not appearing in queue | Verify items are in `draft` status and unassigned (`assignedTo` is null).   |
| `httpx` not found          | Run from the GTC backend directory with `uv run` to use project dependencies. |

> Brought to you by att/GroundTruthCurator

````
