const selectedFilters = {};
const THREESIXTY_COLOURS = ['#9c2061', '#f48320', '#cddc2b', '#53aadd'];

const render_filters = function(data) {
    var filterForm = document.getElementById("dashboard-filter-items");
    filterForm.innerHTML = '';

    var filterTemplate = document.getElementById("js-foldable-template");
    var filterItemTemplate = document.getElementById("filter-item-template");

    for (let [key, value] of Object.entries(data.data.grants)) {
        selectedFilters[key] = [];

        // use template to set up filter element
        var filterEl = document.importNode(filterTemplate.content, true);
        filterEl.querySelector("div.results-page__menu__subsection").setAttribute('id', `df-change-${key}-wrappper`);
        filterEl.querySelector("h4.results-page__menu__subsection-title").innerText = key;
        filterEl.querySelector("h5.results-page__menu__subsection-value").innerText = key;
        filterEl.querySelector("h5.results-page__menu__subsection-value").setAttribute('data-original', key);
        filterEl.querySelector("fieldset").setAttribute('id', `df-change-${key}`);

        // Add list of filters
        var ul = filterEl.querySelector('ul.results-page__menu__checkbox');

        for (let o of value) {
            var filterItemEl = document.importNode(filterItemTemplate.content, true);
            var input = filterItemEl.querySelector('input');
            input.setAttribute('id', `df-change-${key}-${o.bucketId}`);
            input.setAttribute('value', o.bucketId);
            var label = filterItemEl.querySelector('label');
            label.setAttribute('for', `df-change-${key}-${o.bucketId}`);
            if(key=='byFunder'){
                label.innerText = `${o.bucket2Id} (${o.grants})`;
            } else {
                label.innerText = `${o.bucketId} (${o.grants})`;
            }

            // set up what happens when element is clicked
            input.addEventListener("change", function () {
                selectedFilters[key] = [];
                var parentFieldset = this.closest("fieldset");
                for (const inputValue of parentFieldset.querySelectorAll("input[type=checkbox]")) {
                    if (inputValue.checked) {
                        selectedFilters[key].push(inputValue.value);
                    }
                }

                // set the values displayed to the user
                var subsectionValue = this.closest(".results-page__menu__subsection").querySelector("h5.results-page__menu__subsection-value");
                if(selectedFilters[key].length > 0){
                    subsectionValue.innerText = selectedFilters[key].join(", ");
                } else {
                    subsectionValue.innerText = subsectionValue.getAttribute("data-original");
                }
                get_data();
            });

            ul.appendChild(filterItemEl);
        }
        
        // set up the filter toggle
        var titleEl = filterEl.querySelector("h4.results-page__menu__subsection-title");
        titleEl.innerText = key;
        titleEl.addEventListener("click", function(){
            this.classList.toggle("js-foldable-less");
            for (var el of this.parentElement.getElementsByClassName("js-foldable-target")){
                el.classList.toggle("js-foldable-foldTarget");
                if(el.style.opacity==1){
                    el.style.opacity = 0;
                } else {
                    el.style.opacity = 1;
                }
            };
        });

        filterForm.appendChild(filterEl);
    }
}

const get_filters = function () {

    var query = `
query fetchFilters($dataset: String!) {
  grants(dataset: $dataset) {
    byFunderType {
      bucketId
      bucket2Id
      grants
    }
    byFunder {
      bucketId
      bucket2Id
      grants
    }
    byGrantProgramme {
      bucketId
      bucket2Id
      grants
    }
    byAwardYear {
      bucketId
      bucket2Id
      grants
    }
    byCountryRegion {
      bucketId
      bucket2Id
      grants
    }
    byOrgType {
      bucketId
      bucket2Id
      grants
    }
    byAmountAwarded {
      bucketId
      bucket2Id
      grants
    }
    byOrgSize {
      bucketId
      bucket2Id
      grants
    }
    byOrgAge {
      bucketId
      bucket2Id
      grants
    }
  }
}
    `;

    fetch('/api/graphql', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
        },
        body: JSON.stringify({
            query: query,
            variables: { dataset }
        })
    })
        .then(r => r.json())
        .then(render_filters);
}

const format_number = function(value, currency, suffixType){

    var suffix = null;
    var dp = 0;
    if (suffixType!==false){
        if(value > 1000000000){
            suffix = suffixType=='short' ? 'bn' : 'billion';
            dp = 1;
            value = value / 1000000000.0;
        } else if (value > 1000000) {
            suffix = suffixType == 'short' ? 'm' : 'million';
            dp = 1;
            value = value / 1000000.0;
        } else if (value > 10000) {
            suffix = suffixType == 'short' ? 'k' : 'k';
            dp = 0;
            value = value / 1000.0;
        }
    }

    if(currency){
        return [value.toLocaleString('en-gb', {
            style: 'currency',
            currency: 'GBP',
            minimumFractionDigits: dp,
            maximumFractionDigits: dp,
        }), suffix];
    }
    return [value.toLocaleString('en-gb', {
        minimumFractionDigits: dp,
        maximumFractionDigits: dp,
    }), suffix];
}

