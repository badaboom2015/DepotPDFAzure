# Senior Cloud Engineer Infrastructure Design

## Architecture

```text
Internet User
    |
Azure Container Apps external ingress
    |
Streamlit Example Azure Depot PDF container
    |
    +--> Blob Storage via Private Endpoint
    +--> PostgreSQL Flexible Server via private delegated subnet
    +--> Service Bus Queue for async import processing
    +--> Application Insights / Log Analytics

Security:
- User Assigned Managed Identity
- Azure RBAC
- Key Vault with RBAC
- Private Endpoints
- Key Vault public network disabled
- Blob Storage has a private endpoint; its public endpoint remains enabled for Terraform data-plane management, with private containers and authenticated access

Platform:
- Azure Container Registry
- Terraform
- Single revision mode
- Monitor alert for restarts
```

## level

### Network isolation

The infrastructure has a dedicated VNet with separate subnets for:

- Container Apps
- Private Endpoints
- PostgreSQL

### Private endpoints

Key Vault is not publicly reachable. Blob Storage has a private endpoint for application access; its public endpoint remains enabled so Terraform can manage the uploads container from outside the VNet. Anonymous access is disabled.

### Managed Identity

The app receives permissions via User Assigned Managed Identity instead of hardcoded credentials.

### RBAC

The app has specific roles:

- AcrPull
- Storage Blob Data Contributor
- Key Vault Secrets User

### PostgreSQL Flexible Server

The database is deployed with private networking in a delegated subnet.

### Service Bus

The import flow can be decoupled from the UI and scaled independently.

### Observability

Log Analytics and Application Insights are provisioned. A metric alert tracks unexpected restarts.

### Deployment strategy

Container Apps uses single revision mode so a new healthy revision replaces the previous revision without keeping additional revisions running.

## Terraform vs Argo CD

Terraform provisions Azure infrastructure.

Argo CD would be used if the workload runs on Kubernetes:

```text
GitHub Actions builds image
    |
Container Registry
    |
Helm/Kustomize manifests
    |
Argo CD sync
    |
Kubernetes platform
```

## Interview explanation

I first built a working MVP, then evolved the platform design into an enterprise-ready Azure PaaS architecture. The app runs on Container Apps. Data services are protected by private networking. Access is based on Managed Identity and RBAC. Service Bus decouples import processing, and Log Analytics/Application Insights provide observability. Terraform makes the platform reproducible.
