targetScope = 'resourceGroup'

@description('Azure region for all regional resources.')
param location string = resourceGroup().location

@description('Base workload name used to compose resource names.')
param workloadName string

@description('Deployment environment name.')
param environmentName string = 'dev'

@description('Common tags applied to all resources.')
param tags object = {}

type PostgresConfig = {
  name: string
  databaseName: string
  skuName: string
  skuTier: string
  version: string
  storageSizeGB: int
  backupRetentionDays: int
  availabilityZone: string
  delegatedSubnetResourceId: string?
  privateDnsZoneResourceId: string?
  publicNetworkAccess: string
  entraAdminObjectId: string
  entraAdminPrincipalName: string
  entraAdminPrincipalType: string
}

type StorageConfig = {
  name: string
  rawContainer: string
  curatedContainer: string
  enrichedContainer: string
  publicNetworkAccess: string
}

type ServiceBusConfig = {
  name: string
  skuName: string
  skuTier: string
  ingestQueueName: string
  enrichQueueName: string
}

type SearchConfig = {
  name: string
  sku: string
  replicaCount: int
  partitionCount: int
}

type AiConfig = {
  aiServicesName: string
  aiServicesCustomSubdomain: string
  openAiName: string
  openAiCustomSubdomain: string
  aiSku: string
  openAiSku: string
}

type ContainerAppsConfig = {
  managedEnvironmentName: string
  appName: string
  containerImage: string
  targetPort: int
  minReplicas: int
  maxReplicas: int
  cpu: any
  memory: string
  externalIngress: bool
  infrastructureSubnetResourceId: string?
}

type MonitoringConfig = {
  logAnalyticsWorkspaceName: string
  appInsightsName: string
}

param postgres PostgresConfig
param storage StorageConfig
param serviceBus ServiceBusConfig
param search SearchConfig
param ai AiConfig
param containerApps ContainerAppsConfig
param monitoring MonitoringConfig

var namingTags = union(tags, {
  environment: environmentName
  workload: workloadName
})

module identity './modules/identity.bicep' = {
  params: {
    location: location
    name: 'id-${workloadName}-${environmentName}'
    tags: namingTags
  }
}

module monitoringModule './modules/monitoring.bicep' = {
  params: {
    location: location
    logAnalyticsWorkspaceName: monitoring.logAnalyticsWorkspaceName
    appInsightsName: monitoring.appInsightsName
    tags: namingTags
  }
}

module storageModule './modules/storage.bicep' = {
  params: {
    location: location
    storage: storage
    tags: namingTags
  }
}

module serviceBusModule './modules/servicebus.bicep' = {
  params: {
    location: location
    serviceBus: serviceBus
    tags: namingTags
  }
}

module aiModule './modules/ai-services.bicep' = {
  params: {
    location: location
    ai: ai
    tags: namingTags
  }
}

module searchModule './modules/search.bicep' = {
  params: {
    location: location
    search: search
    tags: namingTags
  }
}

module postgresModule './modules/postgres.bicep' = {
  params: {
    location: location
    postgres: postgres
    tags: namingTags
  }
}

module containerAppsModule './modules/container-apps.bicep' = {
  params: {
    location: location
    containerApps: containerApps
    tags: namingTags
    userAssignedIdentityId: identity.outputs.id
    appInsightsConnectionString: monitoringModule.outputs.appInsightsConnectionString
    postgresHost: postgresModule.outputs.host
    postgresDatabaseName: postgresModule.outputs.databaseName
    searchEndpoint: searchModule.outputs.endpoint
    searchIndexName: 'epc-documents'
    aiServicesEndpoint: aiModule.outputs.aiServicesEndpoint
    openAiEndpoint: aiModule.outputs.openAiEndpoint
    serviceBusNamespace: serviceBusModule.outputs.namespaceFqdn
    ingestQueueName: serviceBus.ingestQueueName
    enrichQueueName: serviceBus.enrichQueueName
    storageAccountName: storageModule.outputs.name
    rawContainerName: storage.rawContainer
    curatedContainerName: storage.curatedContainer
    enrichedContainerName: storage.enrichedContainer
  }
}

output managedIdentityResourceId string = identity.outputs.id
output containerAppName string = containerAppsModule.outputs.appName
output containerAppUrl string = containerAppsModule.outputs.appUrl
output postgresServerName string = postgresModule.outputs.serverName
output postgresHost string = postgresModule.outputs.host
output aiServicesEndpoint string = aiModule.outputs.aiServicesEndpoint
output openAiEndpoint string = aiModule.outputs.openAiEndpoint
output searchEndpoint string = searchModule.outputs.endpoint
output storageAccountName string = storageModule.outputs.name
output serviceBusNamespace string = serviceBusModule.outputs.namespaceFqdn
