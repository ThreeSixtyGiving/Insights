import React from 'react';
import { FunderNames } from './Results/FunderNames.jsx'
import { SummaryList } from './Results/SummaryList.jsx'

export const DashboardHeader = function(props) {
    return <section id="dashboard-header" className="results-page__body__content">
        <FunderNames summary={props.summary} byFunder={props.byFunder} />
        <SummaryList summary={props.summary} />
        <div className="results-page__body__section-attribution">
            <p><strong>From the 360Giving data registry</strong></p>
            <p>
                Published by
                            <a href="http://www.essexcommunityfoundation.org.uk/index.php"
                    target="_blank">Essex Community Foundation</a>
                with a
                            <a href="https://creativecommons.org/licenses/by/4.0/"
                    target="_blank">Creative Commons Attribution 4.0 International (CC BY 4.0)</a>
                licence.
                        </p>
            <p><a href="http://www.essexcommunityfoundation.org.uk/images/uploads/ECF_Grants_Awarded.xlsx"
                target="_blank">Download original file</a>(xlsx)
                        </p>
        </div>
    </section>
}
