import React from 'react';
import { Query } from 'react-apollo';
import gql from 'graphql-tag';
import { fetchGrants } from '../queries/fetchGrants.gql';
import { PageHeader } from './PageHeader.jsx';
import { Sidebar } from './Sidebar.jsx';
import { DashboardHeader } from './DashboardHeader.jsx';
import { DashboardOutput } from './DashboardOutput.jsx';
import { WhatsNext } from './WhatsNext.jsx';
import { DashboardFooter } from './DashboardFooter.jsx';

export const Dashboard = function(props) {
    return <Query
        query={fetchGrants}
        variables={{
            dataset: "main",
            area: ["E92000001"],
            // funders: ["GB-CHC-210037", "GB-CHC-251988"], // different currencies
            // funders: ["360G-ArcadiaFund"] // in USD
        }}>
        {({ loading, error, data }) => {
            if (loading) return <p>Good things take time....</p>
            if (error) return <p>Something went wrong...</p>
            return <React.Fragment>
                <PageHeader />
                <div className="results-page__app">
                    <Sidebar />
                    <div className="results-page__body">
                        <section id="dashboard-output" className="results-page__body__content">
                            <DashboardHeader summary={data.grants.summary[0]} byFunder={data.grants.byFunder} />
                            <DashboardOutput data={data.grants} />
                        </section>
                        <WhatsNext />
                        <DashboardFooter />
                    </div>
                </div>
            </React.Fragment>
        }}
    </Query>
}