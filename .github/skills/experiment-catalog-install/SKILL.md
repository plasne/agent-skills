````skill
---
name: experiment-catalog-install
description: Clone, build, and run the Experiment Catalog (plasne/experiment-catalog) locally or in Azure. Provisions an Azure Storage Account, builds the .NET backend and Svelte UI, and starts in the solution. Trigger phrases include "install experiment catalog", "run experiment catalog", "experiment catalog", "experiment catalog dev setup".
---

# Experiment Catalog Installation

The experiment catalog is an open source tool for tracking and analyzing experiments. It provides a structured way to define projects, experiments, permutations, metrics, and results, enabling teams to systematically compare different approaches and configurations.

This skill targets users who have never used the experiment catalog. They may not know what resources are required, what those resources are used for, what configuration options are available, or how to run it once deployed. Provide clear and comprehensive guidance on these topics.

## Guidelines

- Never just stub things out in the configuration, provision everything the user asks for with the appropriate permissions and settings to make it work.

- Never assume you know what to name something or what settings to use. Always ask the user for preferences and guidance on naming, configuration options, and deployment choices.

## Source Code

The experiment catalog is available on GitHub at: <https://github.com/plasne/experiment-catalog>.

You can clone from that location. The folders of interest for installation are:

- catalog
- ui

The other folders are additional tooling and samples, you can ignore those. Additional documentation regarding installation and configuration can be found in the repo. That should be considered the most up-to-date and comprehensive source of information.

This URL has all the configuration options listed: <https://github.com/plasne/experiment-catalog/blob/main/catalog/README.md>.

> **Authoritative source**: The repository README and catalog README are the source of truth for configuration variables, defaults, and supported options. This skill provides a subset for quick guidance. Always fetch the repo docs for the latest details.

There are also video walkthroughs available:

