#!/usr/bin/env bash
set -euo pipefail
: "${AZURE_RESOURCE_GROUP:?Set AZURE_RESOURCE_GROUP}"
: "${AZURE_ML_WORKSPACE:?Set AZURE_ML_WORKSPACE}"
: "${ML_ENDPOINT_NAME:?Set ML_ENDPOINT_NAME}"
# Explicit invocation of this script deletes the named billable endpoint only.
az ml online-endpoint delete --name "$ML_ENDPOINT_NAME" --resource-group "$AZURE_RESOURCE_GROUP" --workspace-name "$AZURE_ML_WORKSPACE" --yes
echo 'Endpoint deleted. The portal remains, but predictions require redeployment. Delete the resource group after grading.'
