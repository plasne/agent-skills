---
name: gtc-install
description: Clone, build, and run the Ground Truth Curator (andrewDoing/GroundTruthCurator). Starts the Cosmos DB Emulator, initializes containers, builds the Python backend and React frontend, and runs in consolidated or development mode. Trigger phrases include "install GTC", "run ground truth curator", "GTC", "GTC dev setup".
---

## Execution Model

> [!IMPORTANT]
> Do not execute this skill directly in the main thread. Delegate each discrete
> task to its own sub-agent and pass this skill path to that sub-agent.

Use phases for larger requests:

1. discovery and plan
2. infrastructure or emulator setup
3. auth setup
4. app deployment and health checks
5. data import or workflow setup
6. validation and handoff

Keep the main thread as coordinator, checkpoint important IDs and URLs in session
artifacts, and summarize successful long-running work instead of replaying full
logs.

# Ground Truth Curator Installation

Use this skill to stand up GTC locally or in Azure. Keep the hot path here and
open `references/full-guide.md` for exhaustive commands and the long
troubleshooting catalog.

## Ask the User First

Before deploying, confirm:

- local vs Azure deployment
- region, resource group, naming prefix, and hosting choice
- whether auth should be enabled
- whether the user wants shared resources with other apps
- whether demo or real ground truths will be loaded

Never invent names or security settings without user direction.

## Source Code

Repo: <https://github.com/andrewDoing/GroundTruthCurator>

You MUST use the release version 1.1.0 (<https://github.com/andrewDoing/GroundTruthCurator/releases/tag/1.1.0>).

Focus on:

- `backend`
- `frontend`
- `infra`

Treat the repo README plus component READMEs as the source of truth for repo
behavior. Use this file as the operator summary.

## Fast Path

### Local

1. Start the Cosmos DB Emulator.
2. Install backend dependencies and initialize Cosmos containers.
3. Configure env files.
4. Run backend.
5. Install frontend dependencies and run frontend.
6. Optionally seed sample data.

Use the exact commands in `references/full-guide.md`.

### Azure

Provision at minimum:

- Azure Cosmos DB for NoSQL
- container hosting, usually Azure Container Apps
- a container image for the backend
- app registration and token configuration if auth is enabled
- token-store backing storage if Container Apps EasyAuth is used

Default recommendation for public Azure deployments:

- Azure Container Apps
- managed identity
- public ingress with auth enabled
- RBAC instead of connection strings where possible

## Critical Configuration

### Ports

- Backend container listens on `8080`.
- Frontend dev server typically uses Vite defaults.
- Cosmos DB Emulator commonly uses `8081`.

If the Container App ingress target port is set to `8000` instead of `8080`,
the app may look healthy while requests fail.

### Authentication

For Azure Container Apps + EasyAuth:

- enable `GTC_EZAUTH_ENABLED=true`
- set `GTC_AUTH_MODE=entra`
- configure the Container App auth settings and app registration
- use a system-assigned identity on the Container App
- enable a blob-backed token store when relying on EasyAuth token headers

Keep these gotchas inline because they are high-frequency failures:

- `allowedAudiences` should include both `<appId>` and `api://<appId>`
- `allowedApplications` must include Azure CLI if `az account get-access-token`
  will be used
- Container Apps auth patching is more reliable with the `2025-07-01` auth API
- `unauthenticatedClientAction` should be `RedirectToLoginPage` for browser UX

For programmatic access, acquire a token with:

```bash
az account get-access-token --resource api://<appId>
```

### Data Model and Storage

- GTC ground truths use the GTC v2 shape with a `history` array.
- Do not seed top-level `question` and `answer` fields directly.
- If Azure Cosmos DB public network access is disabled, Container Apps egress can
  break live workflows such as `Request More` unless networking is configured
  explicitly.

## Validation Checklist

Verify all of the following before handoff:

- backend health endpoint works
- frontend loads
- auth succeeds if enabled
- a bearer token can call a protected API if required
- Cosmos reads and writes succeed
- the target user workflow works end to end, not just health checks

## Local References

- Extended instructions and full troubleshooting: `references/full-guide.md`
- Hardening guidance: `references/hardening.md`
