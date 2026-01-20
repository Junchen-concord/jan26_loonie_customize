import re

import jellyfish
import numpy as np
import pandas as pd
from fuzzywuzzy import fuzz


def auth_feature_check(
    application_info,
    IBV_auth_data,
    labeled_transactions,
):
    ## TODO: Add transactions search into this
    app_fname = application_info["fname"]
    app_lname = application_info["lname"]
    app_account_number = application_info["account_number"]
    app_routing_number = application_info["routing_number"]
    app_bank_name = application_info["bank_name"]
    app_city = application_info["city"]
    app_state = application_info["state"]
    app_zip = application_info["zip"]
    app_phone_number = application_info["phone_number"]
    app_email = application_info["email"]

    IBV_name = IBV_auth_data["name"]
    IBV_account_numbers = IBV_auth_data["account_number"]
    IBV_routing_numbers = IBV_auth_data["routing_number"]
    IBV_bank_names = IBV_auth_data["bank_name"]
    IBV_state = IBV_auth_data["state"]
    IBV_city = IBV_auth_data["city"]
    IBV_zip = IBV_auth_data["zip"]
    IBV_phone_numbers = IBV_auth_data["phone_number"]
    IBV_emails = IBV_auth_data["email"]

    fname_match_rate, lname_match_rate = full_name_match(app_fname, app_lname, IBV_name)
    (
        IBV_from_chase,
        app_from_chase,
        total_match,
        last_four_match,
        first_four_match,
        routing_match,
    ) = check_bank_info(
        IBV_bank_names,
        app_bank_name,
        IBV_account_numbers,
        app_account_number,
        IBV_routing_numbers,
        app_routing_number,
    )
    city_match, state_match, zip_match = check_address_match(app_city, app_state, app_zip, IBV_city, IBV_state, IBV_zip)
    phone_match, email_match = check_phone_and_email(app_phone_number, app_email, IBV_phone_numbers, IBV_emails)

    (
        fname_in_transactions,
        fname_in_transactions_time,
        lname_in_transactions,
        lname_in_transactions_time,
    ) = check_name_in_transaction(app_fname, app_lname, labeled_transactions)
    account_number_in_transactions, account_number_in_transactions_time = check_account_number_in_transaction(
        app_account_number, labeled_transactions
    )

    (
        city_in_transactions,
        city_in_transactions_time,
        state_in_transactions,
        state_in_transactions_time,
        zip_in_transactions,
        zip_in_transactions_time,
    ) = check_address_in_transaction(app_city, app_state, app_zip, labeled_transactions)
    return {
        "fnameMatchRate": fname_match_rate,
        "lnameMatchRate": lname_match_rate,
        "IBVFromChase": IBV_from_chase,
        "appFromChase": app_from_chase,
        "accountNumberMatchAuth": total_match,
        "accountNumberLastFourMatchAuth": last_four_match,
        "accountNumberFirstFourMatchAuth": first_four_match,
        "routingNumberMatch": routing_match,
        "cityMatchAuth": city_match,
        "stateMatchAuth": state_match,
        "zipMatchAuth": zip_match,
        "phoneMatch": phone_match,
        "emailMatch": email_match,
        "fnameInTransactions": fname_in_transactions,
        "fnameInTransactionsTime": fname_in_transactions_time,
        "lnameInTransactions": lname_in_transactions,
        "lnameInTransactionsTime": lname_in_transactions_time,
        "accountNumberInTransactions": account_number_in_transactions,
        "accountNumberInTransactionsTime": account_number_in_transactions_time,
        "cityInTransactions": city_in_transactions,
        "cityInTransactionsTime": city_in_transactions_time,
        "stateInTransactions": state_in_transactions,
        "stateInTransactionsTime": state_in_transactions_time,
        "zipInTransactions": zip_in_transactions,
        "zipInTransactionsTime": zip_in_transactions_time,
    }


def full_name_match(fname, lname, ibvname):
    """
    match names from IBV to names from chirp and plaid
    """
    # data sanity checks
    if pd.isnull(fname) or pd.isnull(lname) or len(ibvname) == 0:
        return np.nan, np.nan

    if (
        not isinstance(ibvname, list)
        or not isinstance(lname, str)
        or not isinstance(fname, str)
        or min([isinstance(name, str) for name in ibvname]) == 0
    ):
        return np.nan, np.nan

    # match the first name or last name with full names from IBV token by token
    ibvname_list = [preprocess_name(name) for name in ibvname]
    ibvname_list = [name for name in ibvname_list if len(name) > 0]

    fname = preprocess_name(fname)
    lname = preprocess_name(lname)
    f_name_match_ratio = max([partial_name_match(fname, name) for name in ibvname_list])
    l_name_match_ratio = max([partial_name_match(lname, name) for name in ibvname_list])
    return f_name_match_ratio, l_name_match_ratio


