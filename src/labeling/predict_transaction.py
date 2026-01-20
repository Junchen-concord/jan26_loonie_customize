import json

import numpy as np
import pandas as pd

from app_utils import logger
from config import config
from config.preload import load_ner_model
from labeling.agent_label_utils import apply_agent_labeling, extract_agent_categories
from labeling.clustering import NER_Clustering
from labeling.knowledgebase import NER_Based_KnowledgeBase, Regex_Based_KnowledgeBase
from labeling.knowledgebase.redis_knowledgebase import RedisKnowledgeBase

# from labeling.knowledgebase.redis_knowledgebase import RedisKnowledgeBase
from labeling.NER import ner_prediction_parallel
from labeling.preprocessing.preprocess import (
    clean_description_clustering,
    clean_description_knowledge_base,
    clean_description_n_gram,
)
from labeling.transaction_prep import initialize_transaction_fields
from labeling.xgboost.analyzers import IA_get_model

# Custom cache for format_ibv_category to handle unhashable types
_format_ibv_category_cache = {}


def format_ibv_category(value):
    """
    Formats a category value based on its type:
    - If None/NaN, returns as is.
    - If an actual list of strings, joins them with '/'.
    - If a stringified list (JSON format), parses and joins string elements with '/'.
    - If a stringified integer, returns config.OTHER.
    - Otherwise, returns the original value.
    """
    import pandas as pd

    # Create a cache key for hashable types
    cache_key = None
    if value is None:
        cache_key = ("none", None)
    elif isinstance(value, (str, int, float)):
        cache_key = (type(value).__name__, value)
    elif isinstance(value, list):
        # Create cache key from list contents
        try:
            cache_key = ("list", tuple(value))  # Only works if list items are hashable
        except TypeError:
            cache_key = ("list", str(value))  # Fallback to string representation

    # Check cache first
    if cache_key is not None and cache_key in _format_ibv_category_cache:
        return _format_ibv_category_cache[cache_key]

    # Original logic
    def _join_list_elements(lst):
        string_elements = [item.strip() for item in lst if item is not None and isinstance(item, str)]
        if len(string_elements) > 0:
            return "/".join(string_elements)
        else:
            return ""

    result = None

    # 1. Handle actual lists (e.g., ["Transfer", "Loan"])
    if isinstance(value, list):
        result = _join_list_elements(value)
    elif pd.isna(value):
        result = value
    # 2. Handle string types (stringified integers, stringified lists, standard strings)
    elif isinstance(value, str):
        # Try to handle stringified lists (JSON format preferred)
        try:
            parsed_value = json.loads(value)
            if isinstance(parsed_value, list):
                result = _join_list_elements(parsed_value)
        except json.JSONDecodeError:
            pass  # Not a valid JSON string, fall through to other checks

        if result is None:
            # Try to handle stringified integers
            try:
                int(value)
                result = config.OTHER
            except ValueError:
                result = value  # Return original string
    elif isinstance(value, (int, float)):
        result = config.OTHER
    else:
        result = value

    # Cache the result if we have a valid cache key
    if cache_key is not None:
        # Limit cache size to prevent memory issues
        if len(_format_ibv_category_cache) >= 500:
            # Remove oldest entries (simple FIFO, not LRU but good enough)
            oldest_key = next(iter(_format_ibv_category_cache))
            del _format_ibv_category_cache[oldest_key]
        _format_ibv_category_cache[cache_key] = result

    return result


# def format_ibv_category(value):
#     if pd.isna(value):
#         return config.OTHER

#     # 1. Handle lists
#     if isinstance(value, list):
#         string_elements = [item.strip() for item in value if item is not None and isinstance(item, str)]
#         if string_elements:
#             return "/".join(string_elements)
#         else:
#             return ""

#     # 2. Handle stringified integers
#     if isinstance(value, str):
#         try:
#             int(value)
#             return config.OTHER
#         except ValueError:
#             pass

#     # Handle stringified lists (e.g. "[\"Shops\", \"Digital\"...]")
#     match = re.search(r"\[(.*?)\]", value)
#     if not match:
#         return value.strip().replace('"', "")
#     content = match.group(1)

#     items = [item.strip().replace('\\"', "").replace('"', "") for item in re.split(r', *(?=")', content)]
#     cleaned_items = [item for item in items if item]

#     return "/".join(cleaned_items)


