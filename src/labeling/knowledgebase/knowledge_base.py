from abc import abstractmethod

import pandas as pd

from app_utils import logger


class Base_KnowledgeBase:
    def __init__(self, data_path):
        self.data_path = data_path
        # self.knowledge_base_data = pd.read_csv(data_path)
        self.trans_through_knowledge_base = 0
        self.transactions_observed = 0

    # The knowledge base should be able to take in a dataframe and return a dataframe with the prediction
    @abstractmethod
    def knowledge_base_prediction(self, df: pd.DataFrame):
        pass

    # The knowledge base should be able to automatically add new knowledge when more data comes in.
    @abstractmethod
    def refresh(self, new_data_path: str):
        pass

    def report(self, kb_type: str) -> None:
        # tracking function on how many transactions goes through knowledge base instead of V15 model.
        # Avoid divideByZero Error in case where transactions_observed = 0
        percent_of_knowledgeBase = 0
        if self.transactions_observed != 0:
            percent_of_knowledgeBase = self.trans_through_knowledge_base / self.transactions_observed * 100

        logger.info(
            "{} transactions went through {} knowledge base , which is {:.2f}% of all transactions".format(
                self.trans_through_knowledge_base,
                kb_type,
                percent_of_knowledgeBase,
            )
        )

    def disable(self) -> None:
        if isinstance(self.knowledge_base_data, pd.DataFrame):
            self.knowledge_base_data = self.knowledge_base_data.head(0)
        if isinstance(self.knowledge_base_data, dict):
            self.knowledge_base_data = dict()
