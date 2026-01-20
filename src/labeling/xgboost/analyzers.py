import warnings

import numpy as np
import pandas as pd
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder
from skopt import BayesSearchCV
from xgboost import XGBClassifier

from config import config
from labeling.clustering import NER_Clustering
from labeling.preprocessing.preprocess import clean_description_clustering, clean_description_n_gram
from labeling.xgboost.analyzer_features import IAFeatures
from utils.decorators import timer

warnings.filterwarnings("ignore", message="Saving into deprecated binary model format")


class IA_Preprocessing(TransformerMixin, BaseEstimator):
    """Clean description and add index column, for join the result back. Cluster credit transactions."""

    def __init__(self, config, target="is_payroll", training=False):
        self.target = target
        self.config = config
        self.training = training

    def fit(self, df, y=None, **fit_params):
        return self

    @timer
    def transform(self, df: pd.DataFrame, **transform_params) -> pd.DataFrame:
        # Picking only credit transactions for payroll
        df.loc[:, "idx"] = df.index
        df["processed_n_gram"] = df[config.IA_ORIGINAL_DESCRIPTION].apply(clean_description_n_gram)
        df["processed_clustering"] = df["processed_n_gram"].apply(clean_description_clustering)
        df.loc[:, self.config.IA_START_DATE] = (
            df.loc[:, self.config.IA_DATE].groupby(df[self.config.IA_CUSTOMER_ID]).transform("min")
        )
        df.loc[:, self.config.IA_END_DATE] = (
            df.loc[:, self.config.IA_DATE].groupby(df[self.config.IA_CUSTOMER_ID]).transform("max")
        )

        # Only run clustering if no clustering has been ran
        if "cluster_label" not in df.columns:
            df = NER_Clustering(config.IA_MAX_DISTANCE).group_transactions(
                df,
                "processed_clustering",
                config.WHO_COL,
                config.HOW_COL,
                config.WHAT_COL,
                config.WHO_CAT_COL,
            )

        return df


class IA_ClusterLevelFeature(TransformerMixin, BaseEstimator):
    """Get cluster level features, will sub-sample the data."""

    def __init__(self, config, target="handlabel_cat", training=False):
        self.target = target
        self.config = config
        self.training = training

    @timer
    def fit(self, df, y=None, **fit_params):
        return self

    @timer
    def transform(self, df: pd.DataFrame, **transform_params) -> pd.DataFrame:
        # Picking only credit transactions for payroll
        # df = df.loc[df.loc[:, self.config.IA_TYPE] == 'CREDIT', :]
        tmp = df.groupby(self.config.IA_CUSTOMER_ID).apply(
            lambda x: IAFeatures.build_cluster_level_features(
                x,
                self.config.IA_START_DATE,
                self.config.IA_END_DATE,
                self.config.IA_DATE,
                self.target,
            )
        )
        tmp = tmp.reindex(sorted(tmp.columns), axis=1)
        tmp = tmp.reset_index()

        # Encode categorical features
        tmp = pd.concat(
            [
                tmp,
                pd.DataFrame(
                    OneHotEncoder(
                        categories=[
                            [
                                "1",
                                "2-5",
                                "6-8",
                                "9-12",
                                "13-17",
                                "18-24",
                                "24-35",
                                "36+",
                            ]
                        ],
                        handle_unknown="ignore",
                    )
                    .fit_transform(np.array(tmp.credit_time_interval_1).reshape(-1, 1))
                    .toarray(),
                    columns=[
                        "credit_t1_1",
                        "credit_t1_2-5",
                        "credit_t1_6-8",
                        "credit_t1_9-12",
                        "credit_t1_13-17",
                        "credit_t1_18-24",
                        "credit_t1_24-35",
                        "credit_t1_36+",
                    ],
                ),
            ],
            axis=1,
        )
        tmp = pd.concat(
            [
                tmp,
                pd.DataFrame(
                    OneHotEncoder(
                        categories=[
                            [
                                "1",
                                "2-5",
                                "6-8",
                                "9-12",
                                "13-17",
                                "18-24",
                                "24-35",
                                "36+",
                            ]
                        ],
                        handle_unknown="ignore",
                    )
                    .fit_transform(np.array(tmp.credit_time_interval_2).reshape(-1, 1))
                    .toarray(),
                    columns=[
                        "credit_t2_1",
                        "credit_t2_2-5",
                        "credit_t2_6-8",
                        "credit_t2_9-12",
                        "credit_t2_13-17",
                        "credit_t2_18-24",
                        "credit_t2_24-35",
                        "credit_t2_36+",
                    ],
                ),
            ],
            axis=1,
        )
        tmp = pd.concat(
            [
                tmp,
                pd.DataFrame(
                    OneHotEncoder(
                        categories=[
                            [
                                "1",
                                "2-5",
                                "6-8",
                                "9-12",
                                "13-17",
                                "18-24",
                                "24-35",
                                "36+",
                            ]
                        ],
                        handle_unknown="ignore",
                    )
                    .fit_transform(np.array(tmp.debit_time_interval_1).reshape(-1, 1))
                    .toarray(),
                    columns=[
                        "debit_t1_1",
                        "debit_t1_2-5",
                        "debit_t1_6-8",
                        "debit_t1_9-12",
                        "debit_t1_13-17",
                        "debit_t1_18-24",
                        "debit_t1_24-35",
                        "debit_t1_36+",
                    ],
                ),
            ],
            axis=1,
        )
        tmp = pd.concat(
            [
                tmp,
                pd.DataFrame(
                    OneHotEncoder(
                        categories=[
                            [
                                "1",
                                "2-5",
                                "6-8",
                                "9-12",
                                "13-17",
                                "18-24",
                                "24-35",
                                "36+",
                            ]
                        ],
                        handle_unknown="ignore",
                    )
                    .fit_transform(np.array(tmp.debit_time_interval_2).reshape(-1, 1))
                    .toarray(),
                    columns=[
                        "debit_t2_1",
                        "debit_t2_2-5",
                        "debit_t2_6-8",
                        "debit_t2_9-12",
                        "debit_t2_13-17",
                        "debit_t2_18-24",
                        "debit_t2_24-35",
                        "debit_t2_36+",
                    ],
                ),
            ],
            axis=1,
        )

        tmp = tmp.drop(
            columns=[
                "credit_time_interval_1",
                "credit_time_interval_2",
                "debit_time_interval_1",
                "debit_time_interval_2",
            ]
        )

        return tmp


