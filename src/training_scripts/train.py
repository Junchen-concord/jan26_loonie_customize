#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Apr  4 00:01:21 2024

@author: ryan
"""
# from model.analyzers import IA_get_model, get_bayes_cv_tuner, GroupKFoldWrapper
# import joblib
# from NER.ner import load_ner, ner_prediction
# from config import config
# import pandas as pd
# import numpy as np
# from sklearn.model_selection import GroupKFold, train_test_split
# import sys
# import os
# from sklearn.metrics import classification_report
# from sklearn.preprocessing import LabelEncoder
# # TODO
# # figure out the correct way for importing
# sys.path.append('/Users/ryan/Documents/Concord_repo/Income_Analyzer_V16/src')
# # sys.path.append('src')
# # print(sys.path)
# # from config import config


# def process_NER_LABEL(x):
#     if x is None:
#         return 'None'
#     if pd.isnull(x):
#         return 'None'
#     else:
#         return x


# def label_encode(y):
#     # I am aware,I just don't want to use label encoder in sklearn
#     out = y.copy()
#     out[y == 'payroll'] = 1
#     out[y == 'other'] = 0
#     out[y == 'transfer'] = 3
#     out[y == 'loan'] = 2
#     return out


# # get the model
# model = IA_get_model(config, load_model=False, training=True)


# # =============================================================================
# # df = pd.read_csv('data/combined_v15_training_new.csv')
# # df = df.rename(columns = {"original_description":'originalDescription','account_guid':'accountGuid'})
# # df.loc[~df.handlabel_cat.isin(['payroll','loan','transfer','benefit']),'handlabel_cat'] = 'other'
# # df.loc[df.handlabel_cat == 'benefit','handlabel_cat'] = 'payroll'
# # nlp = load_ner(os.path.realpath(os.path.join(config.ROOT_DIR, 'model', 'model-best_NER_who_sub')))
# # df = ner_prediction(df, config.IA_ORIGINAL_DESCRIPTION, nlp,progress_bar=True)
# # df.to_csv('intermediate_training_step/after_ner.csv',index = False)
# # =============================================================================
# # df = pd.read_csv('intermediate_training_step/after_ner.csv')
# # df.loc[:, config.WHO_COL] = df.loc[:, config.WHO_COL].apply(lambda x: process_NER_LABEL(x))
# # df.loc[:, config.WHY_COL] = df.loc[:, config.WHY_COL].apply(lambda x: process_NER_LABEL(x))
# # df.loc[:, config.HOW_COL] = df.loc[:, config.HOW_COL].apply(lambda x: process_NER_LABEL(x))
# # #df = df.sample(1000)
# # X = model[0].transform(df)
# # X.to_csv('intermediate_training_step/after_clustering.csv',index = False)
# X = pd.read_csv('intermediate_training_step/after_clustering.csv')
# X = model[1].transform(X)
# # X = X.rename(columns = {'is_payroll':'handlabel_cat'})
# # X.to_csv("intermediate_training_step/cluster_level_feature.csv",index = False)
# X = pd.read_csv("intermediate_training_step/augmented_training.csv")
# # X = X.drop(columns = ['index'])
# y = X.loc[:, 'handlabel_cat']
# sample_weights = np.ones_like(y)
# sample_weights[y == 'payroll'] = 3
# sample_weights[y == 'loan'] = 3
# # X = model[2:5].transform(X)


# X_cred = X[X.debit_only != 1]
# y_cred = X_cred['handlabel_cat']
# y_cred = label_encode(y_cred).astype(int)
# # y_cred_pred = opt_clf.predict(X_cred)

# train_idx, test_idx = train_test_split(X_cred.index, test_size=0.2, random_state=1129)
# X_cred_train = X_cred.loc[train_idx]
# X_cred_test = X_cred.loc[test_idx]
# y_cred_train = y_cred.loc[train_idx]
# y_cred_test = y_cred.loc[test_idx]

# cv_obj = GroupKFoldWrapper(GroupKFold(config.IA_N_FOLD), X_cred_train.accountGuid)
# fit_params = {"sample_weight": sample_weights}
# # bayes_cv_tuner = get_bayes_cv_tuner(model[2:],cv_obj,config,fit_params)
# bayes_cv_tuner = get_bayes_cv_tuner(model[2:], cv_obj, config, {})
# np.int = int
# clf = bayes_cv_tuner.fit(X_cred_train, y_cred_train)
# opt_clf = clf.best_estimator_

# y_pred_test = opt_clf.predict(X_cred_test)

# print(classification_report(y_cred_test, y_pred_test))

# X_cred_test.loc[:, 'pred'] = y_pred_test
# transfer_errors_source = X_cred_test.loc[y_cred_test != y_pred_test, :]

# raw_trans = pd.read_csv('intermediate_training_step/after_clustering.csv')
# transfer_errors_all = raw_trans[['cluster_label', 'accountGuid', 'originalDescription', 'processed_n_gram', 'amount', 'date',
#                                  'WHO', 'HOW', 'WHAT', 'WHO_cat']].merge(transfer_errors_source[['accountGuid', 'cluster_label',
#                                                                                                 'pred', 'handlabel_cat']],
#                                                                          how='inner', on=['accountGuid', 'cluster_label']).sort_values(['accountGuid', 'cluster_label', 'date'])

# payroll_errors = transfer_errors_all.loc[(transfer_errors_all.pred == 1) | (
#     transfer_errors_all.handlabel_cat == 'payroll')]
# loan_errors = transfer_errors_all.loc[(transfer_errors_all.pred == 2) | (
#     transfer_errors_all.handlabel_cat == 'loan')]
# transfer_erros = transfer_errors_all.loc[(transfer_errors_all.pred == 3) | (
#     transfer_errors_all.handlabel_cat == 'transfer')]
# # clustering may need to change (remove easy non-source words)
# # resample data to generate more none - payrolls and payrolls with smaller amount
# # more feature enginering for transfer from keywords etc. checked
# # who cat as a feature checked

# # =============================================================================
# # X = pd.read_csv("intermediate_training_step/cluster_level_feature.csv")
# # X = model[2:5].transform(X)
# # =============================================================================
# #     print("generating cluster level features")
# #     #right now sklearn pipeline doesn't support subsampling (size of X,y changes) in pipeline so well, so need to drag it out before cv
# #     X = model[:2].transform(df)
# #     y = X[config.LABEL]
# #     y = y.fillna(0)
# #
# #     print("fine tuning xgb and count vectorizer to maximize performance on held out customer")
# #     #get the split method, by now ideally split at customer level
# #     cv_obj = GroupKFoldWrapper(GroupKFold(config.N_FOLD),X.account_guid)
# #
# #     #get bayes search cv object in skopt
# #     bayes_cv_tuner = get_bayes_cv_tuner(model[2:],cv_obj,config)
# #
# #     #train model
# #     clf = bayes_cv_tuner.fit(X,y)
# #     opt_clf = clf.best_estimator_
# #     print("model training finished")
# #     print("{} fold evaluation metric ""{}"" result:{:.2f}".format(config.N_FOLD,config.SCORING,clf.best_score_))
# #     print("showing best params for tuning:")
# #     print(clf.best_params_)
# #     #save model
# #     print("saving the model")
# #     io.save_model(clf)
# #     return clf
# #
# # if __name__ == "__main__":
# #     clf = train_xgb(config.TRAINING_DATA_FILE)
# # =============================================================================

# X_cred = X[X.debit_only != 1]
# y_cred = X_cred['handlabel_cat']
# y_cred_pred = opt_clf.predict(X_cred)

# print(classification_report(y_cred, y_cred_pred))

# importance_dict = pd.DataFrame({"column_name": clf.best_estimator_['xgb'].get_booster(
# ).feature_names, "importance": clf.best_estimator_['xgb'].feature_importances_})
# importance_dict = importance_dict[importance_dict.importance >
#                                   0].sort_values("importance", ascending=False)


# cvr_who, cvr_how, cvr_why, xgb = clf.best_estimator_['cvr_WHO'], clf.best_estimator_[
#     'cvr_HOW'], clf.best_estimator_['cvr_WHY'], clf.best_estimator_['xgb']

# joblib.dump([cvr_who, cvr_how, cvr_why, xgb], 'multi_cat_model_partial.pkl')


# cvr_who, cvr_how, cvr_why, xgb = joblib.load('multi_cat_model.pkl')
