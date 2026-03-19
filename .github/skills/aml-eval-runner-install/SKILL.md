---
name: aml-eval-runner-install
description: Clone, configure, and deploy the AML Evaluation Runner (commercial-software-engineering/aml-evaluation-runner). Provisions Azure Machine Learning workspace, Storage Account, and supporting resources. Builds the experiment image and runs evaluation pipelines. Trigger phrases include "install AML eval runner", "run AML evaluation runner", "AML eval runner", "experiment runner setup", "install evaluation runner", "deploy eval runner".
---

## Execution Model

> [!IMPORTANT]
> Do not execute this skill directly in the main thread. Delegate each discrete
> task to its own sub-agent and pass this skill path to that sub-agent.

Use phases for larger requests:

1. discovery and plan
2. resource provisioning
3. auth and RBAC
4. data staging and config
5. pipeline submission and monitoring
6. validation and handoff

Keep the main thread as coordinator, checkpoint IDs and run artifacts, and
summarize successful long-running work.

# AML Evaluation Runner Installation

Use this skill to deploy the runner and its Azure infrastructure. Keep the hot
path here and open `references/full-guide.md` for detailed procedures and the
full troubleshooting matrix.

## Ask the User First

Before deploying, confirm:

- region, resource group, and naming prefix
- whether resources should be shared with other apps
- public endpoints vs private networking
- whether catalog and/or MLflow actions should be enabled
- whether the goal is only installation or also running an experiment

Never invent names or security settings without user input.

## Source Code

Repo: <https://github.com/commercial-software-engineering/aml-evaluation-runner>

This repo is private. Default to SSH cloning.

Focus on:

- `experiment`
- `infra`
- `actions` when optional integrations are used

Ignore reference/demo folders during installation.

## Core Azure Resources

At minimum the runner needs:

- Azure ML workspace
- compute cluster
- storage for inputs and outputs
- ACR for custom images
- identity and RBAC for workspace and compute

Optional but common:

- Application Insights
- catalog action target
- MLflow action setup

## Fast Path

1. Clone the repo via SSH.
2. Provision the Azure resources.
3. Configure AML workspace, compute, datastores, identities, and RBAC.
4. Create the experiment env file.
5. Build or select the image.
6. Stage inputs.
7. Submit a run.
8. Verify outputs and any configured actions.

Use the exact commands in `references/full-guide.md`.

## Critical Configuration

### Workspace and Datastores

Keep these inline because they are common failure points:

- workspace `system_datastores_auth_mode` should be `identity`
- datastores should use identity-based access
- both workspace and compute identities may need blob, table, and queue roles
- if the datastores use an app storage account instead of AML default storage,
  grant the roles there too

### Images

The default flow can build a custom image, but if AML-managed builds or Conda
resolution are unstable, prefer a known-good prebuilt image in ACR and point
`AML_IMAGE_NAME` at it.

On Apple Silicon, build for `linux/amd64`.

`azureml-core` may require `setuptools<75` in custom images if imports fail.

### Catalog Action

If the catalog action is enabled:

- the catalog URL should include `/api`
- the target project must already exist
- the target experiment must already exist
- managed-identity auth requires an Application-type app role on the catalog app

## Validation Checklist

Verify all of the following before handoff:

- AML workspace and compute are healthy
- datastores are reachable with identity auth
- image is accessible
- a pipeline submission succeeds
- logs can be retrieved
- configured actions complete successfully

## Local References

- Extended instructions and full troubleshooting: `references/full-guide.md`
- Hardening guidance: `references/hardening.md`
