from insights.utils import (
    charity_number_to_org_id,
    format_currency,
    get_org_schema,
    get_unique_list,
    list_to_string,
    pluralize,
    to_band,
)


def test_get_org_schema_not_str():
    a, b = get_org_schema(123)
    assert a is None
    assert b == 123


def test_get_org_schema_360G():
    for i in ["360G-123", "360g-123", "360G-123-456", "GB-123"]:
        a, b = get_org_schema(i)
        assert a is None
        assert b == i


def test_get_org_schema_valid():
    for i in [
        ("GB-CHC-12345", "GB-CHC", "12345"),
        ("GB-CHC-12345-678", "GB-CHC", "12345-678"),
    ]:
        a, b = get_org_schema(i[0])
        assert a == i[1]
        assert b == i[2]


def test_to_band():
    assert to_band(1, [0, 3, 5], ["0-3", "4-5"]) == "0-3"
    assert to_band(None, [0, 3, 5], ["0-3", "4-5"]) is None
    assert to_band(0, [0, 3, 5], ["0-3", "4-5"]) is None
    assert to_band(0, [-1, 3, 5], ["0-3", "4-5"]) == "0-3"
    assert to_band(3, [0, 3, 5], ["0-3", "4-5"]) == "0-3"
    assert to_band(4, [0, 3, 5], ["0-3", "4-5"]) == "4-5"
    assert to_band(5, [0, 3, 5], ["0-3", "4-5"]) == "4-5"
    assert to_band(10, [0, 3, 5], ["0-3", "4-5"]) is None


def test_list_to_string():
    lists = [
        (["a"], "a", {}),
        (["a", "b"], "a and b", {}),
        (["a", "b", "c"], "a, b and c", {}),
        (["a", "b", "c", "d"], "a, b, c and d", {}),
        (["a", "b", "c and d", "e"], "a, b, c and d, and e", {}),
        (["a", "b", "c", "d"], "a, b, c, and d", {"oxford_comma": True}),
        (["a", "b", "c", "d"], "a, b, c and d", {"oxford_comma": False}),
        (["a", "b", "c", "d"], "a; b; c and d", {"separator": "; "}),
        (
            ["a", "b", "c", "d"],
            ["a", ", ", "b", ", ", "c", " and ", "d"],
            {"as_list": True},
        ),
        (
            ["a", "b", "c", "d"],
            ["a", ", ", "b", ", ", "c", ", ", " and ", "d"],
            {"as_list": True, "oxford_comma": True},
        ),
    ]
    for l in lists:
        assert l[1] == list_to_string(l[0], **l[2])


def test_pluralize():
    plurals = [
        ["sheep", "sheep", "sheep"],
        ["grant", "grant", "grants"],
        ["recipient", "recipient", "recipients"],
        ["funder", "funder", "funders"],
    ]

    for p in plurals:
        assert p[1] == pluralize(p[0], 1)
        assert p[2] == pluralize(p[0], 2)
        assert p[2] == pluralize(p[0], 200)


def test_unique_list():
    lists = [
        (["a", "b", "c"], ["a", "b", "c"]),
        (["a", "b", "b"], ["a", "b"]),
        (["a", "a", "b", "b"], ["a", "b"]),
        (["a"], ["a"]),
    ]
    for l in lists:
        assert l[1] == get_unique_list(l[0])


def test_format_currency():
    currencies = [
        (10, ("£10", ""), {}),
        (10000, ("£10.0", "thousand"), {}),
        (10000000, ("£10.0", "million"), {}),
        (10000000000, ("£10.0", "billion"), {}),
        # without humanize
        (10, ("£10", ""), {"humanize_": False}),
        (10000, ("£10,000", ""), {"humanize_": False}),
        (10000000, ("£10,000,000", ""), {"humanize_": False}),
        (10000000000, ("£10,000,000,000", ""), {"humanize_": False}),
        # with abbreviations
        (10, ("£10", ""), {"abbreviate": True}),
        (10000, ("£10.0", "k"), {"abbreviate": True}),
        (10000000, ("£10.0", "M"), {"abbreviate": True}),
        (10000000000, ("£10.0", "bn"), {"abbreviate": True}),
        # other currencies
        (10, ("US$10", ""), {"currency": "USD"}),
        (10000, ("€10.0", "thousand"), {"currency": "EUR"}),
        (10000000, ("AUS10.0", "million"), {"currency": "AUS"}),
        (10000000000, ("CND10.0", "billion"), {"currency": "CND"}),
    ]
    for c in currencies:
        assert c[1] == format_currency(c[0], **c[2])


def test_charity_number_to_org_id():
    charity_numbers = [
        (123545, None),
        ("123456", "GB-CHC-123456"),
        ("SC123456", "GB-SC-SC123456"),
        ("NIC123456", "GB-NIC-NIC123456"),
    ]
    for c in charity_numbers:
        assert charity_number_to_org_id(c[0]) == c[1]
