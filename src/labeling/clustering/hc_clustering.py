import pandas as pd
from scipy.cluster.hierarchy import fcluster, linkage
from scipy.spatial.distance import squareform
from sklearn.feature_extraction.text import CountVectorizer, TfidfVectorizer
from sklearn.metrics.pairwise import cosine_distances

from config import config
from labeling.clustering.base_clustering import Base_Clustering
from utils.decorators import timer


class HC_Clustering(Base_Clustering):
    def __init__(
        self,
        max_distance,
        ignore_words=config.STOPWORDS,
        linkage_method="average",
        metric="cosine",
        ngram_range=(1, 1),
        tf_idf=False,
    ):
        """
        Args:
        linkage_method: str, the linkage method to be used in the hierarchical clustering, must be one of ["ward", "complete", "average", "single"]
        metric: str, the metric to be used in the hierarchical clustering, for example, ["euclidean", "l1", "l2", "manhattan", "cosine"]
        ngram_range: tuple, the range of ngram to be used in the count vectorizer
        tf_idf: bool, whether to use tf-idf to transform the count matrix, if False, will use count vectorizer.
        """
        super().__init__(max_distance, ignore_words)
        self.linkage_method = linkage_method
        self.metric = metric
        self.ngram_range = ngram_range
        self.tf_idf = tf_idf
        self.STOPWORDS = ignore_words

    @timer
    def group_transactions(self, df_customer: pd.DataFrame, preprocess_col: str) -> pd.DataFrame:
        if len(df_customer) > 1:
            ## TODO: This try except should be redundant for now, can try to test remove it sometime.
            try:
                if not self.tf_idf:
                    vectorizer = CountVectorizer(
                        stop_words=list(self.STOPWORDS),
                        ngram_range=self.ngram_range,
                    )
                else:
                    vectorizer = TfidfVectorizer(
                        stop_words=list(self.STOPWORDS),
                        ngram_range=self.ngram_range,
                    )
                X = vectorizer.fit_transform(df_customer[preprocess_col])

                # Perform hierarchical clustering
                if self.metric == "cosine":
                    # Compute the pairwise cosine distances for a sparse matrix
                    X_dist = cosine_distances(X)  # X is the sparse matrix

                    # Convert to condensed distance matrix for linkage
                    condensed_dist_matrix = squareform(X_dist, checks=False)

                    # Perform hierarchical clustering
                    Z = linkage(condensed_dist_matrix, method=self.linkage_method)
                else:
                    Z = linkage(X, method=self.linkage_method, metric=self.metric)

                df_customer["cluster_label"] = fcluster(Z, self.max_distance, criterion="distance")
            except Exception:
                df_customer["cluster_label"] = -1
        else:
            df_customer["cluster_label"] = 1

        df_customer["cluster_label"] = df_customer["cluster_label"].astype(str)
        return df_customer
