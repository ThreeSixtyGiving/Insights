import babel.numbers
import humanize
import inflect


def get_org_schema(org_id):
    if not isinstance(org_id, str):
        return (None, org_id)
    if org_id.upper().startswith("360G"):
        return (None, org_id)
    org_id = org_id.split("-", maxsplit=2)
    if len(org_id) > 2:
        return ("-".join(org_id[:-1]), org_id[-1])
    return (None, "-".join(org_id))


def to_band(value, bins, labels):
    bins = bins.copy()
    if value is None:
        return None
    previous_value = bins.pop(0)
    for i, b in enumerate(bins):
        if value > previous_value and value <= b:
            return labels[i]
        previous_value = b


def list_to_string(l, oxford_comma="auto", separator=", ", as_list=False):
    if len(l) == 1:
        return l[0]
    # if oxford_comma == "auto" then if any items contain "and" it is set to true
    if oxford_comma == "auto":
        if len([x for x in l if " and " in x]):
            oxford_comma = True
        else:
            oxford_comma = False

    if as_list:
        return_list = [l[0]]
        for i in l[1:-1]:
            return_list.append(separator)
            return_list.append(i)
        if oxford_comma:
            return_list.append(separator)
        return_list.append(" and ")
        return_list.append(l[-1])
        return return_list

    return "{}{} and {}".format(
        separator.join(l[0:-1]), separator.strip() if oxford_comma else "", l[-1]
    )


def pluralize(string, count):
    p = inflect.engine()
    return p.plural(string, count)


def get_unique_list(l):
    # from https://stackoverflow.com/a/37163210/715621
    used = set()
    return [
        x.strip() for x in l if x.strip() not in used and (used.add(x.strip()) or True)
    ]


def format_currency(
    amount, currency="GBP", humanize_=True, int_format="{:,.0f}", abbreviate=False
):
    abbreviations = {
        "million": "M",
        "billion": "bn",
        "thousand": "k",
    }

    if humanize_:
        amount_str = humanize.intword(amount).split(" ")
        if amount < 1000000 and amount > 1000:
            chopped = amount / float(1000)
            amount_str = ["{:,.1f}".format(chopped), "thousand"]

        if len(amount_str) == 2:
            return (
                babel.numbers.format_currency(
                    float(amount_str[0]),
                    currency,
                    format="¤#,##0.0",
                    currency_digits=False,
                    locale="en_UK",
                ),
                abbreviations.get(amount_str[1], amount_str[1])
                if abbreviate
                else amount_str[1],
            )

    return (
        babel.numbers.format_currency(
            amount, currency, format="¤#,##0", currency_digits=False, locale="en_UK"
        ),
        "",
    )


def get_currency_name(currency, count=2, locale="en_UK"):
    return babel.numbers.get_currency_name(currency, count, locale)


def charity_number_to_org_id(regno):
    if not isinstance(regno, str):
        return None
    if regno.startswith("S"):
        return "GB-SC-{}".format(regno)
    elif regno.startswith("N"):
        return "GB-NIC-{}".format(regno)
    else:
        return "GB-CHC-{}".format(regno)
