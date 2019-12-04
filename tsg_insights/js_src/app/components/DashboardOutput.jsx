import React from 'react';
import { FunderType } from './Results/FunderType.jsx'
import { Funders } from './Results/Funders.jsx'

export const DashboardOutput = function(props) {
    return <React.Fragment>
        <FunderType data={props.data.byFunderType} />
        <Funders data={props.data.byFunder} />
    </React.Fragment>
}
