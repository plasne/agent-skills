---
name: experiment-catalog-demo-data
description: Generate realistic demo data for the experiment catalog including projects, experiments, permutations, results with metrics, metric definitions, and tags.
---

# Generate Demo Data

Populate a running experiment catalog instance with realistic demo data for development, testing, or demonstration purposes. The script creates two projects, multiple experiments per project with different hypotheses, several permutations (sets) per experiment, hundreds of results per permutation, metric definitions, and tags applied to refs.

## Prerequisites

- Python 3.10 or later.
- The `requests` package (`pip install requests` or `uv pip install requests`).
- A running experiment catalog backend (default `http://localhost:6010`).

## Quick Start

Run with defaults against a local catalog instance:

```bash
python scripts/generate_demo_data.py
```

Override the base URL:

```bash
python scripts/generate_demo_data.py --base-url http://localhost:8080
```

## Parameters Reference

| Parameter    | Default                 | Description                        |
| ------------ | ----------------------- | ---------------------------------- |
| `--base-url` | `http://localhost:6010` | Base URL of the catalog API.       |
| `--results`  | `300`                   | Number of results per permutation. |

## What Gets Created

### Projects

- `sprint01` — first sprint of RAG evaluation work.
- `sprint02` — second sprint focused on generation quality.

### Metric Definitions (per project)

| Metric                    | Range | Aggregate | Order |
| ------------------------- | ----- | --------- | ----- |
| `retrieval_accuracy`      | 0 – 1 | Average   | 100   |
| `retrieval_precision`     | 0 – 1 | Average   | 110   |
| `retrieval_recall`        | 0 – 1 | Average   | 120   |
| `generation_correctness`  | 0 – 1 | Average   | 300   |
| `generation_faithfulness` | 0 – 1 | Average   | 310   |
| `meta_inference_time`     | —     | Average   | 1000  |
| `meta_inference_cost`     | —     | Cost      | 1010  |

### Experiments and Permutations

Each project contains two experiments:

| Experiment | Hypothesis                                               | Permutations                       |
| ---------- | -------------------------------------------------------- | ---------------------------------- |
| `top-k`    | Varying the retrieval top-k parameter improves accuracy. | `top-k-3`, `top-k-5`, `top-k-10`   |
| `models`   | Larger models produce better generation quality.         | `gpt-4o-mini`, `gpt-4o`, `gpt-4.1` |

The first permutation in each experiment is set as the baseline.

### Tags

| Tag              | Description               |
| ---------------- | ------------------------- |
| `multi-turn`     | Applied to ~15 % of refs. |
| `complex-query`  | Applied to ~10 % of refs. |
| `domain:finance` | Applied to ~25 % of refs. |
| `domain:legal`   | Applied to ~25 % of refs. |

### Results

Each permutation contains `--results` results (default 100). Each result has:

- A `ref` identifier (`q001` – `q100`).
- All seven metrics with realistic random values. Values shift by permutation to simulate meaningful differences between parameter choices.

## Troubleshooting

| Symptom                   | Fix                                                                                                   |
| ------------------------- | ----------------------------------------------------------------------------------------------------- |
| `ConnectionError`         | Confirm the catalog backend is running and reachable at the base URL.                                 |
| `400 Bad Request`         | The project or experiment may already exist. The script skips 409 conflicts but other errors surface. |
| Missing `requests` module | Run `pip install requests`.                                                                           |

> Brought to you by microsoft/experiment-catalog
