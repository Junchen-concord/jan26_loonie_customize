import os
import socket

import joblib
import numpy as np

from config.preload import create_category_patterns, load_holidays, load_ner_model

hostname = socket.gethostname()
if hostname == "MDLTESTBED01" or hostname == "NJ-CB-DEV-VH1":
    PRINT_TIMESTAMPS = True
else:
    PRINT_TIMESTAMPS = False

ROOT_DIR = os.path.realpath(os.path.join(os.path.dirname(__file__), ".."))

################
# Version
################
VERSION_FILE_PATH = os.path.realpath(os.path.join(ROOT_DIR, "version", "version.txt"))
version_file = open(VERSION_FILE_PATH, "r")
MODEL_VERSION = version_file.readline().strip()
version_file.close()

################
# Preprocessing
################

FEATURES_FIRSTNAME_DATA_FILE = os.path.realpath(os.path.join(ROOT_DIR, "dataset", "common_first_names.csv"))
FEATURES_LASTNAME_DATA_FILE = os.path.realpath(os.path.join(ROOT_DIR, "dataset", "common_last_names.csv"))

#############################
# Config for Income Analyzer
#############################

# Data location
IA_TRAINING_DATA_FILE = "C:/CIPModels/PythonService/IAModel/datasets/HandLabelChirp_20230801.csv"
IA_TESTING_DATA_FILE = "C:/CIPModels/PythonService/IAModel/datasets/HandLabelChirp_20230801.csv"

# Column names
IA_CUSTOMER_ID = "accountGuid"
IA_TXN_ID = "GUID"
IA_ACCOUNT_ID = "accountGuid"
IA_TXN_SHORT = "description"
IA_DATE = "date"
IA_TXN_DATE = "date"
IA_ORIGINAL_DESCRIPTION = "originalDescription"
IA_TXN_DESCRIPTION = "originalDescription"
IA_AMOUNT = "amount"
IA_TXN_AMOUNT = "amount"
IA_TYPE = "type"
IA_LABEL = "is_payroll"
IA_START_DATE = "start_date"
IA_END_DATE = "end_date"
IA_CATEGORY = "category"
IA_AS_OF_DATE = "asOfDate"

TRANS_CATEGORY = "transCategory"
TRANS_GUID = "transGUID"

# Model parameters
IA_TRAIN_TEST_SPLIT = 0.8
IA_VOCABULARY = None

# Estimator name
IA_ESTIMATOR_NAME = "xgb"

# Custom Model Endpoint
CUSTOM_MODEL_BASE_URL = os.environ.get("CUSTOM_MODEL_BASE_URL", default=None)

# Save path
IA_TRAINED_MODEL_DIR = os.path.realpath(os.path.join(ROOT_DIR, "model", "pkl"))
IA_MODEL_NAME = "multi_cat_model"
IA_MODEL_SAVE_FILE = f"{IA_MODEL_NAME}"
IA_MODEL_FILE_PATH = f"{IA_TRAINED_MODEL_DIR}" "/" f"{IA_MODEL_SAVE_FILE}" ".pkl"
IA_MULTI_CAT_MODEL_COMPONENTS = joblib.load(IA_MODEL_FILE_PATH)
IA_CVR_FILE_PATH = f"{IA_TRAINED_MODEL_DIR}" "/Count_vectorizer_raw.pkl"
IA_VISUALIZATION_OUTPUT_PATH = "evaluation"
IA_CONFUSION_MATRIX_PATH = os.path.join(
    IA_TRAINED_MODEL_DIR,
    IA_VISUALIZATION_OUTPUT_PATH,
    "validation_confusion_matrix.png",
)
IA_FALSE_POSITIVES_PATH = os.path.join(IA_TRAINED_MODEL_DIR, IA_VISUALIZATION_OUTPUT_PATH, "false_positives.csv")
IA_FALSE_NEGATIVES_PATH = os.path.join(IA_TRAINED_MODEL_DIR, IA_VISUALIZATION_OUTPUT_PATH, "false_negatives.csv")

# Tuning parameters
# IA_OBJECTIVE = 'binary:logistic'
IA_OBJECTIVE = "multi:softmax"
IA_EVAL_METRIC = "auc"
IA_SILENT = 1
IA_TREE_METHOD = "approx"
IA_SCALE_POS_WEIGHT = (1, 3)
IA_N_ESTIMATORS = (5, 20)
IA_LEARNING_RATE = (0.01, 1.0, "log-uniform")
IA_MIN_CHILD_WEIGHT = (1, 10)
IA_MAX_DEPTH = (2, 6)
IA_MAX_DELTA_STEP = (0, 20)
IA_SUBSAMPLE = (0.5, 1.0, "uniform")
IA_COLSAMPLE_BYTREE = (0.5, 1.0, "uniform")
IA_COLSAMPLE_BYLEVEL = (0.5, 1.0, "uniform")
IA_N_GRAM_RANGE = ["(1,1)", "(1,2)", "(2,2)"]
IA_MIN_DF = (1, 10)
IA_MAX_FEATURES = (1000, 10000)
IA_REG_ALPHA = (0.01, 1, "log-uniform")
IA_SCORING = "f1_micro"
IA_CV = 5
IA_N_JOBS = -1
IA_N_ITER = 10
IA_N_FOLD = 5
IA_VERBOSE = 10
IA_REFIT = True
IA_RANDOM_STATE = 0
IA_REG_ALPHA = (1e-9, 1.0, "log-uniform")

