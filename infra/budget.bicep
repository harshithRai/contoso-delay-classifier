targetScope = 'resourceGroup'
@description('Monthly alert threshold in your subscription billing currency; this does not cap spending.')
param amount int = 1000
param email string
@description('First day of this month, e.g. 2026-10-01T00:00:00Z.')
param startDate string
param endDate string = '2027-10-01T00:00:00Z'
resource budget 'Microsoft.Consumption/budgets@2023-11-01' = {
  name: 'contoso-assignment-budget'
  properties: {
    category: 'Cost'
    amount: amount
    timeGrain: 'Monthly'
    timePeriod: { startDate: startDate, endDate: endDate }
    notifications: {
      actual80: {
        enabled: true
        operator: 'GreaterThanOrEqualTo'
        threshold: 80
        contactEmails: [email]
        thresholdType: 'Actual'
      }
      actual100: {
        enabled: true
        operator: 'GreaterThanOrEqualTo'
        threshold: 100
        contactEmails: [email]
        thresholdType: 'Actual'
      }
    }
  }
}
