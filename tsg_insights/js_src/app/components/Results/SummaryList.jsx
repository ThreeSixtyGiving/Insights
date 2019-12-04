import React from 'react';
import pluralize from 'pluralize'
import { formatCurrency } from '../../Utils.js'
 
export const SummaryList = function (props) {

    var currencies = props.summary.currencies.sort((a, b) => (b.total - a.total));
    var mainCurrency = currencies[0];
    var otherCurrencies = currencies.filter(x => (x.currency != mainCurrency.currency));

    var others = [
        <p>*mean</p>
    ];

    if(otherCurrencies.length > 0){
        others.push(
            <p key='currency-explanation-multiple'>
                These results include grants in {currencies.length} currencies.
                The amounts above refer to {pluralize('grant', mainCurrency.grants, true)} grants in {mainCurrency.currency}.
                <br />
                There is also 
                {otherCurrencies.map((c, i) => [
                    i > 0 && ", ",
                    <React.Fragment key={i}> {formatCurrency(c.total, {currency: c.currency}).join("")} in {c.grants} {pluralize('grant', c.grants)}</React.Fragment>
                ])}
                .
            </p>
        )
    } else if(mainCurrency.currency != 'GBP'){
        others.push(
            <p key='currency-explanation-single'>
                These results show grants made in {mainCurrency.currency}.
            </p>
        )
    }

    var total = formatCurrency(mainCurrency.total, { currency: mainCurrency.currency, suffix: 'long' });
    var average = formatCurrency(mainCurrency.mean, { currency: mainCurrency.currency, suffix: 'long' });

    return <React.Fragment>
        <div className="results-page__body__content__spheres">
            <div className="results-page__body__content__sphere" style={{ backgroundColor: 'rgb(156, 32, 97)' }}>
                <p className="total-grants">{props.summary.grants.toLocaleString(undefined, { maximumFractionDigits: 0 })}</p>
                <h4 className="">{pluralize('grants', props.summary.grants)}</h4>
            </div>
            <div className="results-page__body__content__sphere" style={{ backgroundColor: 'rgb(244, 131, 32)' }}>
                <p className="total-recipients">{props.summary.recipients.toLocaleString(undefined, { maximumFractionDigits: 0 })}</p>
                <h4 className="">{pluralize('recipients', props.summary.recipients)}</h4>
            </div>
            <div className="results-page__body__content__sphere" style={{ backgroundColor: 'rgb(83, 170, 221)' }}>
                <p className="total-amount">{total[0]}</p>
                <h4 className="total-amount-suffix">{total[1]}</h4>
                <h4 className="">Total</h4>
            </div>
            <div className="results-page__body__content__sphere"
                style={{ backgroundColor: 'rgb(205, 220, 43)', color: 'rgb(11, 40, 51)' }}>
                <p className="mean-amount">{average[0]}</p>
                <h4 className="mean-amount-suffix">{average[1]}</h4>
                <h4 className="">(Average grant)</h4>
            </div>
        </div>
        <div className='results-page__body__section-attribution'>
            {others}
        </div>
    </React.Fragment>
}