def predict_transaction(df: pd.DataFrame) -> pd.DataFrame:
    # Copy over IBV's categorization "category" into a new column "IBV_category"
    if config.CATEGORY_COLUMN_NAME in df.columns:
        df[config.IBV_CATEGORY] = df[config.CATEGORY_COLUMN_NAME].apply(format_ibv_category)
    else:
        logger.warning(f"Warning: Column '{config.CATEGORY_COLUMN_NAME}' not found in DataFrame.")
        df[config.IBV_CATEGORY] = None

    # initiate model and knowledge base
    redis_knowledge_base = RedisKnowledgeBase()  # TODO: enable once Redis DB is set up
    regex_knowledge_base = Regex_Based_KnowledgeBase(config.KNOWLEDGEBASE_DATA_PATH)
    NER_knowledge_base = NER_Based_KnowledgeBase(config.NER_KNOWLEDGEBASE_DATA_PATH, config.NER_SOURCE_MAP_PATH)
    model = IA_get_model(config, load_model=True, training=False)

    # separate labeled and new transactions, NER will not be performed on labeled transactions
    # ideally, other cleaning steps should not be done in labeled transactions as well, but currently these are not stored in
    # model output so will need to regenerate them.
    if config.IA_LABELING_COLUMN in df.columns:
        df.loc[:, "new_transaction"] = pd.isnull(df.loc[:, config.IA_LABELING_COLUMN])
        df.loc[:, config.STACKING_PREDICTION] = df.loc[:, config.IA_LABELING_COLUMN]
        new_transactions = df[df.new_transaction].copy()
        labeled_transactions = df[~df.new_transaction].copy()
        labeled_transactions = initialize_transaction_fields(labeled_transactions)
        agent_category_transactions = extract_agent_categories(labeled_transactions)
        check_history_label_schema(labeled_transactions, config.STACKING_PREDICTION)
    else:
        # All new transactions
        # Create a copy to avoid SettingWithCopyWarning
        df_copy = df.copy()

        # Use loc for all column assignments
        df_copy.loc[:, "new_transaction"] = True
        df_copy.loc[:, config.STACKING_PREDICTION] = None
        df_copy.loc[:, config.WHO_COL] = None
        df_copy.loc[:, config.WHAT_COL] = None
        df_copy.loc[:, config.HOW_COL] = None
        df_copy.loc[:, "fromModel"] = None

        new_transactions = df_copy.copy()
        labeled_transactions = pd.DataFrame()
        agent_category_transactions = pd.DataFrame()

    # NER
    nlp = config.NLP_MODEL
    if nlp is None:
        nlp = load_ner_model(config.NER_MODEL_PATH)

    if len(new_transactions) > 0:
        new_transactions = ner_prediction_parallel(new_transactions, config.IA_ORIGINAL_DESCRIPTION, nlp)
        new_transactions.loc[:, config.WHO_COL] = new_transactions.loc[:, config.WHO_COL].apply(
            lambda x: NER_knowledge_base.process_NER_LABEL(x)
        )
        new_transactions.loc[:, config.WHAT_COL] = new_transactions.loc[:, config.WHAT_COL].apply(
            lambda x: NER_knowledge_base.process_NER_LABEL(x)
        )
        new_transactions.loc[:, config.HOW_COL] = new_transactions.loc[:, config.HOW_COL].apply(
            lambda x: NER_knowledge_base.process_NER_LABEL(x)
        )

    # TODO: increase the accuracy of person name findings in NER to actually use this, right now it has too many false positives
    # # find person names from NER as a by-product for clustering
    # person_names = list(df.loc[df[config.WHO_CAT_COL] == "Person", config.WHO_COL].unique())
    # person_names = [r"\b" + name.lower() + r"\b" for name in person_names]
    # person_names = []

    # Clustering based on NER
    to_concat = [df for df in [labeled_transactions, new_transactions] if not df.empty]
    df = pd.concat(to_concat, axis=0).reset_index(drop=True)

    # map known similar who, why, how to the same source, for example, interest and dividend should have the same meaning
    df.loc[:, config.WHO_SOURCE] = df.loc[:, config.WHO_COL].apply(
        lambda x: NER_knowledge_base.source_map_entities(x, "WHO")
    )
    df.loc[:, "why_source"] = df.loc[:, config.WHAT_COL].apply(
        lambda x: NER_knowledge_base.source_map_entities(x, "WHY")
    )
    df.loc[:, "how_source"] = df.loc[:, config.HOW_COL].apply(
        lambda x: NER_knowledge_base.source_map_entities(x, "HOW")
    )
    if config.PROCESSED_N_GRAM not in df.columns:
        df[config.PROCESSED_N_GRAM] = df[config.IA_ORIGINAL_DESCRIPTION].apply(clean_description_n_gram)
    if config.PROCESSED_CLUSTERING not in df.columns:
        df[config.PROCESSED_CLUSTERING] = df[config.PROCESSED_N_GRAM].apply(clean_description_clustering)
    if config.PROCESSED_KNOWLEDGE_BASE not in df.columns:
        df[config.PROCESSED_KNOWLEDGE_BASE] = df[config.IA_ORIGINAL_DESCRIPTION].apply(clean_description_knowledge_base)

    df = (
        df.groupby(config.IA_CUSTOMER_ID)
        .apply(
            lambda x: NER_Clustering(config.IA_MAX_DISTANCE).group_transactions(
                x,
                config.WHO_SOURCE,
                config.WHO_CAT_COL,
            )
        )
        .reset_index(drop=True)
    )

    # For testing purpose, user can disable knowledge base
    if not config.USE_REGEX_KNOWLEDGE_BASE:
        regex_knowledge_base.disable()
    if not config.USE_NER_KNOWLEDGE_BASE:
        NER_knowledge_base.disable()

    # We cannot parallelize these steps because it is important everything goes through Regex before going through NER.
    redis_knowledge_base_df, remainder_df = redis_knowledgebase_prediction(df, redis_knowledge_base)
    regex_knowledge_base_df, remainder_df = regex_knowledgebase_prediction(remainder_df, regex_knowledge_base)
    NER_knowledge_base_df, remainder_df = NER_knowledgebase_prediction(remainder_df, NER_knowledge_base)

    to_concat = [df for df in [regex_knowledge_base_df, NER_knowledge_base_df, redis_knowledge_base_df] if not df.empty]
    if to_concat:
        knowledge_base_df = pd.concat(to_concat, axis=0).reset_index(drop=True)
    else:
        logger.warning("No knowledge base dfs")
        expected_kb_df_columns = [
            "originalDescription",
            "description",
            "GUID",
            "accountGuid",
            "category",
            "amount",
            "date",
            "type",
            "ibvCategory",
            "new_transaction",
            "StackingPrediction",
            "WHO",
            "WHAT",
            "HOW",
            "fromModel",
            "ner_result",
            "WHO_ORG",
            "WHO_Person",
            "WHO_Unknown",
            "WHO_cat",
            "who_source",
            "why_source",
            "how_source",
            "processed_n_gram",
            "processed_clustering",
            "processed_knowledge_base",
            "who_processed",
            "cluster_label",
        ]
        knowledge_base_df = pd.DataFrame(columns=expected_kb_df_columns)
    fields = config.TRANSACTION_FIELDS
    existing_fields = [field for field in fields if field in knowledge_base_df.columns]

    # xgboost prediction, best guessing for the label if not in KB
    # no need to go through prediction model if all are handled by knowledge base
    if len(remainder_df) > 0:
        remainder_df.loc[:, "n_new_transactions"] = remainder_df.groupby(
            [config.IA_CUSTOMER_ID, "cluster_label"]
        ).new_transaction.transform("sum")
        remainder_df.loc[:, "n_transactions"] = remainder_df.groupby(
            [config.IA_CUSTOMER_ID, "cluster_label"]
        ).new_transaction.transform("count")
        remainder_df.loc[:, "n_labeled_transactions"] = remainder_df.n_transactions - remainder_df.n_new_transactions

        # TODO: Once redis knowledge base is implemented, where knowledge base will make decisions based on frequency as well
        # we should adjust labels for labeled transactions if we observed a significant frequency/amount change of that cluster
        # for now, new transactions will copy the label from the labeled transactions in the same cluster

        all_labeled_transaction_clusters = remainder_df.loc[
            (remainder_df["n_new_transactions"] == 0) & (remainder_df["n_labeled_transactions"] > 0)
        ]  # will not relabel
        all_new_transaction_clusters = remainder_df.loc[
            (remainder_df["n_new_transactions"] > 0) & (remainder_df["n_labeled_transactions"] == 0)
        ]
        mixed_transaction_clusters = remainder_df.loc[
            (remainder_df["n_new_transactions"] > 0) & (remainder_df["n_labeled_transactions"] > 0)
        ]

        mixed_transaction_clusters = (
            mixed_transaction_clusters.groupby([config.IA_CUSTOMER_ID, "cluster_label"]).apply(
                copy_labels_from_labeled_transactions
            )
            # .reset_index(drop=True)
        )

        # Subset of already labeled transactions
        already_labeled_rows = mixed_transaction_clusters.loc[
            ~mixed_transaction_clusters["new_transaction"], "fromModel"
        ]

        if not already_labeled_rows.empty:
            # Create a mask for better readability and safety
            historical_mask = ~mixed_transaction_clusters["new_transaction"]
            mixed_transaction_clusters.loc[historical_mask, "fromModel"] = "historicalLabeling"

        all_labeled_transaction_clusters.loc[:, "fromModel"] = "historicalLabeling"

        if len(all_new_transaction_clusters) > 0:
            preprocessed_df = model[0].transform(all_new_transaction_clusters)
            preprocessed_df = preprocessed_df.drop(columns=config.STACKING_PREDICTION)
            cluster_level_features = model[1].transform(preprocessed_df)
            y_pred = model[2:].predict(cluster_level_features)
            # Make a copy of the cluster_level_features DataFrame to avoid chained assignment
            features_df = cluster_level_features.copy()
            features_df.loc[:, config.STACKING_PREDICTION] = y_pred

            # Merge operation creates a new DataFrame, so no chained assignment here
            output = preprocessed_df.merge(
                features_df[["cluster_label", config.IA_ACCOUNT_ID, config.STACKING_PREDICTION]],
                how="left",
                on=[config.IA_ACCOUNT_ID, "cluster_label"],
            )

            # Create a copy to ensure we're working with a clean DataFrame
            output_df = output.copy()

            # Use loc for all assignments
            output_df.loc[:, config.STACKING_PREDICTION] = output_df[config.STACKING_PREDICTION].astype(object)
            output_df.loc[output_df.StackingPrediction == 1, config.STACKING_PREDICTION] = "payroll"
            output_df.loc[output_df.StackingPrediction == 2, config.STACKING_PREDICTION] = "loan"
            output_df.loc[output_df.StackingPrediction == 3, config.STACKING_PREDICTION] = "transfer"
            output_df.loc[output_df.StackingPrediction == 0, config.STACKING_PREDICTION] = "other"
            output_df.loc[:, config.STACKING_PREDICTION] = output_df[config.STACKING_PREDICTION].astype(str)

            output = output_df

            output = output[existing_fields]
            # ideally, we should retrain the xgb without the loan label, but very likely the missed loans from knowledgebase
            # will just go into transfer anyway, so we just remove the loan label here until we have a clear boundary of where
            # to guess and where to use knowledge base.

            # xgb should not predict loan, but if it does, we will remove it

            # Catch obvious transfers within loan predictions
            # Create a mask with all conditions to improve readability and avoid chain indexing
            transfer_mask = (
                (output[config.STACKING_PREDICTION] == "loan")
                & (
                    output[config.IA_ORIGINAL_DESCRIPTION].str.contains(
                        r"|".join(["\bdep", "atm", "transfer", "xfer"]), case=False
                    )
                )
                & (
                    ~output[config.IA_ORIGINAL_DESCRIPTION].str.contains(
                        r"|".join(config.FS_NOT_TRANSFER_KWDS), case=False
                    )
                )
            )

            # Apply the modification using loc with the mask
            output.loc[transfer_mask, config.STACKING_PREDICTION] = "transfer"

            # Catch obvious payroll within loan predictions
            # Create a mask for payroll conditions
            payroll_mask = (output[config.STACKING_PREDICTION] == "loan") & output[
                config.IA_ORIGINAL_DESCRIPTION
            ].str.contains("payroll", case=False)

            # Apply the modification using loc with the mask
            output.loc[payroll_mask, config.STACKING_PREDICTION] = "payroll"

            # Do not use xgb on remaining loan predictions
            # Create a simple mask for remaining loan predictions
            remaining_loan_mask = output[config.STACKING_PREDICTION] == "loan"

            # Apply the modification using loc with the mask
            output.loc[remaining_loan_mask, config.STACKING_PREDICTION] = "other"
        else:
            output = pd.DataFrame()

        knowledge_base_df = knowledge_base_df[existing_fields]
        mixed_transaction_clusters = mixed_transaction_clusters[existing_fields]
        all_labeled_transaction_clusters = all_labeled_transaction_clusters[existing_fields]

        to_concat = [
            df
            for df in [
                output,
                knowledge_base_df,
                mixed_transaction_clusters,
                all_labeled_transaction_clusters,
            ]
            if not df.empty
        ]
        output = pd.concat(
            to_concat,
            axis=0,
        ).reset_index()
    else:
        output = knowledge_base_df[existing_fields]

    # Handle agent labeling
    if len(agent_category_transactions) > 0:
        output = apply_agent_labeling(output, agent_category_transactions)

    # Remove some obvious non transfer using keywords
    output.loc[
        (output.StackingPrediction == "transfer")
        & (
            output[config.TA_ORIGINAL_DESCRIPTION]
            .str.contains("|".join(config.FS_NOT_TRANSFER_KWDS), case=False)
            .fillna(0)
            .astype(bool)
        ),
        config.STACKING_PREDICTION,
    ] = config.OTHER
    output.loc[
        (output.StackingPrediction == "payroll") & (output.type == "DEBIT"),
        config.STACKING_PREDICTION,
    ] = config.OTHER
    output.loc[
        (output.StackingPrediction == "gig") & (output.type == "DEBIT"),
        config.STACKING_PREDICTION,
    ] = config.OTHER

    return output


