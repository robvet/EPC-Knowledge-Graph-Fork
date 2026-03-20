param location string
param serviceBus object
param tags object = {}

resource namespace 'Microsoft.ServiceBus/namespaces@2024-01-01' = {
  name: serviceBus.name
  location: location
  tags: tags
  sku: {
    name: serviceBus.skuName
    tier: serviceBus.skuTier
  }
  properties: {
    minimumTlsVersion: '1.2'
    publicNetworkAccess: 'Enabled'
  }
}

resource ingestQueue 'Microsoft.ServiceBus/namespaces/queues@2024-01-01' = {
  name: serviceBus.ingestQueueName
  parent: namespace
  properties: {
    deadLetteringOnMessageExpiration: true
    lockDuration: 'PT1M'
    maxDeliveryCount: 10
    requiresDuplicateDetection: false
  }
}

resource enrichQueue 'Microsoft.ServiceBus/namespaces/queues@2024-01-01' = {
  name: serviceBus.enrichQueueName
  parent: namespace
  properties: {
    deadLetteringOnMessageExpiration: true
    lockDuration: 'PT1M'
    maxDeliveryCount: 10
    requiresDuplicateDetection: false
  }
}

output id string = namespace.id
output name string = namespace.name
output namespaceFqdn string = '${namespace.name}.servicebus.windows.net'
