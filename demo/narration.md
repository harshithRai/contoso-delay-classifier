# Demo narration

Computer-generated macOS Samantha voice.

## Intro

This is Contoso Delivery Intelligence, built for Harshith Rai's Azure assignment. This demo uses actual screen recordings with computer generated narration. Ten thousand historical orders are stored in Azure SQL. The training view exposes eight features and the delayed label. A stratified export reserves two thousand orders for held out testing. Azure Machine Learning AutoML trains the classifier. A Static Web App calls an Azure Functions API, which validates inputs, calls the model, and writes request traces to Cosmos D B. Model and database keys stay in server side settings.

## Models

AutoML completed ten candidates. The voting ensemble won on training cross validation A U C, with a score of zero point seven four three nine. Its held out A U C is zero point seven two four zero. Delayed class precision is zero point eight three three three, recall is zero point zero one three nine, and F one is zero point zero two seven two. It misses three hundred fifty six of three hundred sixty one actual delays. Accuracy alone hides this limitation. The default decision rule needs validation based threshold tuning before a business rollout.

## Prediction

Here is an actual prediction in the public portal. The higher risk example uses India Post, a long distance shipment, a sale day, warehouse backlog and severe weather. The API returns likely delayed, together with its request identifier and separate total and model call latency. The request explorer retrieves the exact recorded attempt. In Azure Cosmos Data Explorer, the same request identifier matches the stored document, including its browser identifier, input, label, status and timing. The requests container uses slash user I D as its partition key and retains detailed logs for thirty days.

## Health

The health panel shows successful request latency at the median and ninety fifth percentile, a rolling fifteen minute error rate, recent latency bars and request history. Invalid input is counted separately from dependency failures. The completed Azure load test sent one hundred requests at concurrency five to one Standard D two A S version four instance. Ninety eight succeeded and two returned tracked errors. Client median latency was eight hundred fifty one milliseconds, and the ninety fifth percentile was one thousand three hundred seventy eight. Client time includes transport and finalization, so it differs from handler latency.

## Failure

For the failure test, the API's server side model key was deliberately replaced with an invalid test value. The real endpoint key was not rotated or exposed. The initial test returned ten recorded failures. In this repeated recording, eight of ten requests failed while settings propagated. This live portal attempt shows a friendly service error with a request identifier. The failed attempt is stored in Cosmos rather than disappearing. The rolling error rate rises above the five percent alert threshold. These deliberate failures are separate from the incidental errors in the original load test.

## Recovery

The real model key is restored in server side settings. A fresh live prediction succeeds again. At concurrency five, the first recovery cohort had one hundred sixteen successes and four errors. A separate follow up at concurrency two had two hundred forty successes and zero errors. The rolling error rate falls below five percent; restoration does not erase previous failures. The endpoint is configured for one in flight request per instance, so queuing or throttling is plausible, but the exact error cause is not established. Model history uses slash model name; requests use slash user I D. Both training clusters are deleted. The live endpoint remains active for the demo and grading window and must be deleted afterward because it bills even when idle.
