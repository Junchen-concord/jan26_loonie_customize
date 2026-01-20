import pandas as pd

from labeling.clustering import NER_Clustering


def test_ner_clustering():
    # Create a sample DataFrame for testing
    df_customer = pd.DataFrame(
        {
            "description": [
                "John bought groceries",
                "Mary bought groceries",
                "John paid rent",
                "Mary paid rent",
            ],
            "accountGuid": ["1", "1", "1", "1"],
            "who": ["John", "Mary", "John", "Mary"],
            "how": ["None", "None", "None", "None"],
            "why": ["groceries", "groceries", "rent", "rent"],
            "who_cat": ["ORG", "ORG", "ORG", "ORG"],
        }
    )

    who_col = "who"

    # Create an instance of NER_Clustering
    clustering = NER_Clustering(max_distance=0.3)

    # Call the group_transactions method
    result = clustering.group_transactions(df_customer, who_col, "who_cat")

    # Assert the expected cluster labels
    expected_labels = ["who_1", "who_2", "who_1", "who_2"]
    assert result["cluster_label"].tolist() == expected_labels
