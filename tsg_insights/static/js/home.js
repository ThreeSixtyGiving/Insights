// modals
const modals = document.getElementsByClassName('js-modal');
const urlParams = new URLSearchParams(window.location.search);
for (const modal of modals) {
    const trigger = document.getElementById(modal.dataset.trigger);
    if(trigger){
        trigger.addEventListener('click', (event) => {
            event.preventDefault();
            modal.classList.remove("hidden");
        });
    }

    for (const close_button of modal.getElementsByClassName('close-button')) {
        close_button.addEventListener('click', (event) => {
            event.preventDefault();
            modal.classList.add("hidden");
        });
    }

    if(urlParams.has(modal.id)){
        trigger.click();
    }
}

// filter by publisher
const datasetFilter = document.getElementById('dataset-filter');
const registryList = document.getElementById('registry-list');
datasetFilter.addEventListener('keyup', (event) => {
    event.preventDefault();
    const search_term = event.target.value.toLowerCase().replace(/[\W_]+/g, " ");
    for (const publisher of registryList.getElementsByClassName('homepage__data-selection__set')){
        var publisher_name = publisher.getElementsByClassName('homepage__data-selection__set-name')[0].textContent;
        publisher_name = publisher_name.toLowerCase().replace(/[\W_]+/g, " ");
        if (publisher_name.includes(search_term)){
            publisher.classList.remove("hidden");
        } else {
            publisher.classList.add("hidden");
        }
    }
});

// function to track a job and update the status
const track_job = function(jobid){
    const uploadProgress = document.getElementById('upload-progress');

    // set loading state
    var progressLoader = document.getElementById("upload-progress-loader");
    progressLoader.style.display = 'flex';
    var resultsButton = document.getElementById("upload-progress-results");
    resultsButton.innerText = 'View results';
    resultsButton.href = '#';
    resultsButton.classList.add("invalid");

    // set progress bar states
    var mainProgress = document.getElementById("upload-progress-main");
    var mainProgressBar = mainProgress.getElementsByTagName("progress")[0];
    mainProgress.getElementsByClassName("homepage__data-fetching__process-name")[0].innerText = 'Fetching data';
    mainProgress.getElementsByClassName("homepage__data-fetching__steps")[0].innerText = '';
    mainProgressBar.value = 0;
    mainProgressBar.max = 10;

    var subProgress = document.getElementById("upload-progress-sub");
    var subProgressBar = subProgress.getElementsByTagName("progress")[0];
    subProgress.getElementsByClassName("homepage__data-fetching__process-name")[0].innerText = '';
    subProgress.getElementsByClassName("homepage__data-fetching__steps")[0].innerText = '';
    subProgress.style.display = "none";
    subProgressBar.value = 0;
    subProgressBar.max = 10;

    // set error display loading state
    var uploadError = document.getElementById("upload-progress-error");
    uploadError.style.display = "none";

    // refresh the job ID every X seconds to get the current status
    const intervalID = setInterval(() => {
        fetch(`/job/${jobid}`)
            .then(function (response) {
                return response.json();
            })
            .then(function (jobStatus) {
                // update the current status in the dialogue
                progressLoader.style.display = 'none';

                switch (jobStatus.status) {
                    case "not-found":
                        uploadError.style.display = "inherit";
                        mainProgress.style.display = "none";
                        uploadError.getElementsByClassName("homepage__data-fetching__process-name")[0].innerText = 'File could not be found';
                        clearInterval(intervalID);
                        break;

                    case "processing-error":
                        uploadError.style.display = "inherit";
                        mainProgress.style.display = "none";
                        var p = document.createElement('p');
                        p.innerText = 'Error processing the file ';
                        var e_details = document.createElement('div');
                        e_details.innerHTML = `<pre>${jobStatus.exc_info}</pre>`;
                        e_details.style['display'] = 'none'; 
                        e_details.style['overflow'] = 'scroll';
                        e_details.style['maxHeight'] = '250px';
                        e_details.classList.add("hidden");

                        var e_toggle = document.createElement('a');
                        e_toggle.innerText = 'Show error';
                        e_toggle.setAttribute('href', '#');
                        e_toggle.addEventListener('click', (event) => {
                            event.preventDefault();
                            e_details.classList.toggle('hidden');
                            if(e_details.classList.contains('hidden')){
                                e_toggle.innerText = 'Show error';
                                e_details.style['display'] = 'none';
                            } else {
                                e_toggle.innerText = 'Hide error';
                                e_details.style['display'] = 'inherit';
                            }
                        })
                        
                        uploadError.getElementsByClassName("homepage__data-fetching__process-name")[0].innerHTML = '';
                        uploadError.getElementsByClassName("homepage__data-fetching__process-name")[0].append(p);
                        uploadError.getElementsByClassName("homepage__data-fetching__steps")[0].innerHTML = '';
                        uploadError.getElementsByClassName("homepage__data-fetching__steps")[0].append(e_toggle);
                        uploadError.getElementsByClassName("homepage__data-fetching__display-error")[0].innerHTML = '';
                        uploadError.getElementsByClassName("homepage__data-fetching__display-error")[0].append(e_details);
                        clearInterval(intervalID);
                        break;

                    case "in-progress":
                        if(!jobStatus.progress){
                            progressLoader.style.display = 'flex';
                            break;
                        }

                        /**
                         * jobStatus.stages has a description of the different stages
                         * jobStatus.progress['stage'] gives the index of the current stage
                         * jobStatus.progress['progress'] holds an array [currentindex, totalsize] of progress through the current stage
                         */
                        mainProgress.style.display = "inherit";
                        mainProgress.getElementsByClassName("homepage__data-fetching__process-name")[0].innerText = jobStatus.stages[jobStatus.progress['stage'] + 1];
                        mainProgress.getElementsByClassName("homepage__data-fetching__steps")[0].innerText = `Stage ${jobStatus.progress['stage'] + 1} of ${jobStatus.stages.length}`;
                        mainProgressBar.value = jobStatus.progress['stage'] + 1;
                        mainProgressBar.max = jobStatus.stages.length;

                        if (jobStatus.progress['progress']) {
                            subProgress.style.display = "inherit";
                            subProgress.getElementsByClassName("homepage__data-fetching__process-name")[0].innerText = `${jobStatus.progress['progress'][0]} of ${jobStatus.progress['progress'][1]}`;
                            // subProgress.getElementsByClassName("homepage__data-fetching__steps")[0].innerText = `${jobStatus.progress['progress'][0]} of ${jobStatus.progress['progress'][1]}`;
                            subProgressBar.value = jobStatus.progress['progress'][0];
                            subProgressBar.max = jobStatus.progress['progress'][1];
                        } else {
                            subProgress.style.display = "none";
                        }
                        break;

                    case "completed":
                        // redirect to the file when the fetch has finished
                        clearInterval(intervalID);

                        var resultUrl = `/file/${jobStatus.result[0]}`;

                        // set up progress bars
                        subProgress.style.display = "none";
                        mainProgress.getElementsByClassName("homepage__data-fetching__process-name")[0].innerText = 'Completed';
                        mainProgress.getElementsByClassName("homepage__data-fetching__steps")[0].innerText = '';
                        mainProgressBar.value = mainProgressBar.max;
                        
                        // add href to results button
                        resultsButton.innerText = 'View results';
                        resultsButton.href = resultUrl;
                        resultsButton.classList.remove("invalid");

                        // document.getElementById('upload-progress-modal').classList.add("hidden");
                        window.location.href = resultUrl;
                        break;

                    default:
                        progressLoader.style.display = 'flex';

                }
            });
    }, 2000);


}

