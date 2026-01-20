import pandas as pd
from config import config
from utils.decorators import timer

from labeling.clustering import HC_Clustering
from labeling.clustering.base_clustering import Base_Clustering
from labeling.preprocessing.preprocess import clean_description_clustering


class NER_Clustering(Base_Clustering):
    def __init__(self, max_distance, ignore_words=config.STOPWORDS):
        super().__init__(max_distance, ignore_words)
        self.hc_clustering = HC_Clustering(max_distance)  # Reuse this instance if possible

    @timer
    def group_transactions(
        self,
        df_customer: pd.DataFrame,
        who_col: str,
        who_cat_col: str,
        used_who_cat=["ORG", "Unknown"],
    ) -> pd.DataFrame:
        df_customer["who_processed"] = df_customer[who_col].apply(clean_description_clustering)

        df_with_who = df_customer[(df_customer[who_col] != "None") & (df_customer[who_cat_col].isin(used_who_cat))]

        # add who person to clustering, the algo will use WHO_Person as key to cluster if no WHO_Org is found
        # COMMENTED OUT: Model performance on person entities is not reliable enough
        # df_with_who_person = df_customer[
        #     (df_customer[who_col] != "None") & (~df_customer[who_cat_col].isin(used_who_cat))
        # ]

        # Combine who_person transactions with df_without_who since model performance is not good
        df_without_who = df_customer[(df_customer[who_col] == "None") | (~df_customer[who_cat_col].isin(used_who_cat))]

        if len(df_with_who) >= 1:
            df_with_who = (
                df_with_who.groupby(config.IA_CUSTOMER_ID)
                .apply(self.hc_clustering.group_transactions, who_col)
                .reset_index(drop=True)
            )
            df_with_who["cluster_label"] = "who_" + df_with_who["cluster_label"].astype(str)

            # Ensure transactions with the same who_col value are in the same cluster
            if who_col in df_with_who.columns:
                df_with_who = (
                    df_with_who.groupby(who_col, group_keys=False)
                    .apply(self._select_cluster_label)
                    .reset_index(drop=True)
                )

        # COMMENTED OUT: Model performance on person entities is not reliable enough
        # if len(df_with_who_person) >= 1:
        #     df_with_who_person = (
        #         df_with_who_person.groupby(config.IA_CUSTOMER_ID)
        #         .apply(
        #             self.hc_clustering.group_transactions,
        #             who_col,
        #         )
        #         .reset_index(drop=True)
        #     )
        #     df_with_who_person["cluster_label"] = "who_person_" + df_with_who_person["cluster_label"].astype(str)

        if len(df_without_who) >= 1:
            df_without_who = (
                df_without_who.groupby(config.IA_CUSTOMER_ID)
                .apply(
                    self.hc_clustering.group_transactions,
                    "processed_clustering",
                )
                .reset_index(drop=True)
            )

            df_without_who["cluster_label"] = "processed_desc_" + df_without_who["cluster_label"].astype(str)

        # Handle empty dataframe concatenation to avoid warnings
        dfs_to_concat = []
        if len(df_with_who) >= 1:
            dfs_to_concat.append(df_with_who)
        # COMMENTED OUT: Model performance on person entities is not reliable enough
        # if len(df_with_who_person) >= 1:
        #     dfs_to_concat.append(df_with_who_person)
        if len(df_without_who) >= 1:
            dfs_to_concat.append(df_without_who)

        # Only concatenate if we have dataframes to concatenate
        if dfs_to_concat:
            df = pd.concat(dfs_to_concat).reset_index(drop=True)
        else:
            # Create an empty dataframe with the same structure as the input
            df = df_customer.copy().iloc[0:0]
            # Add cluster_label column if it doesn't exist
            if "cluster_label" not in df.columns:
                df["cluster_label"] = None
            return df

        # Hardcode cluster labels for transactions with identical processed_n_gram
        # Priority: who_ > who_person_ > processed_desc_

        # Apply the hardcoding logic
        if config.PROCESSED_N_GRAM in df.columns:
            df = (
                df.groupby(config.PROCESSED_N_GRAM, group_keys=False)
                .apply(self._select_cluster_label)
                .reset_index(drop=True)
            )

        return df

    def _select_cluster_label(self, group):
        """Select the cluster label with highest priority for a group."""
        cluster_labels = group["cluster_label"].unique()
        if len(cluster_labels) == 1:
            return group

        # Priority mapping: lower number = higher priority
        # Updated priority: who_ > processed_desc_ (who_person_ commented out due to poor model performance)
        def get_priority(label):
            if label.startswith("who_"):
                return 0
            elif label.startswith("processed_desc_"):
                return 1
            # COMMENTED OUT: Model performance on person entities is not reliable enough
            # elif label.startswith("who_person_"):
            #     return 1
            else:
                return 2  # Unknown type

        # Select the label with highest priority (lowest number)
        selected_label = min(cluster_labels, key=get_priority)
        group["cluster_label"] = selected_label
        return group
