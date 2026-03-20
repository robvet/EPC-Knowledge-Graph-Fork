param location string
param containerApps object
param tags object = {}
param userAssignedIdentityId string
param appInsightsConnectionString string
param postgresHost string
param postgresDatabaseName string
param searchEndpoint string
param searchIndexName string
param aiServicesEndpoint string
param openAiEndpoint string
param serviceBusNamespace string
param ingestQueueName string
param enrichQueueName string
param storageAccountName string
param rawContainerName string
param curatedContainerName string
param enrichedContainerName string

var useDedicatedSubnet = !empty(containerApps.infrastructureSubnetResourceId)

resource environment 'Microsoft.App/managedEnvironments@2024-03-01' = {
  name: containerApps.managedEnvironmentName
  location: location
  tags: tags
  properties: union({
    peerAuthentication: {
      mtls: {
        enabled: true
      }
    }
    peerTrafficConfiguration: {
      encryption: {
        enabled: true
      }
    }
  }, useDedicatedSubnet ? {
    vnetConfiguration: {
      infrastructureSubnetId: containerApps.infrastructureSubnetResourceId
      internal: false
    }
  } : {})
}

resource app 'Microsoft.App/containerApps@2024-03-01' = {
  name: containerApps.appName
  location: location
  identity: {
    type: 'UserAssigned'
    userAssignedIdentities: {
      '${userAssignedIdentityId}': {}
    }
  }
  tags: tags
  properties: {
    environmentId: environment.id
    configuration: {
      activeRevisionsMode: 'Single'
      ingress: {
        allowInsecure: false
        external: containerApps.externalIngress
        targetPort: containerApps.targetPort
        traffic: [
          {
            latestRevision: true
            weight: 100
          }
        ]
      }
    }
    template: {
      containers: [
        {
          name: 'epc-api'
          image: containerApps.containerImage
          env: [
            {
              name: 'APP_MODE'
              value: 'azure'
            }
            {
              name: 'APP_ENVIRONMENT'
              value: 'dev'
            }
            {
              name: 'APPLICATIONINSIGHTS_CONNECTION_STRING'
              value: appInsightsConnectionString
            }
            {
              name: 'AZURE_OPENAI_ENDPOINT'
              value: openAiEndpoint
            }
            {
              name: 'AZURE_AI_SERVICES_ENDPOINT'
              value: aiServicesEndpoint
            }
            {
              name: 'AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT'
              value: aiServicesEndpoint
            }
            {
              name: 'AZURE_CONTENT_UNDERSTANDING_ENDPOINT'
              value: aiServicesEndpoint
            }
            {
              name: 'AZURE_POSTGRES_HOST'
              value: postgresHost
            }
            {
              name: 'AZURE_POSTGRES_DATABASE'
              value: postgresDatabaseName
            }
            {
              name: 'AZURE_SEARCH_ENDPOINT'
              value: searchEndpoint
            }
            {
              name: 'AZURE_SEARCH_INDEX'
              value: searchIndexName
            }
            {
              name: 'AZURE_STORAGE_ACCOUNT_NAME'
              value: storageAccountName
            }
            {
              name: 'AZURE_STORAGE_RAW_CONTAINER'
              value: rawContainerName
            }
            {
              name: 'AZURE_STORAGE_CURATED_CONTAINER'
              value: curatedContainerName
            }
            {
              name: 'AZURE_STORAGE_ENRICHED_CONTAINER'
              value: enrichedContainerName
            }
            {
              name: 'AZURE_SERVICEBUS_NAMESPACE'
              value: serviceBusNamespace
            }
            {
              name: 'AZURE_SERVICEBUS_INGEST_QUEUE'
              value: ingestQueueName
            }
            {
              name: 'AZURE_SERVICEBUS_ENRICH_QUEUE'
              value: enrichQueueName
            }
          ]
          resources: {
            cpu: containerApps.cpu
            memory: containerApps.memory
          }
        }
      ]
      scale: {
        minReplicas: containerApps.minReplicas
        maxReplicas: containerApps.maxReplicas
      }
    }
  }
}

output appName string = app.name
output appUrl string = 'https://${app.properties.latestRevisionFqdn}'