const dataFromURL = function (url) {
     // open the fetch file dialogue
    document.getElementById('upload-progress-modal').classList.remove("hidden");
    document.getElementById('upload-dataset-modal').classList.add("hidden");

    var formData = new FormData();
    formData.append('url', url);

    fetch('/fetch/url', {
        method: 'POST',
        body: formData
    }).then(function (response) {
        return response.json();
    }).then( function (jobJson) {
        const jobid = jobJson['job'];
        track_job(jobid);
    });
}

if (window.location.search.startsWith("?url=")) {
    var urlToFetch = window.location.search.replace("?url=", "");

    dataFromURL(decodeURIComponent(urlToFetch));
}

const sendFile = function (file) {

    // open the fetch file dialogue
    document.getElementById('upload-progress-modal').classList.remove("hidden");
    document.getElementById('upload-dataset-modal').classList.add("hidden");

    var formData = new FormData();
    formData.append('file', file);

    // start the job and get the job ID
    fetch('/fetch/upload', {
        method:'POST',
        body: formData
    })
        .then(function (response) {
            return response.json();
        })
        .then(function (jobJson) {
            const jobid = jobJson['job'];
            track_job(jobid);
        });

}

// trigger the fetch from registry
for (const registryLink of document.getElementsByClassName("fetch-from-registry")){
    registryLink.addEventListener('click', (event) => {
        event.preventDefault();

        // open the fetch file dialogue
        document.getElementById('upload-progress-modal').classList.remove("hidden");
        document.getElementById('file-selection-modal').classList.add("hidden");

        // start the job and get the job ID
        fetch(registryLink.href)
            .then(function (response) {
                return response.json();
            })
            .then(function (jobJson) {
                const jobid = jobJson['job'];
                track_job(jobid);
            });
    })

    // if we've been given a "fetch" parameter then start the fetch
    if (urlParams.get('fetch') == registryLink.dataset.identifier) {
        registryLink.click();
    }
}

// trigger upload when a file is dropped onto the dropzone
const dropzone = document.getElementById('file-upload-dropzone');
const fileInput = document.getElementById('file-upload-input');

dropzone.onclick = function (event) {
    event.preventDefault();
    fileInput.click();
}

dropzone.ondragover = dropzone.ondragenter = function (event) {
    event.stopPropagation();
    event.preventDefault();
    dropzone.classList.add("highlight");
}

dropzone.ondragleave = dropzone.ondragend = dropzone.ondragexit = function (event) {
    event.stopPropagation();
    event.preventDefault();
    dropzone.classList.remove("highlight");
}

dropzone.ondrop = function (event) {
    event.stopPropagation();
    event.preventDefault();

    const filesArray = event.dataTransfer.files;
    for (let i = 0; i < filesArray.length; i++) {
        sendFile(filesArray[i]);
    }
}

fileInput.onchange = function (event) {
    event.stopPropagation();
    event.preventDefault();

    const filesArray = event.target.files;
    for (let i = 0; i < filesArray.length; i++) {
        sendFile(filesArray[i]);
    }
}