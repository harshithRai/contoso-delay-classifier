import os
from azure.ai.ml import MLClient
from azure.identity import DefaultAzureCredential
def client():
    return MLClient(DefaultAzureCredential(),os.environ['AZURE_SUBSCRIPTION_ID'],os.environ['AZURE_RESOURCE_GROUP'],os.environ['AZURE_ML_WORKSPACE'])
