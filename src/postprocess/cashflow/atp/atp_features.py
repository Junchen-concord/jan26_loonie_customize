import pandas as pd

from postprocess.cashflow.atp.get_peak_features import get_all_peak_features
from utils.decorators import timer


@timer
def ATP_features(transactions: pd.DataFrame) -> pd.DataFrame:
    all_atp_features = (
        transactions.groupby("accountGuid")
        .apply(get_all_peak_features)
        .reset_index()
    )
    return all_atp_features
