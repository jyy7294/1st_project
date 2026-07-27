import math

from scripts.import_cards import clean_nested_value, clean_value


def test_nan_like_values_become_none():
    for value in (float("nan"), "nan", "NaN", " null ", "NONE", "<NA>", "  "):
        assert clean_value(value) is None


def test_nested_nan_like_values_become_none():
    value = {"merchant_list": "nan", "items": [math.nan, "스타벅스"]}

    assert clean_nested_value(value) == {
        "merchant_list": None,
        "items": [None, "스타벅스"],
    }
