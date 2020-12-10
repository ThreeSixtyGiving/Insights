import { formatNumber } from './components/filters.js';

Vue.filter('formatNumber', formatNumber);

var app = new Vue({
    el: '#app',
    delimiters: ["<%", "%>"],
    data() {
        return {
            uploadModal: false,
            loading: false,
            uploadStatus: null,
            uploadFile: null,
            uploadSourceTitle: null,
            uploadSourceDescription: null,
            uploadSourceLicense: null,
            uploadSourceLicenseName: null,
            uploadError: null,
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
        addFile: function(e){
            let droppedFiles;
            if(e.dataTransfer){
                droppedFiles = e.dataTransfer.files;
            } else {
                droppedFiles = e.target.files;
            }
            if(!droppedFiles) return;
            this.uploadFile = droppedFiles[0];
            this.uploadSourceTitle = droppedFiles[0].name;
            this.uploadStatus = 'ready';
        },
        startUpload: function(){
            var component = this;
            this.uploadError = null;
            this.uploadStatus = 'uploading';
            this.loading = true;
            let formData = new FormData();
            formData.append('file', this.uploadFile);
            formData.append('source_title', this.uploadSourceTitle);
            formData.append('source_description', this.uploadSourceDescription);
            formData.append('source_license', this.uploadSourceLicense);
            formData.append('source_license_name', this.uploadSourceLicenseName);
            fetch(UPLOAD_URL, {method: "POST", body: formData})
                .then(response => response.json())
                .then(data => {
                    console.log(data);
                    window.location.replace(data.data_url);
                })
                .catch(error => {
                    component.uploadError = 'Could not upload file';
                    component.loading = false;
                    component.uploadStatus = 'ready';
                });
        },
        openFileDialog: function(){
            this.$refs.uploadFileInput.click();
        }
    }
});