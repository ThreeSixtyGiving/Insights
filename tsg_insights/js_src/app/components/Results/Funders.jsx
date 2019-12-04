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
        return <ChartWrapper title="Funders" subtitle="(number of grants)">
            
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