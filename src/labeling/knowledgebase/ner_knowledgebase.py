import pickle

import pandas as pd
from config import config
from utils.decorators import timer

from labeling.clustering import NER_Clustering
from labeling.knowledgebase.knowledge_base import Base_KnowledgeBase
from labeling.preprocessing.preprocess import (
    clean_description_clustering,
    clean_description_knowledge_base,
    clean_description_n_gram,
)


# V16 NER (WHO, WHY, HOW) based knowledge base
class NER_Based_KnowledgeBase(Base_KnowledgeBase):
    def __init__(self, data_path, source_map_path):
        super().__init__(data_path)
        # self.source_map = pd.read_csv(source_map_path)
        # self.make_source_mapping()
        # self.make_knowledge_base_mapping()

        with open(data_path, "rb") as f:
            knowledge_base_data = pickle.load(f)
        with open(source_map_path, "rb") as f:
            source_map = pickle.load(f)
        self.source_map = source_map
        self.source_map = dict()  # need more POC to actually see source map works
        self.knowledge_base_data = knowledge_base_data

    @timer
    def knowledge_base_prediction(self, df: pd.DataFrame) -> pd.DataFrame:
        # The input from upstream (NER) should contain additional information for transaction (WHO, WHY, HOW), prediction will based on these info

        # The new clustering will only be based on WHO, HOW and WHY
        # This step is for adding cluster label for the transactions that go through knowledge base and do not go to guessing model (so they will not have a cluster_label otherwise)

        # Take only the first WHO find in transaction
        # TODO: Maybe change the preprocessing once we know split the who by org and person

        # df.loc[:, who_col_name] = df.loc[:, who_col_name].apply(lambda x: self.process_NER_LABEL(x))
        # df.loc[:, why_col_name] = df.loc[:, why_col_name].apply(lambda x: self.process_NER_LABEL(x))
        # df.loc[:, how_col_name] = df.loc[:, how_col_name].apply(lambda x: self.process_NER_LABEL(x))

        # # map known similar who, why, how to the same source, for example, interest and dividend should have the same meaning
        # df.loc[:, "who_source"] = df.loc[:, who_col_name].apply(lambda x: self.source_map_entities(x, 'WHO'))
        # df.loc[:, "why_source"] = df.loc[:, why_col_name].apply(lambda x: self.source_map_entities(x, 'WHY'))
        # df.loc[:, "how_source"] = df.loc[:, how_col_name].apply(lambda x: self.source_map_entities(x, 'HOW'))

        if "processed_n_gram" not in df.columns:
            df["processed_n_gram"] = df[config.IA_ORIGINAL_DESCRIPTION].apply(clean_description_n_gram)
        if "processed_clustering" not in df.columns:
            df["processed_clustering"] = df["processed_n_gram"].apply(clean_description_clustering)
        if "processed_knowledge_base" not in df.columns:
            df["processed_knowledge_base"] = df[config.IA_ORIGINAL_DESCRIPTION].apply(clean_description_knowledge_base)

        #  Right now the NER seems to be missing a lot of WHOs, which harms the clustering a lot,
        # so just be conservative and use the old clustering for now
        # if 'cluster_label' not in df.columns:
        #     df = df.groupby(config.IA_CUSTOMER_ID).apply(lambda x: PreProcess(
        #     ).group_transactions(x, "processed_clustering", config.IA_MAX_DISTANCE))

        if "cluster_label" not in df.columns:
            df = df.groupby(config.IA_CUSTOMER_ID).apply(
                lambda x: NER_Clustering(config.IA_MAX_DISTANCE).group_transactions(
                    x,
                    "who_source",
                    config.WHO_CAT_COL,
                )
            )

        deduped_df = df.groupby(config.IA_TXN_DESCRIPTION).first().reset_index()
        deduped_df.loc[:, "StackingPrediction"] = deduped_df.apply(
            lambda x: self.match_who_why_how(x.who_source, x.why_source, x.how_source),
            axis=1,
        )
        deduped_df = deduped_df.rename(columns={"StackingPrediction": "knowledgeBasePrediction"})

        df = df.merge(
            deduped_df[[config.IA_TXN_DESCRIPTION, "knowledgeBasePrediction"]],
            how="left",
            on=config.IA_TXN_DESCRIPTION,
        )

        # Track all trans that has been labelled by knowledgebase
        df.loc[:, config.FROM_MODEL] = "LabelingModel"
        df.loc[df.knowledgeBasePrediction != "Undecided", config.FROM_MODEL] = "NERKnowledge"
        self.trans_through_knowledge_base = df.loc[df.loc[:, "knowledgeBasePrediction"] != "Undecided"].shape[0]
        self.transactions_observed = df.shape[0]
        # to align with the refresh labeling logic, it will copy from what labels are gathered from kb instead of overwriting it.
        df.loc[df.knowledgeBasePrediction != "Undecided", "StackingPrediction"] = df.knowledgeBasePrediction
        df = df.drop(columns=["knowledgeBasePrediction"])
        if config.PRINT_REPORT:
            self.report(kb_type="NER")

        return df

    @timer
    def match_who_why_how(self, who_source: str, why_source: str, how_source: str) -> str:
        # There are in total 8 possible combinations of who, why, how, the prediction will be prioritized based on each combination
        # 1. WHO,HOW,WHY all present
        # 2. WHO,WHY present, HOW absent
        # 3. HOW,WHY present, WHO absent
        # 4. WHY present, WHO, HOW absent
        # 5. WHO,HOW present, WHY absent
        # 6. WHO present, WHY, HOW absent
        # 7. HOW present, WHO, WHY absent
        # 8. All absent
        out = self.knowledge_base_data.get(
            frozenset([("WHO", who_source), ("WHY", why_source), ("HOW", how_source)]),
            None,
        )
        if out is not None:
            return out

        out = self.knowledge_base_data.get(frozenset([("WHO", who_source), ("WHY", why_source)]), None)
        if out is not None:
            return out

        out = self.knowledge_base_data.get(frozenset([("HOW", how_source), ("WHY", why_source)]), None)
        if out is not None:
            return out

        out = self.knowledge_base_data.get(frozenset([("WHY", why_source)]), None)
        if out is not None:
            return out

        out = self.knowledge_base_data.get(frozenset([("WHO", who_source), ("HOW", how_source)]), None)
        if out is not None:
            return out

        out = self.knowledge_base_data.get(frozenset([("WHO", who_source)]), None)
        if out is not None:
            return out

        out = self.knowledge_base_data.get(frozenset([("HOW", how_source)]), None)
        if out is not None:
            return out

        return "Undecided"

    @timer
    def source_map_entities(self, name: str, category: str):
        assert category in {
            "WHO",
            "WHY",
            "HOW",
        }, "category must be either [who], [why] or [how]"
        if category == "WHO":
            key = ("WHO", name)
        elif category == "WHY":
            key = ("WHY", name)
        elif category == "HOW":
            key = ("HOW", name)
        return self.source_map.get(key, name)

    @timer
    def make_source_mapping(self):
        # create a raw who to a commonly understood who stored in knowledgebase
        # return a hashmap for optimized runtime
        source_map_dict = dict()
        for i in range(len(self.source_map)):
            ner_label, raw, source = self.source_map.loc[:, ["NER_Label", "Raw", "Source"]].iloc[i]
            source_map_dict[(ner_label, raw)] = source
        self.source_map = source_map_dict

    @timer
    def process_NER_LABEL(self, x: str) -> str:
        assert isinstance(x, str) or x is None, "The input should be a string or None, not {}".format(type(x))
        if x is None:
            return "None"
        else:
            return x
