import React from 'react';
import Plot from 'react-plotly.js';
import { ChartWrapper } from './ChartWrapper.jsx';
import { DEFAULT_LAYOUT, DEFAULT_CONFIG, getBarData, THREESIXTY_COLOURS } from './ChartUtils.jsx';

export const AwardDate = function (props) {

    var data = props.data.map(o => ({
        date: new Date(o.bucketId),
        grants: o.grants
    }));
    var maxDate = new Date(Math.max(...data.map(o => o.date)));
    var minDate = new Date(Math.min(...data.map(o => o.date)));

    if (maxDate.getFullYear() == minDate.getFullYear() && maxDate.getMonth() == minDate.getMonth()){
        return <div className=''>
            <h2 className='results-page__body__section-title'>Award Date</h2>
            <div className='results-page__body__section-note'>
                <p>All grants were awarded in {maxDate.getFullYear()}</p>
            </div>
        </div>
    }

    const xbinsSizes = [
        ['M1', 'by month'],
        ['M3', 'by quarter'],
        ['M12', 'by year']
    ];

    var xbinsSize = 'M1';
    if(maxDate.getFullYear() - minDate.getFullYear() >= 5){
        xbinsSize = 'M12';
    } else if (maxDate.getFullYear() - minDate.getFullYear() >= 1){
        xbinsSize = 'M3';
    }

    const chartData = [{
        autobinx: false,
        autobiny: true,
        marker: {
            color: THREESIXTY_COLOURS[1]
        },
        name: 'date',
        type: 'histogram',
        xbins: {
            start: minDate.getFullYear().toString() + '-01-01',
            end: maxDate.getFullYear().toString() + '-12-31',
            size: xbinsSize
        },
        x: data.map(o => Array(o.grants).fill(o.date)).flat(1)
    }];

    const updatemenus = [{
        x: 0.1,
        y: 1.15,
        xref: 'paper',
        yref: 'paper',
        yanchor: 'top',
        active: xbinsSizes.map(b => b[0]).find(b => b == xbinsSize),
        showactive: true,
        buttons: xbinsSizes.map(b => (
            {
                args: ['xbins.size', b[0]],
                label: b[1],
                method: 'restyle',
            }
        ))
    }]

    var layout = Object.assign({}, DEFAULT_LAYOUT);
    layout['updatemenus'] = updatemenus;
    layout['xaxis']['type'] = 'date';
    layout['yaxis']['visible'] = true;
    layout['yaxis']['showline'] = false;
    
    return <ChartWrapper title="Awards over time" subtitle="(number of grants)">
        <Plot
            id='awards_over_time'
            data={chartData}
            layout={layout}
            config={DEFAULT_CONFIG}
        />
    </ChartWrapper>
;

}