const render_summary = function(data){
    var summary = data.summary[0];
    console.log(data);

    // work out date string
    if (summary.maxDate == summary.minDate) {
        var dateRangePrefix = 'in';
        var dateRange = `${summary.minDate}`;
    } else {
        var dateRangePrefix = 'between';
        var dateRange = `${summary.minDate} and ${summary.maxDate}`;
    }

    // work out funder title
    if (summary.funders > 1){
        var funderTitle = `${format_number(summary.funders).join("")} funders`;
    } else {
        var funderTitle = data.byFunder[0].bucket2Id;
    }

    // work out the amount string
    var totalAmount = format_number(summary.grantAmount.find(item => item.currency == "GBP").value, 'GBP');
    var meanAmount = format_number(summary.meanGrant.find(item => item.currency == "GBP").value, 'GBP');
    if(meanAmount[1]=="k"){
        meanAmount = [`${meanAmount[0]}k`, ''];
    }

    [
        ['funder-title', funderTitle],
        ['date-prefix', dateRangePrefix],
        ['date-range', dateRange],
        ['total-grants', format_number(summary.grants).join("")],
        ['total-recipients', format_number(summary.recipients).join("")],
        ['total-amount', totalAmount[0]],
        ['total-amount-suffix', totalAmount[1]],
        ['mean-amount', meanAmount[0]],
        ['mean-amount-suffix', meanAmount[1]],
    ].forEach(newValue => {
        Array.from(document.getElementsByClassName(newValue[0])).forEach(
            el => el.innerText = newValue[1]
        );
    });
}

const render_chart = function (title, data, container) {
    // funder type chart
    var chartTemplate = document.getElementById("chart-wrapper-template");
    var funderTypeChart = document.importNode(chartTemplate.content, true);

    data = data.filter(x => x.bucketId); // only include grants where the label is present
    data.sort((a, b) => b.grants - a.grants); // sort by the largest values
    var values = data.map(x => x.grants); // get the values
    // create the labels
    if(title=='byFunder'){
        var labels = data.map(x => x.bucket2Id);
    } else {
        var labels = data.map(x => x.bucketId);
    }
    var totalValues = values.reduce((a, b) => a + b, 0); // get the total N for the data
    funderTypeChart.querySelector('.figure-n').innerText = format_number(totalValues).join("");
    funderTypeChart.querySelector(".results-page__body__section-title").innerText = title; // set the page title

    if(values.length > 15){
        var placeholder = document.createElement("p");
        placeholder.innerText = `${format_number(values.length)} values`;
        funderTypeChart.appendChild(placeholder);
        container.appendChild(funderTypeChart);
        return;
    } else if (values.length == 1) {
        var placeholder = document.createElement("p");
        placeholder.innerText = `${labels[0]} (${values[0]})`;
        funderTypeChart.appendChild(placeholder);
        container.appendChild(funderTypeChart);
        return;
    }

    console.log(data);
    Plotly.plot(funderTypeChart.querySelector(".js-plotly-plot"), [{
        x: labels,
        y: values,
        text: values.map(x => format_number(x).join("")),
        textposition: 'outside',
        cliponaxis: false,
        constraintext: 'none',
        textfont: {
            size: 18,
            family: 'neusa-next-std-compact, sans-serif;',
        },
        hoverinfo: 'text+x',
        type: 'bar',
        name: title,
        marker: {
            color: THREESIXTY_COLOURS[0]
        },
        fill: 'tozeroy',
    }], {
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
    }, {
        displayModeBar: 'hover',
        modeBarButtons: [[
            'toImage', 'sendDataToCloud'
        ]],
        scrollZoom: 'gl3d',
    });

    container.appendChild(funderTypeChart);
}

const render_data = function (data) {
    const dashboardOutput = document.getElementById("dashboard-output");
    dashboardOutput.innerHTML = '';
    for(const [title, itemData] of Object.entries(data.data.grants)){
        if(title=='summary'){
            render_summary(data.data.grants);
        } else if(title=='byAmountAwarded') {
            var newItemData = itemData.filter(d => d.bucketId == 'GBP').map(d => Object.assign(d, {
                bucketId: d.bucket2Id
            }))
            render_chart(title, newItemData, dashboardOutput);
        } else {
            render_chart(title, itemData, dashboardOutput);
        }
    }
}

const get_data = function(){

    var query = `
    fragment bucket on GrantBucket {
        bucketId
        bucket2Id
        grants
        recipients
        funders
        grantAmount {
            currency
            value
        }
    }

    query fetchGrants(
        $dataset: String!, 
        $funders: [String],
        $funderTypes: [String],
        $grantProgrammes: [String], 
        $area: [String], 
        $orgtype: [String]
    ){
        grants(
            dataset: $dataset,
            funders: $funders,
            funderTypes: $funderTypes,
            grantProgrammes: $grantProgrammes,
            area: $area,
            orgtype: $orgtype
        ) {
          summary {
            bucketId
            bucket2Id
            grants
            recipients
            funders
            maxDate
            minDate
            grantAmount {
                currency
                value
            }
            meanGrant {
                currency
                value
            }
          }
          byFunderType {
              ...bucket
          }
          byFunder {
              ...bucket
          }
          byAmountAwarded {
              ...bucket
          }
          byGrantProgramme {
              ...bucket
          }
          byAwardDate {
              ...bucket
          }
          byOrgType {
              ...bucket
          }
          byCountryRegion {
              ...bucket
          }
          byOrgAge {
              ...bucket
          }
          byOrgSize {
              ...bucket
          }
        }
    }
    `;

    fetch('/api/graphql', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
        },
        body: JSON.stringify({ 
            query: query,
            variables: { 
                dataset: dataset, 
                funders: selectedFilters["byFunder"],
                funderTypes: selectedFilters["byFunderType"],
                grantProgrammes: selectedFilters["byGrantProgramme"],
                orgtype: selectedFilters["byOrgType"],
                area: selectedFilters["byCountryRegion"],
            }
        })
    })
        .then(r => r.json())
        .then(render_data);
}


document.addEventListener("DOMContentLoaded", function () {
    get_filters();
    get_data();
});
