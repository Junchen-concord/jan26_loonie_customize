import itertools
import multiprocessing as mp
import re
from concurrent.futures import ThreadPoolExecutor
from functools import partial

import pandas as pd
import spacy
from tqdm import tqdm

from api.config.config import logger

from labeling.NER.preprocess import PreProcess
from utils.decorators import timer

tqdm.pandas()

PAT_DIGITS = re.compile(r"(\d+)")
PAT_NONALNUM = re.compile(r"[^a-zA-Z0-9\s]")


# === Final unified fallback cleaner for missing WHO (matches Redis exactly) ===
def fill_missing_who(df: pd.DataFrame, text_col="description", stopwords_nltk=None) -> pd.DataFrame:
    """
    Fill missing WHO values using the same cleaning logic as Redis writer
    (ensures no digits or placeholders like xxx234xxxxx56 remain).
    """
    preprocess = PreProcess(stopwords_nltk or [])

    def _fallback(text: str) -> str:
        cleaned = preprocess.clean_description_GPT_knowledge_base(str(text))
        cleaned = re.sub(r"\d+", " ", cleaned)  # remove all digits
        cleaned = re.sub(r"[^a-zA-Z]+", " ", cleaned)  # keep only letters/spaces
        cleaned = " ".join(cleaned.split()).strip().lower()
        return cleaned if cleaned else "NO DESCRIPTION"

    mask = df["WHO"].isnull() | (df["WHO"] == "")
    df.loc[mask, "WHO"] = df.loc[mask, text_col].apply(_fallback)
    df.loc[mask, "WHO_cat"] = "From_cleaned_description"
    return df


@timer
def clean(t: str) -> str:
    t = PAT_DIGITS.sub(r" \1 ", t)  # find all sequences of digits in the string t and surround each with spaces ...
    t = " ".join(t.split(" / "))
    t = " ".join(t.split(" *"))
    t = " ".join(t.split("*"))
    t = remove_punctuation(t)
    return t


@timer
def remove_punctuation(input_string: str) -> str:
    res = PAT_NONALNUM.sub(" ", input_string)
    words = res.split()
    result_string = " ".join(words)
    return result_string


@timer
def get_ner_label(doc, category: str) -> str:
    ent_names = set()
    output = []
    for ent in doc.ents:
        if ent.label_ == category:
            if ent.text not in ent_names:
                ent_names.add(ent.text.lower())
                output.append(ent.text.lower())
    if len(output) == 0:
        return None
    else:
        output = " ".join(output).split()
        # remove consecutive duplicates
        return " ".join([g for g, _ in itertools.groupby(output)])


@timer
def ner_prediction(
    df: pd.DataFrame,
    text_column_name: str,
    nlp: spacy.Language,
    who_priority=["ORG", "Person", "Unknown"],
    progress_bar=False,
    # stopwords_nltk=None,
) -> pd.DataFrame:
    ner_labels = nlp.pipeline[-1][-1].labels
    for who_sub in who_priority:
        assert (
            "WHO_" + who_sub in ner_labels
        ), f"WHO_{who_sub} not in the NER model, Adjust who_priority so that it exists in the existing nlp object"
    if not progress_bar:
        clean_texts = df[text_column_name].apply(clean)
        unique_texts = clean_texts.unique()
        unique_ner_results = list(nlp.pipe(unique_texts))
        text_to_ner_result = dict(zip(unique_texts, unique_ner_results))
        df["ner_result"] = clean_texts.apply(lambda x: text_to_ner_result[x])
    else:
        df.loc[:, "ner_result"] = df.loc[:, text_column_name].progress_apply(lambda x: nlp(clean(x)))
    for ner_label in ner_labels:
        df.loc[:, ner_label] = df.loc[:, "ner_result"].apply(lambda x: get_ner_label(x, ner_label))
    df.loc[:, "WHO"] = None
    df.loc[:, "WHO_cat"] = None
    for who_sub in who_priority[::-1]:
        df.loc[~df.loc[:, "WHO_" + who_sub].isnull(), "WHO"] = df.loc[
            ~df.loc[:, "WHO_" + who_sub].isnull(), "WHO_" + who_sub
        ]
        df.loc[~df.loc[:, "WHO_" + who_sub].isnull(), "WHO_cat"] = who_sub
    # df = fill_missing_who(df, text_col=text_column_name, stopwords_nltk=stopwords_nltk)
    return df


def _process_ner_batch(texts_batch, nlp: spacy.Language):
    """
    Process a batch of texts with NER model in a thread.

    Args:
        texts_batch: List of cleaned text strings to process
        nlp: Shared spaCy Language model

    Returns:
        List of spaCy Doc objects with NER results
    """
    # Use the shared model (threads can share memory)
    return list(nlp.pipe(texts_batch))


def ner_prediction_parallel(
    df: pd.DataFrame,
    text_column_name: str,
    nlp: spacy.Language,
    who_priority=["ORG", "Person", "Unknown"],
    max_workers=None,
    batch_size=None,
    # stopwords_nltk=None,
) -> pd.DataFrame:
    ner_labels = nlp.pipeline[-1][-1].labels
    for who_sub in who_priority:
        assert (
            "WHO_" + who_sub in ner_labels
        ), f"WHO_{who_sub} not in the NER model, Adjust who_priority so that it exists in the existing nlp object"

    # Clean texts and get unique values for processing
    clean_texts = df[text_column_name].apply(clean)
    unique_texts = clean_texts.unique()

    # Only use parallel processing for larger datasets to avoid overhead
    if len(unique_texts) < 500:
        logger.info("Sequential NER processing")
        # Sequential processing for small datasets
        unique_ner_results = list(nlp.pipe(unique_texts))
        text_to_ner_result = dict(zip(unique_texts, unique_ner_results))
        df["ner_result"] = clean_texts.apply(lambda x: text_to_ner_result[x])
    else:
        logger.info("Parallel NER processing")
        # Parallel processing for larger datasets
        if max_workers is None:
            max_workers = min(mp.cpu_count(), 2)  # Conservative cap

        if batch_size is None:
            # Larger batch size to reduce overhead
            batch_size = max(100, len(unique_texts) // max_workers)

        logger.info(f"{len(unique_texts)} unique texts, max_workers: {max_workers}, batch_size: {batch_size}")

        # Split unique texts into batches for parallel processing
        text_batches = [unique_texts[i : i + batch_size] for i in range(0, len(unique_texts), batch_size)]

        # Process batches in parallel using ThreadPoolExecutor
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            batch_results = list(executor.map(partial(_process_ner_batch, nlp=nlp), text_batches))

        # Flatten results and create lookup dictionary
        unique_ner_results = []
        for batch_result in batch_results:
            unique_ner_results.extend(batch_result)

        text_to_ner_result = dict(zip(unique_texts, unique_ner_results))
        df["ner_result"] = clean_texts.apply(lambda x: text_to_ner_result[x])

    for ner_label in ner_labels:
        df.loc[:, ner_label] = df.loc[:, "ner_result"].apply(lambda x: get_ner_label(x, ner_label))

    df.loc[:, "WHO"] = None
    df.loc[:, "WHO_cat"] = None
    for who_sub in who_priority[::-1]:
        df.loc[~df.loc[:, "WHO_" + who_sub].isnull(), "WHO"] = df.loc[
            ~df.loc[:, "WHO_" + who_sub].isnull(), "WHO_" + who_sub
        ]
        df.loc[~df.loc[:, "WHO_" + who_sub].isnull(), "WHO_cat"] = who_sub
    # df = fill_missing_who(df, text_col=text_column_name, stopwords_nltk=stopwords_nltk)
    return df
