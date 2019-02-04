// Foldable

const foldableElements = document.getElementsByClassName('js-foldable')
for (const foldableElement of foldableElements) {
  const classes = foldableElement.classList.values()
  for (const clazz of classes) {
    if (clazz.startsWith('js-foldable-aim-')) {
      const targetId = clazz.substring(16)
      const targets = document.getElementsByClassName(`js-foldable-target-${targetId}`)
      const hideTargets = foldableElement.classList.contains('js-foldable-more')
      for (const target of targets) {
        if (target.classList.contains('js-foldable-target')) {
          target.style.maxHeight = `${target.getBoundingClientRect().height}px`
          if (hideTargets) {
            if (!target.classList.contains('js-folgable-opposite-target')) target.classList.add('js-foldable-foldTarget')
          } else if (target.classList.contains('js-folgable-opposite-target')) {
            target.classList.add('js-foldable-foldTarget')
          }
        }
      }
      foldableElement.addEventListener('click', (event) => {
        event.preventDefault()
        if (foldableElement.classList.contains('js-foldable-less')) {
          foldableElement.classList.remove('js-foldable-less')
        } else {
          foldableElement.classList.add('js-foldable-less')
        }
        for (const target of targets) {
          if (target.classList.contains('js-foldable-foldTarget')) {
            target.classList.remove('js-foldable-foldTarget')
          } else {
            target.classList.add('js-foldable-foldTarget')
          }
        }
      })
      break
    }
  }
}

// Range selector
function getLowestRangeValue (inputs) {
  for (let i = 0, j = inputs.length; i < j; ++i) {
    const el = inputs[i]
    if (el.checked) {
      return parseInt(el.value)
    }
  }
  return Number.MAX_SAFE_INTEGER
}

function getHighestRangeValue (inputs) {
  for (let i = inputs.length - 1; i >= 0; --i) {
    const el = inputs[i]
    if (el.checked) {
      return parseInt(el.value)
    }
  }
  return Number.MIN_SAFE_INTEGER
}

function createRangeSelectorUpdater (inputs) {
  const inputsLength = inputs.length
  let lowest = getLowestRangeValue(inputs)
  let highest = getHighestRangeValue(inputs)
  return (event) => {
    const isChecked = event.target.checked
    const targetValue = parseInt(event.target.value)
    if (isChecked) {
      lowest = getLowestRangeValue(inputs)
      highest = getHighestRangeValue(inputs)
    } else {
      if (lowest === targetValue) {
        lowest = getLowestRangeValue(inputs)
      }
      if (highest === targetValue) {
        highest = getHighestRangeValue(inputs)
      }
      const distanceLowest = targetValue - lowest
      const distanceHighest = highest - targetValue
      if (distanceLowest > distanceHighest) {
        let foundTarget = false
        for (let i = inputsLength - 1; i >= 0; --i) {
          const el = inputs[i]
          const value = parseInt(el.value)
          if (foundTarget) {
            highest = value
            break
          } else if (value === targetValue) {
            foundTarget = true
          }
        }
      } else if (distanceHighest > distanceLowest) {
        let foundTarget = false
        for (let i = 0; i < inputsLength; ++i) {
          const el = inputs[i]
          const value = parseInt(el.value)
          if (foundTarget) {
            lowest = value
            break
          } else if (value === targetValue) {
            foundTarget = true
          }
        }
      } else if (distanceHighest === distanceLowest) {
        lowest = (highest = targetValue)
      }
    }
    for (let i = 0; i < inputsLength; ++i) {
      const el = inputs[i]
      const value = parseInt(el.value)
      if (value >= lowest && value <= highest) {
        if (!el.checked) {
          el.checked = true
        }
        if ((value === highest || value === lowest) && !el.classList.contains('show-label')) {
          el.classList.add('show-label')
        }
      } else {
        if (el.checked) {
          el.checked = false
        }
      }
      if (el.classList.contains('show-label') && !(value === highest || value === lowest)) {
        el.classList.remove('show-label')
      }
    }
  }
}

