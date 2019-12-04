import React from 'react';
import { Query } from 'react-apollo';
import gql from 'graphql-tag';
import { PageHeader } from './PageHeader.jsx';
import { Sidebar } from './Sidebar.jsx';
import { DashboardHeader } from './DashboardHeader.jsx';
import { DashboardOutput } from './DashboardOutput.jsx';
import { WhatsNext } from './WhatsNext.jsx';
import { DashboardFooter } from './DashboardFooter.jsx';

const fetchGrants = gql`

    fragment bucket on GrantBucket {
        bucketId
        grants
        recipients
        funders
        grantAmount {
            currency
            value
        }
    }

    query fetchGrants(
        $dataset: String!, 
        $funders: [String],
        $grantProgrammes: [String], 
        $area: [String], 
        $orgtype: [String]
    ){
        grants(
            dataset: $dataset,
            funders: $funders,
            grantProgrammes: $grantProgrammes,
            area: $area,
            orgtype: $orgtype
        ) {
            summary {
                ...bucket
            }
            byFunder {
                ...bucket
            }
            byFunderType {
                ...bucket
            }
        }
    }
`;

export const Dashboard = function(props) {
    return <Query
        query={fetchGrants}
        variables={{
            dataset: "main",
            area: "E92000001"
        }}>
        {({ loading, error, data }) => {
            if (loading) return <p>Good things take time....</p>
            if (error) return <p>Something went wrong...</p>
            return <React.Fragment>
                <PageHeader />
                <div className="results-page__app">
                    <Sidebar />
                    <div className="results-page__body">
                        <DashboardHeader data={data} />
                        <DashboardOutput />
                        <WhatsNext />
                        <DashboardFooter />
                    </div>
                </div>
            </React.Fragment>
        }}
    </Query>
}