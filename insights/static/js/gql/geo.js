import { queryHeader } from './query.js'

export const GEO_GQL = `
${queryHeader('geoGrants', 'grants')} {
    insightsGeoLat
    insightsGeoLong
    amountAwarded
    awardDate
    currency
    recipientOrganizationName
    fundingOrganizationName
  }
}`