import os
import subprocess

# Get the list of all files and directories
# all 2k Plaid customers
# path = "C:/CIPModels/Data/Plaid/PlaidTransactions/"
# sample JSONS for initial test after each version update
# path = "C:/CIPModels/Data/Plaid/Transactiontest/"
path = "C:/CIPModels/Data/Plaid/Transactions/"
# path = "C:/CIPModels/Data/Plaid/NDDPlaidTest-IRR/"
# plaid retro data path
# path = "C:/CIPModels/Data/Plaid/PlaidRetroTransactions/"
# path for DDPlaid
# path ="C:/CIPModels/Data/Plaid/DDPlaidTest-IA/"
# akshits test
# path= "C:/CIPModels/Data/Plaid/08242023/"
# sample JSONS for initial V15 model testing
# path = "C:/CIPModels/Data/Plaid/V15Transactions/"
pythonexe = "C:/Anaconda3/envs/MDLV16/python.exe"

dir_list = os.listdir(path)

# prints all files
# print(dir_list)


for file in dir_list:
    fullpath = path + str(file)
    # print("----------------------------------")
    # print(fullpath)
    # print("----------------------------------")

    command = (
        "C:/Anaconda3/envs/MDLV16/python.exe C:/CIPModels/PythonService/IAModelV16/test_scripts/run_plaid_for_notazo_load_to_db.py "
        + fullpath
    )

    # print("(PlaidIPMTestUtility) Start time: ", datetime.utcnow().isoformat(sep=' ', timespec='milliseconds'))
    result = subprocess.run(command, capture_output=True, text=True)
    print(result.stdout)
    print(result.stderr)
    # print("(PlaidIPMTestUtility) End time: ", datetime.utcnow().isoformat(sep=' ', timespec='milliseconds'))
