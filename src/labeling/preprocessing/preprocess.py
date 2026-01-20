import re
from functools import lru_cache

import pandas as pd
from config import config
from dataset.us_cities import get_us_cities
from scipy.cluster.hierarchy import fcluster, linkage
from sklearn.feature_extraction.text import CountVectorizer

CAPS_SPLIT_PATTERN = re.compile(r"[A-Z]+[^A-Z]*")
LONG_DIGITS_SPLIT_PATTERN = re.compile(r"(\d{5,})")
SPECIAL_CHAR_REMOVE_PATTERN = re.compile(r"[^a-zA-Z\d\*\s_]")
PAYROLL_LEFT_PATTERN = re.compile(r"\bpayroll")
PAYROLL_RIGHT_PATTERN = re.compile(r"payroll\b")

STOPWORDS = config.STOPWORDS

cities = get_us_cities()
_STATE_ABBR = config.STATE_ABBR
STATE_ABBR = [r"\b" + x.lower() + r"\b" for x in _STATE_ABBR]
irrelevant_words = config.IRRELEVANT_WORDS

irrelevant_bigrams = [re.compile(r"\b" + re.escape(bigram) + r"\b") for bigram in [r"cash app", r"los angelos"]]
capital_split_re = re.compile(r"[A-Z]+[^A-Z]*")
long_number_split_re = re.compile(r"(\d{5,})")
special_char_re = re.compile(r"[^a-zA-Z\d\s_]")
card_number_re = re.compile(r"x{4,}")
short_digits_re = re.compile(r"\b(\d{1,3})\b")
four_digits_re = re.compile(r"\b(\d{4})\b")
long_digits_re = re.compile(r"\b([a-z]*\d{5,17}\w*)\b")
extremely_long_digits_re = re.compile(r"\b([a-z]*\d{18,}\w*)\b")
mixed_long_digits_re = re.compile(r"\b(([a-z]*[0-9]){3,}\w*)\b")
long_word_with_numbers_re = re.compile(r"\b(?=\w*[^\W\d_])(?=\w*\d)\w{9,}\b")
conf_number_re = re.compile(r"\b(?:CONF(?:IRMATION)?|AUTH|CODE|ID|REF#?|CONF#)[:\s#]*[a-z0-9]+\b", re.IGNORECASE)
long_token_with_digits_re = re.compile(r"\b(?=(?:\w*\d){5})\w{12,}\b")
indn_re = re.compile(r"\b(indn#?:?\s?[a-z0-9]+)\b")
# Matches dates: MM/DD/YYYY, YYYY-MM-DD, Month DD YYYY, DD Month YYYY, Month DD, DD Month, MM/DD, etc.
date_re = re.compile(
    r"\b(\d{1,2}[-/]\d{1,2}[-/]\d{2,4}|\d{4}[-/]\d{1,2}[-/]\d{1,2}|\d{1,2}[-/]\d{1,2}(?!\d)|(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\s+\d{1,2}(?:[,\s]+\d{2,4})?|\d{1,2}\s+(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*(?:[,\s]+\d{2,4})?)\b"
)
single_char_re = re.compile(r"\b\w\b")
star_re = re.compile(r"\*")


@lru_cache(maxsize=1000)
def clean_description_n_gram(text: str) -> str:
    # Replace confirmation numbers and long tokens with digits with CONFNUMBER (before splitting long numbers)
    text = conf_number_re.sub(" CONFNUMBER ", text)
    text = long_token_with_digits_re.sub(" CONFNUMBER ", text)

    # Split word by Capital letter
    text = " ".join(" ".join(capital_split_re.findall(x)) if x[0].isupper() else x for x in text.split())

    # Cast to lower case
    text = text.lower()

    # Split long numbers from string
    # TODO: Honestly I can't rememeber clearly why I added this, likely for better getting entity names, but we probably should still
    # Remove long confirmation code before this step is done.
    text = long_number_split_re.sub(r" \1 ", text)

    # Replace dates with DATEABBR
    text = date_re.sub(" DATEABBR ", text)

    # Encode city names
    ## TODO: Right now it is case sensitive and may create inconsistencies, but changing this directly might cause instability too.
    text = " ".join("CITYABBR" if x in cities and bool(re.search(cities[x], text)) else x for x in text.split())

    # Special character to space
    text = special_char_re.sub(" ", text)

    # Strings that have 4+ X encoded to 0
    text = card_number_re.sub("0000", text)

    # Encode numbers separated by space, remove short numbers (1-3 digits)
    text = short_digits_re.sub(" ", text)

    # Digits shows up more than 4 times
    text = four_digits_re.sub(" FourDigits ", text)
    text = long_digits_re.sub(" LongDigits ", text)
    text = mixed_long_digits_re.sub(" LongDigits ", text)
    text = long_word_with_numbers_re.sub(" LongDigits ", text)

    # Extremely long digits
    text = extremely_long_digits_re.sub(" ExLongDigits ", text)

    # Remove single characters
    text = single_char_re.sub(" ", text)

    # Remove *
    text = star_re.sub(" ", text)

    # State abbr encoded
    s_state_encoded = re.sub("|".join(STATE_ABBR), " StateAbbr ", text)

    # Concatenates each term of the list to the string
    text = s_state_encoded.strip()
    text = find_payroll(text)
    text = find_direct_deposit(text)

    # No word left return "no description"
    if len(text) == 0 or sum([x not in STOPWORDS for x in text.lower().split()]) == 0:
        text = "NO DESCRIPTION"
    return text


