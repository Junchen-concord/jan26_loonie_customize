from collections import defaultdict
from copy import deepcopy

from utils.utils import remove_account_guid


def get_nested_value(d, keys, default=None):
    for key in keys:
        d = d.get(key, {})
        if not isinstance(d, dict):
            return default
    return d or default


def key_by_account(output_json):
    def create_score_schema():
        return {"score": 0, "modelReasons": []}

    score_schema_account = {
        "redZone": create_score_schema(),
        "repeat": create_score_schema(),
        "loanPaidOff": create_score_schema(),
        "isBad": create_score_schema(),
    }

    score_schema_customer = {
        "redZone": create_score_schema(),
        "repeat": create_score_schema(),
        "loanPaidOff": create_score_schema(),
        "isBad": create_score_schema(),
    }

    new_schema = {
        "accountInfo": defaultdict(
            lambda: {
                "summary": {},
                "incomeSources": [],
                "loanSources": [],
                "overdraftIncidents": [],
                "majorIncomeSource": {},
                "cashflow": {},
                "scores": deepcopy(score_schema_account),
                "lendingGuide": {},
                "creditTrans": [],
                "debitTrans": [],
            }
        ),
        "customerInfo": {
            "redZoneBehavior": {},
            "alertsAndInsights": {},
            "recommendedBankAccount": "",
            "scores": deepcopy(score_schema_customer),
            "lendingGuide": {},
        },
    }

    # =====================
    # Populate accountInfo
    for summary in output_json.get("summaryInfo", []):
        account_guid = summary["accountGuid"]
        new_schema["accountInfo"][account_guid]["summary"] = summary

    # Income Sources
    for income_source in output_json.get("incomeSources", []):
        account_guid = income_source["accountGuid"]
        new_schema["accountInfo"][account_guid]["incomeSources"].append(income_source)

    # Loan Sources
    for loan_source in output_json.get("loanSources", []):
        account_guid = loan_source["accountGuid"]
        new_schema["accountInfo"][account_guid]["loanSources"].append(loan_source)

    # Overdrafts Incidents
    for overdraft_incident in output_json.get("overdraftIncidents", []):
        account_guid = overdraft_incident["accountGuid"]
        new_schema["accountInfo"][account_guid]["overdraftIncidents"].append(overdraft_incident)

    # Major Income Source
    for major_income_source in output_json.get("majorIncomeSource", []):
        account_guid = major_income_source["accountGuid"]
        new_schema["accountInfo"][account_guid]["majorIncomeSource"] = major_income_source

    # Cashflow
    for cashflow in output_json.get("cashFlow", []):
        account_guid = cashflow["accountGuid"]
        new_schema["accountInfo"][account_guid]["cashflow"] = cashflow

    # Scores
    scores = output_json.get("scores", {})
    redzone_account_level = get_nested_value(scores, ["redZone", "accountLevel"], {})
    repeat_account_level = get_nested_value(scores, ["repeat", "accountLevel"], {})
    loanPaidOff_account_level = get_nested_value(scores, ["loanPaidOff", "accountLevel"], {})
    isBad_account_level = get_nested_value(scores, ["isBad", "accountLevel"], {})

    # Redzone
    for item in redzone_account_level.get("modelReasons", []):
        account_guid = item["accountGuid"]
        new_schema["accountInfo"][account_guid]["scores"]["redZone"]["modelReasons"].append(item)

    for item in redzone_account_level.get("modelScore", []):
        account_guid = item["accountGuid"]
        new_schema["accountInfo"][account_guid]["scores"]["redZone"]["score"] = item["riskScore"]

    # Repeat
    for item in repeat_account_level.get("modelReasons", []):
        account_guid = item["accountGuid"]
        new_schema["accountInfo"][account_guid]["scores"]["repeat"]["modelReasons"].append(item)

    for item in repeat_account_level.get("modelScore", []):
        account_guid = item["accountGuid"]
        new_schema["accountInfo"][account_guid]["scores"]["repeat"]["score"] = item["repeatScore"]

    # LoanPaidOff
    for item in loanPaidOff_account_level.get("modelReasons", []):
        account_guid = item["accountGuid"]
        new_schema["accountInfo"][account_guid]["scores"]["loanPaidOff"]["modelReasons"].append(item)

    for item in loanPaidOff_account_level.get("modelScore", []):
        account_guid = item["accountGuid"]
        new_schema["accountInfo"][account_guid]["scores"]["loanPaidOff"]["score"] = item["totalLoanPaidOffScore"]

    # IsBad
    for item in isBad_account_level.get("modelReasons", []):
        account_guid = item["accountGuid"]
        new_schema["accountInfo"][account_guid]["scores"]["isBad"]["modelReasons"].append(item)

    for item in isBad_account_level.get("modelScore", []):
        account_guid = item["accountGuid"]
        new_schema["accountInfo"][account_guid]["scores"]["isBad"]["score"] = item["isBadScore"]

    # Lending Guide
    for account in output_json.get("accounts", []):
        account_guid = account["accountGuid"]
        lending_guide = account["lendingGuide"]
        lending_guide["accountGuid"] = account_guid
        new_schema["accountInfo"][account_guid]["lendingGuide"] = lending_guide

    # Credit & Debit Trans
    credit_trans = output_json.get("creditTrans", [])
    debit_trans = output_json.get("debitTrans", [])
    account_guid_list = [acct for acct in new_schema["accountInfo"]]
    credits_grouped_dict = defaultdict(list)
    debits_grouped_dict = defaultdict(list)
    for item in credit_trans:
        credits_grouped_dict[item["accountGuid"]].append(item)
    for item in debit_trans:
        debits_grouped_dict[item["accountGuid"]].append(item)

    credits_dict = dict(credits_grouped_dict)
    debits_dict = dict(debits_grouped_dict)
    for account_guid in account_guid_list:
        new_schema["accountInfo"][account_guid]["creditTrans"] = credits_dict.get(account_guid, [])
        new_schema["accountInfo"][account_guid]["debitTrans"] = debits_dict.get(account_guid, [])

    # =====================
    # Populate customerInfo
    additionalInfo = output_json.get("additionalInfo", {})
    new_schema["customerInfo"]["alertsAndInsights"] = additionalInfo.get("alertsAndInsightsCustomer", [])[0]

    # Scores
    customer_scores = deepcopy(scores)
    remove_account_guid(customer_scores)
    redzone_customer_level = get_nested_value(customer_scores, ["redZone", "customerLevel"], {})
    repeat_customer_level = get_nested_value(customer_scores, ["repeat", "customerLevel"], {})
    loanPaidOff_customer_level = get_nested_value(customer_scores, ["loanPaidOff", "customerLevel"], {})
    isBad_customer_level = get_nested_value(customer_scores, ["isBad", "customerLevel"], {})
    new_schema["customerInfo"]["scores"]["redZone"]["score"] = redzone_customer_level.get("modelScore", [])[0][
        "riskScore"
    ]
    new_schema["customerInfo"]["scores"]["redZone"]["modelReasons"] = redzone_customer_level.get("modelReasons", [])
    new_schema["customerInfo"]["scores"]["repeat"]["score"] = repeat_customer_level.get("modelScore", [])[0][
        "repeatScore"
    ]
    new_schema["customerInfo"]["scores"]["repeat"]["modelReasons"] = repeat_customer_level.get("modelReasons", [])
    new_schema["customerInfo"]["scores"]["loanPaidOff"]["score"] = loanPaidOff_customer_level.get("modelScore", [])[0][
        "totalLoanPaidOffScore"
    ]
    new_schema["customerInfo"]["scores"]["loanPaidOff"]["modelReasons"] = loanPaidOff_customer_level.get(
        "modelReasons", []
    )
    new_schema["customerInfo"]["scores"]["isBad"]["score"] = isBad_customer_level.get("modelScore", [])[0]["isBadScore"]
    new_schema["customerInfo"]["scores"]["isBad"]["modelReasons"] = isBad_customer_level.get("modelReasons", [])

    # lendingGuide
    new_schema["customerInfo"]["lendingGuide"] = output_json.get("lendingGuide", {})

    # recommendedBankAccount
    new_schema["customerInfo"]["recommendedBankAccount"] = additionalInfo.get("recommendedBankAccount", "")

    # redZoneBehavior
    new_schema["customerInfo"]["redZoneBehavior"] = additionalInfo.get("redZoneBehaviorCustomer", [])[0]

    # mdoelVersion
    new_schema["modelVersion"] = output_json.get("modelVersion", "")

    # Convert defaultdict back to a regular dict
    new_schema["accountInfo"] = dict(new_schema["accountInfo"])

    return new_schema
