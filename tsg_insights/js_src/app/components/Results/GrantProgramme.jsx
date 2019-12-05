import React from 'react';
import Plot from 'react-plotly.js';
import { ChartWrapper } from './ChartWrapper.jsx';
import { DEFAULT_LAYOUT, DEFAULT_CONFIG, getBarData } from './ChartUtils.jsx';
import _ from 'lodash';


export const GrantProgramme = function (props) {

    var layout = _.defaultsDeep({}, DEFAULT_LAYOUT);
    var config = _.defaultsDeep({}, DEFAULT_CONFIG);
    var chartType = 'bar';
    var data = props.data.filter(o => o.bucketGroup[0].name);
    data.sort((a, b) => (b.grants - a.grants));

    if (data.length <= 1) {
        return null;
    } else if (data.length > 14) {
        data.reverse();
        var description = 'Showing 10 largest grant programmes of ' + data.length;
        return <ChartWrapper title="Grant programmes" subtitle="(number of grants)" description={description}>
            <p>
                {data.slice(0, 10).map((o, i) =>
                    <span style={{ marginRight: '6px' }} key={i}>
                        <span className='results-page__body__content__title'
                            style={{ fontSize: '1.2rem', lineHeight: '12px' }}>
                            {o.bucketGroup[0].name}
                        </span>
                        {" ("}
                        <span>
                            {o.grants.toLocaleString(undefined, { maximumFractionDigits: 0 })}
                            {i == 0 ? " grants" : null}
                        </span>)
                    </span>
                )}
            </p>
        </ChartWrapper>
    } else if (data.length > 5) {
        layout.yaxis.visible = true;
        layout.yaxis.automargin = true;
        layout.xaxis.visible = false;
        chartType = 'column';
        data = data.reverse();
    }

    return <ChartWrapper title="Grant programmes" subtitle="(number of grants)">
        <Plot 
            id='grant_programmes'
            data={[getBarData({
                x: data.map(o => o.bucketGroup[0].name), 
                y: data.map(o => o.grants), 
                text: data.map(o => o.grants.toLocaleString(undefined, { maximumFractionDigits: 0 })),
                name: 'Grant programmes',
                type: chartType
            })]}
            style={{ width: '100%' }}
            layout={layout}
            config={config}
        />
    </ChartWrapper>

}