# Verified Azure evidence

Captured from the deployed services and the signed-in Azure Portal on 27 October 2026 IST. JSON capture timestamps use UTC. These are actual service results and screenshots, not reconstructed Azure screens.

| Requirement | Service output | Screenshots |
|---|---|---|
| 10,000 orders and three SQL analyses | [SQL results](../evidence/azure-sql-analysis.json) | [Count](../screenshots/azure-sql-count.jpg), [carrier](../screenshots/azure-sql-carrier.jpg), [sale day](../screenshots/azure-sql-sale-day.jpg), [backlog](../screenshots/azure-sql-backlog.jpg) |
| Completed AutoML and ten ranked candidates | [Leaderboard](../evidence/azure-leaderboard.json), [held-out metrics and importance](../evidence/azure-training.json) | [Completed job](../screenshots/azure-automl-completed.jpg), [leaderboard](../screenshots/azure-automl-leaderboard.jpg) |
| Two stored model results | [Live SDK verification](../evidence/azure-evidence-verification.json) | [Deployed voting model](../screenshots/azure-cosmos-deployed-model.jpg), [runner-up stack model](../screenshots/azure-cosmos-runner-up-model.jpg) |
| Runs ordered by held-out AUC: 3.16 RU | [Cosmos results](../evidence/azure-cosmos.json) | [Results](../screenshots/azure-cosmos-auc-query-results.jpg), [Query Stats](../screenshots/azure-cosmos-auc-query-stats.jpg) |
| Count deployed runs: 2.82 RU | [Cosmos results](../evidence/azure-cosmos.json) | [Results](../screenshots/azure-cosmos-deployed-query-results.jpg), [Query Stats](../screenshots/azure-cosmos-deployed-query-stats.jpg) |
| Recall below 0.5: 2.85 RU | [Cosmos results](../evidence/azure-cosmos.json) | [Results](../screenshots/azure-cosmos-recall-query-results.jpg), [Query Stats](../screenshots/azure-cosmos-recall-query-stats.jpg) |
| Original live prediction and exact matching Cosmos document | [1-RU point read](../evidence/azure-cosmos.json) | [Prediction](../screenshots/azure-user-prediction.jpg), [Cosmos request](../screenshots/azure-cosmos-matching-request.jpg), [health and API lookup](../screenshots/azure-user-health-and-lookup.jpg) |
| 100 requests at concurrency 5 on one Standard_D2as_v4 instance | [Load report and every request ID](../evidence/azure-load-test.json), [verified failure documents](../evidence/azure-evidence-verification.json) | [Live portal health and lookup](../screenshots/azure-user-health-and-lookup.jpg) |
| Endpoint healthy; training clusters deleted | [Live SDK verification](../evidence/azure-evidence-verification.json) | Service state is recorded in JSON. |

The supplied prediction is `b5084d64-a2dc-4992-a570-a6131695e95f`, in browser partition `69b110b0-5173-4ac0-a320-2d45bc08521c`. It returned `delayed`, HTTP 200, with 751 ms handler time, 445 ms model time and 305 ms initial database write time.

The load test recorded **98 successes and two HTTP 502 errors**, client p50 **851 ms**, client p95 **1,378 ms**, error rate **2%**, elapsed **20.285 seconds**. These cohort measurements are preserved. Both errors were independently read from Cosmos. Their generic safe messages do not establish the upstream status or root cause. The portal uses a rolling 15-minute error window, so a later screenshot can show 0% after those failures age out. It also reports server handler latency rather than client wall time.

Model selection used training cross-validation AUC before evaluating the held-out data. Sorting stored runs by held-out AUC does not change the selected deployment. The poor delayed-class recall is documented in the README.

The original AutoML job summary can say “No registration yet” or “No deployment yet” because model registration and deployment were performed separately with the SDK. The independently verified `blue` deployment is `Succeeded`, uses the registered CV winner and receives all endpoint traffic.

The deliberate failure/recovery tests and [silent 3:47 demo](https://github.com/harshithRai/contoso-delay-classifier/releases/download/demo-2026-10-27/contoso-delay-demo-silent.mp4) are now complete. Initial wrong-key testing produced 10/10 errors, followed by 116/120 successes at concurrency 5 and 240/240 at concurrency 2. The saved-video repeat produced 8/10 errors during settings propagation, followed by 240/240 restored successes. [Final video request documents](../evidence/azure-video.json) independently verify the exact recorded success, failure and restoration attempts. Still pending: posting/editing the single class comment and endpoint cleanup after the demo/grading window.