# Seed
IA_RANDOM_SEED = 1129

# Inference
IA_THRESHOLD = 0.85

# Clustering
IA_MAX_DISTANCE = 0.3

#############################
# Config for Loan Analyzer
#############################

# Data location
LA_TRAINING_DATA_FILE = "C:/CIPModels/PythonService/IAModel/datasets/V15_train_360account_mostcomplete.csv"
LA_TESTING_DATA_FILE = "C:/CIPModels/PythonService/IAModel/datasets/76sampleaccount.csv"

# Column names
LA_CUSTOMER_ID = "accountGuid"
LA_TXN_ID = "GUID"
LA_ACCOUNT_ID = "accountGuid"
LA_TXN_SHORT = "description"
LA_DATE = "date"
LA_TXN_DATE = "date"
LA_ORIGINAL_DESCRIPTION = "originalDescription"
LA_TXN_DESCRIPTION = "originalDescription"
LA_AMOUNT = "amount"
LA_TXN_AMOUNT = "amount"
LA_TYPE = "type"
LA_LABEL = "is_loan"
LA_START_DATE = "start_date"
LA_END_DATE = "end_date"

# Model parameters
LA_TRAIN_TEST_SPLIT = 0.8
LA_VOCABULARY = None

# Estimator name
LA_ESTIMATOR_NAME = "xgb"

# Save path
LA_TRAINED_MODEL_DIR = os.path.realpath(os.path.join(ROOT_DIR, "model", "pkl"))
LA_MODEL_NAME = "loan_prediction_chirp"
LA_MODEL_SAVE_FILE = f"{LA_MODEL_NAME}_output_v1"
LA_MODEL_FILE_PATH = f"{LA_TRAINED_MODEL_DIR}" "/" f"{LA_MODEL_SAVE_FILE}" ".pkl"
LA_CVR_FILE_PATH = f"{LA_TRAINED_MODEL_DIR}" "/Count_vectorizer_raw.pkl"
LA_VISUALIZATION_OUTPUT_PATH = "evaluation"
LA_CONFUSION_MATRIX_PATH = os.path.join(
    LA_TRAINED_MODEL_DIR,
    LA_VISUALIZATION_OUTPUT_PATH,
    "validation_confusion_matrix.png",
)
LA_FALSE_POSITIVES_PATH = os.path.join(LA_TRAINED_MODEL_DIR, LA_VISUALIZATION_OUTPUT_PATH, "false_positives.csv")
LA_FALSE_NEGATIVES_PATH = os.path.join(LA_TRAINED_MODEL_DIR, LA_VISUALIZATION_OUTPUT_PATH, "false_negatives.csv")

# Tuning parameters
LA_OBJECTIVE = "binary:logistic"
LA_EVAL_METRIC = "auc"
LA_SILENT = 1
LA_TREE_METHOD = "approx"
LA_SCALE_POS_WEIGHT = (1, 3)
LA_N_ESTIMATORS = (5, 20)
LA_LEARNING_RATE = (0.01, 1.0, "log-uniform")
LA_MIN_CHILD_WEIGHT = (1, 10)
LA_MAX_DEPTH = (2, 6)
LA_MAX_DELTA_STEP = (0, 20)
LA_SUBSAMPLE = (0.5, 1.0, "uniform")
LA_COLSAMPLE_BYTREE = (0.5, 1.0, "uniform")
LA_COLSAMPLE_BYLEVEL = (0.5, 1.0, "uniform")
LA_N_GRAM_RANGE = ["(1,1)", "(1,2)", "(2,2)"]
LA_MIN_DF = (1, 10)
LA_MAX_FEATURES = (1000, 10000)
LA_REG_ALPHA = (0.01, 1, "log-uniform")
LA_SCORING = "roc_auc"
LA_CV = 5
LA_N_JOBS = 1
LA_N_ITER = 10
LA_N_FOLD = 5
LA_VERBOSE = 10
LA_REFIT = True
LA_RANDOM_STATE = 0
LA_REG_ALPHA = (1e-9, 1.0, "log-uniform")

