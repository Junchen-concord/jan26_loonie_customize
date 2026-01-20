import os

import numpy as np
import pandas as pd

from config import config
from labeling.knowledgebase import NER_Based_KnowledgeBase, Regex_Based_KnowledgeBase

sample_data_path = os.path.realpath(
    os.path.join(config.ROOT_DIR, "..", "tests", "data", "sample_input_knowledgebase.csv")
)
regex_knowledge_base = Regex_Based_KnowledgeBase(config.KNOWLEDGEBASE_DATA_PATH)
NER_knowledge_base = NER_Based_KnowledgeBase(config.NER_KNOWLEDGEBASE_DATA_PATH, config.NER_SOURCE_MAP_PATH)


def test_Regex_Based_KnowledgeBase():
    # Test the Regex_Based_KnowledgeBase class
    assert set(regex_knowledge_base.knowledge_base_data.category.unique()) <= {
        "payroll",
        "loan",
        "transfer",
        "gig",
        "benefit",
        "Other",
    }


def test_Regex_Based_KnowledgeBase_knowledge_base_prediction():
    # Test the knowledge_base_prediction method of the Regex_Based_KnowledgeBase class
    df = pd.read_csv(sample_data_path)
    output = regex_knowledge_base.knowledge_base_prediction(df)
    # Add assertions for the expected output
    assert "StackingPrediction" in output.columns
    assert "fromModel" in output.columns
    assert set(output.fromModel.unique()) <= {"LabelingModel", "RegexSearchKnowledge"}
    # make sure clustering output correctly
    assert "cluster_label" in output.columns
    assert np.sum(output.cluster_label.str.contains("-1")) == 0


def test_NER_Based_KnowledgeBase():
    # Test the NER_Based_KnowledgeBase class
    knowledge_base = NER_knowledge_base
    assert isinstance(knowledge_base.knowledge_base_data, dict)
    assert isinstance(knowledge_base.source_map, dict)


def test_NER_Based_KnowledgeBase_knowledge_base_prediction():
    # Test the knowledge_base_prediction method of the NER_Based_KnowledgeBase class
    knowledge_base = NER_knowledge_base
    df = pd.read_csv(sample_data_path)  # Replace with a mock DataFrame for testing
    df = df.rename(columns={"who_CAT": "WHO_cat"})
    df.loc[df.WHO.isnull(), "WHO"] = None
    df.loc[df.HOW.isnull(), "HOW"] = None
    df.loc[df.WHY.isnull(), "WHY"] = None
    df.loc[df.WHO.isnull(), "who_source"] = "None"
    df.loc[df.HOW.isnull(), "how_source"] = "None"
    df.loc[df.WHY.isnull(), "why_source"] = "None"
    output = knowledge_base.knowledge_base_prediction(df)
    # Add assertions for the expected output
    assert "who_source" in output.columns
    assert "why_source" in output.columns
    assert "how_source" in output.columns
    assert "StackingPrediction" in output.columns
    assert "fromModel" in output.columns
    assert set(output.fromModel.unique()) <= {"LabelingModel", "NERKnowledge"}


def test_NER_Based_KnowledgeBase_match_who_why_how():
    # Test the match_who_why_how method of the NER_Based_KnowledgeBase class
    knowledge_base = NER_knowledge_base
    who_source = "7 eleven"
    why_source = "None"
    how_source = "None"
    output = knowledge_base.match_who_why_how(who_source, why_source, how_source)
    # Add assertions for the expected output
    assert output == "Undecided"


def test_NER_Based_KnowledgeBase_source_map_entities():
    # Test the source_map_entities method of the NER_Based_KnowledgeBase class
    knowledge_base = NER_knowledge_base
    name = "None"
    category = "WHO"
    output = knowledge_base.source_map_entities(name, category)
    assert output == "None"
    assert output == "None"
