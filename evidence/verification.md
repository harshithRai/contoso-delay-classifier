# Verification record — 26 October 2026

## Executed

- Supplied CSV: 10,000 rows, 1,807 delayed. SHA-256 recorded in README and the training report.
- Real local training: LogisticRegression and balanced RandomForest with fold-local preprocessing, seed 42, 3-fold training CV, untouched 2,000-row test split.
- Node behavioral suite: 11 passing tests for validation without model invocation, class parsing, persistent success/failure/timeout logs, unavailable storage, partial finalization failure, user-partition lookup isolation, median/p95/error-rate arithmetic, idle marker retention and separate time windows.
- Model report check: class metrics agree with confusion matrices and local runs are explicitly not deployed.
- All Python files parsed with `ast.parse`.
- `npm ci`/installation of API package: Azure Cosmos SDK installed; dependency audit reported zero known vulnerabilities at installation time. SDK type definitions inspected for transactional batch and Patch operation compatibility.
- Official Microsoft Bicep compiler 0.48.1: both `infra/main.bicep` and `infra/budget.bicep` compiled successfully to temporary ARM JSON without diagnostics. This checks template syntax/types, not subscription policies, quotas or actual deployment.
- Browser: actual lower-/higher-risk prediction workflow, readable upstream failure, logged failures, health/error-rate change, and request history. Screenshots use the `local-` prefix.
- Local load: 100 calls, concurrency 5, no errors, client median 9 ms / p95 12 ms, 0.206 seconds total.
- Local wrong-key test: 10 calls, all tracked errors; recovery cohort: 120 calls, no errors.

The saved JSON reports contain the request IDs for each test cohort. Local logs and model binaries are ignored and retained only in this workspace.

The reviewed source was published publicly at https://github.com/harshithRai/contoso-delay-classifier using GitHub CLI after the user approved browser authorization. The authenticated account was verified as `harshithRai`. Credentials, local request logs, virtual environments and model binaries are excluded from the repository.

## Azure execution — 27 October 2026 IST

- Azure Resource Manager infrastructure deployment succeeded in Central India; Free Static Web App in East Asia. Trial offer and spending limit `On` verified. ₹500 INR resource-group budget deployment succeeded with 80%/100% notifications. Budget alerts do not cap spending.
- SQL Entra-token connection with TLS certificate/hostname validation succeeded using Python TDS. The TLS dependency is constrained below pyOpenSSL 26 because Python TDS 1.17 uses the older X509 extension API.
- Imported 10,000 rows; ran count and all three analyses against Azure SQL. Actual results: `azure-sql-analysis.json`.
- Exported the SQL training view; saved 8,000 training / 2,000 held-out rows, stratified seed 42. Provenance: `azure-data-provenance.json`.
- Submitted AutoML job `gentle_iron_9ymzptm5gm`, weighted AUC, 30-minute limit, 10 maximum trials, one concurrent trial; training node allocation verified running.
- GitHub Actions deployed the portal and managed Node 22 Functions successfully: run `40378675827`. Live URL: https://polite-flower-00190c500.1.azurestaticapps.net.
- Actual cloud invalid-input request returned HTTP 400, was persisted to Cosmos DB, and retrieved using its `(id, userId)` point address. Global health counted one invalid request and zero system errors. Evidence: `azure-validation.json`.
- Full resource/deployment metadata without credentials: `azure-deployment.json`.

## Not executed

- Cloud SQL portal screenshots (actual SQL query JSON is available).
- AutoML model collection/evaluation and managed online endpoint deployment; training is running.
- Two real model-run documents and actual query RU charge measurement. Request transaction and point read have passed.
- Successful live model prediction.
- Azure load/failure/cold-start tests, Application Insights instrumentation or cleanup.
- Demo video recording/publication.

The remaining cloud steps and demo are required before claiming assignment completion.