# Seed
LA_RANDOM_SEED = 1129

# Inference
LA_THRESHOLD = 0.85

# Clustering
LA_MAX_DISTANCE = 0.3

##############################
# Config for Transfer Analyzer
##############################

# Data location
TA_TRAINING_DATA_FILE = "C:/CIPModels/PythonService/IAModel/datasets/HandLabelChirp_20230801.csv"
TA_TESTING_DATA_FILE = "C:/CIPModels/PythonService/IAModel/datasets/HandLabelChirp_20230801.csv"

# Column data
TA_CUSTOMER_ID = "accountGuid"
TA_TXN_ID = "GUID"
TA_DATE = "date"
TA_ORIGINAL_DESCRIPTION = "originalDescription"
TA_AMOUNT = "amount"
TA_TYPE = "type"
TA_LABEL = "is_transfer"
TA_SUB_LABEL = "transfer_subcategory"

# Model parameters
TA_TRAIN_TEST_SPLIT = 0.8
TA_N_GRAM_RANGE = (1, 2)
TA_MIN_DF = 5
TA_MAX_FEATURES = 5000
TA_VOCABULARY = None

# Save path
TA_TRAINED_MODEL_DIR = os.path.realpath(os.path.join(ROOT_DIR, "model", "pkl"))
TA_MODEL_NAME = "transfer_prediction_chirp"
TA_MODEL_SAVE_FILE = f"{TA_MODEL_NAME}_output_v1"
TA_SUB_CATEGORY_MODEL_SAVE_FILE = "transfer_subcategory_prediction_chirp_output_v1"
TA_MODEL_FILE_PATH = f"{TA_TRAINED_MODEL_DIR}" "/" f"{TA_MODEL_SAVE_FILE}" ".pkl"
TA_SUB_CATEGORY_MODEL_FILE_PATH = f"{TA_TRAINED_MODEL_DIR}" "/transfer_subcategory_prediction_chirp_output_v1.pkl"
TA_CVR_FILE_PATH = f"{TA_TRAINED_MODEL_DIR}" "/Count_vectorizer_raw.pkl"
TA_VISUALIZATION_OUTPUT_PATH = "evaluation"
TA_CONFUSION_MATRIX_PATH = os.path.join(
    TA_TRAINED_MODEL_DIR,
    TA_VISUALIZATION_OUTPUT_PATH,
    "validation_confusion_matrix.png",
)
TA_FALSE_POSITIVES_PATH = os.path.join(TA_TRAINED_MODEL_DIR, TA_VISUALIZATION_OUTPUT_PATH, "false_positives.csv")
TA_FALSE_NEGATIVES_PATH = os.path.join(TA_TRAINED_MODEL_DIR, TA_VISUALIZATION_OUTPUT_PATH, "false_negatives.csv")

# Tuning parameters
TA_OBJECTIVE = "binary:logistic"
TA_EVAL_METRIC = "auc"
TA_SILENT = 1
TA_TREE_METHOD = "approx"
TA_SCALE_POS_WEIGHT = 1
TA_N_ESTIMATORS = (5, 20)
TA_LEARNING_RATE = (0.01, 1.0, "log-uniform")
TA_MIN_CHILD_WEIGHT = (1, 10)
TA_MAX_DEPTH = (2, 6)
TA_MAX_DELTA_STEP = (0, 20)
TA_SUBSAMPLE = (0.5, 1.0, "uniform")
TA_COLSAMPLE_BYTREE = (0.5, 1.0, "uniform")
TA_COLSAMPLE_BYLEVEL = (0.5, 1.0, "uniform")
TA_SCORING = "roc_auc"
TA_CV = 5
TA_N_JOBS = 4
TA_N_ITER = 3
TA_VERBOSE = 0
TA_REFIT = True
TA_RANDOM_STATE = 0
TA_REG_ALPHA = (1e-9, 1.0, "log-uniform")
TA_SCORING_SUBCATEGORY = "balanced_accuracy"
TA_OBJECTIVE_SUBCATEGORY = "multi:softmax"
TA_EVAL_METRIC_SUBCATEGORY = "merror"

# Inference
TA_MAIN_THRESHOLD = 0.5
TA_SUB_THRESHOLD = 0.5

########################
# Five Category Stacking
########################

# Load standard scaler and stacking model
FS_TRAINED_MODEL_DIR = os.path.realpath(os.path.join(ROOT_DIR, "model", "pkl"))
FS_MODEL_NAME = "stacking_model"
FS_MODEL_SAVE_FILE = f"{FS_MODEL_NAME}_v2_1"
FS_MODEL_FILE_PATH = f"{FS_TRAINED_MODEL_DIR}" "/" f"{FS_MODEL_SAVE_FILE}" ".pkl"
FS_SCALER_MODEL_NAME = "standardscaler"
FS_SCALER_MODEL_SAVE_FILE = f"{FS_SCALER_MODEL_NAME}_v2_1"
FS_SCALER_MODEL_FILE_PATH = f"{FS_TRAINED_MODEL_DIR}" "/" f"{FS_SCALER_MODEL_SAVE_FILE}" ".pkl"

