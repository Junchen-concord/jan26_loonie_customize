import numpy as np
import pandas as pd

from config import config
from labeling.predict_transaction import format_ibv_category


def test_standard_string_category():
    """Tests that standard string categories are returned as is."""
    assert format_ibv_category("Groceries") == "Groceries"
    assert format_ibv_category("Shopping") == "Shopping"
    assert format_ibv_category("Education Fees") == "Education Fees"
    assert format_ibv_category("Miscellaneous") == "Miscellaneous"


def test_stringified_integer_category():
    """Tests that stringified integers are mapped to config.OTHER."""
    assert format_ibv_category("123") == config.OTHER
    assert format_ibv_category("45678") == config.OTHER
    assert format_ibv_category("0") == config.OTHER
    assert format_ibv_category("-99") == config.OTHER


def test_actual_list_of_strings_category():
    """Tests that actual lists of strings are joined by '/'."""
    assert format_ibv_category(["Food", "Dining"]) == "Food/Dining"
    assert format_ibv_category(["Bills", "Rent", "Utilities"]) == "Bills/Rent/Utilities"
    assert format_ibv_category(["Travel"]) == "Travel"
    assert format_ibv_category(["One", "Two", "Three", "Four"]) == "One/Two/Three/Four"


def test_actual_list_with_mixed_types():
    """
    Tests that lists with non-string elements are handled gracefully,
    ignoring non-string types during joining.
    """
    # Numbers should now be ignored, only strings are joined
    assert format_ibv_category(["Category1", 123, "Category2"]) == "Category1/Category2"
    assert format_ibv_category(["Item", 45.67, "Another"]) == "Item/Another"
    assert format_ibv_category([True, "BooleanString", False]) == "BooleanString"
    # None values within the list should still be skipped
    assert format_ibv_category(["Start", None, "End"]) == "Start/End"
    assert format_ibv_category([None, "OnlyStringItem"]) == "OnlyStringItem"
    assert format_ibv_category(["OnlyStringItem", None]) == "OnlyStringItem"
    # List containing only non-strings or None should result in an empty string
    assert format_ibv_category([123, 45.67, True, None]) == ""


def test_empty_list_category():
    """Tests that an empty list returns an empty string."""
    assert format_ibv_category([]) == ""
    assert format_ibv_category([None, None]) == ""


def test_none_value_category():
    """Tests that a None input returns None."""
    assert format_ibv_category(None) is None


def test_pandas_na_value_category():
    """Tests that a pandas.NA input returns pandas.NA."""
    result = format_ibv_category(pd.NA)
    assert pd.isna(result)


def test_numpy_nan_value_category():
    """Tests that a numpy.nan input returns numpy.nan."""
    result = format_ibv_category(np.nan)
    assert np.isnan(result)


def test_other_numeric_types():
    """Tests that raw numeric types (int, float) are returned as is."""
    assert format_ibv_category(100) == config.OTHER
    assert format_ibv_category(50.50) == config.OTHER
    assert format_ibv_category(-25) == config.OTHER


def test_stringified_json_list_of_strings():
    """Tests that JSON-formatted stringified lists of strings are parsed and joined."""
    assert format_ibv_category('["Shops", "Digital"]') == "Shops/Digital"
    assert format_ibv_category('["Home", "Garden"]') == "Home/Garden"
    assert format_ibv_category('["SingleItem"]') == "SingleItem"
    assert format_ibv_category('["Category with spaces"]') == "Category with spaces"
    # Test case with escaped double quotes within the stringified list elements
    assert (
        format_ibv_category('["Category with \\"quotes\\"", "Another Category"]')
        == 'Category with "quotes"/Another Category'
    )


def test_stringified_json_list_with_mixed_types():
    """Tests that JSON-formatted stringified lists with non-string elements ignore them."""
    assert format_ibv_category('["Cat1", 123, "Cat2"]') == "Cat1/Cat2"
    assert format_ibv_category('["Item", true, "Another"]') == "Item/Another"
    assert format_ibv_category('["Start", null, "End"]') == "Start/End"  # JSON null is Python None
    assert format_ibv_category('[1, 2, "String", 4.5, "Last"]') == "String/Last"


def test_stringified_json_empty_list():
    """Tests that an empty JSON stringified list results in an empty string."""
    assert format_ibv_category("[]") == ""
    assert format_ibv_category("[null, 123]") == ""  # List with only non-strings/null


def test_malformed_stringified_list():
    """
    Tests that non-JSON or malformed stringified lists are not processed
    and returned as their original string value.
    """
    # These are not valid JSON, so they should not be parsed as lists
    assert format_ibv_category("[Transfer, Loan]") == "[Transfer, Loan]"  # Missing double quotes
    assert format_ibv_category("['Food', 'Dining']") == "['Food', 'Dining']"  # Single quotes not valid JSON
    assert format_ibv_category("not a list string") == "not a list string"
    assert format_ibv_category("{'key': 'value'}") == "{'key': 'value'}"  # JSON object, not list
    assert format_ibv_category("123 Main St") == "123 Main St"  # Not a number or a list