const rangeSelectors = document.getElementsByClassName('results-page__menu__range-select')
for (const rangeSelector of rangeSelectors) {
  const classes = rangeSelector.classList.values()
  for (const clazz of classes) {
    if (clazz.startsWith('js-range-select-')) {
      const targetName = clazz.substring(16)
      const inputs = document.querySelectorAll(`input[name="${targetName}"]`)
      const updater = createRangeSelectorUpdater(inputs)
      for (const input of inputs) {
        input.addEventListener('change', updater)
      }
      break
    }
  }
}

// Results - Navigation Title
const resultsHeader = document.getElementsByClassName('results-page__header')[0]
const resultsBodyElement = document.getElementsByClassName('results-page__body')[0]
const resultsBodyHeader = document.getElementsByClassName('results-page__body__header')[0]
const resultsBodyHeaderTitle = document.getElementsByClassName('results-page__body__header__title')[0]
const resultsBodyTitle = document.getElementsByClassName('results-page__body__content__title')[0]
const resultsBodyTitleYMax = (resultsBodyTitle.getBoundingClientRect().height + resultsHeader.getBoundingClientRect().height) - 44

function buildTitleScrollExecutor (noMoreComplete, onComplete, onProgress, onEnter, onLeave) {
  const primaryBounds = resultsBodyTitle.getBoundingClientRect()
  const secondaryBounds = resultsBodyHeaderTitle.getBoundingClientRect()
  const initial = {
    deltaX: primaryBounds.left - secondaryBounds.left,
    deltaY: primaryBounds.top - secondaryBounds.top,
    deltaW: primaryBounds.width / secondaryBounds.width,
    deltaH: primaryBounds.height / secondaryBounds.height
  }
  const calc = (i, f) => {
    const j = 1 + i - (i * f)
    if (j > i) {
      onLeave()
      return i
    } else {
      onEnter()
      return j
    }
  }
  let last = initial
  let completed = false
  return (progressFactor) => {
    if (progressFactor >= 1) {
      if (completed) {
        return
      }
      completed = true
      onComplete()
    } else if (completed) {
      noMoreComplete()
      completed = false
    }
    onProgress(progressFactor)
    const deltas = {
      deltaX: calc(initial.deltaX, progressFactor),
      deltaY: calc(initial.deltaY, progressFactor),
      deltaW: calc(initial.deltaW, progressFactor),
      deltaH: calc(initial.deltaH, progressFactor)
    }
    window.requestAnimationFrame(() => {
      resultsBodyHeaderTitle.animate([{
        transformOrigin: 'top left',
        transform: `
          translate(${last.deltaX}px, ${last.deltaY}px)
          scale(${last.deltaW}, ${last.deltaH})
        `
      }, {
        transformOrigin: 'top left',
        transform: `
          translate(${deltas.deltaX}px, ${deltas.deltaY}px)
          scale(${deltas.deltaW}, ${deltas.deltaH})
        `
      }], {
        duration: 230,
        easing: 'cubic-bezier(0.4, 0.0, 0.2, 1)',
        fill: 'both'
      })
      last = deltas
    })
  }
}

const titleExecutor = buildTitleScrollExecutor(
  () => (resultsBodyHeaderTitle.style.fontWeight = 300),
  () => (resultsBodyHeaderTitle.style.fontWeight = 400),
  (progress) => (resultsBodyHeader.style.opacity = progress),
  () => {
    resultsBodyHeaderTitle.style.opacity = 1
    resultsBodyTitle.style.opacity = 0
  },
  () => {
    resultsBodyTitle.style.opacity = 1
    resultsBodyHeaderTitle.style.opacity = 0
  }
)

let scrollUpdater = null
resultsBodyElement.addEventListener('scroll', (event) => {
  const f = (scrollTop) => titleExecutor(scrollTop >= resultsBodyTitleYMax ? 1 : scrollTop / resultsBodyTitleYMax)
  f(event.target.scrollTop)
  scrollUpdater = setTimeout(() => {
    if (scrollUpdater !== null) {
      clearTimeout(scrollUpdater)
      scrollUpdater = null
    }
    f(event.target.scrollTop)
  }, 100)
})

titleExecutor(0)
