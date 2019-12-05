import React from 'react';
import { FunderType } from './Results/FunderType.jsx'
import { Funders } from './Results/Funders.jsx'
import { GrantProgramme } from './Results/GrantProgramme.jsx';
import { AmountAwarded } from './Results/AmountAwarded.jsx';
import { AwardDate } from './Results/AwardDate.jsx';

export const DashboardOutput = function(props) {
    return <React.Fragment>
        <FunderType data={props.data.byFunderType} />
        <Funders data={props.data.byFunder} />
        <AmountAwarded data={props.data.byAmountAwarded} />
        <GrantProgramme data={props.data.byGrantProgramme} />
        <AwardDate data={props.data.byAwardDate} />
    </React.Fragment>
}
