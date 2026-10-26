# Submission status

The updated post requires a public repository and **one comment**, edited for updates. Due: **Monday, 26 October 2026, 11:59 PM IST**. Session name and video URL are pending. AutoML training and the model endpoint are deployed; portal integration and final evidence are in progress.

Do not submit the template as completed until the Azure portal, evidence and video are ready.

```markdown
| Field | Details |
|---|---|
| Name | Harshith Rai |
| GitHub | @harshithRai |
| 🔗 Repo | https://github.com/harshithRai/contoso-delay-classifier |
| 🌐 Live portal URL | https://polite-flower-00190c500.1.azurestaticapps.net |
| 🎥 Demo video | Pending |
| 🧭 Approach (2–4 lines) | Loaded 10,000 orders into Azure SQL and trained AutoML classifiers using the training view export.<br>A Static Web App calls a validating Functions API; Cosmos DB stores model results and request logs, while the portal shows predictions, latency and error rate. |
| 🚧 Unfinished / stuck on | Demo video and Azure load/failure tests are pending. Model limitations and measured metrics are documented in the README. |
```

## Actual Cosmos RU charges — pending

| Query | RU charge | Evidence |
|---|---|---|
| Runs ordered by AUC | Not measured | Pending Azure Data Explorer |
| Count deployed runs | Not measured | Pending Azure Data Explorer |
| Recall below 0.5 | Not measured | Pending Azure Data Explorer |

## Deployment record — in progress

| Field | Actual value |
|---|---|
| Azure region and quota changes | Central India; DSv2 dedicated CPU quota 6 cores; training DS3_v2, min 0/max 1. Static Web App Free in East Asia. |
| Training job ID | gentle_iron_9ymzptm5gm (Completed; 10 candidates) |
| Best / runner-up run IDs | gentle_iron_9ymzptm5gm_8 / gentle_iron_9ymzptm5gm_9 |
| Endpoint name, VM size, instances | contoso-delay-o3fj7jzsdlnla-v2; Standard_D2as_v4; 1 instance. Direct tests returned [false] / [true]. |
| Live URL | https://polite-flower-00190c500.1.azurestaticapps.net |
| Azure load and failure results | Not run |
| Cleanup time/evidence | Pending after model testing/demo; trial spending limit enabled; ₹500 alert active. |

SQL import/analysis and the live API validation/Cosmos logging/point lookup/health smoke test passed. Both held-out model evaluations and successful live inference are verified.
