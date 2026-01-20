from abc import abstractmethod

from config import config


# abstract class for a clustering function, that takes the input of a list of strings, and cluster similar strings into the same group
class Base_Clustering:
    def __init__(self, max_distance: float, ignore_words=config.STOPWORDS):
        """
        Args:
        max_distance: float, the maximum distance for two strings to be considered similar
        ignore_words: set, the set of words to be ignored when clustering
        """
        self.max_distance = max_distance
        self.ignore_words = ignore_words

    @abstractmethod
    def group_transactions(self, df):
        pass
