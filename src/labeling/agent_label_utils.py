import pandas as pd


def apply_agent_labeling(labeled_transactions: pd.DataFrame, transactions_to_change: pd.DataFrame) -> pd.DataFrame:
    liveAgentEdit = "LiveAgentEdit"
    if transactions_to_change.empty:
        return labeled_transactions
    required_cols = ["originalDescription", "agentCategory", "isEntireCluster"]
    if not all(col in transactions_to_change.columns for col in required_cols):
        return labeled_transactions
        
    # Create a copy of the dataframe to avoid chained assignment warnings
    result_df = labeled_transactions.copy()

    for _, row in transactions_to_change.iterrows():
        originalDescription = row["originalDescription"]
        agent_category = row["agentCategory"]
        is_entire_cluster = row["isEntireCluster"]

        # Change all strict originalDescriptions
        mask = result_df["originalDescription"] == originalDescription
        filtered_indices = result_df[mask].index

        if not filtered_indices.empty:
            result_df.loc[filtered_indices, "category"] = agent_category
            result_df.loc[filtered_indices, "StackingPrediction"] = agent_category
            result_df.loc[filtered_indices, "fromModel"] = liveAgentEdit

            # Change all cluster label
            if str(is_entire_cluster).lower() == "true":
                top_index = filtered_indices[0]
                if "cluster_label" in result_df.columns:
                    cluster_label = result_df.loc[top_index, "cluster_label"]
                    cluster_mask = result_df["cluster_label"] == cluster_label
                    cluster_filtered_indices = result_df[cluster_mask].index
                    if not cluster_filtered_indices.empty:
                        result_df.loc[cluster_filtered_indices, "category"] = agent_category
                        result_df.loc[cluster_filtered_indices, "StackingPrediction"] = agent_category
                        result_df.loc[cluster_filtered_indices, "fromModel"] = liveAgentEdit

    return result_df


def extract_agent_categories(transactions: pd.DataFrame):
    """
    Iterates over a list of transaction dictionaries and extracts
    'originalDescription' and 'agentCategory' for transactions where
    'agentCategory' is not null or empty.
    """
    if transactions.empty:
        return pd.DataFrame()

    if not ("agentCategory" in transactions.columns and "description" in transactions.columns):
        return pd.DataFrame()

    filtered_transactions = transactions[transactions["agentCategory"].astype(str).str.strip() != ""]
    filtered_transactions = filtered_transactions[
        filtered_transactions["agentCategory"].apply(lambda x: isinstance(x, str))
    ]
    filtered_transactions = filtered_transactions.drop_duplicates(subset=["description"], keep="first")

    extracted_df = pd.DataFrame(
        {
            "originalDescription": filtered_transactions["description"],
            "agentCategory": filtered_transactions["agentCategory"],
            "isEntireCluster": "true",
        }
    )

    return extracted_df
