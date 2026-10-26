# Submission status

The updated post requires a public repository and **one comment**, edited for updates. Due: **Monday, 26 October 2026, 11:59 PM IST**. Session name and video URL are pending. The portal is deployed; model training is in progress.

Do not submit the template as completed until the Azure portal, evidence and video are ready.

```markdown
| Field | Details |
|---|---|
| Name | Harshith Rai |
| GitHub | @harshithRai |
| 🔗 Repo | https://github.com/harshithRai/contoso-delay-classifier |
| 🌐 Live portal URL | https://polite-flower-00190c500.1.azurestaticapps.net (model deployment pending) |
| 🎥 Demo video | <viewable 3–5 minute screen recording URL> |
| 🧭 Approach (2–4 lines) | Azure SQL stores the supplied orders and exposes a training view. AutoML trains and deploys the classifier; a Static Web App calls a validating Functions API. Cosmos stores real model metrics and request logs; the portal shows predictions, p50/p95, error rate and request lookup. |
| 🚧 Unfinished / stuck on | AutoML training is running. Model endpoint, model-run evidence, Azure load/failure tests and demo video remain pending. |
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
| Training job ID | gentle_iron_9ymzptm5gm (running) |
| Best / runner-up run IDs | Not run |
| Endpoint name, VM size, instances | Planned: small supported VM, one instance |
| Live URL | https://polite-flower-00190c500.1.azurestaticapps.net |
| Azure load and failure results | Not run |
| Cleanup time/evidence | Pending after model testing/demo; trial spending limit enabled; ₹500 alert active. |

SQL import/analysis and the live API validation/Cosmos logging/point lookup/health smoke test passed. Training results and successful live model inference are not yet verified.
