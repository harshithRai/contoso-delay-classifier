# Submission status

The updated post requires a public repository and **one comment**, edited for updates. Due: **Monday, 26 October 2026, 11:59 PM IST**. Session name has not been supplied; the demo video is published. The live portal works; SQL/AutoML/Cosmos evidence and the Azure load test are captured.

The portal, evidence and demo are ready. Post one comment or edit the existing comment; do not post a second one.

```markdown
| Field | Details |
|---|---|
| Name | Harshith Rai |
| GitHub | @harshithRai |
| 🔗 Repo | https://github.com/harshithRai/contoso-delay-classifier |
| 🌐 Live portal URL | https://polite-flower-00190c500.1.azurestaticapps.net |
| 🎥 Demo video | https://github.com/harshithRai/contoso-delay-classifier/releases/download/demo-2026-10-27/contoso-delay-demo.mp4 |
| 🧭 Approach (2–4 lines) | Loaded 10,000 orders into Azure SQL and trained AutoML classifiers using the training view export.<br>A Static Web App calls a validating Functions API; Cosmos DB stores model results and request logs, while the portal shows predictions, latency and error rate. |
| 🚧 Unfinished / stuck on | No implementation items pending. Demo, SQL/AutoML/Cosmos evidence and Azure load/failure/recovery tests are published. Default-threshold model recall remains low and is documented; endpoint cleanup follows demo/grading. |
```

## Actual Cosmos RU charges

| Query | RU charge | Evidence |
|---|---|---|
| Runs ordered by AUC | 3.16 RU | `evidence/azure-cosmos.json`; `screenshots/azure-cosmos-auc-query-stats.jpg` |
| Count deployed runs | 2.82 RU | `evidence/azure-cosmos.json`; `screenshots/azure-cosmos-deployed-query-stats.jpg` |
| Recall below 0.5 | 2.85 RU | `evidence/azure-cosmos.json`; `screenshots/azure-cosmos-recall-query-stats.jpg` |

The request point read used 1 RU and matched `(b5084d64-a2dc-4992-a570-a6131695e95f, 69b110b0-5173-4ac0-a320-2d45bc08521c)`. These charges were reported by the live Azure service and confirmed in Data Explorer.

## Deployment record

| Field | Actual value |
|---|---|
| Azure region and quota changes | Central India; DSv2 dedicated CPU quota 6 cores; training DS3_v2, min 0/max 1. Static Web App Free in East Asia. |
| Training job ID | gentle_iron_9ymzptm5gm (Completed; 10 candidates) |
| Best / runner-up run IDs | gentle_iron_9ymzptm5gm_8 / gentle_iron_9ymzptm5gm_9 |
| Endpoint name, VM size, instances | contoso-delay-o3fj7jzsdlnla-v2; Standard_D2as_v4; 1 instance. Direct tests returned [false] / [true]. |
| Live URL | https://polite-flower-00190c500.1.azurestaticapps.net |
| Azure load results | 100 requests, concurrency 5; 98 successful, 2 HTTP 502 errors; client p50 851 ms/p95 1,378 ms; 2% error rate; 20.285 seconds. |
| Deliberate Azure failure/recovery test | Initial wrong-key cohort: 10/10 errors. First restored cohort: 116/120 successes. Lower-concurrency cohort: 240/240 successes. Saved-video repeat: 8/10 errors during propagation, followed by 240/240 restored successes; final recorded health 3.6%. |
| Cleanup time/evidence | Both training clusters deleted; verified empty compute listing in `evidence/azure-evidence-verification.json`. Endpoint remains active for demo/grading; trial spending limit enabled; ₹500 alert active. |

SQL import/analysis and the live API validation/Cosmos logging/point lookup/health smoke test passed. Both held-out model evaluations and successful live inference are verified.