- [Installation](https://youtu.be/KHsnsHpdq00?si=XsN7gJrInF1GvrO-) (6:08)
- [Usage](https://youtu.be/CFwjwU7okl0?si=007W84sZ3tyVRWI6) (30:56)
- [Configuration](https://youtu.be/-ZjgL27pGNk?si=WFFrDMWxGrQK3EZn) (16:36)

## Prerequisites

Before running the experiment catalog, the following must be installed:

- [.NET 10 SDK](https://dotnet.microsoft.com/download/dotnet/10.0) — required to build and run the catalog backend.
- [Node.js 20+](https://nodejs.org/) — required to build the UI.
- [Docker](https://www.docker.com/) — optional, but required for containerized deployment.

For local development, the user also needs the [Azure CLI](https://learn.microsoft.com/cli/azure/install-azure-cli) if using `INCLUDE_CREDENTIAL_TYPES=azcli`.

## Local Deployment

When the user is intending to run the experiment catalog locally, they still need the following Azure resources:

- Azure Storage Account (blob)

The minimum configuration required to run the experiment catalog includes creating an .env file with the following content:

```bash
INCLUDE_CREDENTIAL_TYPES=azcli
AZURE_STORAGE_ACCOUNT_NAME=<your-storage-account>
```

Alternatively, a connection string can be used instead of an account name:

```bash
AZURE_STORAGE_ACCOUNT_CONNSTRING=<your-connection-string>
```

The user will require "Storage Blob Data Contributor" permissions on the storage account (unless using a connection string with account keys).

Use VS Code tasks (`create_and_run_task`) so that each process runs in a visible, interactive terminal the user can monitor. Do **not** use background terminals (`isBackground` on `run_in_terminal`), because the user cannot see or interact with those.

## Azure Deployment

When the user is intending to run the experiment catalog in the Azure cloud, they will need the following Azure resources:

- Azure Storage Account (blob)
- Some solution that can host containers:
  - Azure Container Apps (default if the user has no preference)
  - Azure Kubernetes Service
  - Azure App Service for Containers
  - Azure Virtual Machines with Docker

The hosting solution must have Managed Identity enabled and that identity must have "Storage Blob Data Contributor" permissions on the storage account.

The minimum configuration required to run the experiment catalog includes creating an .env file with the following content:

```bash
INCLUDE_CREDENTIAL_TYPES=mi
AZURE_STORAGE_ACCOUNT_NAME=<your-storage-account>
```

Alternatively, a connection string can be used instead of an account name:

```bash
AZURE_STORAGE_ACCOUNT_CONNSTRING=<your-connection-string>
```

## Docker / Container Image

A pre-built container image is published to the GitHub Container Registry:

```text
ghcr.io/plasne/experiment-catalog/catalog
```

To build the image locally from the repository root (the Dockerfile builds both the UI and API into a single image):

```bash
docker build --rm -t exp-catalog:latest -f catalog.Dockerfile .
```

To run the container:

```bash
docker run -p 6010:6010 \
  -e AZURE_STORAGE_ACCOUNT_CONNSTRING=<your-connection-string> \
  exp-catalog:latest
```

When building on Apple Silicon (arm64) for deployment to Azure (amd64), use `--platform linux/amd64`.

## Port

The catalog API listens on port **6010** by default. When running the API, Swagger documentation is available at `/swagger`. To change the port, set the `PORT` environment variable:

```bash
PORT=<desired-port>
```

## What resources are used for

- Azure Storage Account: This is used to store all experiments. Each experiment will be a container.
- Container hosting solution: This is used to run the experiment catalog application which provides the API and UI for interacting with the experiments stored in Azure Storage.

## UI

The UI can be hosted by the API, separately, or both. There is no downside to allowing the API to host the UI, so you should always do that. You can run `npm run build` and move the artifacts under the `catalog` folder in a `wwwroot` subfolder. There is a script that does this properly you could use or copy from: <https://github.com/plasne/experiment-catalog/blob/main/catalog/refresh-ui.sh>.

If the user is going to be making changes to the UI code, it is recommended to run the UI in development mode using `npm run dev` from the `ui` folder. This will allow for hot reloading and faster development iterations.

## Telemetry

The experiment catalog can output telemetry to Application Insights. To enable this, set the following environment variable:

```bash
OPEN_TELEMETRY_CONNECTION_STRING=<your-connection-string>
```

## Support Documents

When experiments are run, a URL for the output of inference and/or evaluation might be sent to the catalog. The intent is that the user can view the output details to determine why an experiment run produced the results it did. This output could be stored in Azure Blob Storage, and the URL sent to the catalog would be a link to that blob. If the user requests to use this feature, the download must be enabled in the catalog configuration:

```bash
ENABLE_DOWNLOAD=true
```

If the Azure Storage Account being used for support documents is not the same as the one used for experiments, then the user will need to provide the storage account name for support documents as well (in addition, the user and/or managed identity running the catalog will need "Storage Blob Data Contributor" permissions on this storage account):

```bash
AZURE_STORAGE_ACCOUNT_NAME_FOR_SUPPORT_DOCS=<your-storage-account-for-support-docs>
```

## Statistics

If the user requests automatic statistics calculation, the following environment variable must be set:

```bash
CALC_PVALUES_EVERY_X_MINUTES=<number-of-minutes>
```

## Optimization

Append blobs are used for storing experiment results in Azure Storage. This allows for very fast and high concurrency writes (you could have hundreds of evaluation runs all writing to the same experiment at the same time with no performance degradation). However, append blobs will have slow read performance if there are a large number of blocks (each write is a block). To mitigate this, the catalog can automatically optimize blobs (after a period of inactivity) by copying them to a new blob (which has a large block size) and deleting the old one (which may have hundreds or thousands of blocks).

Almost always the first cloud-deployed version of the catalog should have this feature enabled to ensure good read performance. To enable the feature you must set the following environment variable:

```bash
AZURE_STORAGE_OPTIMIZE_EVERY_X_MINUTES=<number-of-minutes>
```

## Cache

To improve performance, the catalog can create an on-disk cache of experiment data. This is not always required, but if the user requests it or their performance is slow, you can enable it by setting the following environment variable:

```bash
AZURE_STORAGE_CACHE_FOLDER=<path-to-cache-folder>
```

A good default for an instance running in a container might be `/tmp/cache`.

## Authentication

The catalog supports three authentication modes:

- **Anonymous** (default): No authentication is required. This is appropriate for local development, testing, or when the catalog runs on localhost as part of an evaluation image. Many users run without auth and this is perfectly fine when the instance is not publicly exposed.
- **EasyAuth**: When hosted in Azure App Service or Container Apps, EasyAuth can be configured with the Microsoft identity provider or an OpenID Connect provider. The catalog can optionally validate the tokens passed by EasyAuth for defense-in-depth. On Container Apps, the token store must be enabled with a blob storage backing for the `X-MS-TOKEN-AAD-ID-TOKEN` header to be forwarded to the application. The app registration must also have `--enable-id-token-issuance true` set.
- **OpenID Connect (OIDC)**: For direct OIDC authentication using providers such as Microsoft Entra ID, Auth0, or Okta. Requires setting `OIDC_AUTHORITY`, `OIDC_CLIENT_ID`, and optionally `OIDC_CLIENT_SECRET`.

The catalog does not have authorization levels — either a user can do everything or nothing.

Full authentication details are in: <https://github.com/plasne/experiment-catalog/blob/main/catalog/auth.md>.

## Multiple Instances

It is fine for multiple API instances to point to the same storage account. This allows for some of these scenarios:

- the catalog is deployed in Azure, and locally for one or more users
- multiple instances of the catalog are deployed in Azure for redundancy or performance
- the catalog is deployed in Azure, but evaluation runs are pushing results to a local instance of the catalog API

However, if multiple instances are running at the same time, only one instance should be calculating statistics (CALC_PVALUES_EVERY_X_MINUTES) and only one instance should be optimizing blobs (AZURE_STORAGE_OPTIMIZE_EVERY_X_MINUTES).

## Deployment Options

Based on the user's input, your recommendations, or asking for guidance, you may deploy these resources using:

- azure-cli commands
- Bicep
- ARM templates
- Terraform
- or any other method

When deploying for production or within a customer environment, consider a desired-state-configuration approach using infrastructure-as-code (Bicep, ARM, Terraform) rather than manual deployment with azure-cli commands.

## Hardening

When deploying for production or within a customer environment, consider defense-in-depth principles to protect the catalog and its data. Detailed hardening recommendations (token validation, network isolation, WAF, managed identity, logging) are in [references/hardening.md](references/hardening.md). Ask the user before applying these measures.

## Troubleshooting

| Issue                                        | Cause                                                         | Solution                                                                                                                                             |
| -------------------------------------------- | ------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------- |
| `dotnet: command not found`                  | .NET SDK missing                                              | Install from <https://dotnet.microsoft.com/download/dotnet/10.0>                                                                                     |
| `node: command not found`                    | Node.js missing                                               | Install from <https://nodejs.org/>                                                                                                                   |
| `az: command not found`                      | Azure CLI missing                                             | Install from <https://learn.microsoft.com/cli/azure/install-azure-cli>                                                                               |
| `docker: command not found`                  | Docker missing                                                | Install from <https://www.docker.com/>                                                                                                               |
| Storage account name rejected                | Not unique or invalid chars                                   | Use 3–24 lowercase alphanumeric; try a different name                                                                                                |
| ACR name rejected                            | Not unique or invalid chars                                   | Use 5–50 alphanumeric; try a different name                                                                                                          |
| `403 Forbidden` on blobs                     | Missing RBAC role                                             | Assign **Storage Blob Data Contributor** to your identity or managed identity                                                                        |
| `403 AuthorizationFailure` right after setup | RBAC propagation delay                                        | Wait 1–5 minutes for the role assignment to propagate, then retry                                                                                    |
| `403` or network error from storage          | Public network access disabled                                | Run `az storage account update --name <name> --resource-group <rg> --public-network-access Enabled`                                                  |
| `KeyBasedAuthenticationNotPermitted`         | Shared key access disabled on the account                     | Use `INCLUDE_CREDENTIAL_TYPES=azcli` with `AZURE_STORAGE_ACCOUNT_NAME` instead of `AZURE_STORAGE_ACCOUNT_CONNSTRING`                                 |
| Port 6010 in use                             | Another process on the same port                              | Set `PORT` to a different value or stop the other process                                                                                            |
| ACR login fails                              | Not authenticated                                             | Run `az acr login --name <acr-name>`                                                                                                                 |
| Container App not reachable                  | Ingress not enabled                                           | Ensure `--ingress external` was passed during creation                                                                                               |
| Image pull fails                             | Registry credentials missing                                  | Ensure `--registry-server` is set and ACR admin is enabled or a managed identity pull is configured                                                  |
| `image OS/Arc must be linux/amd64`           | Image built for wrong platform (e.g., arm64 on Apple Silicon) | Rebuild with `docker build --platform linux/amd64`                                                                                                   |
| `failed to scan dependencies` during `az acr build` | Dockerfile uses `$BUILDPLATFORM` / `$TARGETARCH` args unsupported by ACR | Remove `--platform=$BUILDPLATFORM` and `$TARGETARCH` from the Dockerfile, or build locally with `docker build` and push with `docker push`  |
| `Credential lifetime exceeds max value` when creating app secret | Org policy limits secret duration | Use a shorter `--end-date`, for example `--end-date "$(date -u -v+30d +%Y-%m-%dT%H:%M:%SZ)"`, and adjust until within policy limits               |
| EasyAuth redirect loop                       | Misconfigured redirect URI or missing ID token issuance       | Verify the redirect URI matches `https://<fqdn>/.auth/login/aad/callback` and that `--enable-id-token-issuance true` was set on the app registration |
| `401` despite EasyAuth enabled               | Token validation header mismatch                              | Ensure `OIDC_VALIDATE_HEADER` is set to `X-MS-TOKEN-AAD-ID-TOKEN` (exact case)                                                                      |
| `401` on API calls after EasyAuth login (Container Apps) | Token store not enabled; `X-MS-TOKEN-AAD-ID-TOKEN` header not forwarded | Enable the token store with blob backing: `az containerapp auth update --token-store true --blob-container-uri https://<account>.blob.core.windows.net/tokenstore`. Log out and back in after enabling. |
````
