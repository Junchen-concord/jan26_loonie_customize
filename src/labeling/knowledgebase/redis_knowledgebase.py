import json
import os
import time

import pandas as pd
import redis
from api.config.config import logger
from config import config
from dotenv import load_dotenv
from utils.decorators import timer
from labeling.NER.ner import fill_missing_who

from labeling.knowledgebase.knowledge_base import Base_KnowledgeBase
from labeling.knowledgebase.KnowledgeBase_Features.knowledgebase_features import kb_calculate_frequency_amount
from labeling.preprocessing.preprocess import (
    clean_description_clustering,
    clean_description_knowledge_base,
    clean_description_n_gram,
    group_transactions,
)

load_dotenv(override=True)  # Load .env file, override existing env vars


def attach_frequency_and_amount_to_df(df: pd.DataFrame) -> pd.DataFrame:
    """
    Adds frequency/amount-related columns to each transaction cluster.

    For each cluster_label in the dataframe:
    - frequency: N/A, bi-weekly, weekly, monthly
    - frequency_pattern: "N/A", "consistent", "mostly consistent", "inconsistent", "unknown"
    - transaction_amount: Minor, Medium, Major
    - transaction_frequency: Similar pattern to frequency_pattern
    """
    required_columns = ["cluster_label", "date", "amount"]
    for col in required_columns:
        if col not in df.columns:
            raise ValueError(f"Missing required column: {col}")

    # Initialize new columns with "N/A"
    new_columns = ["frequency", "frequency_pattern", "transaction_amount", "transaction_frequency"]
    for col in new_columns:
        df[col] = "N/A"

    # Process each cluster separately
    grouped = df.groupby("cluster_label")
    for cluster_label, group in grouped:
        if group.empty:
            continue

        # kb_calculate_frequency_amount returns multiple frequency/amount metrics
        frequency, _, _, freq_pattern, cluster_amount_class, cluster_amount_pattern = kb_calculate_frequency_amount(
            group
        )

        # Assign computed values back to all rows in this cluster
        df.loc[df["cluster_label"] == cluster_label, "frequency"] = frequency
        df.loc[df["cluster_label"] == cluster_label, "frequency_pattern"] = freq_pattern
        df.loc[df["cluster_label"] == cluster_label, "transaction_amount"] = cluster_amount_class
        df.loc[df["cluster_label"] == cluster_label, "transaction_frequency"] = cluster_amount_pattern

    return df


def create_key(list_):
    """Serialize a Python list into a JSON string (used as Redis key)."""
    return json.dumps(list_)


def create_keys(values):
    """
    Generate multiple candidate keys for Redis lookup.
    Order of keys = priority for KB search (TDS-95 logic):
    1. All 7 values
    2. Debit/Credit + Who + What/Why + Frequency + Frequency Pattern
    3. Debit/Credit + Who + What/Why + Transaction Amount + Transaction Consistency
    4. Debit/Credit + Who + What/Why
    5. Debit/Credit + Who
    6. Debit/Credit + Frequency + Frequency Pattern + Transaction Amount + Transaction Consistency
    """
    d_or_c = values[0]
    who = values[1]
    what_why = values[2]
    frequency = values[3]
    frequency_pattern = values[4]
    transaction_amount = values[5]
    transaction_consistency = values[6]

    # Construct prioritized search keys
    first_key = create_key(values)
    second_key = create_key([d_or_c, who, what_why, frequency, frequency_pattern])
    third_key = create_key([d_or_c, who, what_why, transaction_amount, transaction_consistency])
    fourth_key = create_key([d_or_c, who, what_why])
    fifth_key = create_key([d_or_c, who])
    sixth_key = create_key([d_or_c, frequency, frequency_pattern, transaction_amount, transaction_consistency])

    return [first_key, second_key, third_key, fourth_key, fifth_key, sixth_key]


