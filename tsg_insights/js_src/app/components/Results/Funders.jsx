import React from 'react';
import Plot from 'react-plotly.js';
import { ChartWrapper } from './ChartWrapper.jsx';
import { DEFAULT_LAYOUT, DEFAULT_CONFIG, getBarData } from './ChartUtils.jsx';


export const Funders = function (props) {

    var layout = Object.assign({}, DEFAULT_LAYOUT);
    var chart_type = 'bar';
    props.data.sort((a, b) => (a.grants - b.grants));

    if(props.data.length <= 1){
        return null;
    } else if(props.data.length > 14){
        props.data.reverse();
        var description = 'Showing 10 largest funders of ' + props.data.length;
        return <ChartWrapper title="Funders" subtitle="(number of grants)" description={description}>
            <p>
                {props.data.slice(0, 10).map((o, i) =>
                    <span style={{marginRight: '6px'}} key={i}>
                        <span className='results-page__body__content__title'
                            style={{ fontSize: '1.2rem', lineHeight: '12px' }}>
                            {o.bucket2Id} 
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
    } else if (props.data.length > 5) {
        layout.yaxis.visible = true;
        layout.yaxis.automargin = true;
        layout.xaxis.visible = false;
        chart_type = 'column';
        props.data.reverse();
    }

    return <ChartWrapper title="Funders" subtitle="(number of grants)">
        <Plot 
            id='funders'
            data={[getBarData({
                x: props.data.map(o => o.bucket2Id), 
                y: props.data.map(o => o.grants), 
                text: props.data.map(o => o.grants.toLocaleString(undefined, { maximumFractionDigits: 0 })),
                name: 'Funders',
                type: chart_type
            })]}
            layout={layout}
            config={DEFAULT_CONFIG}
        />
    </ChartWrapper>

}