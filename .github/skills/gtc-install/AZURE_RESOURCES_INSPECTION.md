# Azure Resources Inspection - Detailed Reference

## Subscription & Tenant Information
- **Subscription ID**: `50cff123-a1a7-466f-b103-2cb28dee6c62`
- **Tenant ID**: `16b3c013-d300-468d-ac64-7eda0820b6d3`
- **Resource Group**: `pelasne-eval-12` (eastus2)
- **Resource Group ID**: `/subscriptions/50cff123-a1a7-466f-b103-2cb28dee6c62/resourceGroups/pelasne-eval-12`

---

## Resource IDs & Details

### Container Apps Environment
- **Name**: `eval12-cae`
- **Status**: ✅ Succeeded
- **Location**: East US 2
- **Static IP**: `20.122.234.68`
- **Resource ID**: `/subscriptions/50cff123-a1a7-466f-b103-2cb28dee6c62/resourceGroups/pelasne-eval-12/providers/Microsoft.App/managedEnvironments/eval12-cae`

### Container App (GTC)
- **Name**: `eval12-gtc`
- **Status**: ✅ Succeeded
- **FQDN**: `eval12-gtc.bluemoss-1148c3da.eastus2.azurecontainerapps.io`
- **Image**: `eval12acr.azurecr.io/gtc-backend:latest`
- **Ingress Target Port**: `8080`
- **External**: `true` (publicly accessible)
- **Transport**: `Auto`
- **Allow Insecure**: `false`
- **Resource ID**: `/subscriptions/50cff123-a1a7-466f-b103-2cb28dee6c62/resourceGroups/pelasne-eval-12/providers/Microsoft.App/containerapps/eval12-gtc`

#### Container App Identities
**System-Assigned**:
- Principal ID: `6e0303d4-0249-4754-9c1d-43d38e121021`
- Type: `SystemAssigned`

**User-Assigned**:
- Name: `eval12-gtc-mi`
- Principal ID: `3e0bea3a-a1da-48f8-ba06-bf1f0eb964e9`
- Client ID: `ed923a5b-38bc-4766-93dd-922b0c761774`
- Resource ID: `/subscriptions/50cff123-a1a7-466f-b103-2cb28dee6c62/resourcegroups/pelasne-eval-12/providers/Microsoft.ManagedIdentity/userAssignedIdentities/eval12-gtc-mi`

#### Container App Environment Variables
```
GTC_REPO_BACKEND=cosmos
GTC_COSMOS_ENDPOINT=https://eval12gtccosmos01.documents.azure.com:443/
GTC_COSMOS_DB_NAME=gt-curator
GTC_COSMOS_CONTAINER_GT=ground_truth
GTC_COSMOS_CONTAINER_ASSIGNMENTS=assignments
GTC_COSMOS_CONTAINER_TAGS=tags
GTC_COSMOS_CONTAINER_TAG_DEFINITIONS=tag_definitions
GTC_AZ_MONITOR_CONNECTION_STRING=InstrumentationKey=aee74dbf-5259-424c-8849-471d024be9d6;IngestionEndpoint=https://eastus2-3.in.applicationinsights.azure.com/;LiveEndpoint=https://eastus2.livediagnostics.monitor.azure.com/;ApplicationId=e11c304a-69d4-464b-9507-60d75531e8d1
APPLICATIONINSIGHTS_CONNECTION_STRING=InstrumentationKey=aee74dbf-5259-424c-8849-471d024be9d6;IngestionEndpoint=https://eastus2-3.in.applicationinsights.azure.com/;LiveEndpoint=https://eastus2.livediagnostics.monitor.azure.com/;ApplicationId=e11c304a-69d4-464b-9507-60d75531e8d1
GTC_EXPORT_STORAGE_BACKEND=blob
GTC_EXPORT_BLOB_ACCOUNT_URL=https://eval12sharedsa.blob.core.windows.net
GTC_EXPORT_BLOB_CONTAINER=groundtruths
GTC_EZAUTH_ENABLED=true
GTC_AUTH_MODE=entra
GTC_EZAUTH_ALLOW_ANONYMOUS_PATHS=/healthz,/metrics
AZURE_CLIENT_ID=ed923a5b-38bc-4766-93dd-922b0c761774
```

