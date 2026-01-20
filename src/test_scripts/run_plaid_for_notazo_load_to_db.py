import sys
from model.run_model import run_model
from config import config
import os
import json
import warnings
import pandas as pd
import pyodbc
from datetime import datetime
warnings.filterwarnings("ignore")


def asOfDate_compatible(json_str):
    try:
        data = json.loads(json_str)
        if "asOfDate" not in data:
            transactions_df = pd.DataFrame.from_dict(data['transactions'])
            # New feature as of date
            transactions_df[config.IA_DATE] = pd.to_datetime(transactions_df[config.IA_DATE]).dt.date
            asOfDate = str(transactions_df[config.IA_DATE].max())
            data['asOfDate'] = asOfDate
        return json.dumps(data)
    except json.JSONDecodeError as e:
        return print(e)


data_input_path = sys.argv[1]
filename = (os.path.basename(data_input_path))

try:
    with open(data_input_path) as f:
        json_str = f.read()
except FileNotFoundError:
    print(f"File not found: {data_input_path}")

print(filename)
if (config.PRINT_TIMESTAMPS):
    print("*" * 20)

if (config.PRINT_TIMESTAMPS):
    print("(run_plaid_for_notazo_load_to_db.py: Call Model with JSON input) Start time: ",
          datetime.utcnow().isoformat(sep=' ', timespec='milliseconds'))

json_str = asOfDate_compatible(json_str)

output_final = run_model(json_str)

if (config.PRINT_TIMESTAMPS):
    print("(run_plaid_for_notazo_load_to_db.py: Call Model with JSON input) End time: ",
          datetime.utcnow().isoformat(sep=' ', timespec='milliseconds'))

# ############## load to db ###############

temp_lst = [filename, output_final]

# print(temp_lst)


output_table = "[AzureDB].[dbo].[Income_model_outputs_json_plaid] "

connStr = pyodbc.connect(
    'Driver={ODBC Driver 17 for SQL Server};SERVER=MDLTESTBED01;DATABASE=AzureDB;UID=azureuser;PWD=$trongM0del413')
cursor = connStr.cursor()


# Insert into EvaluationsJSON
sql = (
    "Insert Into [AzureDB].[dbo].[Income_model_outputs_json_plaid] (filename, output_json)" "VALUES (?, ?);")

# print(sql)
# print("*"*20)

if (config.PRINT_TIMESTAMPS):
    print("(run_plaid_for_notazo_load_to_db.py: JSON DB Insert) Start time: ",
          datetime.utcnow().isoformat(sep=' ', timespec='milliseconds'))

cursor.execute(sql, temp_lst)
connStr.commit()
cursor.close()
connStr.close()
if (config.PRINT_TIMESTAMPS):
    print('successfully inserted data')

if (config.PRINT_TIMESTAMPS):
    print("(run_plaid_for_notazo_load_to_db.py: JSON DB Insert) End time: ",
          datetime.utcnow().isoformat(sep=' ', timespec='milliseconds'))
