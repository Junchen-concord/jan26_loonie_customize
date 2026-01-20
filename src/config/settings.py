import os

from dotenv import load_dotenv

load_dotenv()


def get_env_var_as_bool(name, default=False):
    value = os.environ.get(name, str(default))
    return value.lower() in ["true", "1", "t", "yes", "y"]


def get_env_var_as_int(name, default=0):
    try:
        return int(os.environ.get(name, default))
    except Exception:
        return default


def get_env_var_as_float(name, default=0.0):
    try:
        return float(os.environ.get(name, default))
    except Exception:
        return default


# -------------- General Settings --------------
STAGE = os.environ.get("STAGE", default="prod")
PORT = os.environ.get("PORT", default="80")
PRINT_TIMESTAMPS_THRESHOLD = get_env_var_as_int("PRINT_TIMESTAMPS_THRESHOLD", default=100)

# -------------- Model Settings --------------
LOW_REDZONE_SCORE_CM = get_env_var_as_int("LOW_REDZONE_SCORE_CM", default=50)

# -------------- Lending Guide Settings --------------

PAYMENT_TO_REDZONE_MIN = get_env_var_as_float("PAYMENT_TO_REDZONE_MIN", default=0.843)
PAYMENT_TO_REDZONE_MAX = get_env_var_as_float("PAYMENT_TO_REDZONE_MAX", default=1.185)

LOAN_AMOUNT_TO_REDZONE_MIN = get_env_var_as_float("LOAN_AMOUNT_TO_REDZONE_MIN", default=2.988)
LOAN_AMOUNT_TO_REDZONE_MAX = get_env_var_as_float("LOAN_AMOUNT_TO_REDZONE_MAX", default=3.928)

LOAN_AMOUNT_MIN = get_env_var_as_int("LOAN_AMOUNT_MIN", default=300)
LOAN_AMOUNT_MAX = get_env_var_as_int("LOAN_AMOUNT_MAX", default=1000)
PAYMENT_AMOUNT_MIN = get_env_var_as_float("PAYMENT_AMOUNT_MIN", default=90)
PAYMENT_AMOUNT_MAX = get_env_var_as_float("PAYMENT_AMOUNT_MAX", default=300)

# -------------- Output Settings --------------
OUTPUT_FEATURES = get_env_var_as_bool("OUTPUT_FEATURES", default=True)
OUTPUT_APPLICATION_CHECK = get_env_var_as_bool("OUTPUT_APPLICATION_CHECK", default=True)
OUTPUT_REDZONE_EXPLANATION = get_env_var_as_bool("OUTPUT_REDZONE_EXPLANATION", default=False)
OUTPUT_ATP_FEATURES = get_env_var_as_bool("OUTPUT_ATP_FEATURES", default=False)
TREAT_BALANCE_TRANSFER_AS_INFLOW = get_env_var_as_bool("TREAT_BALANCE_TRANSFER_AS_INFLOW", default=True)

settings_dict = {
    "LOW_REDZONE_SCORE_CM": LOW_REDZONE_SCORE_CM,
    "OUTPUT_ATP_FEATURES": OUTPUT_ATP_FEATURES,
    "OUTPUT_REDZONE_EXPLANATION": OUTPUT_REDZONE_EXPLANATION,
    "TREAT_BALANCE_TRANSFER_AS_INFLOW": TREAT_BALANCE_TRANSFER_AS_INFLOW,
}
