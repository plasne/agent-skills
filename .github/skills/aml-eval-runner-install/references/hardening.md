# Hardening

When deploying for production or within a customer environment, consider defense-in-depth principles to protect the AML Evaluation Runner and its data. The recommendations below are ordered roughly from essential to advanced. You should ask the user before deploying the resources this way.

## Managed Identity and Least Privilege

Use managed identity for all service-to-service authentication. The runner uses a user-assigned managed identity on the AML compute cluster to access the storage account, Key Vault, and Container Registry. Assign only the minimum required RBAC roles:

- **Storage Blob Data Contributor** scoped to the specific storage account (not the resource group or subscription).
- **AcrPull** on the Container Registry for image pulls.
- **Key Vault Secrets User** for accessing secrets such as the Application Insights connection string.

Avoid storing connection strings or account keys. If keys are unavoidable, store them in Azure Key Vault and reference them via Key Vault secret URLs (the runner supports this pattern for `AML_APP_INSIGHTS_CONNECTION_STRING`).

Reference: <https://learn.microsoft.com/en-us/entra/identity/managed-identities-azure-resources/overview>

## Network Isolation

Place the AML workspace, storage account, Key Vault, and Container Registry inside an Azure Virtual Network. Use private endpoints so traffic never traverses the public internet. The `infra/modules/network.bicep` template provisions a VNet with dedicated subnets and private DNS zones for these resources.

Disable public network access on the storage account and Key Vault once private endpoints are in place. Ensure the AML compute cluster subnet has the `Microsoft.MachineLearningServices` delegation configured.

Reference: <https://learn.microsoft.com/en-us/azure/machine-learning/how-to-secure-workspace-vnet>

## Key Vault for Secrets

Store all sensitive values (API keys, connection strings, service tokens) in Azure Key Vault rather than in `.env` files or plain environment variables. The runner already supports Key Vault secret URL references for the Application Insights connection string. Extend this pattern to inference and evaluation secrets using the `INF_OVERRIDE_` and `EVAL_OVERRIDE_` prefixes with Key Vault URLs.

Reference: <https://learn.microsoft.com/en-us/azure/key-vault/general/overview>

## Container Registry Security

Use Azure Container Registry with Premium SKU for private endpoint support. Disable the admin account and use managed identity for image pulls. Scan images for vulnerabilities before pushing to the registry.

Reference: <https://learn.microsoft.com/en-us/azure/container-registry/container-registry-best-practices>

## Diagnostic Logging and Monitoring

Enable diagnostic settings on the AML workspace, storage account, and Key Vault to stream logs to a Log Analytics workspace. The runner integrates with Application Insights via `AML_APP_INSIGHTS_CONNECTION_STRING` for job-level telemetry. Configure alerts for anomalous access patterns, failed authentication attempts, and job failures.

Reference: <https://learn.microsoft.com/en-us/azure/machine-learning/monitor-azure-machine-learning>

## Data Protection

Ground truth data, inference outputs, and evaluation results are stored as immutable artifacts in Azure Storage via AML datastores. Enable blob versioning and soft delete on the storage account to protect against accidental deletion. Consider enabling storage encryption with customer-managed keys for sensitive evaluation data.

Reference: <https://learn.microsoft.com/en-us/azure/storage/blobs/versioning-overview>

## Additional Resources

For a comprehensive checklist covering identity, networking, encryption, and operational security across Azure services, see the Azure Security Baseline documentation:

Reference: <https://learn.microsoft.com/en-us/security/benchmark/azure/overview>
