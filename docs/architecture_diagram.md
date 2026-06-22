# Architecture Diagram

```text
                        Internet
                           |
                           v
              Azure Container Apps Ingress
                           |
                           v
              Streamlit Portfolio Analyzer
                 /        |        |       \
                v         v        v        v
        Blob Storage   PostgreSQL  Service Bus  App Insights
        Private EP     Private     Queue        Log Analytics
                       Subnet

Security:
- Managed Identity
- RBAC
- Key Vault
- Private Endpoints

Platform:
- Terraform
- Azure Container Registry
- GitHub Actions
- Optional Argo CD for Kubernetes
```
