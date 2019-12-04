import React from 'react';
import ReactDOM from 'react-dom';
import ApolloClient from 'apollo-boost';
import { ApolloProvider } from 'react-apollo';
import { Dashboard } from './components/Dashboard.jsx';

const client = new ApolloClient({
    uri: '/api/graphql',
})

ReactDOM.render(
    <ApolloProvider client={client}>
        <Dashboard />
    </ApolloProvider>,
    document.getElementById('dashboard-container')
);