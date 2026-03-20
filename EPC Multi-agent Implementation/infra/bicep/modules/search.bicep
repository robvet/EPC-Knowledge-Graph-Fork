param location string
param search object
param tags object = {}

resource service 'Microsoft.Search/searchServices@2023-11-01' = {
  name: search.name
  location: location
  identity: {
    type: 'SystemAssigned'
  }
  sku: {
    name: search.sku
  }
  tags: tags
  properties: {
    disableLocalAuth: true
    hostingMode: 'default'
    partitionCount: search.partitionCount
    replicaCount: search.replicaCount
  }
}

output id string = service.id
output endpoint string = 'https://${service.name}.search.windows.net'
