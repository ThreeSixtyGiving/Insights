export const SOURCE_GQL = `
query($sources: [String]!) {
    sourceFiles(ids: $sources){
      id
      title
      issued
      modified
      license
      licenseName
      description
      publisher {
        website
        name
      }
      distribution {
        accessURL
        downloadURL
      }
    }
  }
`