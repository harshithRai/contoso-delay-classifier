# Evidence and 3–5 minute demo

Screenshots in this repository currently prefixed `local-` are local previews. Do not rename them as Azure proof. Azure screenshots and RU charges must come from actual deployed resources. Never show key/connection-string/settings blades in a recording.

Actual cloud results and screenshots are now linked in [AZURE_EVIDENCE.md](AZURE_EVIDENCE.md). SQL count/analyses, AutoML completion/leaderboard, both Cosmos model documents, the three query charges, the supplied live prediction/point read and the 100-request Azure load test are captured. Deliberate Azure failure/recovery and the [demo video](../demo/README.md) are now complete.

## Evidence checklist

- [ ] SQL count = 10,000; Entra-only configuration; the three actual analysis results.
- [ ] AutoML leaderboard, best metrics, delayed-class confusion matrix, feature importance.
- [ ] Endpoint Test tab for a lower-risk order and higher-risk order, without a visible key.
- [x] Two real documents in `model_runs`, including best/second-best metrics.
- [x] Three Cosmos query results with their actual RU charges.
- [ ] Portal prediction, client/server validation error, model-failure error.
- [ ] Health counts, p50, p95, error rate and last-50 latency chart.
- [x] Last-20 requests and one exact ID found via `(id, userId)` lookup.
- [x] 100-request Azure load-test output, actual VM size and instance count.
- [x] Wrong-key 10-request errors and restored-key recovery, including request documents.
- [ ] Budget alert and endpoint cleanup, without sensitive identifiers/settings exposed.
- [ ] Public repo URL, working live portal URL and viewable demo link.

Suggested names: `01-azure-sql-count.png`, `02-azure-carrier.png`, `03-azure-sale.png`, `04-azure-backlog.png`, `05-azure-leaderboard.png`, `06-azure-metrics.png`, `07-azure-endpoint-tests.png`, `08-cosmos-runs.png`, `09-cosmos-query-rus.png`, `10-live-prediction.png`, `11-live-validation.png`, `12-live-failure.png`, `13-health.png`, `14-lookup.png`, `15-load.png`, `16-recovery.png`, `17-cleanup.png`.

## Recording script (~4 minutes)

**0:00–0:35 — What it does.** Show the public README architecture. Say SQL is historical truth; the SQL view is exported for training; Functions protects credentials; Cosmos records model runs and requests. State the model's real Azure AUC/precision/recall/F1 and mention class imbalance.

**0:35–1:20 — Prediction and trace.** Open the live URL, pick a sample and predict. Read the class, request ID and latency. Copy the request ID, find it in the portal, then show the same `id` and `userId` in Cosmos Data Explorer. Point out status, timing and 30-day TTL. Avoid inventing certainty for the prediction.

**1:20–2:00 — Health.** Show request count, median and p95 successful latency, error rate excluding invalid, last-50 chart, and recent requests. Briefly show real 100-call load-test results and VM size/instance count. Explain why client elapsed time and handler timing differ.

**2:00–3:15 — Failure and recovery.** Pre-open a terminal with the safe configure command (no keys visible). Activate the intentionally wrong server-side key, allow propagation, send ten requests, and show the friendly portal error and recorded failures. Explain the 5% alert. Restore the key immediately, make successful calls, and show the rolling rate recovering. Prepare this flow before recording so propagation does not consume the whole video.

**3:15–4:00 — Tradeoffs and cost.** Explain `/userId` for request grouping/point reads and `/modelName` for the small model history. Explain a false negative and threshold tradeoff, what was hardest, and one production improvement. Show budget/cleanup evidence or state the agreed grading window and delete the endpoint afterward.

Record an actual screen session using your usual screen recorder. Narration is optional; the assignment asks for the visible flow and does not require audio. Verify readable text and sharing permissions before submitting. A script and local screenshots are not a substitute for the requested video.

## Short oral-answer prompts

1. Why can an always-on-time model score 82%? Because 81.93% of all examples are on time, so accuracy hides zero delayed-class recall.
2. Why `(id, userId)`? Together they locate the exact Cosmos item without a cross-partition search; the browser ID groups synthetic requests rather than authenticates a human.
3. Why exclude invalid requests from error rate? A 400 is an input rejection, not a model/dependency failure; count it separately.
4. Where does time go? Endpoint network/inference, persistence and Function overhead; client time also includes transport/finalization/rendering. Actual Azure cold-start cost still needs measurement.
5. Why only a class? Default AutoML serving often returns the predicted class; a percentage needs a real probability response and calibration, not a made-up conversion.
