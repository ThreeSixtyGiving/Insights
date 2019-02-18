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
    console.log(modal.id);

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
    uploadProgress.innerHTML = `<p>Processing file</p>`;

    // refresh the job ID every X seconds to get the current status
    const intervalID = setInterval(() => {
        fetch(`/job/${jobid}`)
            .then(function (response) {
                return response.json();
            })
            .then(function (jobStatus) {
                // update the current status in the dialogue

                switch (jobStatus.status) {
                    case "not-found":
                        uploadProgress.innerHTML = `<p>File could not be found</p>`;
                        clearInterval(intervalID);
                        break;

                    case "processing-error":
                        uploadProgress.innerHTML = `
                            <p>Error processing the file</p>
                            <pre>${jobStatus.exc_info}</pre>
                            `;
                        clearInterval(intervalID);
                        break;

                    case "in-progress":
                        /**
                         * jobStatus.stages has a description of the different stages
                         * jobStatus.progress['stage'] gives the index of the current stage
                         * jobStatus.progress['progress'] holds an array [currentindex, totalsize] of progress through the current stage
                         */
                        uploadProgress.innerHTML = `
                                    <p>Stage ${jobStatus.progress['stage'] + 1} of ${jobStatus.stages.length}</p>
                                    <p>${jobStatus.stages[jobStatus.progress['stage']+1]}</p>
                                    <p>${jobStatus.progress['progress'][0]} of ${jobStatus.progress['progress'][1]}</p>
                                    `;
                        break;

                    case "completed":
                        // redirect to the file when the fetch has finished
                        clearInterval(intervalID);
                        document.getElementById('upload-progress-modal').classList.add("hidden");
                        window.location.href = `/file/${jobStatus.result[0]}`;
                        break;

                    default:
                        uploadProgress.innerHTML = `
                                    <p>Processing file</p>
                                    `;

                }
            });
    }, 2000);


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
    // @TODO:  add styles here to signal that they're in the right place
    // eg: border: 8px dashed lightgray;
}

dropzone.ondrop = function (event) {
    event.stopPropagation();
    event.preventDefault();

    const filesArray = event.dataTransfer.files;
    for (let i = 0; i < filesArray.length; i++) {
        console.log(filesArray[i]);
        sendFile(filesArray[i]);
    }
}

fileInput.onchange = function (event) {
    event.stopPropagation();
    event.preventDefault();

    const filesArray = event.target.files;
    for (let i = 0; i < filesArray.length; i++) {
        console.log(filesArray[i]);
        sendFile(filesArray[i]);
    }
}