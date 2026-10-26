targetScope = 'resourceGroup'

@description('3-11 lowercase letters/numbers; resource suffix is added automatically.')
@minLength(3)
@maxLength(11)
param prefix string = 'contoso'
param location string = resourceGroup().location
@description('Static Web Apps availability can differ from the ML/SQL region.')
param swaLocation string = 'eastasia'
@description('Object ID of the signed-in Entra user who will administer SQL.')
param adminObjectId string
param adminLogin string
@description('Your current public IPv4 address. No broad Azure-services firewall rule is created.')
param clientIp string

var suffix = uniqueString(resourceGroup().id)
var base = '${prefix}-${suffix}'
var tags = { project: 'contoso-delay-assignment', owner: adminLogin }

resource storage 'Microsoft.Storage/storageAccounts@2023-05-01' = {
  name: '${prefix}${suffix}'
  location: location
  tags: tags
  sku: { name: 'Standard_LRS' }
  kind: 'StorageV2'
  properties: { supportsHttpsTrafficOnly: true, minimumTlsVersion: 'TLS1_2', allowBlobPublicAccess: false }
}
resource vault 'Microsoft.KeyVault/vaults@2023-07-01' = {
  name: '${prefix}-kv-${suffix}'
  location: location
  tags: tags
  properties: {
    tenantId: tenant().tenantId
    sku: { family: 'A', name: 'standard' }
    enableRbacAuthorization: true
    accessPolicies: []
  }
}
resource insights 'Microsoft.Insights/components@2020-02-02' = {
  name: '${base}-insights'
  location: location
  kind: 'web'
  tags: tags
  properties: { Application_Type: 'web' }
}
resource workspace 'Microsoft.MachineLearningServices/workspaces@2024-04-01' = {
  name: '${base}-ml'
  location: location
  tags: tags
  identity: { type: 'SystemAssigned' }
  properties: {
    friendlyName: 'Contoso delay classifier'
    storageAccount: storage.id
    keyVault: vault.id
    applicationInsights: insights.id
    publicNetworkAccess: 'Enabled'
  }
}
resource compute 'Microsoft.MachineLearningServices/workspaces/computes@2024-04-01' = {
  parent: workspace
  name: 'cpu-cluster'
  location: location
  properties: {
    computeType: 'AmlCompute'
    properties: {
      vmSize: 'Standard_DS3_v2'
      vmPriority: 'Dedicated'
      scaleSettings: { minNodeCount: 0, maxNodeCount: 1, nodeIdleTimeBeforeScaleDown: 'PT120S' }
    }
  }
}
resource sql 'Microsoft.Sql/servers@2023-08-01' = {
  name: '${base}-sql'
  location: location
  tags: tags
  properties: {
    version: '12.0'
    minimalTlsVersion: '1.2'
    administrators: {
      administratorType: 'ActiveDirectory'
      principalType: 'User'
      login: adminLogin
      sid: adminObjectId
      tenantId: tenant().tenantId
      azureADOnlyAuthentication: true
    }
  }
}
resource firewall 'Microsoft.Sql/servers/firewallRules@2023-08-01' = {
  parent: sql
  name: 'client-only'
  properties: { startIpAddress: clientIp, endIpAddress: clientIp }
}
resource database 'Microsoft.Sql/servers/databases@2023-08-01' = {
  parent: sql
  name: 'contoso'
  location: location
  sku: { name: 'GP_S_Gen5_1', tier: 'GeneralPurpose', family: 'Gen5', capacity: 1 }
  properties: { autoPauseDelay: 60, minCapacity: json('0.5'), maxSizeBytes: 2147483648 }
}
resource cosmos 'Microsoft.DocumentDB/databaseAccounts@2024-05-15' = {
  name: '${base}-cosmos'
  location: location
  tags: tags
  kind: 'GlobalDocumentDB'
  properties: {
    databaseAccountOfferType: 'Standard'
    capabilities: [{ name: 'EnableServerless' }]
    locations: [{ locationName: location, failoverPriority: 0 }]
    consistencyPolicy: { defaultConsistencyLevel: 'Session' }
    minimalTlsVersion: 'Tls12'
    publicNetworkAccess: 'Enabled'
  }
}
resource cosmosDb 'Microsoft.DocumentDB/databaseAccounts/sqlDatabases@2024-05-15' = {
  parent: cosmos
  name: 'contoso'
  properties: { resource: { id: 'contoso' } }
}
resource runs 'Microsoft.DocumentDB/databaseAccounts/sqlDatabases/containers@2024-05-15' = {
  parent: cosmosDb
  name: 'model_runs'
  properties: { resource: { id: 'model_runs', partitionKey: { paths: ['/modelName'], kind: 'Hash' } } }
}
resource requests 'Microsoft.DocumentDB/databaseAccounts/sqlDatabases/containers@2024-05-15' = {
  parent: cosmosDb
  name: 'requests'
  properties: {
    resource: {
      id: 'requests'
      partitionKey: { paths: ['/userId'], kind: 'Hash' }
      defaultTtl: 2592000
    }
  }
}
resource swa 'Microsoft.Web/staticSites@2023-12-01' = {
  name: '${base}-portal'
  location: swaLocation
  tags: tags
  sku: { name: 'Free', tier: 'Free' }
  properties: { buildProperties: { appLocation: 'app', apiLocation: 'api', appArtifactLocation: '' } }
}

output mlWorkspace string = workspace.name
output sqlServer string = sql.properties.fullyQualifiedDomainName
output cosmosAccount string = cosmos.name
output cosmosEndpoint string = cosmos.properties.documentEndpoint
output staticWebApp string = swa.name
output portalUrl string = 'https://${swa.properties.defaultHostname}'
output applicationInsights string = insights.name
