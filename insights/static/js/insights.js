import { lineChart } from './components/line-chart.js';
import { barChart } from './components/bar-chart.js';
import { mapboxMap } from './components/map.js';
import { GQL, graphqlQuery } from './gql/query.js';
import { SOURCE_GQL } from './gql/sources.js';
import { GEO_GQL } from './gql/geo.js';
import { formatCurrency, formatDate, formatNumber, getAmountSuffix, formatNumberSuffix } from './components/filters.js';
import { debounce } from './lib/debounce.js';

const COLOURS = {
    yellow: "#EFC329",
    red: "#BC2C26",
    teal: "#4DACB6",
    orange: "#DE6E26",
}


Vue.component('bar-chart', barChart);
Vue.component('line-chart', lineChart);
Vue.component('mapbox-map', mapboxMap);
Vue.component('multi-select', window.VueMultiselect.default)

Vue.filter('formatCurrency', formatCurrency);
Vue.filter('formatDate', formatDate);
Vue.filter('formatNumber', formatNumber);
Vue.filter('getAmountSuffix', getAmountSuffix);
Vue.filter('formatNumberSuffix', formatNumberSuffix);

function initialFilters(useQueryParams) {
    if(useQueryParams){
        var params = new URLSearchParams(window.location.search);
    } else {
        var params = new URLSearchParams();
    }
    return {
        awardAmount: {
            min: params.get("awardAmount.min"),
            max: params.get("awardAmount.max"),
        },
        awardDates: {
            min: params.get("awardDates.min"),
            max: params.get("awardDates.max"),
        },
        orgSize: {
            min: params.get("orgSize.min"),
            max: params.get("orgSize.max"),
        },
        orgAge: {
            min: params.get("orgAge.min"),
            max: params.get("orgAge.max"),
        },
        search: params.get("search") || '',
        area: params.getAll("area"),
        orgtype: params.getAll("orgtype"),
        grantProgrammes: params.getAll("grantProgrammes"),
        funders: params.getAll("funders"),
        funderTypes: params.getAll("funderTypes"),
    }
}

