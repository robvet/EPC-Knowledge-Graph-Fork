param location string
param ai object
param tags object = {}

resource aiServices 'Microsoft.CognitiveServices/accounts@2024-10-01' = {
  name: ai.aiServicesName
  location: location
  kind: 'AIServices'
  sku: {
    name: ai.aiSku
  }
  tags: tags
  properties: {
    customSubDomainName: ai.aiServicesCustomSubdomain
    disableLocalAuth: true
    publicNetworkAccess: 'Enabled'
  }
}

resource openAi 'Microsoft.CognitiveServices/accounts@2024-10-01' = {
  name: ai.openAiName
  location: location
  kind: 'OpenAI'
  sku: {
    name: ai.openAiSku
  }
  tags: tags
  properties: {
    customSubDomainName: ai.openAiCustomSubdomain
    disableLocalAuth: true
    publicNetworkAccess: 'Enabled'
  }
}

output aiServicesEndpoint string = aiServices.properties.endpoint
output openAiEndpoint string = openAi.properties.endpoint
