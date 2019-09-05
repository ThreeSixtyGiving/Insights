

const show_data = function(data){   
    const totalGrantsNodes = document.getElementsByClassName('total-grants');
    const totalAmountNodes = document.getElementsByClassName('total-amount');
    const numFundersNodes = document.getElementsByClassName('num-funders');

    for (const g of totalGrantsNodes){
        g.innerText = data.data.grants.summary[0].grants;
    }

    for (const g of numFundersNodes){
        g.innerText = data.data.grants.summary[0].funders;
    }

    var totalAmount = data.data.grants.summary[0].grantAmount.find(item => item.currency == "GBP").value;
    for (const g of totalAmountNodes){
        g.innerText = totalAmount;
    }
}

const get_funders = function () {

    var query = `
    query fetchFunders($dataset: String!){
        grants(dataset: $dataset) {
            byFunder {
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
        .then(data => {
            var funderSelect = document.getElementById("funder-select");
            funderSelect.innerHTML = '';
            var funders = data.data.grants.byFunder.sort((a, b) => b.grants - a.grants);
            for (const f of funders){
                var opt = document.createElement("option");
                opt.value = f.bucketId;
                opt.innerText = `${f.bucket2Id} (${f.grants})`;
                funderSelect.append(opt);
            }
        });
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
        .then(show_data);
}


document.addEventListener("DOMContentLoaded", function () {
    get_funders();
    get_data();
});

document.getElementById("funder-select").addEventListener("change", function(){
    get_data();
})