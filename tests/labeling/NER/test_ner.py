import json
import os

import pandas as pd
from pandas.testing import assert_frame_equal

from config import config
from config.preload import load_ner_model
from labeling.NER import clean, ner_prediction, remove_punctuation

ner_prediction_input = os.path.realpath(
    os.path.join(config.ROOT_DIR, "..", "tests", "data", "ner_prediction_input_df.json")
)


def test_ner_prediction():
    with open(ner_prediction_input, "r") as fp:
        data = json.load(fp)
    df = pd.DataFrame.from_dict(data)
    nlp = load_ner_model(config.NER_MODEL_PATH)
    ner_df = ner_prediction(df, config.IA_ORIGINAL_DESCRIPTION, nlp)
    ner_df["category"] = ner_df["category"].astype(str)
    ner_df["ner_result"] = ner_df["ner_result"].astype(str)
    expected_output_path = os.path.realpath(
        os.path.join(config.ROOT_DIR, "..", "tests", "data", "expected_ner_output.csv")
    )
    expected_df = pd.read_csv(expected_output_path)
    expected_df.drop(columns="Unnamed: 0", inplace=True)
    expected_df["category"] = expected_df["category"].astype(str)
    assert_frame_equal(ner_df, expected_df, check_dtype=False, atol=0.01, rtol=0.01)


def test_remove_punctuation():
    # Basic functionality test
    assert remove_punctuation("Hello, world!") == "Hello world", "Failed to remove basic punctuation"

    # Test with numbers and possessive case
    assert (
        remove_punctuation("Example 123! It's a test.") == "Example 123 It s a test"
    ), "Failed with numbers and apostrophes"

    # Test multiple spaces are reduced to single spaces
    assert remove_punctuation("This   is a  test.") == "This is a test", "Failed to collapse multiple spaces"

    # Test no punctuation input
    assert remove_punctuation("Just some text") == "Just some text", "Failed with no punctuation input"

    # Test empty string
    assert remove_punctuation("") == "", "Failed with empty string"


def test_clean():
    # Test handling numbers
    assert (
        clean("There are 2 numbers 15 in this sentence") == "There are 2 numbers 15 in this sentence"
    ), "Failed to handle numbers correctly"

    # Test removing slashes and stars
    assert clean("Split/this*string/correctly") == "Split this string correctly", "Failed to handle slashes and stars"

    # Test complex string with various operations
    text = "Cleaning 123 / a complex * string with, punctuation!"
    expected = "Cleaning 123 a complex string with punctuation"
    assert clean(text) == expected, "Failed with complex string cleaning"

    # Test empty string
    assert clean("") == "", "Failed with empty string"

    # Test string with only punctuation
    assert clean("!?,.*") == "", "Failed with string of only punctuation"