FS_LOAN_TO_PAYROLL = [r"\bpayroll\b", r"\bpayrol\b", r"\blogistics\b"]
FS_LOAN_TO_OHTERS_CREDIT = [
    r"\brefund\b",
    r"\badjust\b",
    r"\breturn\b",
    r"\breversal\b",
    r"\brebate\b",
    r"\breverse\b",
    r"\btreas\b",
    r"\bpaychec\b",
    r"\bzelle\b",
    r"\bvenmo\b",
    r"\bpaypal\b",
    r"\bmember\b",
    r"\bpayrol\b",
    r"\bpurchase\b",
    r"\bhealth\b",
    r"\binsurance\b",
    r"\bcash app\b",
    r"\buber\b",
    r"\blyft\b",
    r"\bvia\b",
    r"\batm\b",
    r"\bdividen\b",
    r"\boverdraft\b",
    r"\bsufficient\b",
    r"\breturn payment\b",
    r"\bfee\b",
    r"\bshop\b",
    r"\bbread\b",
    r"\bpizza\b",
    r"\bfood\b",
    r"\bchick\b",
    r"\bpurchase\b",
    r"\bnsf\b",
    r"\b'credit\s*card\b",
    r"\bsports\b",
    r"\bcash\s*back\b",
    r"\bmobile\b",
    r"\bsharedpour\b",
    r"\bwknare\b",
    r"\bdispute\b",
    r"\bresume\b",
    r"\bincome\b",
    r"\bmembership\b",
    r"\bsubscript\b",
    r"\bvideo\b",
    r"\byoutube\b",
    r"\bamazon\b",
    r"\bwalmart\b",
    r"\bameritrade\b",
    r"\b'adore\b",
    r"\bapple\b",
    r"\bhellofresh\b",
    r"\bbark\b",
    r"\bpenara\b",
    r"\bparamount\b",
]

FS_TRANSFER_KWDS = [
    r"\bcash app\b",
    r"\bvenmo\b",
    r"\bpaypal\b",
    r"\bapple pay\b",
    r"\bcheck deposit\b",
    r"\bmobile deposit\b",
    r"\bcash deposit\b",
    r"\batm\b",
    r"\bonline deposit\b",
    r"\bedeposit\b",
    r"\bremote deposit\b",
]
FS_NOT_TRANSFER_KWDS = [
    r"\bdir\b",
    r"\bach\b",
    r"\bfee\b",
    r"\breturn\b",
    r"^(?=.*\brefund\b)(?!.*\btax\b).*$",
]
FS_LOAN_BRANDS = []
FS_NOT_LOAN_KWDS = []

GIG_MIN_AMOUNT = 50
GIG_KEYWORDS = [
    r"\buber",
    r"door.?dash",
    r"grub.?hub",
    r"\blyft",
    r"ubereats",
    r"insta.?cart",
    r"post.?mate",
    r"go.?puff",
]
NOT_GIG_KEYWORDS = [
    r"adj",
    r"return",
    r"rtn",
    r"revers",
    r"refund",
    r"rebat",
    r"fee",
]
FS_BENEFIT_DATA_FILE = os.path.realpath(os.path.join(ROOT_DIR, "config", "benefit_list.csv"))
FS_LOAN_DATA_FILE = os.path.realpath(os.path.join(ROOT_DIR, "config", "loan_list.csv"))

###############
# PostProcess
###############

# Recency
PS_RECENCY_CHECK_W = 10
PS_RECENCY_CHECK_B = 18
PS_RECENCY_CHECK_S = 18
PS_RECENCY_CHECK_M = 35
PS_RECENCY_CHECK = 30

# Amount
PS_LOW_AMOUNT_CHECK = 10

PS_ACCOUNT_ID = "accountGuid"
PS_TXN_ID = "guid"
PS_START_DATE = "start_date"
PS_END_DATE = "end_date"
PS_TXN_DATE = "date"
PS_TXN_DESCRIPTION = "originalDescription"
PS_TXN_SHORT = "description"
PS_TXN_AMOUNT = "amount"

PS_FEATURES = [
    PS_ACCOUNT_ID,
    PS_TXN_ID,
    PS_START_DATE,
    PS_END_DATE,
    PS_TXN_DATE,
    PS_TXN_DESCRIPTION,
    PS_TXN_SHORT,
    PS_TXN_AMOUNT,
]

