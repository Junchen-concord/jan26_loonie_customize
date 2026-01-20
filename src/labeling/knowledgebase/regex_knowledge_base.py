import pandas as pd

from config import config
from dataset.knowledge_base_proto import get_knowledge_base
from labeling.knowledgebase.knowledge_base import Base_KnowledgeBase
from labeling.preprocessing.preprocess import (
    clean_description_clustering,
    clean_description_knowledge_base,
    clean_description_n_gram,
    group_transactions,
)
from utils.decorators import timer


# V15.5 regex based knowledge base
class Regex_Based_KnowledgeBase(Base_KnowledgeBase):
    # very simple version of prototype knowledge base given by limited data, the knowledge base will only give decisions
    # based on the entity name or obvious HOW like zelle, cash app etc.

    # The matching is based on substring search which means the time complexity is O(mn) where m is the number of the
    # transaction and n is the number of the entity in the knowledge base. Need to find a scaleable solution
    # when knowledge base grows. Typically, if we can use NER and use exact matching on WHO, WHAT and WHY,
    # knowledge base can become a hashmap and the complexity will become O(m).
    def __init__(self, data_path):
        super().__init__(data_path)
        kb = get_knowledge_base()
        self.knowledge_base_data = pd.DataFrame(kb)
        assert set(self.knowledge_base_data.category.unique()) <= {
            "payroll",
            "loan",
            "transfer",
            "gig",
            "benefit",
            "Other",
        }, "The category in the knowledge base is not valid"

    @timer
    def knowledge_base_prediction(self, df: pd.DataFrame) -> pd.DataFrame:
        if len(df) == 0:
            df = df.reindex(
                df.columns.union([config.FROM_MODEL, "StackingPrediction"]),
                axis=1,
            )
            return df
        # despite that knowledge base can works directly on transaction level, we still need to assign cluster label for source level analysis
        if "processed_n_gram" not in df.columns:
            df["processed_n_gram"] = df[config.IA_ORIGINAL_DESCRIPTION].apply(clean_description_n_gram)
        if "processed_clustering" not in df.columns:
            df["processed_clustering"] = df["processed_n_gram"].apply(clean_description_clustering)
        if "processed_knowledge_base" not in df.columns:
            df["processed_knowledge_base"] = df[config.IA_ORIGINAL_DESCRIPTION].apply(clean_description_knowledge_base)

        # Only run clustering if no clustering has been ran
        if "cluster_label" not in df.columns:
            df = df.groupby(config.IA_CUSTOMER_ID).apply(
                lambda x: group_transactions(x, "processed_clustering", config.IA_MAX_DISTANCE)
            )

        deduped_df = df.groupby(config.IA_TXN_DESCRIPTION).first().reset_index()
        deduped_df.loc[:, "StackingPrediction"] = "Undecided"

        for category in [
            "payroll",
            "loan",
            "transfer",
            "gig",
            "benefit",
            "Other",
        ]:
            entity_list = self.knowledge_base_data[
                self.knowledge_base_data.loc[:, config.CATEGORY_COLUMN_NAME] == category
            ]["entity"].to_list()
            if len(entity_list) == 0:
                continue
            # Escape each entity to ensure no special regex characters are misinterpreted - UNCOMMENTING THIS LINE IS AFFECTING RISK SCORE SIGNIFICANTLY??
            # entity_reg_expr = r"|".join(re.escape(entity) for entity in entity_list)
            # entity_reg_expr = r"|".join(entity_list)
            # deduped_df.loc[
            #     deduped_df.loc[:, "processed_knowledge_base"].str.contains(entity_reg_expr, case=False, regex=),
            #     "StackingPrediction",
            # ] = category
            escaped = [e.replace("(", r"\(").replace(")", r"\)") for e in entity_list]
            entity_reg_expr = "|".join(escaped)

            mask = deduped_df["processed_knowledge_base"].str.contains(entity_reg_expr, case=False, na=False)

            deduped_df.loc[mask, "StackingPrediction"] = category
        deduped_df = deduped_df.rename(columns={"StackingPrediction": "knowledgeBasePrediction"})

        df = df.merge(
            deduped_df[[config.IA_TXN_DESCRIPTION, "knowledgeBasePrediction"]],
            how="left",
            on=config.IA_TXN_DESCRIPTION,
        )

        # Track all trans that has been labelled by knowledgebase
        df.loc[:, config.FROM_MODEL] = "LabelingModel"
        df.loc[df.knowledgeBasePrediction != "Undecided", config.FROM_MODEL] = "RegexSearchKnowledge"
        self.trans_through_knowledge_base = df.loc[df.loc[:, "knowledgeBasePrediction"] != "Undecided"].shape[0]
        self.transactions_observed = df.shape[0]
        # change the remainder category back to other so that 'undecided' are not really showing up in the category.
        # to align with the refresh labeling logic, it will copy from what labels are gathered from kb instead of overwriting it.
        df.loc[df.knowledgeBasePrediction != "Undecided", "StackingPrediction"] = df.knowledgeBasePrediction
        df = df.drop(columns=["knowledgeBasePrediction"])
        if config.PRINT_REPORT:
            self.report(kb_type="REGEX")
        return df

    def refresh(self, new_data_path: str) -> None:
        new_data = pd.read_csv(new_data_path)

        # Handle empty dataframe concatenation to avoid warnings
        if not self.knowledge_base_data.empty and not new_data.empty:
            self.knowledge_base_data = pd.concat([self.knowledge_base_data, new_data], axis=0)
        elif not new_data.empty:
            # If current knowledge base is empty, just use the new data
            self.knowledge_base_data = new_data.copy()
        # If new_data is empty, keep existing knowledge_base_data unchanged

        # deduplication (only if we have data)
        if not self.knowledge_base_data.empty:
            self.knowledge_base_data = self.knowledge_base_data.drop_duplicates(subset=["entity", "category"])
            self.knowledge_base_data.to_csv(self.data_path, index=False)
