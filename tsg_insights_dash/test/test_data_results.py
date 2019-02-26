import pandas as pd

from tsg_insights_dash.data.results import *

def test_get_ctry_rgn():
    df = pd.DataFrame({
        "__geo_ctry": ["England", "England", "England", None, "Scotland", "Northern Ireland", None],
        "__geo_rgn": ["South East", "South West", "South West", None, "Scotland", None, None],
        "Title": ["A", "B", "C", "D", "E", "F", "G"],
        "Amount Awarded": [300, 150, 200, 400, 500, 600, 0]
    })

    # check no results returned if columns not present
    assert get_ctry_rgn(df[["__geo_rgn", "Title", "Amount Awarded"]]) is None
    assert get_ctry_rgn(df[["__geo_ctry", "Title", "Amount Awarded"]]) is None
    assert get_ctry_rgn(df[["Title", "Amount Awarded"]]) is None

    ctry_rgn = get_ctry_rgn(df)

    # check basic results
    assert "Title" not in ctry_rgn.columns
    assert "Grants" in ctry_rgn.columns
    assert ctry_rgn.loc[("England", "South West"), "Grants"] == 2
    assert ctry_rgn.loc[("England", "South West"), "Amount Awarded"] == 350
    assert len(ctry_rgn) == 5
    
    # check Northern Ireland has been renamed
    assert ("Northern Ireland", "Unknown") not in ctry_rgn.index
    assert ("Northern Ireland", "Northern Ireland") in ctry_rgn.index

    # check Unknown moved to the end
    assert ctry_rgn.iloc[-1].name == ("Unknown", "Unknown")
    assert ctry_rgn.iloc[-1]["Grants"] == 2

    # check sort order
    assert ctry_rgn.iloc[0].name == ("Scotland", "Scotland")
    assert ctry_rgn.iloc[-2].name == ("England", "South East")
