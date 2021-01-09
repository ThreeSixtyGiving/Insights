export function queryHeader(queryName, queryType){
  return `
  query ${queryName}(
      $dataset: String!,
      $funders: [String],
      $publishers: [String],
      $files: [String],
      $awardAmount: MaxMin,
      $awardDates: MaxMinDate,
      $search: String!,
      $area: [String],
      $orgtype: [String],
      $grantProgrammes: [String],
      $funderTypes: [String],
      $orgSize: MaxMin,
    ) {
        ${queryType}(
          dataset: $dataset,
          funders: $funders,
          publishers: $publishers,
          files: $files,
          awardAmount: $awardAmount,
          awardDates: $awardDates,
          q: $search,
          area: $area,
          orgtype: $orgtype,
          grantProgrammes: $grantProgrammes,
          funderTypes: $funderTypes,
          orgSize: $orgSize,
        ) `
}

export const GQL = `
${queryHeader('insightsData', 'grantAggregates')} {
        summary {
        grants
        recipients
        funders
        maxDate
        minDate
        currencies {
          currency
          total
          median
          mean
          grants
        }
      }
      bySource {
        bucketGroup {
          id
        }
      }
      byFunder {
        ...chartFields
      }
      byFunderType {
        ...chartFields
      }
      byGrantProgramme {
        ...chartFields
      }
      byAmountAwarded {
        ...chartFields
      }
      byAwardDate {
        ...chartFields
      }
      byOrgType {
        ...chartFields
      }
      byOrgSize {
        ...chartFields
      }
      byOrgAge {
        ...chartFields
      }
      byCountryRegion {
        ...chartFields
      }
      byGeoSource {
        ...chartFields
      }
    }
  }
  
fragment chartFields on GrantBucket {
  bucketGroup {
    id
    name
  }
  grants
  recipients
  currencies {
    total
    grants
  }
}
`

export function graphqlQuery(query, vars) {
    const formData = new FormData();
    formData.append('query', query);
    formData.append('variables', JSON.stringify(vars));
    return fetch(GRAPHQL_ENDPOINT, {
        method: 'POST',
        mode: 'same-origin',
        body: formData
    }).then((response) => response.json());
}