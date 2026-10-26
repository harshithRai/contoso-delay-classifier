# Verification record — 26 October 2026

## Executed

- Supplied CSV: 10,000 rows, 1,807 delayed. SHA-256 recorded in README and the training report.
- Real local training: LogisticRegression and balanced RandomForest with fold-local preprocessing, seed 42, 3-fold training CV, untouched 2,000-row test split.
- Node behavioral suite: validation does not call the model; class parsing; persistent success/failure/timeout logs; unavailable storage returns 503; user-partition lookup isolation; median/p95/error-rate arithmetic; idle marker; separate time windows.
- Model report check: class metrics agree with confusion matrices and local runs are explicitly not deployed.
- All Python files parsed with `ast.parse`.
- `npm ci`/installation of API package: Azure Cosmos SDK installed; dependency audit reported zero known vulnerabilities at installation time. SDK type definitions inspected for transactional batch and Patch operation compatibility.
- Official Microsoft Bicep compiler 0.48.1: both `infra/main.bicep` and `infra/budget.bicep` compiled successfully to temporary ARM JSON without diagnostics. This checks template syntax/types, not subscription policies, quotas or actual deployment.
- Browser: actual lower-/higher-risk prediction workflow, readable upstream failure, logged failures, health/error-rate change, and request history. Screenshots use the `local-` prefix.
- Local load: 100 calls, concurrency 5, no errors, client median 9 ms / p95 12 ms, 0.206 seconds total.
- Local wrong-key test: 10 calls, all tracked errors; recovery cohort: 120 calls, no errors.

The saved JSON reports contain the request IDs for each test cohort. Local logs and model binaries are ignored and retained only in this workspace.

## Not executed

- Azure provisioning/SQL connection/import and cloud SQL screenshots.
- AutoML submission, model collection/evaluation, managed online endpoint deployment.
- Cosmos service transactions/TTL/point reads or actual RU charge measurement.
- Static Web Apps/Functions cloud deployment and runtime verification.
- Azure load/failure/cold-start tests, Application Insights instrumentation or cleanup.
- Demo video recording/publication.

No Azure subscription is available. The cloud runbook and scripts are prepared, but cloud execution remains necessary before claiming assignment completion.
