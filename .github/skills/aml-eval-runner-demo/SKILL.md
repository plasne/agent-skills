---
name: aml-eval-runner-demo
description: Deploy demo inference and evaluation modules for the AML Evaluation Runner. Provides a zero-dependency end-to-end pipeline using GTC v2 ground truth exports with lightweight string-similarity metrics.
---

## Execution Model

> [!IMPORTANT]
> Do not execute this skill directly in the main thread. Delegate each discrete
> task to its own sub-agent and pass this skill path to that sub-agent.

Use phases for larger requests:

1. inspect current runner deployment
2. install demo modules
3. prepare or export ground truths
4. stage data and configure the run
5. submit and monitor AML
6. validate outputs and handoff

Keep the main thread as coordinator, checkpoint run IDs and artifact paths, and
summarize successful long-running work.

# AML Evaluation Runner Demo

Use this skill to set up the demo inference/evaluation pair and run an end-to-end
pipeline with minimal dependencies. Open `references/full-guide.md` for the
full command set, auth walkthroughs, and diagnostic procedures.

## Prerequisites

Before using this skill, ensure:

- the AML runner repo is already cloned
- the AML workspace and compute already exist
- input and output datastores are configured
- the user has decided whether sample data, GTC exports, or another dataset will
  be used

## Fast Path

1. Copy or generate the demo inference and demo evaluation modules.
2. Prepare ground truths in the expected JSON shape.
3. Stage the ground truths to the runner input datastore.
4. Configure `.exp.env`.
5. Pre-create the catalog project and experiment if catalog publishing is enabled.
6. Submit the run.
7. Verify the AML outputs and downstream catalog results.

## Critical Configuration

### Ground Truth Format

Keep these inline because they are the most important compatibility rules:

- the demo modules expect GTC v2 style records
- preserve the `history`-based structure
- do not flatten the records into top-level `question` and `answer` fields only
  before the demo modules consume them

### Infrastructure Expectations

- workspace datastore auth should be identity-based
- both workspace and compute identities may need blob, table, and queue roles
- if AML image builds are unreliable, use a prebuilt image and set
  `AML_IMAGE_NAME` directly

### Catalog Publishing

If publishing to the Experiment Catalog:

- create the target project before the run
- create the target experiment before the run
- use the catalog `/api` base URL
- for managed-identity auth, ensure the catalog app exposes an Application-type
  app role

## Validation Checklist

Verify all of the following before handoff:

- staged ground truths are readable by AML
- demo modules are in the expected runner locations
- the AML pipeline completes
- evaluation metrics are produced
- catalog results are visible if publishing is enabled

## Local References

- Extended instructions and diagnostics: `references/full-guide.md`
