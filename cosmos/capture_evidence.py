"""Capture real query results/RU charges and one partitioned request point read."""
import argparse
import json
import os
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from azure.cosmos import CosmosClient


def az(*args):
    result = subprocess.run(['az', *args, '--only-show-errors', '-o', 'json'], capture_output=True, text=True)
    if result.returncode:
        raise RuntimeError('Azure settings lookup failed; no credentials were displayed.')
    return json.loads(result.stdout)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--request-id', required=True)
    parser.add_argument('--user-id', required=True)
    args = parser.parse_args()
    group, account = os.environ['AZURE_RESOURCE_GROUP'], os.environ['COSMOS_ACCOUNT']
    endpoint = az('cosmosdb', 'show', '-g', group, '-n', account)['documentEndpoint']
    key = az('cosmosdb', 'keys', 'list', '-g', group, '-n', account)['primaryMasterKey']
    database = CosmosClient(endpoint, credential=key).get_database_client('contoso')
    runs, requests = database.get_container_client('model_runs'), database.get_container_client('requests')
    queries = [
        ('Runs ordered by AUC', 'SELECT c.id, c.algorithm, c.metrics.auc, c.trainedAt FROM c ORDER BY c.metrics.auc DESC'),
        ('Count deployed runs', 'SELECT VALUE COUNT(1) FROM c WHERE c.deployed = true'),
        ('Recall below 0.5', 'SELECT c.id, c.metrics.recall FROM c WHERE c.metrics.recall < 0.5'),
    ]
    results = []
    for name, query in queries:
        charges = []
        rows = list(runs.query_items(query, enable_cross_partition_query=True,
                    response_hook=lambda headers, _: charges.append(float(headers.get('x-ms-request-charge', 0)))))
        results.append({'name': name, 'query': query, 'requestCharge': sum(charges), 'results': rows})
    if len(results[0]['results']) < 2:
        raise RuntimeError('Two real model runs must be stored before capturing final evidence.')
    charges = []
    point = requests.read_item(args.request_id, partition_key=args.user_id,
                 response_hook=lambda headers, _: charges.append(float(headers.get('x-ms-request-charge', 0))))
    properties = {}
    for name, container in [('model_runs', runs), ('requests', requests)]:
        settings = container.read()
        properties[name] = {'partitionKey': settings['partitionKey']['paths'], 'defaultTtl': settings.get('defaultTtl')}
    report = {'source': 'Azure Cosmos DB SDK; service-reported request charges',
              'capturedAt': datetime.now(timezone.utc).isoformat(), 'containers': properties,
              'queries': results, 'pointRead': {'requestCharge': sum(charges), 'document': point}}
    output = Path(__file__).resolve().parents[1] / 'evidence/azure-cosmos.json'
    output.write_text(json.dumps(report, indent=2) + '\n')
    for result in results:
        print(f"{result['name']}: {result['requestCharge']} RU; {len(result['results'])} rows")
    print(f'Point read: {sum(charges)} RU. Evidence saved to {output.name}.')


if __name__ == '__main__':
    main()
