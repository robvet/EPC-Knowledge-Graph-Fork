param location string
param postgres object
param tags object = {}

var usePrivateNetwork = !empty(postgres.delegatedSubnetResourceId) && !empty(postgres.privateDnsZoneResourceId)

resource server 'Microsoft.DBforPostgreSQL/flexibleServers@2024-08-01' = {
  name: postgres.name
  location: location
  tags: tags
  sku: {
    name: postgres.skuName
    tier: postgres.skuTier
  }
  properties: {
    authConfig: {
      activeDirectoryAuth: 'Enabled'
      passwordAuth: 'Disabled'
      tenantId: tenant().tenantId
    }
    availabilityZone: postgres.availabilityZone
    backup: {
      backupRetentionDays: postgres.backupRetentionDays
      geoRedundantBackup: 'Disabled'
    }
    highAvailability: {
      mode: 'Disabled'
    }
    network: usePrivateNetwork
      ? {
          delegatedSubnetResourceId: postgres.delegatedSubnetResourceId
          privateDnsZoneArmResourceId: postgres.privateDnsZoneResourceId
          publicNetworkAccess: 'Disabled'
        }
      : {
          publicNetworkAccess: postgres.publicNetworkAccess
        }
    storage: {
      storageSizeGB: postgres.storageSizeGB
    }
    version: postgres.version
  }
}

resource database 'Microsoft.DBforPostgreSQL/flexibleServers/databases@2024-08-01' = {
  name: postgres.databaseName
  parent: server
  properties: {
    charset: 'UTF8'
    collation: 'en_US.utf8'
  }
}

resource entraAdmin 'Microsoft.DBforPostgreSQL/flexibleServers/administrators@2024-08-01' = {
  name: postgres.entraAdminObjectId
  parent: server
  properties: {
    principalName: postgres.entraAdminPrincipalName
    principalType: postgres.entraAdminPrincipalType
    tenantId: tenant().tenantId
  }
}

resource ageExtension 'Microsoft.DBforPostgreSQL/flexibleServers/configurations@2024-08-01' = {
  name: 'azure.extensions'
  parent: server
  properties: {
    source: 'user-override'
    value: 'AGE'
  }
}

output serverName string = server.name
output host string = '${server.name}.postgres.database.azure.com'
output databaseName string = database.name