@lru_cache(maxsize=1000)
def clean_description_clustering(text: str) -> str:
    """Additional preprocessing used for clustering. Removes irrelevant keywords for finding the entity names in the description, so the cluster can work better on group."""

    original_text = text

    # remove person names after INDN
    text = re.sub(indn_re, " ", text)

    # remove person names found by NER
    # if len(person_names) > 0:
    #     text = re.sub(r"|".join(person_names), " ", text)
    # Remove irrelevant words

    words = text.split()
    words_filtered = [word for word in words if word not in irrelevant_words]

    # Join filtered words back into a string
    s_irrelevant_words_removed = " ".join(words_filtered)

    # Remove irrelevant bigrams
    for irrelevant_bigram in irrelevant_bigrams:
        s_irrelevant_words_removed = irrelevant_bigram.sub(" ", s_irrelevant_words_removed)

    s_irrelevant_words_removed = s_irrelevant_words_removed.strip()

    # Remove duplicates
    text = remove_duplicates(s_irrelevant_words_removed)

    # No word left return "no description"
    if not text or all(word in STOPWORDS for word in text.lower().split()):
        text = original_text

    return text


@lru_cache(maxsize=1000)
def clean_description_knowledge_base(text: str) -> str:
    # Split word by Capital letter
    text = " ".join(" ".join(CAPS_SPLIT_PATTERN.findall(x)) if x[0].isupper() else x for x in text.split())
    # Cast to lower case
    s_lower = text.lower()
    # split long numbers from string
    s_long_digits_splited = " ".join(LONG_DIGITS_SPLIT_PATTERN.split(s_lower))
    # Special character to space
    s_special_char_removed = SPECIAL_CHAR_REMOVE_PATTERN.sub(" ", s_long_digits_splited)

    text = s_special_char_removed.strip()

    # No word left return "no description"
    if len(text) == 0 or sum([x not in STOPWORDS for x in text.lower().split()]) == 0:
        text = "NO DESCRIPTION"
    return text


@lru_cache(maxsize=1000)
def remove_duplicates(s: str) -> str:
    """Remove duplicate names in one description, e.g. Dave Dave."""

    word_list = s.split()
    unique_words = set()
    out = []
    for word in word_list:
        if word not in unique_words:
            unique_words.add(word)
            out.append(word)
    return " ".join(out)


@lru_cache(maxsize=1000)
def find_payroll(x: str) -> str:
    """Change anything looks like a payroll into payroll."""

    tokens = x.split()
    output = []
    for token in tokens:
        # Check for payroll inside token, then split words.
        search_left = PAYROLL_LEFT_PATTERN.search(token)
        search_right = PAYROLL_RIGHT_PATTERN.search(token)
        if search_left is not None:
            end = search_left.end()
            output = output + ["payroll", token[end:]]
        elif search_right is not None:
            start = search_right.start()
            output = output + ["payroll", token[:start]]
        elif token in [
            "payrol",
            "payrll",
            "pyrll",
            "paycheck",
            "salary",
        ]:  # Check for misspelled payroll
            output.append("payroll")
        else:
            output.append(token)
    return " ".join(output)


@lru_cache(maxsize=1000)
def find_direct_deposit(x: str) -> str:
    """Change anything that looks like direct deposit into dir dep."""

    tokens = x.split()
    # Return the input if only one word
    if len(tokens) <= 1:
        return x
    output = tokens.copy()
    for i in range(len(tokens) - 1):
        bigram = (tokens[i], tokens[i + 1])
        # Format all things look like direct deposit just into dir dep
        if bigram[0] in ["direct", "dir"] and bigram[1] in [
            "deposit",
            "dep",
        ]:
            output[i], output[i + 1] = "dir", "dep"
        # Add the modified text back
    return " ".join(output)


# Cannot be cached as df_customer is an unhashable type
def group_transactions(
    df_customer: pd.DataFrame,
    preprocess_col: str,
    max_distance: float,
    linkage_method="average",
    metric="cosine",
    ngram_range=(1, 1),
) -> pd.DataFrame:
    if len(df_customer) > 1:
        try:
            vectorizer = CountVectorizer(stop_words=list(STOPWORDS), ngram_range=ngram_range)
            X = vectorizer.fit_transform(df_customer[preprocess_col])

            # Perform hierarchical clustering
            Z = linkage(X.toarray() + 1e-4, method=linkage_method, metric=metric)

            # Form flat clusters from the hierarchical clustering defined by the given linkage matrix
            df_customer["cluster_label"] = fcluster(Z, max_distance, criterion="distance")

        except Exception:
            df_customer["cluster_label"] = -1
    else:
        df_customer["cluster_label"] = 1
    # Change cluster to string to avoid a very rare bug where this collides with dataframe index, making pandas drop cluster_label unexpectively
    df_customer["cluster_label"] = df_customer["cluster_label"].astype(str)
    return df_customer
