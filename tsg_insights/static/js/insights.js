

const render_filters = function(data) {
    var filter_form = document.getElementById("dashboard-filter-items");
    filter_form.innerHTML = '';

    for (let [key, value] of Object.entries(data.data.grants)) {
        console.log(`${key}: ${value}`);
        var containerDiv = document.createElement('div');
        containerDiv.setAttribute('id', `df-change-${key}-wrappper`);
        containerDiv.classList.add("results-page__menu__subsection");

        var heading = document.createElement('h4');
        heading.classList = ["results-page__menu__subsection-title js-foldable js-foldable-more"];
        heading.innerText = key;
        containerDiv.appendChild(heading);

        var subhead = document.createElement('h4');
        subhead.classList = ["results-page__menu__subsection-value js-foldable-target"];
        subhead.innerText = key;
        containerDiv.appendChild(subhead);

        var target = document.createElement('div');
        target.classList = ["js-foldable-target js-foldable-foldTarget"];
        
        var fieldset = document.createElement('fieldset');
        fieldset.setAttribute("id", "df-change-funders");

        var ul = document.createElement('ul');
        ul.classList = ["results-page__menu__checkbox"];

        for(let o of value){
            var li = document.createElement('li');
            var input = document.createElement('input');
            input.setAttribute('type', 'checkbox');
            input.setAttribute('id', `df-change-${key}-${o.bucketId}`);
            var label = document.createElement('label');
            label.setAttribute('for', `df-change-${key}-${o.bucketId}`)
            label.innerText = `${o.bucketId} (${o.grants})`;
            li.appendChild(input);
            li.appendChild(label);
            ul.appendChild(li);
        }

        fieldset.appendChild(ul);
        target.appendChild(fieldset);
        containerDiv.appendChild(target);
        filter_form.appendChild(containerDiv);
        

        // <div id="df-change-funders-wrapper" class="results-page__menu__subsection undefined"
        //     style="display: none;">
        //     <h4 class="results-page__menu__subsection-title js-foldable js-foldable-more undefined">
        //         Funders</h4>
        //     <h5 class="results-page__menu__subsection-value js-foldable-target undefined"
        //         style="max-height: 16px; opacity: 1;">Funder</h5>
        //     <div class="js-foldable-target js-foldable-foldTarget" style="opacity: 0;">
        //         <fieldset id="df-change-funders">
        //             <ul class="results-page__menu__checkbox">
        //                 <li class="">
        //                     <input type="checkbox" id="df-change-funders-Essex Community Foundation"
        //                         class="" value="on">
        //                         <label for="df-change-funders-Essex Community Foundation" class="">Essex
        //                                         Community Foundation (1299)</label>
        //                                 </li>
        //                             </ul>
        //                         </fieldset>
        //                     </div>
        //     </div>
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
        // .then(data => {
        //     var funderSelect = document.getElementById("funder-select");
        //     funderSelect.innerHTML = '';
        //     var funders = data.data.grants.byFunder.sort((a, b) => b.grants - a.grants);
        //     for (const f of funders){
        //         var opt = document.createElement("option");
        //         opt.value = f.bucketId;
        //         opt.innerText = `${f.bucket2Id} (${f.grants})`;
        //         funderSelect.append(opt);
        //     }
        // });
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

    var funders = Array.from(document.getElementById("funder-select").querySelectorAll("option:checked"), e => e.value);

    var query = `
    query fetchGrants($dataset: String!, $funders: [String]){
        grants(dataset: $dataset, funders: $funders) {
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
            variables: { dataset, funders }
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