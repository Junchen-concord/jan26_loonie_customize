import re

import pandas as pd
import spacy

from dataset.knowledge_base_proto import get_knowledge_base


def load_ner_model(model_path: str) -> spacy.Language:
    nlp = spacy.load(model_path, disable=["parser", "tagger"])
    return nlp


def load_holidays(holidays_path: str) -> pd.DataFrame:
    holidays = pd.read_csv(holidays_path)
    return holidays


def create_category_patterns():
    kb = get_knowledge_base()
    knowledge_base_data = pd.DataFrame(kb)
    assert set(knowledge_base_data.category.unique()) <= {
        "payroll",
        "loan",
        "transfer",
        "gig",
        "benefit",
        "Other",
    }, "The category in the knowledge base is not valid"
    category_patterns = {}
    for category in [
        "payroll",
        "loan",
        "transfer",
        "gig",
        "benefit",
        "Other",
    ]:
        entity_list = knowledge_base_data[knowledge_base_data.loc[:, "category"] == category]["entity"].tolist()
        if entity_list:
            category_patterns[category] = re.compile(r"|".join(entity_list), re.IGNORECASE)
    return category_patterns
