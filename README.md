# Example Azure Depot PDF – Senior Azure Infrastructure Version

Example Azure Depot PDF demonstrates a portfolio statement analyzer MVP and an enterprise-style Azure PaaS infrastructure design for a Senior Cloud Engineer interview.

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
docker build -t example-azure-depot-pdf:local .
docker run -p 8501:8501 example-azure-depot-pdf:local
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
terraform apply -var="container_image=<acr-login-server>/example-azure-depot-pdf:latest"
```

## Interview pitch

I started with a pragmatic MVP, then evolved the infrastructure into an enterprise-ready Azure PaaS design. The application runs on Azure Container Apps. Storage, Key Vault and PostgreSQL are isolated through private networking. Access is handled with Managed Identity and RBAC instead of secrets in code. Service Bus decouples import processing, and observability is handled through Log Analytics and Application Insights. Terraform provisions the platform reproducibly.

## Project naming

The display name is **Example Azure Depot PDF**; Docker images and Terraform resource names use `example-azure-depot-pdf`. The `app/portfolio` package retains its domain name because the portfolio analysis logic is unchanged.

The JSON files in `infra/terraform` are reference snapshots, not live Azure inventory. Renaming local configuration does not rename deployed resources. Review a Terraform plan before applying: resource name changes can require replacement.

## Deploying to the replacement subscription

The active subscription is **Example Azure Depot PDF**. Use the `azure-depot-pdf` Terraform workspace for this subscription; the `default` workspace contains historical state for the old subscription and must not be applied to the replacement subscription. Local workspace state is stored under `infra/terraform/terraform.tfstate.d/` and must be backed up securely. It contains credentials and is excluded from Git.

```bash
scripts/deploy-azure.sh <subscription-id>
```

This script bootstraps ACR, builds the application remotely for Linux/AMD64, creates a plan using the real image, and applies it. It incurs Azure usage charges. Required resource providers must be registered first. The script saves the selected subscription and image in the Git-ignored `infra/terraform/deployment.auto.tfvars.json` for subsequent Terraform commands. The application uses single revision mode, 0.5 vCPU / 1 GiB, and exactly one replica so Streamlit sessions and file uploads remain on the same instance.

### Runtime verification

The public application URL is available from:

```bash
terraform -chdir=infra/terraform output -raw container_app_url
```

Streamlit exposes its health endpoint at `/_stcore/health`. Upload `samples/sample_depot.csv` to verify the complete import and analysis flow. The expected total is **16,700.00**.

The runtime explicitly selects the user-assigned managed identity through `AZURE_CLIENT_ID`. PyArrow is pinned to a NumPy-compatible version so Streamlit can render the position tables. Neither change alters portfolio calculations.
