import { formatNumber } from './components/filters.js';

Vue.filter('formatNumber', formatNumber);

var app = new Vue({
    el: '#app',
    delimiters: ["<%", "%>"],
    data() {
        return {
            uploadModal: false,
            datasetSelect: DATASET_SELECT,
            datasetSelectSections: DATASET_SELECT_SECTIONS,
            datasetSearch: null,
            maxListLength: 10,
        }
    },
    methods: {
        getDatasetOptions: function (field) {
            if (this.datasetSearch) {
                return this.datasetSelect[field].filter((v) => {
                    var searchStr = v.name
                        .concat(" ", v.id)
                        .toLowerCase();
                    return searchStr.includes(this.datasetSearch.toLowerCase());
                });
            }
            return this.datasetSelect[field].slice(0, this.maxListLength);
        },
        getDatasetOptionsOtherN: function (field) {
            if (this.datasetSearch) {
                return 0;
            }
            return this.datasetSelect[field].length - this.getDatasetOptions(field).length;
        },
    }
});