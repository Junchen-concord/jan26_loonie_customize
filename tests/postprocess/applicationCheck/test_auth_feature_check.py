import numpy as np
import pandas as pd
import pytest

from postprocess.applicationCheck.auth_feature_check import (
    check_account_number_match_multiple,
    check_address_match,
    check_phone_and_email,
    check_routing,
    full_name_match,
)


@pytest.mark.parametrize(
    "IBV, app, expected",
    [
        # 1) app routing is NaN → np.nan
        (["123", "456"], np.nan, np.nan),
        # 2) IBV list is empty → np.nan
        ([], "123", np.nan),
        # 3) IBV list only has nulls → np.nan
        ([np.nan, pd.NA], "123", np.nan),
        # 4) exact match → True
        (["00123", "0456"], "123", True),
        # 5) no match → False
        (["789", "012"], "123", False),
    ],
)
def test_check_routing_various(IBV, app, expected):
    result = check_routing(IBV, app)
    if isinstance(expected, float) and np.isnan(expected):
        assert isinstance(result, float) and np.isnan(result)
    else:
        assert result is expected


def test_full_name_match():
    fname_match_ratio, lname_match_ratio = full_name_match("Lindsey", "Massey", ["APRIL MASSEY"])
    assert fname_match_ratio == 25
    assert lname_match_ratio == 100


def test_check_address_match():
    city_matches, state_matches, zip_matches = check_address_match(
        "Memphis", "TN", "38117", ["Memphis"], ["TN"], ["38117-1808"]
    )
    assert city_matches
    assert state_matches
    assert zip_matches


def test_check_phone_and_email():
    phone_matches, email_matches = check_phone_and_email(
        ["9012391815", "9012252352"], "lindsey.massey01@gmail.com", ["+19012391815"], ["afmassey01@gmail.com"]
    )
    assert phone_matches
    assert not email_matches


def test_check_account_number_match_multiple():
    total_match, last_four_match, first_four_match = check_account_number_match_multiple(
        ["1000043110203"], "1000043110203"
    )
    assert total_match
    assert last_four_match
    assert first_four_match
    assert first_four_match
