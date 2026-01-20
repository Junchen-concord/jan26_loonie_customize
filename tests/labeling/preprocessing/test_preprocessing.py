from labeling.preprocessing.preprocess import clean_description_n_gram


def test_preprocessing_ngram_consistency():
    """Simple end-to-end test for clean_description_n_gram function."""
    ##TODO: This function is mainly for making sure similar transactions are preprocessed into the same text so they are
    ## guaranteed to be clustered together. We can add more test cases later.
    input_string1 = "MONEY TRANSFER AUTHORIZED ON 08/28 FROM Instacash MoneyLion NY P000000153671130 CARD 6109"
    input_string2 = "MONEY TRANSFER AUTHORIZED ON 08/15 FROM Instacash MoneyLion NY P000000885630848 CARD 6109"
    assert clean_description_n_gram(input_string1) == clean_description_n_gram(input_string2)
