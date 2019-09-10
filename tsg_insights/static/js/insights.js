const selectedFilters = {};

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

const render_data = function (data) {
    const totalGrantsNodes = document.getElementsByClassName('total-grants');
    const totalAmountNodes = document.getElementsByClassName('total-amount');
    const numFundersNodes = document.getElementsByClassName('num-funders');

    for (const g of totalGrantsNodes) {
        g.innerText = data.data.grants.summary[0].grants;
    }

    for (const g of numFundersNodes) {
        g.innerText = data.data.grants.summary[0].funders;
    }

    var totalAmount = data.data.grants.summary[0].grantAmount.find(item => item.currency == "GBP").value;
    for (const g of totalAmountNodes) {
        g.innerText = totalAmount;
    }
}

const get_data = function(){

    console.log(selectedFilters);

    var query = `
    query fetchGrants(
        $dataset: String!, 
        $funders: [String],
        $grantProgrammes: [String], 
        $area: [String], 
        $orgtype: [String]
    ){
        grants(
            dataset: $dataset,
            funders: $funders,
            grantProgrammes: $grantProgrammes,
            area: $area,
            orgtype: $orgtype
        ) {
            summary {
                bucketId
                grants
                recipients
                funders
                grantAmount {
                    currency
                    value
                }
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

document.getElementById("funder-select").addEventListener("change", function(){
    get_data();
})