#### Container Registry Configuration
- **Server**: `eval12acr.azurecr.io`
- **Authentication**: Identity-based (using `eval12-gtc-mi`)
- **Username**: (empty)
- **Password Secret Reference**: (empty)
- **Identity Used**: `/subscriptions/50cff123-a1a7-466f-b103-2cb28dee6c62/resourcegroups/pelasne-eval-12/providers/Microsoft.ManagedIdentity/userAssignedIdentities/eval12-gtc-mi`

#### Container App Secrets
- `microsoft-provider-authentication-secret` (for Azure AD provider)

#### Container App Authentication Settings
- **Platform Enabled**: `true`
- **Global Validation - Unauthenticated Action**: `RedirectToLoginPage`
- **Excluded Paths**: `/healthz`, `/metrics`

**Azure AD Configuration**:
- **App Registration Client ID**: `a58e7dbb-6413-44d2-b247-0a87f90d2613`
- **Tenant**: `16b3c013-d300-468d-ac64-7eda0820b6d3`
- **Issuer**: `https://login.microsoftonline.com/16b3c013-d300-468d-ac64-7eda0820b6d3/v2.0`
- **Allowed Audiences**: 
  - `a58e7dbb-6413-44d2-b247-0a87f90d2613`
  - `api://a58e7dbb-6413-44d2-b247-0a87f90d2613`
- **Allowed Applications**: `04b07795-8ddb-461a-bbee-02f9e1bf7b46` (Azure CLI)

**Token Store**:
- **Enabled**: `true`
- **Storage Type**: Azure Blob Storage
- **Container URI**: `https://eval12sharedsa.blob.core.windows.net/gtc-tokenstore`

---

### Container Registry (ACR)
- **Name**: `eval12acr`
- **Status**: ✅ Succeeded
- **Location**: `eastus2`
- **SKU**: `Basic` (Tier: Basic)
- **Login Server**: `eval12acr.azurecr.io`
- **Repositories**: `gtc-backend`
- **Resource ID**: `/subscriptions/50cff123-a1a7-466f-b103-2cb28dee6c62/resourceGroups/pelasne-eval-12/providers/Microsoft.ContainerRegistry/registries/eval12acr`

---

### Storage Account
- **Name**: `eval12sharedsa`
- **Kind**: `StorageV2`
- **SKU**: `Standard_LRS`
- **Location**: `eastus2`
- **Resource ID**: `/subscriptions/50cff123-a1a7-466f-b103-2cb28dee6c62/resourceGroups/pelasne-eval-12/providers/Microsoft.Storage/storageAccounts/eval12sharedsa`

**Blob Endpoints**:
- Account: `https://eval12sharedsa.blob.core.windows.net`
- Token Store Container: `https://eval12sharedsa.blob.core.windows.net/gtc-tokenstore`
- Export Container: `https://eval12sharedsa.blob.core.windows.net/groundtruths`

---

### Cosmos DB Account
- **Name**: `eval12gtccosmos01`
- **Status**: ✅ Succeeded
- **Location**: `East US 2`
- **Document Endpoint**: `https://eval12gtccosmos01.documents.azure.com:443/`
- **Account Type**: `Standard`
- **Capabilities**: `EnableServerless`
- **Default Identity**: `FirstPartyIdentity` (key-based auth enabled)
- **Disable KeyBased Metadata Write Access**: `false` (keys enabled)
- **Public Network Access**: `Enabled`
- **Resource ID**: `/subscriptions/50cff123-a1a7-466f-b103-2cb28dee6c62/resourceGroups/pelasne-eval-12/providers/Microsoft.DocumentDB/databaseAccounts/eval12gtccosmos01`