PS_DATE_VARS = [PS_START_DATE, PS_END_DATE, PS_TXN_DATE]

# For the intial model, precision is more important than recall, that is, we should be at least confident about
# what we predicted as loan/payroll/transfer.
# So use a high threshold for model, but please understand that this is not a fix for everything.
PS_MAX_DISTANCE = 0.5
POS_PAYROLL_THRESHOLD = 0.5
POS_LOAN_THRESHOLD = 0.6
POS_TRANSFER_THRESHOLD = 0.6
# POS_LOAN_MIN_ORIGINATION_AMOUNT = 50
POS_LOAN_MIN_AMOUNT = 50
# POS_LOAN_MIN_PAYMENT_AMOUNT = 50

# For generating alerts and insights
LOW_TOTAL_CREDIT = 6000
HIGH_TOTAL_CREDIT = 15000
LOW_MONTHLY_INCOME = 0
LOW_NUM_PAYMENT = 0
GOOD_INCOME_HISTORY = 30
LOW_LOAN_PAYMENT = 0
LOW_NUM_ORIGINATIONS = 0
# LOW_REDZONE_SCORE = 95  # Speedy's threshold
HIGH_TOTAL_DEBITS = 50000

# Redzone and Alerts model config
REDZONE_TRAINED_MODEL_DIR = os.path.realpath(os.path.join(ROOT_DIR, "model", "pkl"))
REDZONE_MODEL_NAME = "Speedy_RedZone_model_V16.pkl"
REDZONE_MODEL_FILE_PATH = os.path.join(REDZONE_TRAINED_MODEL_DIR, REDZONE_MODEL_NAME)

REDZONE_MODEL_NAME_CM = "CashMax_RedZone_model_2024.pkl"
REDZONE_MODEL_FILE_PATH_CM = os.path.join(REDZONE_TRAINED_MODEL_DIR, REDZONE_MODEL_NAME_CM)

REDZONE_MODEL_FILE_PATH_V2 = os.path.join(
    os.path.realpath(os.path.join(ROOT_DIR, "model")), "autogluon_models_FPDAA_20250904_010918"
)
CALIBRATOR_DATA_PATH = os.path.realpath(os.path.join(ROOT_DIR, "model", "redzone_calibrator_data.pkl"))

# Repeat Model file Path
REPEAT_TRAINED_MODEL_DIR = os.path.realpath(os.path.join(ROOT_DIR, "model", "model_jsons"))
REPEAT_MODEL_NAME = "xgb_model_onboarding2repeat.json"
REPEAT_MODEL_FILE_PATH = os.path.join(REPEAT_TRAINED_MODEL_DIR, REPEAT_MODEL_NAME)
REPEAT_MODEL_LOW_THRESHOLD = 150
REPEAT_MODEL_HIGH_THRESHOLD = 215

# TotalLoanPaidOff Model file Path
TOTALLOANPAIDOFF_TRAINED_MODEL_DIR = os.path.realpath(os.path.join(ROOT_DIR, "model", "pkl"))
TOTALLOANPAIDOFF_MODEL_NAME = "Speedy_RedZone_model_TotalLoanPaidOff.pkl"
TOTALLOANPAIDOFF_MODEL_FILE_PATH = os.path.join(TOTALLOANPAIDOFF_TRAINED_MODEL_DIR, TOTALLOANPAIDOFF_MODEL_NAME)

# IsBad Model file Path
ISBAD_TRAINED_MODEL_DIR = os.path.realpath(os.path.join(ROOT_DIR, "model", "pkl"))
ISBAD_MODEL_NAME = "Speedy_RedZone_model_IsBad_V2.pkl"
ISBAD_MODEL_FILE_PATH = os.path.join(ISBAD_TRAINED_MODEL_DIR, ISBAD_MODEL_NAME)

# Underwritable income config

# Withdrawn model for agent agreement chance
WITHDRAWN_MODEL_PATH = os.path.realpath(
    os.path.join(ROOT_DIR, "model", "model_jsons/agent_withdrawn_chance_model.json")
)

# Active check
LATEST_INCOME_DATE = 35
INCOME_DROP_TOLERANCE = 0.5
INCOME_HISTORY_M = 30
INCOME_HISTORY_B = 30
INCOME_HISTORY_W = 30
INCOME_HISTORY_I = 45
MISSING_PAYMENT_DAY_TOLERANCE = 35
# Correct gap threshold for monthly benefits should be 39, but just to be safe
MISSING_PAYMENT_DAY_TOLERANCE_M = 40

# Recurring check
SAME_DAY_FREQ_TOLERANCE = 0.75
DEBIT_DIFF_DATE_TOLERENCE = 3
CLOSE_DAY_DEBIT_TOLERANCE = 0.75
MINIMUM_N_PAYDAYS_FOR_FREQ_I_HAVE_REGULAR_PAYDAY = 4

