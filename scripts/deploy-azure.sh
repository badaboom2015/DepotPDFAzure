#!/usr/bin/env bash
set -euo pipefail

subscription_id="${1:?Usage: scripts/deploy-azure.sh <subscription-id>}"
repo_dir="$(cd "$(dirname "$0")/.." && pwd)"
terraform_dir="$repo_dir/infra/terraform"
export ARM_SUBSCRIPTION_ID="$subscription_id"
export ARM_SKIP_PROVIDER_REGISTRATION=true

az account show --subscription "$subscription_id" --output none
terraform -chdir="$terraform_dir" init -input=false
if ! terraform -chdir="$terraform_dir" workspace select azure-depot-pdf; then
  terraform -chdir="$terraform_dir" workspace new azure-depot-pdf
fi

# Refuse to reuse an existing workspace for a different subscription.
state_file="$(mktemp)"
trap 'rm -f "$state_file"' EXIT
if terraform -chdir="$terraform_dir" state pull > "$state_file"; then
  python3 - "$state_file" "$subscription_id" <<'PYGUARD'
import json, sys
state = json.load(open(sys.argv[1]))
expected = '/subscriptions/' + sys.argv[2].lower() + '/'
for resource in state.get('resources', []):
    if resource.get('type') == 'azurerm_resource_group':
        for instance in resource.get('instances', []):
            actual = instance.get('attributes', {}).get('id', '').lower()
            if actual and not actual.startswith(expected):
                raise SystemExit('Workspace belongs to another subscription; refusing to apply.')
PYGUARD
fi

# Bootstrap the registry so the app image exists before Container Apps pulls it.
terraform -chdir="$terraform_dir" apply -input=false -auto-approve \
  -target=azurerm_container_registry.main \
  -var="subscription_id=$subscription_id" \
  -var='container_image=example-azure-depot-pdf:pending-build'
registry_server="$(terraform -chdir="$terraform_dir" output -raw acr_login_server)"
registry_name="${registry_server%%.*}"
image_tag="$(date -u +%Y%m%d%H%M%S)"
image_path="example-azure-depot-pdf:$image_tag"
az acr build --subscription "$subscription_id" --registry "$registry_name" \
  --platform linux/amd64 --image "$image_path" "$repo_dir/app"
python3 - "$terraform_dir/deployment.auto.tfvars.json" "$subscription_id" "$registry_server/$image_path" <<'PYVARS'
import json, sys
with open(sys.argv[1], 'w') as output:
    json.dump({'subscription_id': sys.argv[2], 'container_image': sys.argv[3]}, output, indent=2)
    output.write('\n')
PYVARS
terraform -chdir="$terraform_dir" plan -input=false -out=deployment.tfplan
terraform -chdir="$terraform_dir" apply -input=false deployment.tfplan
terraform -chdir="$terraform_dir" output -raw container_app_url
