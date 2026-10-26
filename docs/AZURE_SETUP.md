# Azure deployment runbook

Cloud provisioning is underway in this workspace on an active trial subscription. This reusable runbook describes the full process; the README records which steps have actually completed. Account creation/payment/terms are completed by the account owner. Use [Azure account setup](https://azure.microsoft.com/en-us/free/) and check eligibility/terms directly; no credit or quota availability is assumed for a different account.

## 1. Tools, login and scope

Install the official [Azure CLI](https://learn.microsoft.com/en-us/cli/azure/install-azure-cli), Python 3.10/3.11, Node 22, and Git. For SQL, the loader uses Microsoft ODBC Driver 18 when installed, or the TLS-enabled Python TDS driver from `requirements-azure.txt` otherwise. A cloud workstation/Cloud Shell can be used if local tools are unavailable. The deployment identity needs resource creation plus the ability to list Cosmos/ML keys and update SWA settings.

```bash
az login
az account list --output table
az account set --subscription '<your-subscription-id>'
az extension add --name ml --upgrade
az bicep install
export AZURE_SUBSCRIPTION_ID='<your-subscription-id>'
export AZURE_RESOURCE_GROUP='contoso-delay-assignment'
export AZURE_ML_COMPUTE='cpu-cluster'
az group create --name "$AZURE_RESOURCE_GROUP" --location centralindia
```

Use a dedicated group. Check regional availability/quota for the training VM (`Standard_DS3_v2`) and endpoint (`Standard_DS2_v2`) before training; AutoML and endpoint quota may differ. Record substitutions in README. The Static Web App has a separate region parameter because regional availability differs.

## 2. Provision infrastructure and budget

Retrieve your Entra object ID and principal name, and determine your current public IPv4 address from your network settings/service. No passwords are required for SQL.

```bash
az ad signed-in-user show --query '{objectId:id,login:userPrincipalName}'
az deployment group what-if --resource-group "$AZURE_RESOURCE_GROUP" \
  --template-file infra/main.bicep \
  --parameters adminObjectId='<object-id>' adminLogin='<principal-name>' clientIp='<public-ipv4>'
az deployment group create --resource-group "$AZURE_RESOURCE_GROUP" \
  --name contoso-infra --template-file infra/main.bicep \
  --parameters adminObjectId='<object-id>' adminLogin='<principal-name>' clientIp='<public-ipv4>'
az deployment group show -g "$AZURE_RESOURCE_GROUP" -n contoso-infra --query properties.outputs
```

The template creates Entra-only SQL with one client-IP firewall rule, serverless Cosmos, the two containers, ML workspace/dependencies, a 0–1-node cluster, Application Insights, and a Free Static Web App. Resource group creation does not deploy a billable ML endpoint yet. Review the what-if before the create command; costs begin when resources are provisioned/used.

Create a monthly budget, choosing an amount in the subscription's billing currency. This is an alert, not a spending limit. Use the first day of the current month and an appropriate end date:

```bash
az deployment group create -g "$AZURE_RESOURCE_GROUP" --name contoso-budget \
  --template-file infra/budget.bicep \
  --parameters amount=1000 email='<your-alert-email>' \
  startDate='2026-10-01T00:00:00Z' endDate='2027-10-01T00:00:00Z'
```

Set the following **nonsecret** values from the deployment outputs:

```bash
export SQL_SERVER='<sqlServer output>'
export SQL_DATABASE='contoso'
export AZURE_ML_WORKSPACE='<mlWorkspace output>'
export COSMOS_ACCOUNT='<cosmosAccount output>'
export SWA_NAME='<staticWebApp output>'
export ML_ENDPOINT_NAME='<choose-a-globally-unique-endpoint-name>'
.venv/bin/python -m pip install -r requirements-azure.txt
npm ci --prefix api
```

The Bicep SQL admin is a User principal; adjust it deliberately if your organization requires an Entra group/service principal. Your current IP must remain permitted when loading/exporting. Verify Entra-only status in Azure's SQL authentication panel.

## 3. SQL import, analysis and export

```bash
.venv/bin/python sql/load_data.py
.venv/bin/python ml/export_data.py
```

The loader creates the schema/table/view, refuses a nonempty table, imports 10,000 rows, and saves real query output to `evidence/azure-sql-analysis.json`. Use Query Editor or your SQL client to run `sql/analysis.sql` and screenshot the count and each result. Never use the local CSV analysis as proof that Azure SQL was loaded. The export reads the view and emits `ml/export/full.csv`, `train/{MLTable,data.csv}`, `test/{MLTable,data.csv}` and provenance.

If loading fails before the commit, it rolls back. If a later evidence query fails after import committed, inspect the table and rerun the analysis separately; do not delete/reimport merely to obtain screenshots.

## 4. Train AutoML and evaluate both candidates

```bash
.venv/bin/python ml/train_azure.py
.venv/bin/python ml/collect_azure.py
```

Training uses 30 minutes and weighted AUC, with cross-validation only on the 8,000 training rows. The remaining 2,000 rows are reserved for test evaluation. Open the recorded Studio job link and capture the leaderboard, metrics, explanation and confusion matrix. The collector downloads the top two completed candidates' `outputs/mlflow-model` artifacts, registers them, and submits evaluation jobs in their own conda environments. Review job status/logs if a candidate artifact/environment differs from the current AutoML export layout; no fabricated metrics are substituted.

Actual per-class results are written to `artifacts/azure/model_runs.json` and `evidence/azure-training.json`. Review best/runner-up comparison and update the README's cloud results. The local model binaries are never uploaded as AutoML evidence.

If your environment cannot run the collector because of a changed AutoML artifact/flavor, use the actual leaderboard confusion matrix and exported metrics to compute delayed-class precision/recall/F1, recording exactly which run produced them. Resolve this before marking Part B complete.

## 5. Deploy the endpoint and save model runs

This starts billable managed compute:

```bash
.venv/bin/python ml/deploy_azure.py --name "$ML_ENDPOINT_NAME" --vm-size Standard_DS2_v2
.venv/bin/python cosmos/push_results.py
```

The deploy script routes 100% of traffic to one instance and marks only the best run deployed. The Cosmos script upserts two actual Azure runs. It retrieves credentials using your CLI login in memory; it does not print keys. In Cosmos Data Explorer, execute the three model-run queries from `cosmos/queries.sql`; record each real RU charge in `docs/SUBMISSION.md` and capture screenshots.

After a live prediction, the same queries and a request point read can also be captured reproducibly with service-reported RU charges:

```bash
.venv/bin/python cosmos/capture_evidence.py --request-id '<request-id>' --user-id '<browser-id>'
```

This writes `evidence/azure-cosmos.json`; it does not fabricate Data Explorer screenshots.

Endpoint Test tab input shape (copy both low/high-risk orders from the portal presets for separate tests):

```json
{"input_data":{"columns":["carrier","distance_km","weight_kg","items","order_hour","is_sale_day","warehouse_backlog","weather_index"],"index":[0],"data":[["IndiaPost",5500,12,7,22,1,65,0.85]]}}
```

The API accepts Azure AutoML class arrays such as `[0]`/`[1]`; verify the actual endpoint's response contract in Test. Never put the key in frontend code.

## 6. Publish the repository and deploy the portal

The project is already published at **https://github.com/harshithRai/contoso-delay-classifier**. Review source/evidence before every update; keep `.venv`, `artifacts`, `.local`, `.env`, `local.settings.json`, keys and sensitive screenshots out. From the existing project checkout, publish changes with:

```bash
git add .
git diff --cached --stat
git diff --cached
git commit -m 'Add verified Azure deployment results and evidence'
git push origin main
```

Inspect the staged content/history before publishing. If a key is committed, rotate it immediately and remove it from history; deleting the latest copy does not remove history.

In Azure Portal, open the Static Web App and use **Manage deployment token**. Copy its token directly into the GitHub repository Actions secret named `AZURE_STATIC_WEB_APPS_API_TOKEN`; do not paste it into chat, source, or screenshots. Run the **Deploy Azure portal** workflow manually from GitHub Actions. It deploys `app/` and the Node 22 managed Functions in `api/`.

Set server settings without printing credentials:

```bash
.venv/bin/python scripts/configure_swa.py --swa "$SWA_NAME" \
  --cosmos "$COSMOS_ACCOUNT" --endpoint "$ML_ENDPOINT_NAME"
```

Wait for settings/deployment propagation, then open the `portalUrl` output. Check both a prediction and a point lookup. If the deployment UI asks for build values, use app location `app`, API `api`, and no app build output folder. The workflow uses the deploy action's normal API dependency installation.

The Bicep Application Insights instance is linked to ML. For the optional Functions monitoring bonus, explicitly enable Application Insights for the Static Web App in its portal settings and verify a Function request appears; merely creating Insights does not verify Function instrumentation. Useful KQL after data arrives:

```kusto
requests | summarize avg(duration), count() by bin(timestamp, 5m)
requests | summarize failures=countif(success == false) by bin(timestamp, 5m)
```

## 7. Execute cloud load and failure tests

```bash
python3 tests/load_test.py --url 'https://<your-live-host>' --count 100 --concurrency 5 \
  --environment azure --vm-size Standard_DS2_v2 --out evidence/azure-load-test.json
```

Use the portal's anonymous browser ID with `--user-id '<browser-id>'` if you want those calls in the browser's recent table. Health metrics are global. Choose a quiet testing window so unrelated traffic does not obscure the cohort.

For the deliberate failure test, this script changes only the API's copy of the endpoint key; it does not rotate the real endpoint key. Do this while recording the exercise and restore immediately:

```bash
.venv/bin/python scripts/configure_swa.py --swa "$SWA_NAME" \
  --cosmos "$COSMOS_ACCOUNT" --endpoint "$ML_ENDPOINT_NAME" --failure-test
python3 tests/load_test.py --url 'https://<your-live-host>' --count 10 --concurrency 1 \
  --environment azure --vm-size Standard_DS2_v2 --user-id '<browser-id>' \
  --out evidence/azure-failure-test.json
.venv/bin/python scripts/configure_swa.py --swa "$SWA_NAME" \
  --cosmos "$COSMOS_ACCOUNT" --endpoint "$ML_ENDPOINT_NAME"
```

Wait for setting propagation before each phase. Capture error health/history and the same request in Cosmos. After restoring, send successful traffic, capture recovery, and record it. A rolling 15-minute error rate declines as successful calls arrive or old failures age out; it should not reset instantly on restoring a key. Repeated calls incur inference/database usage.

## 8. Record, submit and clean up

Follow `docs/EVIDENCE_AND_DEMO.md`. Make sure the live portal is working at the required grading time. Fill the **one comment** template in `docs/SUBMISSION.md`; edit that same comment for updates. Nothing in this project posts to the class on your behalf.

After demo/testing, delete the billable endpoint:

```bash
bash scripts/cleanup.sh
az ml online-endpoint list -g "$AZURE_RESOURCE_GROUP" -w "$AZURE_ML_WORKSPACE" -o table
```

Deleting the endpoint stops predictions. If the instructor requires a working URL later, agree on a demonstration/grading window and redeploy as needed rather than leave compute billing indefinitely. After grading, review the dedicated resource group and delete it:

```bash
az group delete --name "$AZURE_RESOURCE_GROUP" --yes
```

That final command deletes the whole named group. Verify no unrelated resources are in it first. Check Azure Cost Management afterward and record cleanup evidence. Region/quota, runtime behavior, actual charges and Azure end-to-end testing remain your cloud validation steps.