# Amount stability check
MINIMUM_N_PAYS_M = 2
MINIMUM_N_PAYS_B = 2
MINIMUM_N_PAYS_W = 2
MINIMUM_N_PAYS_I = 4
LOW_STD = 0.33
MEDIUM_STD = 0.5

# Minimal Appearance for ignoring smaller amounts
MINIMUM_N_PAYS_AMOUNT_TWEAK_M = 4

# Knowledge base settings
USE_REGEX_KNOWLEDGE_BASE = True
USE_NER_KNOWLEDGE_BASE = True
PRINT_REPORT = True
CATEGORY_COLUMN_NAME = "category"
ENTITY_COLUMN_NAME = "entity"
FROM_MODEL = "fromModel"
KNOWLEDGEBASE_DATA_PATH = os.path.realpath(os.path.join(ROOT_DIR, "config", "knowledge_base_proto.csv"))
NER_KNOWLEDGEBASE_DATA_PATH = os.path.realpath(os.path.join(ROOT_DIR, "config", "knowledge_base_hashmap.pkl"))
NER_SOURCE_MAP_PATH = os.path.realpath(os.path.join(ROOT_DIR, "config", "source_map.pkl"))
CATEGORY_PATTERNS = create_category_patterns()

# Holidays
HOLIDAYS_PATH = os.path.realpath(os.path.join(ROOT_DIR, "dataset", "holidays.csv"))
HOLIDAYS = load_holidays(HOLIDAYS_PATH)

# NER
NER_MODEL_PATH = os.path.realpath(os.path.join(ROOT_DIR, "model", "model-best_NER_who_sub"))
NLP_MODEL = load_ner_model(NER_MODEL_PATH)
WHO_COL = "WHO"
HOW_COL = "HOW"
WHAT_COL = "WHAT"
WHO_CAT_COL = "WHO_cat"
WHO_SOURCE = "who_source"

SOURCE_NAME = "sourceName"

# predict_transaction.py
STACKING_PREDICTION = "StackingPrediction"
CLUSTER_LABEL = "cluster_label"
PROCESSED_CLUSTERING = "processed_clustering"
IBV_CATEGORY = "ibvCategory"
ID = "id"
TRANSACTION_FIELDS = [
    ID,
    IA_ACCOUNT_ID,
    IA_TXN_ID,
    IA_DATE,
    IA_AMOUNT,
    IA_ORIGINAL_DESCRIPTION,
    IA_TXN_SHORT,
    IA_CATEGORY,
    IA_TYPE,
    FROM_MODEL,
    WHO_COL,
    WHO_CAT_COL,
    WHO_SOURCE,
    HOW_COL,
    WHAT_COL,
    STACKING_PREDICTION,
    CLUSTER_LABEL,
    PROCESSED_CLUSTERING,
    IBV_CATEGORY,
]

PROCESSED_N_GRAM = "processed_n_gram"
PROCESSED_KNOWLEDGE_BASE = "processed_knowledge_base"

# Common Labels
OTHER = "Other"