def copy_labels_from_labeled_transactions(df_cluster):
    """
    Copy labels from labeled transactions to new transactions in the same cluster.
    Guard against clusters that do not actually contain historical rows or where those
    rows are missing a stacking prediction so we avoid mode()/iloc failures.
    """

    labeled_rows = df_cluster[~df_cluster.new_transaction]
    if labeled_rows.empty:
        return df_cluster

    majority_series = labeled_rows.StackingPrediction.dropna()
    if majority_series.empty:
        return df_cluster

    majority_label = majority_series.astype(str).mode()
    if majority_label.empty:
        return df_cluster

    label = majority_label.iloc[0]
    new_transaction_mask = df_cluster.new_transaction
    df_cluster.loc[new_transaction_mask, config.STACKING_PREDICTION] = label
    df_cluster.loc[new_transaction_mask, "fromModel"] = "copiedFromHistory"
    return df_cluster


def redis_knowledgebase_prediction(df, redis_knowledge_base: RedisKnowledgeBase):
    """
    Predicts transaction labels using redis knowledge base
    """
    # Redis KB (controlled by env var REDIS_KB_ENABLED)
    if redis_knowledge_base.enabled:
        df = redis_knowledge_base.knowledge_base_prediction(df)
        redis_knowledge_base_df = df[df[config.FROM_MODEL] == "RedisKnowledgeBase"]
        remainder_df = df[df[config.FROM_MODEL] != "RedisKnowledgeBase"]
        return redis_knowledge_base_df, remainder_df
    else:
        logger.info("Skipping Redis KB as REDIS_KB_ENABLED is set to false")
        return pd.DataFrame(), df


