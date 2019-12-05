import React from 'react';
import Plot from 'react-plotly.js';
import { ChartWrapper } from './ChartWrapper.jsx';
import { DEFAULT_LAYOUT, DEFAULT_CONFIG, getBarData, THREESIXTY_COLOURS } from './ChartUtils.jsx';


export const AmountAwarded = function (props) {

    var byCurrency = {};
    var byCurrencyTotal = {};
    for(var i of props.data){
        if(!Object.keys(byCurrency).includes(i.bucketId)){
            byCurrency[i.bucketId] = {};
            byCurrencyTotal[i.bucketId] = 0;
        }
        byCurrency[i.bucketId][i.bucket2Id] = i.grants;
        byCurrencyTotal[i.bucketId] += i.grants;
    }
    var currencySort = Object.keys(byCurrencyTotal).sort((a, b) => (byCurrencyTotal[b] - byCurrencyTotal[a]));

    var awardBands = [
        'Under £500',
        '£500 - £1k',
        '£1k - £2k',
        '£2k - £5k',
        '£5k - £10k',
        '£10k - £100k',
        '£100k - £1m',
        'Over £1m',
    ];

    var colours = {
        "GBP": 0,
        "USD": 1,
        "EUR": 2,
    }
    var units = '(number of grants)';
    if (currencySort.length > 1 || !["GBP", "EUR", "USD"].includes(currencySort[0])) {
        awardBands = awardBands.map(b => b.replace("£", ""))
        units += ' Currencies: ' + currencySort.join(", ")
    } else if (currencySort.includes("USD")) {
        awardBands = awardBands.map(b => b.replace("£", "$"))
        units += ' Currencies: ' + currencySort.join(", ")
    } else if (currencySort.includes("EUR")) {
        awardBands = awardBands.map(b => b.replace("£", "€"))
        units += ' Currencies: ' + currencySort.join(", ")
    }

    var bars = currencySort.map((o, i) => {
        var vals = byCurrency[o];
        return getBarData({
            x: awardBands,
            y: awardBands.map(b => vals[b.replace(/[£\$€]/g, '')] ? vals[b.replace(/[£\$€]/g, '')] : 0),
            text: awardBands,
            visible: (i == 0) ? null : 'legendonly',
            name: `${o} (${byCurrencyTotal[o]}${(i==0) ? ' grants' : ''})`,
            marker: {
                color: THREESIXTY_COLOURS[(colours[o] || i + 3) % THREESIXTY_COLOURS.length]
            }
        })
    });

    return <ChartWrapper title="Amount awarded" subtitle="(number of grants)">
        <Plot
            id='amount_awarded'
            data={bars}
            layout={DEFAULT_LAYOUT}
            config={DEFAULT_CONFIG}
        />
    </ChartWrapper>

}