# Model Assessment Reasons
# TODO: the numbers a subject to change with a data test
REDZONE_INCOME_SOURCE_LIMIT = 3
ALL_TIME_MONTHLY_INCOME_POSITIVE_UPPER_LIMIT = 4000
ALL_TIME_MONTHLY_INCOME_POSITIVE_LOWER_LIMIT = 1000
INFLOW_UPPER_LIMIT = 5000
INFLOW_LOWER_LIMIT = 1250
OD_ALL_NEGATIVE_UPPER_LIMIT = 2
OD_ALL_NEGATIVE_LOWER_LIMIT = 0
AVERAGE_MONTHLY_BALANCE_ALL_POSITIVE_UPPER_LIMIT = 3000
AVERAGE_MONTHLY_BALANCE_ALL_POSITIVE_LOWER_LIMIT = 0
INCOME_HISTORY_ALL_TIME_POSITIVE_UPPER_LIMIT = 3
INCOME_HISTORY_ALL_TIME_POSITIVE_LOWER_LIMIT = 0
LOAN_PMT_ALL_TIME_POSITIVE_UPPER_LIMIT = 5000
LOAN_PMT_ALL_TIME_POSITIVE_LOWER_LIMIT = 0
RECURRING_MONTHLY_INCOME_POSITIVE_UPPER_LIMIT = 4000
RECURRING_MONTHLY_INCOME_POSITIVE_LOWER_LIMIT = 1000
INCOME_COUNT1_BENEFIT_POSITIVE_UPPER_LIMIT = 3
INCOME_COUNT1_BENEFIT_POSITIVE_LOWER_LIMIT = 0
ACTIVE_MONTHLY_INCOME_POSITIVE_UPPER_LIMIT = 4000
ACTIVE_MONTHLY_INCOME_POSITIVE_LOWER_LIMIT = 1000
TOTAL_DEBITS_POSITIVE_LOWER_LIMIT = 500
TOTAL_DEBITS_POSITIVE_UPPER_LIMIT = 500
INCOME_COUNT1_PAYROLL_POSITIVE_UPPER_LIMIT = 3
INCOME_COUNT1_PAYROLL_POSITIVE_LOWER_LIMIT = 0
TOTAL_TYPE_MONTHLY1_PAYROLL_POSITIVE_UPPER_LIMIT = 3000
TOTAL_TYPE_MONTHLY1_PAYROLL_POSITIVE_LOWER_LIMIT = 0
TOTAL_TYPE_MONTHLY1_BENEFIT_POSITIVE_UPPER_LIMIT = 3000
TOTAL_TYPE_MONTHLY1_BENEFIT_POSITIVE_LOWER_LIMIT = 0
NUM_OF_ORIGINATIONS_POSITIVE_LOWER_LIMIT = 5
NUM_OF_ORIGINATIONS_POSITIVE_UPPER_LIMIT = 5
NUM_OF_PAYS_POSITIVE_UPPER_LIMIT = 5
NUM_OF_PAYS_POSITIVE_LOWER_LIMIT = 0
ACTIVE_COUNT_1_POSITIVE_UPPER_LIMIT = 3
ACTIVE_COUNT_1_POSITIVE_LOWER_LIMIT = 0
ACTIVE_MONTHLY_1_POSITIVE_UPPER_LIMIT = 3000
ACTIVE_MONTHLY_1_POSITIVE_LOWER_LIMIT = 0
ATP_POSITIVE_UPPER_LIMIT = np.inf
ATP_POSITIVE_LOWER_LIMIT = 0
ATP_NEGATIVE_UPPER_LIMIT = np.inf
ATP_NEGATIVE_LOWER_LIMIT = 0

# For labeling at refresh
IA_LABELING_COLUMN = "StackingPrediction"

# N gram vocabulary
COMMON_WHO = [
    "earnin",
    "brigit",
    "dave inc",
    "instacash",
    "klover app boost",
    "usaa",
    "uber",
    "cleo",
    "earnin earnin",
    "floatme",
    "albert instant",
    "empower finance inc",
    "grubhub",
    "grid",
    "albert corporation",
    "lyft",
    "daily pay",
    "texas oag",
    "line financial",
    "sunshine loans",
    "klover plus",
    "constance s jones",
    "empower cash advance",
    "nicholas sheafer",
    "moneylion",
]
COMMON_HOW = [
    "deposit",
    "zelle",
    "online",
    "cash app",
    "home banking",
    "ach",
    "atm",
    "cash app cash out",
    "online banking",
    "direct dep",
    "visa direct",
    "venmo",
    "paypal",
    "mobile",
    "deposit ach",
    "internet",
    "real time transfer",
    "chime",
    "dir dep",
    "apple cash",
    "remote online deposit",
    "atm deposit",
    "real time payment",
    "cash app deposit",
    "self service transfer from share 01",
    "deposit visa direct",
    "signature credit",
    "debit card",
    "eb",
    "dailypay",
]
COMMON_WHY = [
    "transfer",
    "payment",
    "cash out",
    "pmnt rcvd",
    "keepthechange credit",
    "money transfer",
    "payroll",
    "cash",
    "credit",
    "return of posted check",
    "funds transfer",
    "funds",
    "round up checking",
    "deposit",
    "adjustment",
    "purchase return",
    "payment recover",
    "rtp",
    "cash deposit",
    "fund",
    "reversal",
    "xpay",
    "xfer credit",
    "rebate",
    "credit recd",
    "dailypay",
    "xfer",
    "check",
    "dividend",
    "income",
]

