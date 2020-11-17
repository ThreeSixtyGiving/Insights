export function getAllFunders(dataset) {
    const formData = new FormData();
    formData.append('query', `
    query allFunders($dataset: String!, $funders: [String]) {
        grantAggregates(dataset: $dataset, funders: $funders) {
          byFunder {
            bucketGroup {
              id
              name
            }
            grants
          }
        }
      }
    `);
    formData.append('variables', JSON.stringify({ dataset }));
    return fetch(GRAPHQL_ENDPOINT, {
        method: 'POST',
        mode: 'same-origin',
        body: formData
    }).then((response) => response.json())
        .then((data) => data.data.grantAggregates.byFunder.map((f) => ({
            id: f.bucketGroup[0].id,
            name: f.bucketGroup[0].name,
            grants: f.grants,
        })));
}