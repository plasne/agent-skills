---
name: gtc-demo-data
description: Generate realistic sample ground truth items for the Ground Truth Curator so SMEs can test the self-serve queue and "request more" workflow.
---

## Execution Model

> [!IMPORTANT]
> Do not execute this skill directly in the main thread. Delegate the data
> generation or import task to its own sub-agent and pass this skill path to
> that sub-agent.

Keep data generation separate from deployment or AML pipeline tasks. Save counts,
dataset names, and artifact paths in session state instead of replaying bulk
logs.

# Generate GTC Sample Data

Use this skill to populate a running GTC instance with realistic draft or
approved items. Open `references/full-guide.md` for the long-form walkthrough
and the full parameter list.

## Prerequisites

- Python 3.11+
- `uv`
- a reachable GTC backend

## Fast Path

Generate default sample data:

```bash
cd GroundTruthCurator/backend
uv run python scripts/generate_gtc_sample_data.py
```

Generate across multiple datasets:

```bash
uv run python scripts/generate_gtc_sample_data.py --count 200 --datasets demo,support-kb
```

Generate approved items:

```bash
uv run python scripts/generate_gtc_sample_data.py --dataset golden --count 50 --approve
```

## Critical Format Rule

Keep this inline because it matters beyond GTC import:

- when generating portable data directly, use the GTC v2 shape with `history`
- do not reduce items to top-level `question` and `answer` fields only
- AML demo flows commonly derive question/answer from the `history` entries

## Key Parameters

- `--base-url`
- `--dataset` or `--datasets`
- `--count`
- `--approve`
- `--multi-turn`
- `--seed`

## Validation Checklist

Verify all of the following before handoff:

- the target GTC instance is reachable
- the expected datasets were populated
- counts match the request
- draft vs approved status matches the request
- any generated JSON artifact was saved for reuse if needed

## Local References

- Extended instructions and troubleshooting: `references/full-guide.md`
