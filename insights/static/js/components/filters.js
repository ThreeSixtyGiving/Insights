export function formatNumber(amount, options) {
    var formatter = new Intl.NumberFormat('en-gb', {
        minimumFractionDigits: 0,
        maximumFractionDigits: 0,
        ...options
    });
    return formatter.format(amount);
}

export function formatNumberSuffix(amount, options) {
    var dp = 0;
    var multiple = 1;
    var suffix = getAmountSuffix(amount);
    if (suffix) {
        dp = 1;
        multiple = {
            billion: 1000000000,
            million: 1000000,
            thousand: 1000,
        }[suffix]
    }
    return formatNumber(amount / multiple, {
        minimumFractionDigits: dp,
        maximumFractionDigits: dp,
        ...options
    });
}

export function formatCurrency(amount, currency, suffix = true) {
    var options = {
        style: 'currency',
        currency: currency,
    }
    if (!suffix) {
        return formatNumber(amount, options);
    }
    return formatNumberSuffix(amount, options);
}

export function getAmountSuffix(amount, short) {
    if (amount > 1000000000) {
        return (short ? 'bn' : 'billion')
    } else if (amount > 1000000) {
        return (short ? 'm' : 'million')
    } else if (amount > 10000) {
        return (short ? 'k' : 'thousand')
    }
    return null;
}

export function formatDate(str, format) {
    // turn a date string into a format
    let d = new Date(str);
    if (format == 'year') {
        return d.getFullYear();
    }
    if (format == 'month') {
        return new Intl.DateTimeFormat('en-GB', {
            year: 'numeric',
            month: 'long'
        }).format(d);
    }
    return new Intl.DateTimeFormat('en-GB').format(d);
}
