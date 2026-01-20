#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Apr  8 15:49:17 2024

@author: ryan
"""
import pandas as pd
import numpy as np
df = pd.read_csv("intermediate_training_step/cluster_level_feature.csv")

# For payroll clusters, duplicate x% clusters to make the amount 1/y smaller, but need to be > 50
# For transfer/loan clusters, duplicate x% clusters to make the amount y larger, given that the initial amount_mean > 50


def augment_data(df):
    payrolls = df[df.handlabel_cat == 'payroll']
    transfers = df[df.handlabel_cat == 'transfer']
    loans = df[df.handlabel_cat == 'loan']
    new_payrolls = augment_amount_payroll(payrolls)
    new_transfers = augment_amount_loans_transfers(transfers)
    new_loans = augment_amount_loans_transfers(loans)
    return pd.concat([df, new_payrolls, new_transfers, new_loans], axis=0).reset_index(drop=True)


def augment_amount_payroll(df, random_state=1129):
    augmented_payrolls = df.copy()
    amount_columns = [x for x in augmented_payrolls.columns if 'amount' in x]
    np.random.seed(random_state)
    random_shrinkage = np.random.randint(low=3, high=5, size=len(augmented_payrolls))
    for column in amount_columns:
        augmented_payrolls.loc[:, column] = augmented_payrolls.loc[:, column]/random_shrinkage
    originate_amount_large_enough = augmented_payrolls[augmented_payrolls.originated_amount_mean >= 50]
    new_samples = originate_amount_large_enough.sample(int(len(augmented_payrolls)*0.2))
    return new_samples


def augment_amount_loans_transfers(df, random_state=1129):
    augmented_df = df.copy()
    amount_columns = [x for x in augmented_df.columns if 'amount' in x]
    np.random.seed(random_state)

    large_enough_original_amount = augmented_df[augmented_df.originated_amount_mean >= 50]
    random_expansion = np.random.randint(low=2, high=5, size=len(large_enough_original_amount))

    for column in amount_columns:
        large_enough_original_amount.loc[:,
                                         column] = large_enough_original_amount.loc[:, column]*random_expansion
    new_samples = large_enough_original_amount.sample(int(len(augmented_df)), replace=True)
    return new_samples


new_df = augment_data(df)
new_df.to_csv("intermediate_training_step/augmented_training.csv", index=False)