class Wrapped_CVR(TransformerMixin, BaseEstimator):
    """A wrapper of countvectorizer for parameter tuning."""

    def __init__(
        self,
        ngram_range,
        min_df,
        max_features,
        vocabulary,
        description,
        target="handlabel_cat",
        customer_id=config.IA_ACCOUNT_ID,
    ):
        self.__dict__ = CountVectorizer().__dict__
        self.ngram_range = ngram_range
        self.min_df = min_df
        self.max_features = max_features
        self.vocabulary = vocabulary

        # Skopt's bayes seems cannot take tuples as categorical features, so something is required to wrap/unwrapp the ngram_range variable
        actual_n_gram_range = (
            int(self.ngram_range.split(",")[0][1]),
            int(self.ngram_range.split(",")[1][0]),
        )
        self.cvr = CountVectorizer(
            lowercase=False,
            ngram_range=actual_n_gram_range,
            min_df=self.min_df,
            max_features=self.max_features,
            vocabulary=self.vocabulary,
        )
        self.description = description
        self.customer_id = customer_id
        self.target = target

    @timer
    def fit(self, df, y=None, **fit_params):
        if fit_params:
            self.cvr.fit(df[self.description], fit_params)
        else:
            self.cvr.fit(df[self.description])
        return self

    @timer
    def transform(self, df: pd.DataFrame, **transform_params) -> pd.DataFrame:
        if transform_params:
            res = self.cvr.transform(df[self.description], transform_params).toarray()
        else:
            res = self.cvr.transform(df[self.description]).toarray()

        # Only check occurence, not count
        res[res > 1] = 1
        vocab = self.cvr.vocabulary_
        vocab = {v: k for k, v in sorted(vocab.items(), key=lambda item: item[1])}
        vocab = list(vocab.values())

        # Prevent overlapping feature names in training
        vocab = ["n_gram_" + self.description + "_" + x for x in vocab]
        res = pd.DataFrame(res, columns=vocab)

        # TODO
        # Only pick n_grams that have high correlations with label in training?
        features = df
        if "cluster_label" in features.columns:
            features = features.drop(columns="cluster_label")
        if self.target in features.columns:
            features = features.drop(columns=self.target)
        if self.customer_id in features.columns:
            features = features.drop(columns=self.customer_id)
        features = features.drop(columns=self.description)
        out = pd.concat([features.reset_index(drop=True), res], axis=1)

        out = out[out.columns.drop(list(out.filter(regex="SEPARATOR")))]

        return out.reset_index(drop=True)