stopwords_nltk = [
    "the",
    "at",
    "weren",
    "our",
    "too",
    "nor",
    "both",
    "yours",
    "should've",
    "wouldn't",
    "it's",
    "had",
    "same",
    "themselves",
    "doesn't",
    "itself",
    "above",
    "didn't",
    "here",
    "few",
    "than",
    "ve",
    "down",
    "are",
    "to",
    "where",
    "because",
    "couldn",
    "you'd",
    "m",
    "don't",
    "shouldn't",
    "were",
    "this",
    "no",
    "does",
    "over",
    "most",
    "hers",
    "shouldn",
    "theirs",
    "haven't",
    "they",
    "some",
    "you're",
    "yourselves",
    "during",
    "off",
    "you've",
    "y",
    "isn't",
    "your",
    "me",
    "i",
    "him",
    "hadn't",
    "why",
    "wasn",
    "isn",
    "mightn",
    "is",
    "how",
    "that",
    "with",
    "don",
    "wouldn",
    "do",
    "ll",
    "am",
    "if",
    "d",
    "did",
    "haven",
    "will",
    "having",
    "only",
    "re",
    "ours",
    "she",
    "again",
    "didn",
    "further",
    "ma",
    "won't",
    "in",
    "ourselves",
    "shan",
    "and",
    "you",
    "aren't",
    "has",
    "them",
    "then",
    "for",
    "through",
    "these",
    "aren",
    "should",
    "doesn",
    "hasn't",
    "until",
    "or",
    "he",
    "but",
    "any",
    "so",
    "can",
    "now",
    "o",
    "couldn't",
    "her",
    "from",
    "all",
    "whom",
    "shan't",
    "needn",
    "wasn't",
    "what",
    "mightn't",
    "between",
    "as",
    "herself",
    "ain",
    "himself",
    "we",
    "other",
    "against",
    "those",
    "more",
    "on",
    "by",
    "out",
    "you'll",
    "own",
    "s",
    "under",
    "it",
    "up",
    "when",
    "a",
    "myself",
    "be",
    "just",
    "been",
    "into",
    "my",
    "who",
    "hadn",
    "an",
    "won",
    "there",
    "not",
    "once",
    "before",
    "their",
    "have",
    "mustn",
    "hasn",
    "its",
    "that'll",
    "his",
    "after",
    "weren't",
    "which",
    "doing",
    "such",
    "mustn't",
    "very",
    "needn't",
    "about",
    "t",
    "each",
    "of",
    "while",
    "yourself",
    "being",
    "below",
    "she's",
    "was",
]
STOPWORDS = set(stopwords_nltk)

STATE_ABBR = [
    "AL",
    "AK",
    "AZ",
    "AR",
    "CA",
    "CO",
    "CT",
    "DE",
    "DC",
    "FL",
    "GA",
    "HI",
    "ID",
    "IL",
    "IN",
    "IA",
    "KS",
    "KY",
    "LA",
    "ME",
    "MD",
    "MA",
    "MI",
    "MN",
    "MS",
    "MO",
    "MT",
    "NE",
    "NV",
    "NH",
    "NJ",
    "NM",
    "NY",
    "NC",
    "ND",
    "OH",
    "OK",
    "OR",
    "PA",
    "PR",
    "RI",
    "SC",
    "SD",
    "TN",
    "TX",
    "UT",
    "VT",
    "VA",
    "VI",
    "WA",
    "WV",
    "WI",
    "WY",
]

IRRELEVANT_WORDS = [
    "LongDigits",
    "StateAbbr",
    "CITYABBR",
    "CONFNUMBER",
    "FourDigits",
    "ExLongDigits",
    "card",
    "dir",
    "payroll",
    "salary",
    "orig",  # Originating company name
    "entry",
    "descr",  # Entry Description
    "sec",  # Standard entry class code
    "inc",
    "debit",
    "payment",
    "authorized",
    "transfer",
    "ppd",
    "credit",
    "des",
    "indn",
    "checkcard",
    "recurring",
    "web",
    "deposit",
    "purchase",
    "direct",
    "san",
    "ach",
    "com",
    "pos",
    "withdrawal",
    "visa",
    "funds",
    "pmnt",
    "rcvd",
    "ref",
    "online",
    "pmt",
    "check",
    "fee",
    "plus",
    "zelle",
    "paypal",
    "",
    "transaction",
    "llc",
    "balance",
    "xxx",
    "canceled",
    "xfer",
    "httpswww",
    "date",
    "texas",
    "dep",
    "fund",
    "banking",
    "pymt",
    "repayment",
    "name",
    "p2p",
    "st",
    "sent",
    "dbt",
    "checking",
    "crd",
    "insufficient",
    "recd",
    "rd",
    "interest",
    "recovery",
    "repaymen",
    "paymen",
    "bkofamerica",
    "category",
    "cc",
    "loanpaymnt",
    "reversal",
    "withdrwl",
    "pymnts",
    "repayme",
    "membership",
    "iid",
    "aba",
    "reference",
    "sq",
    "pm",
    "el",
    "dr",
    "edeposit",
    "electronic",
    "auth",
    "francisc",
    "loanpmt",
    "xpay",
    "preauthpmt",
    "uncollected",
    "membrshp",
    "debits",
    "on",
    "from",
    "to",
    "via",
    "jan",
    "feb",
    "mar",
    "apr",
    "may",
    "jun",
    "jul",
    "june",
    "july",
    "aug",
    "sep",
    "oct",
    "nov",
    "dec",
    "adjustment",
    "chk",
    "sav",
    "saving",
]
