# CSS Portfolio Analyzer – Senior Azure Infrastructure Version

This repository demonstrates a portfolio statement analyzer MVP and an enterprise-style Azure PaaS infrastructure design for a Senior Cloud Engineer interview.

## What the MVP does

- Imports CSV/PDF depot statements
- Extracts positions
- Calculates total value, weightings, top positions and concentration risks
- Generates an educational investor summary
- Does not let the LLM invent financial numbers

## Senior infrastructure focus

- Azure Container Apps
- Azure Container Registry
- Azure Blob Storage with private endpoint
- Azure Key Vault with private endpoint
- Azure PostgreSQL Flexible Server with private networking
- Azure Service Bus for async processing
- Azure Log Analytics and Application Insights
- Managed Identity and Azure RBAC
- Terraform IaC
- GitHub Actions CI
- Argo CD / GitOps explanation for Kubernetes environments

## Local run

```bash
cd app
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

## Docker

```bash
cd app
docker build -t portfolio-analyzer:local .
docker run -p 8501:8501 portfolio-analyzer:local
```

## Terraform

```bash
cd infra/terraform
terraform init
terraform validate
terraform plan
```

For a real deployment, first push your image to ACR and set:

```bash
terraform apply -var="container_image=<acr-login-server>/portfolio-analyzer:latest"
```

## Interview pitch

I started with a pragmatic MVP, then evolved the infrastructure into an enterprise-ready Azure PaaS design. The application runs on Azure Container Apps. Storage, Key Vault and PostgreSQL are isolated through private networking. Access is handled with Managed Identity and RBAC instead of secrets in code. Service Bus decouples import processing, and observability is handled through Log Analytics and Application Insights. Terraform provisions the platform reproducibly.