class RedisKnowledgeBase(Base_KnowledgeBase):
    def __init__(self):
        super().__init__(None)

        # Load from .env
        redis_host = os.getenv("REDIS_HOST")
        redis_port = int(os.getenv("REDIS_PORT", 6379))
        redis_password = os.getenv("REDIS_PASSWORD")
        use_ssl = os.getenv("REDIS_USE_SSL", "True").lower() == "true"
        self.enabled = os.getenv("REDIS_KB_ENABLED", "false").lower() == "true"

        if not self.enabled:
            self.redis_client = None
            return

        try:
            self.redis_client = redis.StrictRedis(
                host=redis_host, port=redis_port, db=0, password=redis_password, ssl=use_ssl, decode_responses=True
            )
            self.redis_client.ping()
            logger.info("Connected to Azure Redis successfully.")
        except Exception as e:
            logger.error(f"Failed to connect to Azure Redis: {e}")
            self.redis_client = None

    def getFromRedis(self, key: str):
        """Retrieve and parse a value from Redis by key."""
        if not self.redis_client:
            return None
        try:
            value = self.redis_client.get(key)
            if value:
                try:
                    return json.loads(value)  # Deserialize if JSON
                except json.JSONDecodeError:
                    return value  # Return raw if not JSON
            return None
        except Exception as e:
            logger.error(f"Failed to retrieve key '{key}' from Azure Redis: {e}")
            return None

    def setToRedis(self, key: str, value):
        """Save a key-value pair into Redis (JSON-encoded if needed)."""
        if not self.redis_client:
            return False
        try:
            if not isinstance(value, str):
                value = json.dumps(value)
            self.redis_client.set(key, value)
            return True
        except Exception as e:
            logger.error(f"Failed to set key '{key}' in Azure Redis: {e}")
            return False

    @timer
    def knowledge_base_prediction(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Run the Redis knowledge base prediction pipeline:
        1. Preprocess text (n-grams, clustering, KB cleaning)
        2. Group by customer → assign cluster labels if missing
        3. Attach frequency/amount info
        4. Deduplicate transactions (per description)
        5. Generate Redis keys and search
        6. Update predictions with KB hits, leave "Undecided" unchanged
        """
        if len(df) == 0:
            # Ensure empty df still has required columns
            df = df.reindex(df.columns.union([config.FROM_MODEL, "StackingPrediction"]), axis=1)
            return df

        # Generate processed versions of transaction descriptions
        if "processed_n_gram" not in df.columns:
            df["processed_n_gram"] = df[config.IA_ORIGINAL_DESCRIPTION].apply(clean_description_n_gram)
        if "processed_clustering" not in df.columns:
            df["processed_clustering"] = df["processed_n_gram"].apply(clean_description_clustering)
        if "processed_knowledge_base" not in df.columns:
            df["processed_knowledge_base"] = df[config.IA_ORIGINAL_DESCRIPTION].apply(clean_description_knowledge_base)

        # Assign cluster labels if missing
        if "cluster_label" not in df.columns:
            df = df.groupby(config.IA_CUSTOMER_ID).apply(
                lambda x: group_transactions(config.stopwords_nltk).group_transactions(
                    x, "processed_clustering", config.IA_MAX_DISTANCE
                )
            )

        # Attach frequency and transaction amount metadata
        df = attach_frequency_and_amount_to_df(df)

        # Deduplicate by transaction description
        deduped_df = df.groupby(config.IA_TXN_DESCRIPTION).first().reset_index()
        deduped_df.loc[:, "StackingPrediction"] = "Undecided"

        # === Redis-specific WHO fallback (ONLY used in knowledge base flow) ===
        df = fill_missing_who(df, text_col=config.IA_ORIGINAL_DESCRIPTION, stopwords_nltk=config.stopwords_nltk)
        deduped_df = fill_missing_who(deduped_df, text_col=config.IA_ORIGINAL_DESCRIPTION, stopwords_nltk=config.stopwords_nltk)

        # Columns used for KB key generation
        columns_to_grab = [
            "type",
            "WHO",
            "WHAT",
            "frequency",
            "frequency_pattern",
            "transaction_amount",
            "transaction_frequency",
        ]

        # Iterate over rows and attempt KB match
        # Step 1: Collect all keys for all rows
        row_key_map = {}  # row index → list_of_keys
        all_keys = []
        for idx, row_values in enumerate(deduped_df[columns_to_grab].values):
            row_values = row_values.tolist()
            list_of_keys = create_keys(row_values)
            row_key_map[idx] = list_of_keys
            all_keys.extend(list_of_keys)

        # Step 2: Deduplicate keys
        all_keys = list(set(all_keys))

        # Step 3: Bulk mget once
        start = time.perf_counter()
        all_results = self.redis_client.mget(all_keys)
        duration = time.perf_counter() - start
        logger.info(f"Bulk mget took {duration:.3f} seconds for {len(all_keys)} keys")

        # Step 4: Build dictionary {key: value}
        key_to_value = {k: v for k, v in zip(all_keys, all_results) if v is not None}

        # Step 5: Assign predictions back to rows
        for idx, list_of_keys in row_key_map.items():
            chosen_value = next((key_to_value.get(k) for k in list_of_keys if k in key_to_value), None)
            if chosen_value:
                deduped_df.at[idx, "StackingPrediction"] = chosen_value

        # Rename column to match pattern from other KB implementations
        deduped_df = deduped_df.rename(columns={"StackingPrediction": "knowledgeBasePrediction"})

        # Merge predictions back into full dataframe
        df = df.merge(
            deduped_df[[config.IA_TXN_DESCRIPTION, "knowledgeBasePrediction"]],
            how="left",
            on=config.IA_TXN_DESCRIPTION,
        )

        # Mark predictions by source
        df.loc[:, config.FROM_MODEL] = "LabelingModel"
        df.loc[df.knowledgeBasePrediction != "Undecided", config.FROM_MODEL] = "RedisKnowledgeBase"

        # Track metrics
        self.trans_through_knowledge_base = df.loc[df.loc[:, "knowledgeBasePrediction"] != "Undecided"].shape[0]
        self.transactions_observed = df.shape[0]

        # Copy KB predictions only for non-Undecided cases (like other KB implementations)
        df.loc[df.knowledgeBasePrediction != "Undecided", "StackingPrediction"] = df.knowledgeBasePrediction
        df = df.drop(columns=["knowledgeBasePrediction"])

        # Optional report
        if config.PRINT_REPORT:
            self.report(kb_type="REDIS")

        return df