var app = new Vue({
    el: '#data-display',
    delimiters: ["<%", "%>"],
    data() {
        return {
            dataset: DATASET,
            bin_labels: BIN_LABELS,
            loading: true,
            initialData: null,
            chartData: {},
            summary: {},
            default_currency: 'GBP',
            funders: [],
            base_filters: BASE_FILTERS,
            filters: initialFilters(true),
            source_ids: [],
            sources: [],
            showFilters: false,
            grants: [],
            mapUrl: PAGE_URLS['map'],
            dataUrl: PAGE_URLS['data'],
        }
    },
    computed: {
        computedFilters() {
            var filters = JSON.parse(JSON.stringify(this.filters));
            ['awardAmount', 'awardDates', 'orgSize', 'orgAge'].forEach((f) => {
                if (filters[f].min === '') { filters[f].min = null; }
                if (filters[f].max === '') { filters[f].max = null; }
            });
            ['area', 'orgtype', 'grantProgrammes', 'funders', 'funderTypes'].forEach((f) => {
                filters[f] = filters[f].map((v) => typeof v=="string" ? v : v.value );
                if (Array.isArray(BASE_FILTERS[f])) {
                    filters[f] = filters[f].concat(BASE_FILTERS[f]);
                    filters[f] = [...new Set(filters[f])];
                }
            });
            return filters;
        },
        funderList: function () {
            if (this.funders.length == 1) {
                return this.funders[0];
            }
            if (this.funders.length < 5) {
                return this.funders.slice(0, -1).join(', ') + " and " + this.funders.slice(-1);
            }
            if (this.funders.length > 0) {
                return `${formatNumber(this.funders.length)} funders`;
            }
            return 'No funders found'
        },
        currencyUsed: function () {
            var currencies = this.summary.currencies.map((c) => c.currency);
            if(currencies.length == 0){
                return this.default_currency;
            }
            if (currencies.includes(this.default_currency)) {
                return this.default_currency;
            }
            return currencies[0];
        },
        geoGrants: function () {
            var grants = this.grants.filter((g) => (g.insightsGeoLat != null && g.insightsGeoLong != null));
            if (grants.length == 0) { return null; }
            return grants;
        },
    },
    watch: {
        'source_ids': function (val, oldVal) {
            if (val.toString() != oldVal.toString()) {
                graphqlQuery(SOURCE_GQL, { 'sources': this.source_ids })
                    .then((data) => { app.sources = data.data.sourceFiles });
            }
        },
        'filters': {
            handler: debounce(function () {
                this.updateUrl();
                this.updateData();
            }, 1000),
            deep: true,
            immediate: true,
        },
    },
    methods: {
        updateUrl() {
            var queryParams = new URLSearchParams();
            Object.entries(this.filters)
                .filter(([k, v]) => v && v.length != 0)
                .forEach(([k, v]) => {
                    if (Array.isArray(v)) {
                        v.filter((w) => w && w.length != 0)
                            .forEach((w, i) => {
                                if(typeof w == "string"){
                                    queryParams.append(k, w);
                                } else {
                                    queryParams.append(k, w.value);
                                }
                            })
                    } else if (typeof v === 'object' && v !== null) {
                        Object.entries(v)
                            .filter(([l, w]) => w && w.length != 0)
                            .forEach(([l, w]) => {
                                queryParams.append(`${k}.${l}`, w);
                            })
                    } else {
                        queryParams.append(k, v);
                    }
                });
            if(queryParams.toString()){
                this.mapUrl = PAGE_URLS['map'] + '?' + queryParams.toString();
                this.dataUrl = PAGE_URLS['data'] + '?' + queryParams.toString();
            } else {
                this.mapUrl = PAGE_URLS['map'];
                this.dataUrl = PAGE_URLS['data'];
            }
            history.pushState(this.filters, '', "?" + queryParams.toString());
        },
        resetFilters() {
            this.filters = initialFilters(false);
        },
        updateData() {
            var app = this;
            app.loading = true;
            graphqlQuery(GQL, {
                dataset: app.dataset,
                ...app.base_filters,
                ...app.computedFilters,
            }).then((data) => {
                app.loading = false;
                Object.entries(data.data.grantAggregates).forEach(([key, value]) => {
                    if (key == "summary") {
                        app.summary = value[0];
                    } else if (key == "bySource") {
                        app.source_ids = value.map((v) => v.bucketGroup[0].id);
                    } else {
                        app.chartData[key] = value;
                    }
                    if (key == "byFunder") {
                        app.funders = value.map((f) => f.bucketGroup[0].name);
                    }
                });
            });
            graphqlQuery(GEO_GQL, {
                dataset: app.dataset,
                ...app.base_filters,
                ...app.computedFilters,
            }).then((data) => {
                app.grants = data.data.grants;
            });
        },
        lineChartData(chart, field, bucketGroup, date_format) {
            var values = this.chartBars(chart, field, bucketGroup);
            if (date_format == 'month') {
                values = values.map((d) => ({
                    label: new Date(d.label + "-01"),
                    value: d.value
                }));
                values.sort((firstEl, secondEl) => firstEl.label - secondEl.label);
            }
            return {
                labels: values.map((d) => d.label),
                datasets: [{
                    label: field,
                    data: values.map((d) => d.value),
                    backgroundColor: COLOURS['orange'],
                    borderColor: COLOURS['orange'],
                    borderWidth: 0,
                    categoryPercentage: 1.0,
                    barPercentage: 1.0,
                }]
            }
        },
        chartBars(chart, field = 'grants', bucketGroup = 0, sort = true) {
            if (!this.chartData[chart]) { return []; }
            var chartData = this.chartData[chart];
            if (chart == 'byAmountAwarded') {
                chartData = chartData.filter((d) => d.bucketGroup[0].id == this.currencyUsed);
            }
            chartData = chartData.filter((d) => d.bucketGroup[bucketGroup].name);
            var maxValue = Math.max(...chartData.map((d) => d[field]));
            var values = chartData.map((d) => ({
                label: d.bucketGroup[bucketGroup].name,
                value: d[field],
                style: {
                    '--value': d[field],
                    '--width': `${(d[field] / maxValue) * 100}%`
                }
            }));
            if (chart in this.bin_labels) {
                values.sort((firstEl, secondEl) => this.bin_labels[chart].indexOf(firstEl.label) - this.bin_labels[chart].indexOf(secondEl.label));
            } else if (sort) {
                values.sort((firstEl, secondEl) => secondEl.value - firstEl.value);
            }
            return values;
        },
        chartN(chart, field = 'grants', bucketGroup = 0) {
            if (!this.chartData[chart]) { return []; }
            return this.chartData[chart].filter((d) => d.bucketGroup[bucketGroup].name).reduce((acc, d) => acc + d[field], 0);
        },
        chartMissing(chart, field = 'grants', bucketGroup = 0) {
            if (!this.chartData[chart]) { return []; }
            return this.chartData[chart]
                .filter((d) => !d.bucketGroup[bucketGroup].name)
                .reduce((acc, d) => acc + d[field], 0);
        },
        getOptions(field) {
            if (!this.initialData[field]) { return []; }
            return this.initialData[field]
                .filter((d) => d.bucketGroup[0].name)
                .map((d) => ({
                    value: d.bucketGroup[0].id,
                    label: d.bucketGroup[0].name,
                }));
        }
    },
    mounted() {
        var app = this;
        graphqlQuery(GQL, {
            dataset: app.dataset,
            ...initialFilters(false),
            ...app.base_filters,
        }).then((data) => {
            app.initialData = {};
            Object.entries(data.data.grantAggregates).forEach(([key, value]) => {
                if (!["summary", "bySource"].includes(key)) {
                    app.initialData[key] = value;
                }
            });
        });
    }
})