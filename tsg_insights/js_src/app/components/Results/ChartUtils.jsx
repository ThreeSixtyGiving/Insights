import _ from 'lodash';

export const THREESIXTY_COLOURS = ['#9c2061', '#f48320', '#cddc2b', '#53aadd'];

export const DEFAULT_LAYOUT = {
    font: {
        family: 'neusa-next-std-compact, "Source Sans Pro", sans-serif;',
        size: 18
    },
    yaxis: {
        visible: false,
        showgrid: false,
        showline: false,
        layer: 'below traces',
        linewidth: 0,
        tickfont: {
            size: 20
        },
    },
    xaxis: {
        automargin: true,
        showgrid: false,
        showline: false,
        layer: 'below traces',
        linewidth: 0,
        tickfont: {
            size: 20
        },
    },
    margin: {
        l: 40,
        r: 24,
        b: 40,
        t: 24,
        pad: 4
    },
};

export const DEFAULT_CONFIG = {
    displayModeBar: 'hover',
    modeBarButtons: [[
        'toImage', 'sendDataToCloud'
    ]],
    scrollZoom: 'gl3d',
}

export const getBarData = function(options) {
    let defaults = {
        textposition: 'outside',
        cliponaxis: false,
        constraintext: 'none',
        textfont: {
            size: 18,
            family: 'neusa-next-std-compact, sans-serif;',
        },
        hoverinfo: 'text+x',
        type: 'bar',
        marker: {
            color: THREESIXTY_COLOURS[0]
        },
        fill: 'tozeroy',
    }

    options = _.defaultsDeep(options, defaults);

    if (options['type'] == 'column') {
        options['type'] = 'bar';
        options['orientation'] = 'h';
        options['hoverinfo'] = 'text';
        var x = options['x'].slice(0);
        options['x'] = options['y'].slice(0);
        options['y'] = x.slice(0);
    }

    return options;
}