def partial_name_match(partial_app_name, ibv_name):
    """
    This is to deal with the massiveness in the application name
    make sure there are multiple tokens in the names given, such as John of the gate as the first name
    as long as John matches with John in IBV, it should be a match unless other tokens are too unsimilar
    """
    app_name_list = partial_app_name.split()
    ibv_name_list = ibv_name.split()
    if len(app_name_list) == 1:
        return max([match_single_word(partial_app_name, ibv_name_token) for ibv_name_token in ibv_name_list])
    else:
        similarity_by_token = []
        for p_name in app_name_list:
            similarity_by_token.append(
                max([match_single_word(p_name, ibv_name_token) for ibv_name_token in ibv_name_list])
            )
        return np.mean(similarity_by_token)


def match_single_word(w1, w2):
    w1 = w1.lower()
    w2 = w2.lower()
    return fuzz.ratio(jellyfish.soundex(w1.lower()), jellyfish.soundex(w2.lower()))


def check_name_in_transaction(fname, lname, trans):
    fname = preprocess_name(fname)
    lname = preprocess_name(lname)
    lname_find, lname_find_time = check_text_in_transactions(lname, trans, "description")
    fname_find, fname_find_time = check_text_in_transactions(fname, trans, "description")
    return lname_find, lname_find_time, fname_find, fname_find_time


def check_account_number_match(account_number, app_number):
    # data sanity check
    if account_number is None or app_number is None or pd.isnull(account_number) or pd.isnull(app_number):
        return np.nan, np.nan, np.nan

    # format the numbers to remove leading zero
    account_number = format_numeric(account_number)
    app_number = format_numeric(app_number)

    return (
        account_number == app_number,
        app_number[-4:] == account_number[-4:],
        app_number[:4] == account_number[:4],
    )


chase_pattern = re.compile(r"\b(chase)\b".lower())


def check_bank_from_chase(IBV_bank_names: list, app_bank_name: str):
    # right now matching bank names thourhg different aliases can be difficult or can be achieved by a hc clustering, but for now
    # want to start with differenciate chase or not because we always get a fake bank account from chase
    if pd.isnull(app_bank_name):
        return np.nan, np.nan

    # Filter out None/NaN from IBV_bank_names
    IBV_bank_names = [bn for bn in IBV_bank_names if not pd.isnull(bn)]

    # If nothing left after filtering, return NaNs
    if len(IBV_bank_names) == 0:
        return np.nan, np.nan

    app_bank_name = app_bank_name.lower()

    IBV_from_chase = False
    app_from_chase = False
    for bank_name in IBV_bank_names:
        bank_name = bank_name.lower()
        if chase_pattern.search(bank_name):
            IBV_from_chase = True
    if chase_pattern.search(app_bank_name):
        app_from_chase = True
    return IBV_from_chase, app_from_chase


def check_account_number_match_multiple(IBV_numbers, app_number):
    """
    account_number: list, account number from IBV
    app_number: str, account number from application
    """
    total_match = False
    last_four_match = False
    first_four_match = False
    for IBV_number in IBV_numbers:
        match, last_four_match_single_account, last_four_match_single_account = check_account_number_match(
            IBV_number, app_number
        )
        total_match = total_match or match
        last_four_match = last_four_match or last_four_match_single_account
        first_four_match = first_four_match or last_four_match_single_account
    return total_match, last_four_match, first_four_match


def check_routing(IBV_routing_numbers: list[str], app_routing_number: str) -> bool:
    if pd.isna(app_routing_number):
        return np.nan

    if not IBV_routing_numbers:
        return np.nan

    cleaned = [r for r in IBV_routing_numbers if not pd.isna(r)]
    if not cleaned:
        return np.nan

    IBV_routing_numbers = [format_numeric(routing) for routing in cleaned]
    app_routing_number = format_numeric(app_routing_number)
    return app_routing_number in IBV_routing_numbers


def check_bank_info(
    IBV_bank_names,
    app_bank_name,
    IBV_numbers,
    app_numbers,
    IBV_routing_numbers,
    app_routing_number,
):
    """
    IBV_bank_names: list, bank names from IBV
    app_bank_name: str, bank name from application
    IBV_numbers: list, account numbers from IBV
    app_numbers: str, account number from application
    """
    IBV_bank_names = remove_nulls(IBV_bank_names)
    IBV_numbers = remove_nulls(IBV_numbers)
    IBV_routing_numbers = remove_nulls(IBV_routing_numbers)

    # Check bank name features - only return NaN if required fields are missing
    if pd.isnull(app_bank_name) or len(IBV_bank_names) == 0:
        IBV_from_chase, app_from_chase = np.nan, np.nan
    else:
        IBV_from_chase, app_from_chase = check_bank_from_chase(IBV_bank_names, app_bank_name)

    # Check account number features - only return NaN if required fields are missing
    if pd.isnull(app_numbers) or len(IBV_numbers) == 0:
        total_match, last_four_match, first_four_match = np.nan, np.nan, np.nan
    else:
        total_match, last_four_match, first_four_match = check_account_number_match_multiple(IBV_numbers, app_numbers)

    # Check routing number features - only return NaN if required fields are missing
    if pd.isnull(app_routing_number) or len(IBV_routing_numbers) == 0:
        routing_match = np.nan
    else:
        routing_match = check_routing(IBV_routing_numbers, app_routing_number)

    return (
        IBV_from_chase,
        app_from_chase,
        total_match,
        last_four_match,
        first_four_match,
        routing_match,
    )


