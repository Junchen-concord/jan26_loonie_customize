import json

import pandas as pd
from flask import Blueprint
from flask_apispec import doc, marshal_with, use_kwargs

from api.common import check_run_error, handle_error
from api.config.config import logger
from api.schemas.error import ErrorResponse, ValidationErrorResponse
from api.schemas.v2_output_schemas import ModelAnalyzeResponseV2
from api.transactions.schemas import TransactionsAnalyzeRequest
from api.transformations.transform_v2_output import transform_v2_output
from labeling.label_transactions import prepare_balance_df
from labeling.transaction_prep import create_analysis_dfs, revert_transaction_labels_for_processing
from postprocess import analyze_transactions

transactions_blueprint = Blueprint("Transaction Analysis", __name__, url_prefix="/model/v2/transactions")


def get_balance_df_from_accounts(accounts, as_of_date):
    balance_df_raw = pd.DataFrame.from_dict(accounts)
    balance_df = prepare_balance_df(balance_df_raw, as_of_date)
    return balance_df


def handle_analyze_transactions(labeled_transactions, balance_df):
    output_str = analyze_transactions(labeled_transactions, labeled_transactions, balance_df)
    output_final_dict = json.loads(output_str)
    run_error = check_run_error(output_final_dict, "v2")
    if run_error:
        return run_error, 400
    output_final_dict = transform_v2_output(output_final_dict)
    return output_final_dict, 200


@transactions_blueprint.route("/analyze", methods=["POST"])
@use_kwargs(TransactionsAnalyzeRequest, location="json")
@marshal_with(ModelAnalyzeResponseV2, code=200)
@marshal_with(ValidationErrorResponse, code=400)
@marshal_with(ErrorResponse, code=500)
@doc(
    description="Performs analysis on a list on already labeled transactions.",
    tags=["Transactions"],
)
def transactions_analyze(labeledTransactions, accounts, asOfDate):
    balance_df = get_balance_df_from_accounts(accounts, asOfDate)
    data = {"labeled_transactions": labeledTransactions, "balance_df": balance_df}
    logger.info("[POST] /model/v2/transactions/analyze")
    labeled_transactions, balance_df = create_analysis_dfs(data)
    try:
        prepped_transactions = revert_transaction_labels_for_processing(labeled_transactions)
        return handle_analyze_transactions(prepped_transactions, balance_df)
    except Exception as e:
        return handle_error(e)
