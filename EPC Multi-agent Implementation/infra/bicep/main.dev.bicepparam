using './main.bicep'

param location = 'centralus'
param workloadName = 'epckg'
param environmentName = 'dev'
param tags = {
  owner: 'platform'
  costCenter: 'innovation'
  environment: 'dev'
}

param postgres = {
  name: 'pg-epckg-dev'
  databaseName: 'epckg'
  skuName: 'Standard_D2ds_v5'
  skuTier: 'GeneralPurpose'
  version: '16'
  storageSizeGB: 128
  backupRetentionDays: 7
  availabilityZone: '1'
  delegatedSubnetResourceId: ''
  privateDnsZoneResourceId: ''
  publicNetworkAccess: 'Enabled'
  entraAdminObjectId: '00000000-0000-0000-0000-000000000000'
  entraAdminPrincipalName: 'Azure SQL Admins'
  entraAdminPrincipalType: 'Group'
}

param storage = {
  name: 'stepckgdev01'
  rawContainer: 'raw'
  curatedContainer: 'curated'
  enrichedContainer: 'enriched'
  publicNetworkAccess: 'Enabled'
}

param serviceBus = {
  name: 'sb-epckg-dev'
  skuName: 'Standard'
  skuTier: 'Standard'
  ingestQueueName: 'document-ingest'
  enrichQueueName: 'document-enrich'
}

param search = {
  name: 'srch-epckg-dev'
  sku: 'basic'
  replicaCount: 1
  partitionCount: 1
}

param ai = {
  aiServicesName: 'ais-epckg-dev'
  aiServicesCustomSubdomain: 'ais-epckg-dev'
  openAiName: 'oai-epckg-dev'
  openAiCustomSubdomain: 'oai-epckg-dev'
  aiSku: 'S0'
  openAiSku: 'S0'
}

param containerApps = {
  managedEnvironmentName: 'cae-epckg-dev'
  appName: 'ca-epckg-api-dev'
  containerImage: 'mcr.microsoft.com/azuredocs/containerapps-helloworld:latest'
  targetPort: 8000
  minReplicas: 1
  maxReplicas: 2
  cpu: 0.5
  memory: '1Gi'
  externalIngress: true
  infrastructureSubnetResourceId: ''
}

param monitoring = {
  logAnalyticsWorkspaceName: 'log-epckg-dev'
  appInsightsName: 'appi-epckg-dev'
}