@timer
def IA_get_model(config, load_model=True, training=False) -> Pipeline:
    data_preprocess = IA_Preprocessing(config, config.IA_LABEL, training)
    cluster_level_feature = IA_ClusterLevelFeature(config, "handlabel_cat", training)
    wrapped_cvr_who = Wrapped_CVR(
        ngram_range="(1,2)",
        min_df=3,
        max_features=5000,
        vocabulary=config.COMMON_WHO,
        description=config.WHO_COL,
        customer_id=config.IA_CUSTOMER_ID,
    )
    wrapped_cvr_how = Wrapped_CVR(
        ngram_range="(1,2)",
        min_df=3,
        max_features=5000,
        vocabulary=config.COMMON_HOW,
        description=config.HOW_COL,
        customer_id=config.IA_CUSTOMER_ID,
    )
    wrapped_cvr_why = Wrapped_CVR(
        ngram_range="(1,2)",
        min_df=3,
        max_features=5000,
        vocabulary=config.COMMON_WHY,
        description="WHY",
        customer_id=config.IA_CUSTOMER_ID,
    )
    if load_model:
        cvr_who, cvr_how, cvr_why, xgb = config.IA_MULTI_CAT_MODEL_COMPONENTS
        wrapped_cvr_who.cvr = cvr_who
        wrapped_cvr_how.cvr = cvr_how
        wrapped_cvr_why.cvr = cvr_why
    # =============================================================================
    #         wrapped_cvr_who = Wrapped_CVR(ngram_range="(1,2)", min_df=3, max_features=5000,
    #                                       vocabulary=config.COMMON_WHO, description=config.WHO_COL)
    #         wrapped_cvr_who.cvr = cvr_who
    #         wrapped_cvr_how = Wrapped_CVR(ngram_range="(1,2)", min_df=3, max_features=5000,
    #                                       vocabulary=config.COMMON_HOW, description=config.HOW_COL)
    #         wrapped_cvr_how.cvr = cvr_how
    #         wrapped_cvr_why = Wrapped_CVR(ngram_range="(1,2)", min_df=3, max_features=5000,
    #                                       vocabulary=config.COMMON_WHY, description='WHY')
    #         wrapped_cvr_why.cvr = cvr_why
    # =============================================================================
    else:
        xgb = XGBClassifier(
            n_jobs=config.IA_N_JOBS,
            objective=config.IA_OBJECTIVE,
            eval_metric=config.IA_EVAL_METRIC,
            # silent= config.SILENT,
            tree_method=config.IA_TREE_METHOD,
            random_state=config.IA_RANDOM_STATE,
            # scale_pos_weight= config.SCALE_POS_WEIGHT
        )
    model = Pipeline(
        [
            ("preprocess", data_preprocess),
            ("cluster_level_feautre", cluster_level_feature),
            ("cvr_WHO", wrapped_cvr_who),
            (
                "cvr_HOW",
                wrapped_cvr_how,
            ),
            ("cvr_WHY", wrapped_cvr_why),
            ("xgb", xgb),
        ]
    )

    return model


@timer
def get_bayes_cv_tuner(model, cv_obj, config, fit_params) -> BayesSearchCV:
    # For training only
    model_name = config.IA_ESTIMATOR_NAME + "__"
    bayes_cv_tuner = BayesSearchCV(
        estimator=model,
        search_spaces={
            "{}n_estimators".format(model_name): config.IA_N_ESTIMATORS,
            "{}learning_rate".format(model_name): config.IA_LEARNING_RATE,
            "{}min_child_weight".format(model_name): config.IA_MIN_CHILD_WEIGHT,
            "{}max_depth".format(model_name): config.IA_MAX_DEPTH,
            "{}max_delta_step".format(model_name): config.IA_MAX_DELTA_STEP,
            "{}subsample".format(model_name): config.IA_SUBSAMPLE,
            "{}colsample_bytree".format(model_name): config.IA_COLSAMPLE_BYTREE,
            "{}colsample_bylevel".format(model_name): config.IA_COLSAMPLE_BYLEVEL,
            "{}reg_alpha".format(model_name): (
                config.IA_REG_ALPHA
                # '{}scale_pos_weight'.format(model_name): (config.IA_SCALE_POS_WEIGHT),
                # 'reg_lambda': (1e-9, 1000, 'log-uniform'),
                # 'reg_alpha': (1e-9, 1.0, 'log-uniform'),
                # 'gamma': (1e-9, 1, 'log-uniform')
                # 'cvr__ngram_range': Categorical(config.IA_N_GRAM_RANGE),
                # 'cvr__min_df': Integer(config.IA_MIN_DF[0], config.IA_MIN_DF[1]),
                # 'cvr__max_features': Integer(config.IA_MAX_FEATURES[0], config.IA_MAX_FEATURES[1])
            ),
        },
        scoring=config.IA_SCORING,
        cv=cv_obj,
        # cv = 5,
        n_jobs=config.IA_N_JOBS,
        n_iter=config.IA_N_ITER,
        verbose=config.IA_VERBOSE,
        refit=config.IA_REFIT,
        # For replicating the cv result, change RANDOM_STATE  to another number to get different parameters
        random_state=config.IA_RANDOM_STATE,
        fit_params=fit_params,
    )

    return bayes_cv_tuner


class GroupKFoldWrapper:
    # for training only
    def __init__(self, cv_obj, groups):
        self.cv = cv_obj
        self.groups = groups

    def split(self, X, y, groups=None):
        return self.cv.split(X, y, groups=self.groups)

    def get_n_splits(self, X, y, groups):
        return self.cv.get_n_splits(X, y, groups)
