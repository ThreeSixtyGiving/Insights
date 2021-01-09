const MS_IN_DAY = (1000 * 60 * 60 * 24); // number of milliseconds in a day

export const barChart = {
    extends: VueChartJs.Bar,
    mixins: [VueChartJs.mixins.reactiveProp],
    props: ['chartData', 'hideLegend', 'percentages'],
    data() {
        return {}
    },
    computed: {
        options: function () {
            var component = this;
            var daysRange = Math.ceil(
                (
                    Math.max(...this.chartData.labels) - Math.min(...this.chartData.labels)
                ) / MS_IN_DAY
            )
            return {
                responsive: true,
                legend: {
                    display: (this.hideLegend ? false : true)
                },
                scales: {
                    xAxes: [{
                        gridLines: {
                            display: false,
                            offsetGridLines: false,
                        },
                        offset: true,
                        ticks: {
                            display: true,
                        },
                        type: 'time',
                        display: true,
                        time: {
                            unit: (daysRange > 365 ? 'year' : 'month')
                        },
                    }],
                    yAxes: [{
                        gridLines: {
                            display: false,
                        },
                        ticks: {
                            beginAtZero: true,
                            precision: 0,
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