import json
import os

from config import config
from model.run_model import run_model
from utils.utils import TimeFrame

file = "2000.json"


def test_model_all():
    abs_path = os.path.realpath(os.path.join(config.ROOT_DIR, "..", "tests", "data", file))
    with open(abs_path) as f:
        json_str = f.read()
    output = run_model(json_str, TimeFrame.ALL)
    output_final_dict = json.loads(output)
    debits = output_final_dict["debitTrans"]
    credits = output_final_dict["creditTrans"]
    transactions = len(debits) + len(credits)
    assert transactions == 2026


def test_model_6m():
    abs_path = os.path.realpath(os.path.join(config.ROOT_DIR, "..", "tests", "data", file))
    with open(abs_path) as f:
        json_str = f.read()
    output = run_model(json_str, TimeFrame.SIX_MONTH)
    output_final_dict = json.loads(output)
    debits = output_final_dict["debitTrans"]
    credits = output_final_dict["creditTrans"]
    transactions = len(debits) + len(credits)
    assert transactions == 1145


def test_model_3m():
    abs_path = os.path.realpath(os.path.join(config.ROOT_DIR, "..", "tests", "data", file))
    with open(abs_path) as f:
        json_str = f.read()
    output = run_model(json_str, TimeFrame.THREE_MONTH)
    output_final_dict = json.loads(output)
    debits = output_final_dict["debitTrans"]
    credits = output_final_dict["creditTrans"]
    transactions = len(debits) + len(credits)
    assert transactions == 575
