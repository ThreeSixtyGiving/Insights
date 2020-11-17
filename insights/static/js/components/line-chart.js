export const lineChart = {
    extends: VueChartJs.Line,
    mixins: [VueChartJs.mixins.reactiveProp],
    props: ['chartData', 'hideLegend', 'percentages'],
    data() {
        return {}
    },
    computed: {
        options: function () {
            var component = this;
            return {
                responsive: true,
                legend: {
                    display: (this.hideLegend ? false : true)
                },
                scales: {
                    xAxes: [{
                        gridLines: {
                            display: false,
                        },
                        ticks: {
                            display: true,
                        },
                        type: 'time',
                        display: true,
                    }],
                    yAxes: [{
                        gridLines: {
                            display: false,
                        },
                    }]
                }
            }
        }
    },
    mounted() {
        this.renderChart(this.chartData, this.options)
    }
}