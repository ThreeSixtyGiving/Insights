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
            label.setAttribute('for', `df-change-${key}-${o.bucketId}`)
            label.innerText = `${o.bucketId} (${o.grants})`;

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

const render_summary = function(data){
    console.log(data); 

    var funderTitle = document.getElementsByClassName('funder-title');
    var datePrefix = document.getElementsByClassName('date-prefix');
    var dateRange = document.getElementsByClassName('date-range');
    Array.from(document.getElementsByClassName('total-grants')).forEach(el => el.innerText = data.grants);
    Array.from(document.getElementsByClassName('total-recipients')).forEach(el => el.innerText = data.recipients);
    var totalAmount = document.getElementsByClassName('total-amount');
    var totalAmountSuffix = document.getElementsByClassName('total-amount-suffix');
    var meanAmount = document.getElementsByClassName('mean-amount');
    var meanAmountSuffix = document.getElementsByClassName('mean-amount-suffix');

    // for (const g of totalGrantsNodes) {
    //     g.innerText = data.grants;
    // }

    // for (const g of numFundersNodes) {
    //     g.innerText = data.funders;
    // }

    // var totalAmount = data.grantAmount.find(item => item.currency == "GBP").value;
    // for (const g of totalAmountNodes) {
    //     g.innerText = totalAmount;
    // }
}

const render_chart = function (title, data) {
    // funder type chart
    var chartTemplate = document.getElementById("chart-wrapper-template");
    var funderTypeChart = document.importNode(chartTemplate.content, true);
    console.log(data);
    funderTypeChart.querySelector(".results-page__body__section-title").innerText = title;
    Plotly.plot(funderTypeChart.querySelector(".js-plotly-plot"), [{
        x: data.map(x => x.bucketId),
        y: data.map(x => x.grants),
        text: data.map(x => x.grants),
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

    const dashboardOutput = document.getElementById("dashboard-output");
    dashboardOutput.appendChild(funderTypeChart);
}

const render_data = function (data) {
    for(const [title, itemData] of Object.entries(data.data.grants)){
        if(title=='summary'){
            render_summary(itemData[0]);
        } else if(title=='byAmountAwarded') {
            var newItemData = itemData.filter(d => d.bucketId == 'GBP').map(d => Object.assign(d, {
                bucketId: d.bucket2Id
            }))
            render_chart(title, newItemData);
        } else {
            render_chart(title, itemData);
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
              ...bucket
          }
          byFunder {
              ...bucket
          }
          byFunderType {
              ...bucket
          }
          byAmountAwarded {
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
