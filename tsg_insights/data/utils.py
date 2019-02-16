from flask.json import JSONEncoder
import hashlib
import inflect
import humanize
import babel.numbers
import pandas as pd
from requests.structures import CaseInsensitiveDict


def list_to_string(l, oxford_comma='auto', separator=", ", as_list=False):
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
        separator.join(l[0:-1]),
        separator.strip() if oxford_comma else "",
        l[-1]
    )


def pluralize(string, count):
    p = inflect.engine()
    return p.plural(string, count)


def get_unique_list(l):
    # from https://stackoverflow.com/a/37163210/715621
    used = set()
    return [x.strip() for x in l if x.strip() not in used and (used.add(x.strip()) or True)]


def format_currency(amount, currency='GBP', humanize_=True, int_format="{:,.0f}", abbreviate=False):
    abbreviations = {
        'million': 'M',
        'billion': 'bn'
    }

    if humanize_:
        amount_str = humanize.intword(amount).split(" ")
        if len(amount_str) == 2:
            return (
                babel.numbers.format_currency(
                    float(amount_str[0]),
                    currency,
                    format="¤#,##0.0",
                    currency_digits=False,
                    locale='en_UK'
                ),
                abbreviations.get(
                    amount_str[1], amount_str[1]) if abbreviate else amount_str[1]
            )

    return (
        babel.numbers.format_currency(
            amount,
            currency,
            format="¤#,##0",
            currency_digits=False,
            locale='en_UK'
        ),
        ""
    )


def get_fileid(contents, filename, date=None):
    hash_str = str(contents) + str(filename) + str(date)
    hash_obj = hashlib.md5(hash_str.encode())
    return hash_obj.hexdigest()


def charity_number_to_org_id(regno):
    if not isinstance(regno, str):
        return None
    if regno.startswith("S"):
        return "GB-SC-{}".format(regno)
    elif regno.startswith("N"):
        return "GB-NIC-{}".format(regno)
    else:
        return "GB-CHC-{}".format(regno)


class CustomJSONEncoder(JSONEncoder):
    def default(self, obj):
        # handling numpy numbers:
        if isinstance(obj, pd.np.generic):
            return pd.np.asscalar(obj)

        # handling pandas dataframes:
        elif isinstance(obj, (pd.Series, pd.DataFrame)):

            # handling dataframes with multiindex
            if isinstance(obj.index, pd.core.index.MultiIndex):
                obj.index = obj.index.map(" - ".join)
            return obj.to_dict()

        # handling request dicts
        elif isinstance(obj, CaseInsensitiveDict):
            return dict(obj)

        else:
            raise TypeError(
                "Unserializable object {} of type {}".format(obj, type(obj))
            )
        # else let the base class do the work
        return JSONEncoder.default(self, obj)
