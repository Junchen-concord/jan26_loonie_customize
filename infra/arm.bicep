param containerapps_sim_bureau_model_name string = 'sim-bureau-model'
param managedEnvironments_Simulator_Internal_CE_externalid string = '/subscriptions/433b92bc-63fa-44cc-a808-4c125a646079/resourceGroups/Simulator_RG/providers/Microsoft.App/managedEnvironments/Simulator-Internal-CE'

resource containerapps_sim_bureau_model_name_resource 'Microsoft.App/containerapps@2024-10-02-preview' = {
  name: containerapps_sim_bureau_model_name
  location: 'Central US'
  kind: 'containerapps'
  identity: {
    type: 'None'
  }
  properties: {
    managedEnvironmentId: managedEnvironments_Simulator_Internal_CE_externalid
    environmentId: managedEnvironments_Simulator_Internal_CE_externalid
    workloadProfileName: 'Consumption'
    configuration: {
      secrets: [
        {
          name: 'reg-pswd-61957432-a481'
        }
      ]
      activeRevisionsMode: 'Single'
      ingress: {
        external: true
        targetPort: 8080
        exposedPort: 0
        transport: 'Auto'
        traffic: [
          {
            weight: 100
            latestRevision: true
          }
        ]
        allowInsecure: false
        stickySessions: {
          affinity: 'none'
        }
      }
      registries: [
        {
          server: 'dmasimulatoracr.azurecr.io'
          username: 'DMASimulatorACR'
          passwordSecretRef: 'reg-pswd-61957432-a481'
        }
      ]
      identitySettings: []
      maxInactiveRevisions: 100
    }
    template: {
      containers: [
        {
          image: 'dmasimulatoracr.azurecr.io/bureaumodel:1.0.1'
          imageType: 'ContainerImage'
          name: containerapps_sim_bureau_model_name
          resources: {
            cpu: json('0.5')
            memory: '1Gi'
          }
          probes: [
            {
              type: 'Liveness'
              httpGet: {
                path: '/liveness'
                port: 8080
                scheme: 'HTTP'
              }
              periodSeconds: 10
            }
            {
              type: 'Readiness'
              httpGet: {
                path: '/readiness'
                port: 8080
                scheme: 'HTTP'
              }
              periodSeconds: 10
            }
          ]
        }
      ]
      scale: {
        minReplicas: 0
        maxReplicas: 10
        cooldownPeriod: 300
        pollingInterval: 30
      }
      volumes: []
    }
  }
}
