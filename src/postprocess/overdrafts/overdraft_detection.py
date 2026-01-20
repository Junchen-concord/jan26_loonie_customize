import pandas as pd

from config import config
from utils.decorators import timer


@timer
def overdraft_detection(df_transaction: pd.DataFrame, balance_df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    all_account_ids = balance_df[[config.IA_ACCOUNT_ID]]

    if "end_date" in df_transaction.columns:
        df_transaction = df_transaction.drop(columns="end_date")

    # Expanded keyword lists
    nsf_keywords = [
        r"\bnsf",
        r"\binsufficient funds\b",
        r"\binsufficient\b",
        r"\bnonsufficient\b",
        r"\bnon-sufficient\b",
        r"\bnon sufficient\b",
        r"\breturned item\b",
        r"\bunpaid item\b",
        r"\breturned check\b",
        r"\bret(urned)? ?chk\b",
        r"\bchargeback\b",
        r"\bdebit return\b",
        r"\bach return\b",
        r"\bpos return\b"
    ]

    overdraft_keywords = [
        r"\boverdraft\b",
        r"\boverdraft fee\b",
        r"\bod fee\b",
        r"\bpaid overdraft item\b",
        r"\bfee withdrawal overdrawn\b",
    ]

    trans_df = df_transaction.copy()
    trans_df.loc[:, "NSFIncident"] = 0
    trans_df.loc[:, "OverdraftFeeIncident"] = 0
    trans_df.loc[:, "OverdraftIncident"] = 0  # Combined

    # Detection
    nsf_mask = trans_df["description"].str.contains("|".join(nsf_keywords), case=False, na=False) & (
        trans_df["type"].str.upper() == "DEBIT"
    )
    odf_mask = trans_df["description"].str.contains("|".join(overdraft_keywords), case=False, na=False) & (
        trans_df["type"].str.upper() == "DEBIT"
    )

    trans_df.loc[nsf_mask, "NSFIncident"] = 1
    trans_df.loc[odf_mask, "OverdraftFeeIncident"] = 1
    trans_df["OverdraftIncident"] = trans_df["NSFIncident"] | trans_df["OverdraftFeeIncident"]

    df_transaction = trans_df

    # Time window
    end_date = balance_df.groupby("accountGuid").agg(end_date=("as_of_date", "max")).reset_index()
    df_transaction = df_transaction.merge(end_date, how="left", on="accountGuid")
    df_transaction["month"] = (
        (pd.to_datetime(df_transaction["end_date"]) - pd.to_datetime(df_transaction["date"])).dt.days / 30
    )

    # Aggregation for each type
    def agg_counts(flag, label):
        all_time = df_transaction.groupby(config.IA_ACCOUNT_ID).agg(**{f"{label}All": (flag, "sum")})
        in_3m = (
            df_transaction[df_transaction["month"] <= 3]
            .groupby(config.IA_ACCOUNT_ID)
            .agg(**{f"{label}3m": (flag, "sum")})
        )
        in_6m = (
            df_transaction[df_transaction["month"] <= 6]
            .groupby(config.IA_ACCOUNT_ID)
            .agg(**{f"{label}6m": (flag, "sum")})
        )
        return all_time, in_3m, in_6m

    od_all, od_3m, od_6m = agg_counts("OverdraftIncident", "od")
    nsf_all, nsf_3m, nsf_6m = agg_counts("NSFIncident", "nsf")
    odf_all, odf_3m, odf_6m = agg_counts("OverdraftFeeIncident", "odf")

    # Merge all into one summary DataFrame
    od_cnt = (
        all_account_ids
        .merge(od_all, how="left", on=config.IA_ACCOUNT_ID)
        .merge(od_3m, how="left", on=config.IA_ACCOUNT_ID)
        .merge(od_6m, how="left", on=config.IA_ACCOUNT_ID)
        .merge(nsf_all, how="left", on=config.IA_ACCOUNT_ID)
        .merge(nsf_3m, how="left", on=config.IA_ACCOUNT_ID)
        .merge(nsf_6m, how="left", on=config.IA_ACCOUNT_ID)
        .merge(odf_all, how="left", on=config.IA_ACCOUNT_ID)
        .merge(odf_3m, how="left", on=config.IA_ACCOUNT_ID)
        .merge(odf_6m, how="left", on=config.IA_ACCOUNT_ID)
        .fillna(0)
        .astype(
            {
                "odAll": "int64",
                "od3m": "int64",
                "od6m": "int64",
                "nsfAll": "int64",
                "nsf3m": "int64",
                "nsf6m": "int64",
                "odfAll": "int64",
                "odf3m": "int64",
                "odf6m": "int64",
            }
        )
    )

    # Incident details
    incidents = df_transaction[df_transaction["OverdraftIncident"] == 1][
        [config.IA_ACCOUNT_ID, "date", "amount", "description"]
    ]
    odf_incidents = df_transaction[df_transaction["OverdraftFeeIncident"] == 1][
        [config.IA_ACCOUNT_ID, "date", "amount", "description"]
    ]
    nsf_incidents = df_transaction[df_transaction["NSFIncident"] == 1][
        [config.IA_ACCOUNT_ID, "date", "amount", "description"]
    ]
    

    return od_cnt, incidents, odf_incidents, nsf_incidents