def regex_knowledgebase_prediction(df, regex_knowledge_base: Regex_Based_KnowledgeBase):
    """
    Predicts transaction labels using regex knowledge base
    """
    df = regex_knowledge_base.knowledge_base_prediction(df)
    regex_knowledge_base_df = df[df[config.FROM_MODEL] == "RegexSearchKnowledge"]
    remainder_df = df[df[config.FROM_MODEL] != "RegexSearchKnowledge"]
    return regex_knowledge_base_df, remainder_df


def NER_knowledgebase_prediction(df, NER_knowledge_base):
    """
    Predicts transaction labels using NER knowledge base
    """
    df = NER_knowledge_base.knowledge_base_prediction(df)
    NER_knowledge_base_df = df[df[config.FROM_MODEL] == "NERKnowledge"]
    remainder_df = df[(df[config.FROM_MODEL] != "NERKnowledge")]
    return NER_knowledge_base_df, remainder_df


def check_history_label_schema(df: pd.DataFrame, column_name: str) -> None:
    allowed_categories = ["payroll", "benefit", "transfer", "deposit", "gig", "loan", "other"]
    column_values = df.loc[:, column_name]
    try:
        lowercased_values = column_values.astype(str).str.lower()
    except AttributeError:
        raise TypeError(f"Column '{column_name}' contains non-string values and cannot be lowercased.")

    invalid_indices = np.where(~lowercased_values.isin(allowed_categories))[0]

    if len(invalid_indices) > 0:
        first_invalid_index = invalid_indices[0]
        first_invalid_value = column_values.iloc[first_invalid_index]  # Use iloc for integer indexing
        raise AssertionError(
            f"Unexpected label category: '{first_invalid_value}' found in column '{column_name}'."
            f" Allowed categories are: {allowed_categories}"
        )
