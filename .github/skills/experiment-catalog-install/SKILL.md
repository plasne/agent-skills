---
name: experiment-catalog-install
description: Clone, build, and run the Experiment Catalog (plasne/experiment-catalog) locally or in Azure. Provisions an Azure Storage Account, builds the .NET backend and Svelte UI, and starts in the solution. Trigger phrases include "install experiment catalog", "run experiment catalog", "experiment catalog", "experiment catalog dev setup".
---

## Execution Model

> [!IMPORTANT]
> Do not execute this skill directly in the main thread. Delegate each discrete
> task to its own sub-agent and pass this skill path to that sub-agent.

Use phases for larger requests:

1. discovery and plan
2. storage and hosting setup
3. auth and app registration setup
4. deployment and verification
5. integration or data setup
6. validation and handoff

Keep the main thread as coordinator, store important IDs and URLs in session
artifacts, and summarize successful long-running work.

# Experiment Catalog Installation

Use this skill to deploy the catalog locally or in Azure. Keep the hot path in
this file. Open `references/full-guide.md` for detailed procedures and the full
troubleshooting matrix.

## Ask the User First

Before deploying, confirm:

- local vs Azure deployment
- region, resource group, naming, and hosting choice
- whether auth should be enabled
- whether support-document download is needed
- whether this instance will receive AML runner results

Never invent names or security settings without user input.

## Source Code

Repo: <https://github.com/plasne/experiment-catalog>

Focus on:

- `catalog`
- `ui`

The repo README and `catalog/README.md` are authoritative for configuration.

## Fast Path

### Local

Minimum Azure dependency:

- one Azure Storage Account

Minimum env:

```bash
INCLUDE_CREDENTIAL_TYPES=azcli
AZURE_STORAGE_ACCOUNT_NAME=<storage-account>
```

The user needs `Storage Blob Data Contributor` on that account.

### Azure

Minimum resources:

- Azure Storage Account
- container host, usually Azure Container Apps
- managed identity on the host

Minimum env:

```bash
INCLUDE_CREDENTIAL_TYPES=mi
AZURE_STORAGE_ACCOUNT_NAME=<storage-account>
```

Default recommendation for Azure:

- use the published GHCR image
- let the API host the UI
- enable auth for publicly reachable deployments
- enable blob optimization on the first cloud instance

## Critical Configuration

### Port

The API listens on `6010` by default.

### Image Choice

Prefer the published image:

```text
ghcr.io/plasne/experiment-catalog/catalog
```

`az acr build` is a poor default for this repo because the Dockerfile uses
BuildKit variables that ACR strips silently.

### Authentication

Supported modes:

- anonymous
- EasyAuth
- OIDC

For Entra ID / OIDC, keep these gotchas inline:

- `OIDC_AUDIENCES` should include both `<appId>` and `api://<appId>`
- register `https://<fqdn>/auth/callback` for browser login
- if EasyAuth is also enabled, also register
  `https://<fqdn>/.auth/login/aad/callback`
- create delegated scopes before adding pre-authorized applications
- managed identities need an Application-type app role, not just a delegated
  scope
- if using Container Apps EasyAuth token headers, enable the token store

For programmatic access, use:

```bash
az account get-access-token --resource api://<appId>
```

## AML Runner Integration

If this catalog will receive AML runner results:

- create the project first
- create the experiment first
- keep the experiment name aligned with `AML_EXPERIMENT_NAME`
- remember the runner posts results only; it does not create projects or
  experiments
- use the `/api` path suffix in the catalog base URL provided to the runner

## Validation Checklist

Verify all of the following before handoff:

- UI loads
- API responds
- storage reads and writes succeed
- auth succeeds if enabled
- a bearer token works for API calls if required
- AML integration targets an existing project and experiment if used

## Local References

- Extended instructions and full troubleshooting: `references/full-guide.md`
- Hardening guidance: `references/hardening.md`
