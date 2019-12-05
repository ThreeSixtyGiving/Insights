import React from 'react';
import pluralize from 'pluralize'

export const FunderNames = function (props) {

    var funderClass = '';
    var funderNames = props.byFunder.filter(x => x.bucketGroup[0].name).sort(function (a, b) {
        return a.grants - b.grants;
    }).map(x => x.bucketGroup[0].name);

    if (funderNames.length > 5) {
        var funders = <span className={funderClass}>
            {funderNames.length.toLocaleString(undefined, { maximumFractionDigits: 0 })} funders
        </span>
    } else if (funderNames) {
        var funders = funderNames.map((f, i) => [
            i > 0 && ", ",
            <span key={i} className={funderClass}>{f}</span>
        ]);
    }

    var years = {
        min: props.summary.minDate.slice(0, 4),
        max: props.summary.maxDate.slice(0, 4)
    };
    if (years.min == years.max) {
        years = [
            " in ",
            <span className='results-page__body__content__date'>{years.max}</span>
        ]
    } else {
        years = [
            " between ",
            <span className='results-page__body__content__date'>{years.min} and {years.max}</span>
        ]
    }

    return <React.Fragment>
        <h5 className="results-page__body__content__grants-made-by">
            {/* {props.summary.grants.toLocaleString(undefined, { maximumFractionDigits: 0 })}  */}
            {pluralize("grant", props.summary.grants)} made by
        </h5>
        <h1 className="results-page__body__content__header">
            <span className="results-page__body__content__title funder-title"
                style={{ opacity: 1 }}>{funders}</span>
            <span className="date-prefix">{years[0]}</span>
            {years[1]}
        </h1>
    </React.Fragment>
}