#### Database
- **Name**: `gt-curator`
- **Database ID**: `/subscriptions/50cff123-a1a7-466f-b103-2cb28dee6c62/resourceGroups/pelasne-eval-12/providers/Microsoft.DocumentDB/databaseAccounts/eval12gtccosmos01/sqlDatabases/gt-curator`

#### Containers
1. **ground_truth**
   - Partition Key Path: `/datasetName`

2. **assignments**
   - Partition Key Path: `/pk`

3. **tags**
   - Partition Key Path: `/pk`

4. **tag_definitions**
   - Partition Key Path: `/tag_key`

---

### Application Insights
- **Name**: `eval12-appinsights`
- **Location**: `eastus2`
- **Instrumentation Key**: `aee74dbf-5259-424c-8849-471d024be9d6`
- **Application ID**: `e11c304a-69d4-464b-9507-60d75531e8d1`
- **Ingestion Endpoint**: `https://eastus2-3.in.applicationinsights.azure.com/`
- **Live Diagnostics Endpoint**: `https://eastus2.livediagnostics.monitor.azure.com/`
- **Resource ID**: `/subscriptions/50cff123-a1a7-466f-b103-2cb28dee6c62/resourceGroups/pelasne-eval-12/providers/Microsoft.Insights/components/eval12-appinsights`

---

### User-Assigned Managed Identity (eval12-gtc-mi)
- **Name**: `eval12-gtc-mi`
- **Location**: `eastus2`
- **Principal ID**: `3e0bea3a-a1da-48f8-ba06-bf1f0eb964e9`
- **Client ID**: `ed923a5b-38bc-4766-93dd-922b0c761774`
- **Resource ID**: `/subscriptions/50cff123-a1a7-466f-b103-2cb28dee6c62/resourcegroups/pelasne-eval-12/providers/Microsoft.ManagedIdentity/userAssignedIdentities/eval12-gtc-mi`

#### Role Assignments
1. **AcrPull**
   - **Scope**: `/subscriptions/50cff123-a1a7-466f-b103-2cb28dee6c62/resourceGroups/pelasne-eval-12/providers/Microsoft.ContainerRegistry/registries/eval12acr`
   - **Resource**: `eval12acr`
   - **Purpose**: Pull container images

2. **Storage Blob Data Contributor**
   - **Scope**: `/subscriptions/50cff123-a1a7-466f-b103-2cb28dee6c62/resourceGroups/pelasne-eval-12/providers/Microsoft.Storage/storageAccounts/eval12sharedsa`
   - **Resource**: `eval12sharedsa`
   - **Purpose**: Read/write blob data

---

## Related Resources in Resource Group

- **Key Vault**: `eval12-kv01` (eastus2)
- **Log Analytics Workspace**: `eval12-logs` (eastus2)
- **Alternative Container App**: `eval12-catalog` (eastus2)
- **Alternative UAMI**: `eval12-aml-mi` (eastus2)
- **Azure ML Workspace**: `eval12-aml` (eastus2)
- **Alert Rule**: `Failure Anomalies - eval12-appinsights` (global)

---

## Access Control Summary

| Service | Authentication Method | Identity | Access Level |
|---------|----------------------|----------|--------------|
| ACR | Identity-based (RBAC) | eval12-gtc-mi | AcrPull |
| Blob Storage | Identity-based (RBAC) | eval12-gtc-mi | Storage Blob Data Contributor |
| Cosmos DB | Key-based (Account Keys) | (keys in config/connection string) | Full |
| App Insights | Connection String | (static connection string) | Instrumentation |

---

## Inspection Status
✅ **All resources exist and are operational**
✅ **No modifications were made**
✅ **All specified resources verified**

Generated: Using Azure CLI
