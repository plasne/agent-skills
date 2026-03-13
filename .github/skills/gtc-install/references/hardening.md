# Hardening

When deploying for production or within a customer environment, consider defense-in-depth principles to protect the Ground Truth Curator and its data. The recommendations below are ordered roughly from essential to advanced. You should ask the user before deploying the resources this way.

## Token Validation

Even when using Azure App Service Authentication (EasyAuth), the application should validate the JWT signature and claims on incoming tokens. EasyAuth can be bypassed in certain network configurations, and relying solely on it leaves a gap if traffic reaches the app through an unexpected path. Validate the `iss`, `aud`, and `exp` claims at minimum. The GTC backend supports `GTC_EZAUTH_ENABLED=true` for EasyAuth integration.

Reference: <https://learn.microsoft.com/en-us/azure/app-service/overview-authentication-authorization>

## Network Isolation

Place the container host and Cosmos DB account inside an Azure Virtual Network. Use private endpoints for Cosmos DB so traffic never traverses the public internet. Disable public network access on the Cosmos DB account once private endpoints are in place.

When the architecture has distinct tiers (front-end, API, database), isolate each tier in its own subnet and apply Network Security Groups (NSGs) that allow only the required traffic between tiers. For example, the API subnet should accept inbound traffic only from the front-end subnet (or the reverse proxy subnet), and the Cosmos DB subnet should accept inbound traffic only from the API subnet.

Reference: <https://learn.microsoft.com/en-us/azure/cosmos-db/how-to-configure-private-endpoints>

## Reverse Proxy / Web Application Firewall

Place Azure Front Door or Azure Application Gateway with WAF in front of the GTC endpoint. This provides DDoS protection, TLS termination, and OWASP rule-based filtering. Lock down the container host so it only accepts traffic from the reverse proxy (for example, using access restrictions or NSGs that allow only the Front Door service tag or the Application Gateway subnet).

Reference: <https://learn.microsoft.com/en-us/azure/frontdoor/front-door-overview>
Reference: <https://learn.microsoft.com/en-us/azure/web-application-firewall/overview>

## Managed Identity and Least Privilege

Use managed identity for all service-to-service authentication. The GTC backend supports Azure AD authentication for Cosmos DB via `--use-aad` in the container manager script and `DefaultAzureCredential` at runtime. Assign only the minimum required RBAC roles (for example, Cosmos DB built-in data roles scoped to the specific database, not at the account or subscription level). Avoid storing connection strings or account keys; if keys are unavoidable, store them in Azure Key Vault and reference them via Key Vault references.

Reference: <https://learn.microsoft.com/en-us/entra/identity/managed-identities-azure-resources/overview>

## Diagnostic Logging and Monitoring

Enable diagnostic settings on the Cosmos DB account and container host to stream logs to a Log Analytics workspace. The GTC backend supports OpenTelemetry export to Azure Monitor via `GTC_AZ_MONITOR_CONNECTION_STRING`. Configure alerts for anomalous access patterns, failed authentication attempts, and unexpected changes to network or RBAC configuration.

Reference: <https://learn.microsoft.com/en-us/azure/cosmos-db/monitor>

## Additional Resources

For a comprehensive checklist covering identity, networking, encryption, and operational security across Azure services, see the Azure Security Baseline documentation:

Reference: <https://learn.microsoft.com/en-us/security/benchmark/azure/overview>
