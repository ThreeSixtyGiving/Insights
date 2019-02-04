const bodyElement = document.body

const utils = {
  lockBody (lock) {
    if (lock) {
      if (!bodyElement.classList.contains('lock')) bodyElement.classList.add('lock')
    } else {
      bodyElement.classList.remove('lock')
    }
  },
  isBodyLocked () {
    return bodyElement.classList.contains('lock')
  },
  setPageLoading (loading) {
    const loadingEl = document.getElementsByClassName('page-loader')[0]
    if (loadingEl) {
      if (loading) {
        this.lockBody(true)
        if (loadingEl.classList.contains('hidden')) {
          loadingEl.classList.remove('hidden')
        }
      } else {
        if (!loadingEl.classList.contains('hidden')) {
          loadingEl.classList.add('hidden')
        }
      }
    }
  }
}

// CHOOSE DATASET
const chooseDataSetButton = document.getElementsByClassName('js-choose-dataset-btn')[0]
const chooseDataSetWindow = document.getElementsByClassName('js-homepage-dataset-selection-window')[0]
const chooseDataSetCloseButton = document.getElementsByClassName('js-homepage-dataset-selection-window-close')[0]
const chooseDataSetOptions = document.getElementsByClassName('homepage__data-selection__data-list__item')
chooseDataSetButton.addEventListener('click', () => {
  chooseDataSetWindow.classList.toggle('hidden')
  utils.lockBody(!utils.isBodyLocked())
})
chooseDataSetWindow.addEventListener('click', (e) => {
  if (e.target.classList.contains('js-homepage-dataset-selection-window') &&
    !chooseDataSetWindow.classList.contains('hidden')) {
    chooseDataSetWindow.classList.add('hidden')
    utils.lockBody(false)
  }
})
chooseDataSetCloseButton.addEventListener('click', () => {
  if (!chooseDataSetWindow.classList.contains('hidden')) {
    chooseDataSetWindow.classList.add('hidden')
    utils.lockBody(false)
  }
})
for (const option of chooseDataSetOptions) {
  option.addEventListener('click', () => {
    utils.setPageLoading(true)
    setTimeout(() => {
      window.location.href = `${window.location.origin}/results.html`
    }, 1500)
  })
}

// UPLOAD DATASET
const uploadDataSetButton = document.getElementsByClassName('js-upload-dataset-btn')[0]
const uploadDataSetWindow = document.getElementsByClassName('js-homepage-dataset-upload-window')[0]
const uploadDataSetCloseButton = document.getElementsByClassName('js-homepage-dataset-upload-window-close')[0]
const uploadDataConfirmButton = document.getElementsByClassName('js-dataset-upload')[0]
uploadDataSetButton.addEventListener('click', () => {
  uploadDataSetWindow.classList.toggle('hidden')
  utils.lockBody(!utils.isBodyLocked())
})
uploadDataSetWindow.addEventListener('click', (e) => {
  if (e.target.classList.contains('js-homepage-dataset-upload-window') &&
    !uploadDataSetWindow.classList.contains('hidden')) {
    uploadDataSetWindow.classList.add('hidden')
    utils.lockBody(false)
  }
})
uploadDataSetCloseButton.addEventListener('click', () => {
  if (!uploadDataSetWindow.classList.contains('hidden')) {
    uploadDataSetWindow.classList.add('hidden')
    utils.lockBody(false)
  }
})
uploadDataConfirmButton.addEventListener('click', () => {
  utils.setPageLoading(true)
  setTimeout(() => {
    window.location.href = `${window.location.origin}/results.html`
  }, 1500)
})
