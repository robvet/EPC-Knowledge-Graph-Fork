param location string
param storage object
param tags object = {}

resource account 'Microsoft.Storage/storageAccounts@2023-05-01' = {
  name: storage.name
  location: location
  tags: tags
  kind: 'StorageV2'
  sku: {
    name: 'Standard_LRS'
  }
  properties: {
    accessTier: 'Hot'
    allowBlobPublicAccess: false
    allowSharedKeyAccess: false
    defaultToOAuthAuthentication: true
    isHnsEnabled: true
    minimumTlsVersion: 'TLS1_2'
    publicNetworkAccess: storage.publicNetworkAccess
    supportsHttpsTrafficOnly: true
  }
}

resource blobService 'Microsoft.Storage/storageAccounts/blobServices@2023-05-01' = {
  name: 'default'
  parent: account
}

resource rawContainer 'Microsoft.Storage/storageAccounts/blobServices/containers@2023-05-01' = {
  name: storage.rawContainer
  parent: blobService
  properties: {
    publicAccess: 'None'
  }
}

resource curatedContainer 'Microsoft.Storage/storageAccounts/blobServices/containers@2023-05-01' = {
  name: storage.curatedContainer
  parent: blobService
  properties: {
    publicAccess: 'None'
  }
}

resource enrichedContainer 'Microsoft.Storage/storageAccounts/blobServices/containers@2023-05-01' = {
  name: storage.enrichedContainer
  parent: blobService
  properties: {
    publicAccess: 'None'
  }
}

output id string = account.id
output name string = account.name
output blobEndpoint string = account.properties.primaryEndpoints.blob
