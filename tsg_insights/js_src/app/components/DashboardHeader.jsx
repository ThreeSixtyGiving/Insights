import React from 'react';

export const DashboardHeader = function(props) {
    return <section id="dashboard-header" className="results-page__body__content">
        <h5 className="results-page__body__content__grants-made-by">Grants made by {props.data.grants.summary[0].funders}</h5>
        <h1 className="results-page__body__content__header">
            <span className="results-page__body__content__title funder-title"
                style={{ opacity: 1 }}></span>
            <span className="date-prefix"> between </span>
            <span className="results-page__body__content__date date-range"></span>
        </h1>
        <div className="results-page__body__content__spheres">
            <div className="results-page__body__content__sphere" style={{ backgroundColor: 'rgb(156, 32, 97)' }}>
                <p className="total-grants"></p>
                <h4 className="">grants</h4>
            </div>
            <div className="results-page__body__content__sphere" style={{ backgroundColor: 'rgb(244, 131, 32)' }}>
                <p className="total-recipients"></p>
                <h4 className="">recipients</h4>
            </div>
            <div className="results-page__body__content__sphere" style={{ backgroundColor: 'rgb(83, 170, 221)' }}>
                <p className="total-amount"></p>
                <h4 className="total-amount-suffix"></h4>
                <h4 className="">Total</h4>
            </div>
            <div className="results-page__body__content__sphere"
                style={{ backgroundColor: 'rgb(205, 220, 43)', color: 'rgb(11, 40, 51)' }}>
                <p className="mean-amount"></p>
                <h4 className="mean-amount-suffix"></h4>
                <h4 className="">(Average grant)</h4>
            </div>
        </div>
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