def check_account_number_in_transaction(account_number, trans):
    account_number_find, account_number_find_time = check_account_number_in_transactions(
        account_number, trans, "description"
    )
    return account_number_find, account_number_find_time


def check_address_match(app_city, app_state, app_zip, IBV_cities, IBV_states, IBV_zips):
    if not isinstance(IBV_cities, list) or not isinstance(IBV_states, list) or not isinstance(IBV_zips, list):
        return np.nan, np.nan, np.nan
    if (
        pd.isnull(app_city)
        or pd.isnull(app_state)
        or pd.isnull(app_zip)
        or len(IBV_cities) == 0
        or len(IBV_states) == 0
        or len(IBV_zips) == 0
    ):
        return np.nan, np.nan, np.nan
    app_city = app_city.lower()
    app_state = app_state.lower()
    IBV_cities = remove_nulls(IBV_cities)
    IBV_states = remove_nulls(IBV_states)
    IBV_cities = [city.lower() for city in IBV_cities]
    IBV_states = [state.lower() for state in IBV_states]
    app_zip = remove_zip_suffix(app_zip)
    IBV_zips = [remove_zip_suffix(zip_code) for zip_code in IBV_zips]

    city_matches = app_city in IBV_cities
    state_matches = app_state in IBV_states
    zip_matches = format_numeric(app_zip) in [format_numeric(x) for x in IBV_zips]
    return city_matches, state_matches, zip_matches


def check_address_in_transaction(app_city, app_state, app_zip, trans):
    city_find, city_find_time = check_text_in_transactions(app_city, trans, "description")
    state_find, state_find_time = check_text_in_transactions(app_city, trans, "description")
    zip_find, zip_find_time = check_text_in_transactions(app_city, trans, "description")
    return (
        city_find,
        city_find_time,
        state_find,
        state_find_time,
        zip_find,
        zip_find_time,
    )


def check_phone_and_email(app_phones, app_email, IBV_phones, IBV_emails):
    if not isinstance(IBV_phones, list) or not isinstance(IBV_emails, list):
        return np.nan, np.nan
    if pd.isnull(app_email) or len(app_phones) == 0 or len(IBV_phones) == 0 or len(IBV_emails) == 0:
        return np.nan, np.nan
    app_phones = [format_numeric(remove_remove_region_code(x)) for x in app_phones]
    IBV_phones = [format_numeric(remove_remove_region_code(x)) for x in IBV_phones]
    phone_matches = any([x in IBV_phones for x in app_phones])
    email_matches = app_email in IBV_emails
    return phone_matches, email_matches


# Utility functions
# TODO: I'm not sure this should be moved into a separate file or under utility folder
def remove_remove_region_code(x):
    if isinstance(x, str):
        return re.sub(r"\+\d", "", x)
    else:
        return x


def remove_zip_suffix(zip_code):
    if isinstance(zip_code, str):
        zip_code = zip_code.split("-")[0]
    return zip_code


single_char_re = re.compile(r"\b\w\b")
prefix_re = re.compile(
    r"\b(Mr|Mrs|Ms|Dr|Prof|Hon|Rev|Capt|Col|Gen|Lt|Cmdr|Adm|Cdr|Sgt|Maj|Pvt|Cpl|Pfc|1stSgt)\.\b".lower()
)
dot_re = re.compile(r"\.")
prefix_re = re.compile(r"\b(Mr\.?)\b".lower())


def preprocess_name(name):
    """
    preprocess names from IBV to remove some middle names and prefix
    """
    name = prefix_re.sub("", name)
    name = single_char_re.sub("", name)
    name = dot_re.sub("", name)
    name = name.strip()
    return name


def format_numeric(x):
    if (
        isinstance(x, float)
        or (isinstance(x, str) and x.isnumeric())
        or isinstance(x, int)
        or isinstance(x, np.integer)
    ) and not pd.isnull(x):
        x = str(int(x))
        x = x.lstrip("0")
    return x


def remove_nulls(li):
    return [x for x in li if not pd.isnull(x)]


def check_text_in_transactions(text, trans, description_col):
    text_regex_search = trans.loc[:, description_col].str.contains(r"\b" + text + r"\b", case=False, na=False)
    text_found = np.max(text_regex_search)
    text_found_times = np.sum(text_regex_search)
    return text_found, text_found_times


def check_account_number_in_transactions(account_number, trans, description_col):
    account_number = format_numeric(account_number)
    last_four_number = account_number[-4:]
    account_number_regex_search = trans.loc[:, description_col].str.contains(
        r"\b(?:x*\d*|x+)?" + last_four_number + r"\b", case=False, na=False
    )
    account_number_found = np.max(account_number_regex_search)
    account_number_found_times = np.sum(account_number_regex_search)
    return account_number_found, account_number_found_times
