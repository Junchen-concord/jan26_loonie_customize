import os
import subprocess

# Get the list of all files and directories
# all 10k chirp customers
# path = "C:/CIPModels/Data/Chirp/ChirpTransactions/"
# sample JSONS for initial test after each version update
# path = "C:/CIPModels/Data/Chirp/Transactiontest/"
path = "C:/CIPModels/Data/Chirp/Transactions/"
# this is the test file to use on 10.11.5.6
# path="C:/CIPModels/Data/Chirp/ChirpTransactions-IA/"
# path="C:/CIPModels/Data/Chirp/ChirpTransactions-IRR/"
# sample JSONS for initial V15 model testing
# path = "C:/CIPModels/Data/Chirp/V15Transactions/"
dir_list = os.listdir(path)
pythonexe = "C:/Anaconda3/envs/MDLV16/python.exe"

# prints all files
# print(dir_list)


for file in dir_list:
    fullpath = path + str(file)
    # print("----------------------------------")
    # print(fullpath)
    # print("----------------------------------")

    command = (
        "C:/Anaconda3/envs/MDLV16/python.exe C:/CIPModels/PythonService/IAModelV16/test_scripts/run_chirp_for_notazo_load_to_db.py "
        + fullpath
    )

    result = subprocess.run(command, capture_output=True, text=True)
    print(result.stdout)
    print(result.stderr)
