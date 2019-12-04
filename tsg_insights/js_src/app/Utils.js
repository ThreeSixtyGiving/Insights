export const formatCurrency = function(value, options){
    let defaults = {
        currency: 'GBP',
        suffix: 'short'
    }
    options = Object.assign({}, defaults, options);
    if(value > 1000000000){
        return [
            (value / 1000000000).toLocaleString(undefined, {
                style: 'currency',
                currency: options.currency,
                minimumFractionDigits: 1,
                maximumFractionDigits: 1
            }),
            options.suffix == 'short' ? 'bn' : 'billion'
        ];
    } else if (value > 1000000) {
        return [
            (value / 1000000).toLocaleString(undefined, {
                style: 'currency',
                currency: options.currency,
                minimumFractionDigits: 1,
                maximumFractionDigits: 1
            }),
            options.suffix == 'short' ? 'm' : 'million'
        ];
    } else if (value > 1000) {
        return [
            (value / 1000).toLocaleString(undefined, {
                style: 'currency',
                currency: options.currency,
                minimumFractionDigits: 0,
                maximumFractionDigits: 0
            }),
            options.suffix == 'short' ? 'k' : 'thousand'
        ];
    } else {
        return [
            value.toLocaleString(undefined, {
                style: 'currency',
                currency: options.currency,
                minimumFractionDigits: 0,
                maximumFractionDigits: 0
            }),
            ""
        ]
    }
}