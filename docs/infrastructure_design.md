# Senior Cloud Engineer Infrastructure Design

## Architecture

```text
Internet User
    |
Azure Container Apps external ingress
    |
Streamlit Portfolio Analyzer container
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
- Storage and Key Vault public network disabled

Platform:
- Azure Container Registry
- Terraform
- Multiple revision mode
- Monitor alert for restarts
```

## Why this is senior-level

### Network isolation

The infrastructure has a dedicated VNet with separate subnets for:

- Container Apps
- Private Endpoints
- PostgreSQL

### Private endpoints

Blob Storage and Key Vault are not publicly reachable.

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

Container Apps uses multiple revisions, enabling rollback and traffic splitting.

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
