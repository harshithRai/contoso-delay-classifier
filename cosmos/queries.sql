-- model_runs container. Record the actual RU charge from Data Explorer for each.
SELECT c.id, c.algorithm, c.metrics.auc, c.trainedAt FROM c ORDER BY c.metrics.auc DESC

SELECT VALUE COUNT(1) FROM c WHERE c.deployed = true

SELECT c.id, c.metrics.recall FROM c WHERE c.metrics.recall < 0.5

-- requests container. Counter documents are excluded explicitly.
SELECT TOP 20 c.id, c.userId, c.at, c.label, c.totalLatencyMs, c.status
FROM c WHERE c.type = 'request' ORDER BY c.at DESC

SELECT c.id, c.error, c.httpStatus FROM c WHERE c.type = 'request' AND c.status = 'error'
