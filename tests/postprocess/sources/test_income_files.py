import json
import os

import pytest
from config import config
from model.run_model import run_model
from utils.utils import TimeFrame

# Global variable to control saving results to notebooks folder
SAVE_RESULTS_TO_NOTEBOOKS = True

# Path to monthly test data
monthly_data_path = os.path.realpath(os.path.join(config.ROOT_DIR, "..", "tests", "data", "by_freq", "Monthly"))

# Path to biweekly test data
biweekly_data_path = os.path.realpath(os.path.join(config.ROOT_DIR, "..", "tests", "data", "by_freq", "Biweekly"))

# Path to weekly test data
weekly_data_path = os.path.realpath(os.path.join(config.ROOT_DIR, "..", "tests", "data", "by_freq", "Weekly"))

# Path to semimonthly test data
semimonthly_data_path = os.path.realpath(os.path.join(config.ROOT_DIR, "..", "tests", "data", "by_freq", "Semimonthly"))


def get_json_files(directory_path):
    """Get list of JSON files from directory."""
    full_path = os.path.realpath(os.path.join(config.ROOT_DIR, "..", directory_path))
    if not os.path.exists(full_path):
        return []
    return [os.path.join(full_path, f) for f in os.listdir(full_path) if f.endswith(".json")]


@pytest.mark.parametrize("json_file", get_json_files("tests/data/by_freq/Monthly")[:10])
def test_monthly_income_file(json_file):
    """
    Test individual monthly income JSON files from tests/data/by_freq/Monthly.
    This tests the new regular payday prediction patterns like 'near end of month' and 'near day X'.
    """
    with open(json_file, "r") as f:
        sample_input = json.load(f)

    # Run the complete model pipeline
    output = run_model(sample_input, TimeFrame.ALL)

    # Basic assertions
    assert output is not None, "Model output should not be None"
    assert isinstance(output, str), "Model output should be a JSON string"

    # Parse the output to extract income source information
    output_dict = json.loads(output)

    # Check that the output has the expected structure
    assert "incomeSources" in output_dict, "Output should contain incomeSources"

    income_sources = output_dict.get("incomeSources", [])

    # Validate payday prediction fields for monthly income sources
    for source in income_sources:
        if source.get("frequency") == "M":  # Monthly frequency
            # These fields should exist for monthly sources
            assert "regularPayDay" in source, "Monthly sources should have regularPayDay field"
            assert "nextPayDay" in source, "Monthly sources should have nextPayDay field"
            assert "paymentNearHoliday" in source, "Monthly sources should have paymentNearHoliday field"
            assert "nextPayDayOnHoliday" in source, "Monthly sources should have nextPayDayOnHoliday field"

            # Only check payday prediction logic when errorCode is 0 (successful processing)
            error_code = source.get("errorCode", -1)
            if error_code == 0:
                regular_payday = source.get("regularPayDay", "")
                if regular_payday and regular_payday != "None":
                    # The new patterns should be processed without errors
                    next_payday = source.get("nextPayDay")
                    assert (
                        next_payday != "None" or "near" in regular_payday
                    ), f"Should predict next payday for pattern: {regular_payday}"

    # Optional: Save results for analysis
    if SAVE_RESULTS_TO_NOTEBOOKS:
        save_test_result(json_file, output_dict)


@pytest.mark.parametrize("json_file", get_json_files("tests/data/by_freq/Biweekly")[:10])
def test_biweekly_income_file(json_file):
    """
    Test individual biweekly income JSON files from tests/data/by_freq/Biweekly.
    This tests biweekly payday prediction patterns and frequency handling.
    """
    with open(json_file, "r") as f:
        sample_input = json.load(f)

    # Run the complete model pipeline
    output = run_model(sample_input, TimeFrame.ALL)

    # Basic assertions
    assert output is not None, "Model output should not be None"
    assert isinstance(output, str), "Model output should be a JSON string"

    # Parse the output to extract income source information
    output_dict = json.loads(output)

    # Check that the output has the expected structure
    assert "incomeSources" in output_dict, "Output should contain incomeSources"

    income_sources = output_dict.get("incomeSources", [])

    # Validate payday prediction fields for biweekly income sources
    for source in income_sources:
        if source.get("frequency") == "B":  # Biweekly frequency
            # These fields should exist for biweekly sources
            assert "regularPayDay" in source, "Biweekly sources should have regularPayDay field"
            assert "nextPayDay" in source, "Biweekly sources should have nextPayDay field"
            assert "paymentNearHoliday" in source, "Biweekly sources should have paymentNearHoliday field"
            assert "nextPayDayOnHoliday" in source, "Biweekly sources should have nextPayDayOnHoliday field"

            # Only check payday prediction logic when errorCode is 0 (successful processing)
            error_code = source.get("errorCode", -1)
            if error_code == 0:
                regular_payday = source.get("regularPayDay", "")
                if regular_payday and regular_payday != "None":
                    # The biweekly patterns should be processed without errors
                    next_payday = source.get("nextPayDay")
                    assert next_payday != "None", f"Should predict next payday for biweekly pattern: {regular_payday}"

    # Optional: Save results for analysis
    if SAVE_RESULTS_TO_NOTEBOOKS:
        save_test_result(json_file, output_dict)


@pytest.mark.parametrize("json_file", get_json_files("tests/data/by_freq/Weekly")[:10])
def test_weekly_income_file(json_file):
    """
    Test individual weekly income JSON files from tests/data/by_freq/Weekly.
    This tests weekly payday prediction patterns and frequency handling.
    """
    with open(json_file, "r") as f:
        sample_input = json.load(f)

    # Run the complete model pipeline
    output = run_model(sample_input, TimeFrame.ALL)

    # Basic assertions
    assert output is not None, "Model output should not be None"
    assert isinstance(output, str), "Model output should be a JSON string"

    # Parse the output to extract income source information
    output_dict = json.loads(output)

    # Check that the output has the expected structure
    assert "incomeSources" in output_dict, "Output should contain incomeSources"

    income_sources = output_dict.get("incomeSources", [])

    # Validate payday prediction fields for weekly income sources
    for source in income_sources:
        if source.get("frequency") == "W":  # Weekly frequency
            # These fields should exist for weekly sources
            assert "regularPayDay" in source, "Weekly sources should have regularPayDay field"
            assert "nextPayDay" in source, "Weekly sources should have nextPayDay field"
            assert "paymentNearHoliday" in source, "Weekly sources should have paymentNearHoliday field"
            assert "nextPayDayOnHoliday" in source, "Weekly sources should have nextPayDayOnHoliday field"

            # Only check payday prediction logic when errorCode is 0 (successful processing)
            error_code = source.get("errorCode", -1)
            if error_code == 0:
                regular_payday = source.get("regularPayDay", "")
                if regular_payday and regular_payday != "None":
                    # The weekly patterns should be processed without errors
                    next_payday = source.get("nextPayDay")
                    assert next_payday != "None", f"Should predict next payday for weekly pattern: {regular_payday}"

    # Optional: Save results for analysis
    if SAVE_RESULTS_TO_NOTEBOOKS:
        save_test_result(json_file, output_dict)


@pytest.mark.parametrize("json_file", get_json_files("tests/data/by_freq/Semimonthly")[:10])
def test_semimonthly_income_file(json_file):
    """
    Test individual semimonthly income JSON files from tests/data/by_freq/Semimonthly.
    This tests semimonthly payday prediction patterns and frequency handling.
    """
    with open(json_file, "r") as f:
        sample_input = json.load(f)

    # Run the complete model pipeline
    output = run_model(sample_input, TimeFrame.ALL)

    # Basic assertions
    assert output is not None, "Model output should not be None"
    assert isinstance(output, str), "Model output should be a JSON string"

    # Parse the output to extract income source information
    output_dict = json.loads(output)

    # Check that the output has the expected structure
    assert "incomeSources" in output_dict, "Output should contain incomeSources"

    income_sources = output_dict.get("incomeSources", [])

    # Validate payday prediction fields for semimonthly income sources
    for source in income_sources:
        if source.get("frequency") == "S":  # Semimonthly frequency
            # These fields should exist for semimonthly sources
            assert "regularPayDay" in source, "Semimonthly sources should have regularPayDay field"
            assert "nextPayDay" in source, "Semimonthly sources should have nextPayDay field"
            assert "paymentNearHoliday" in source, "Semimonthly sources should have paymentNearHoliday field"
            assert "nextPayDayOnHoliday" in source, "Semimonthly sources should have nextPayDayOnHoliday field"

            # Only check payday prediction logic when errorCode is 0 (successful processing)
            error_code = source.get("errorCode", -1)
            if error_code == 0:
                regular_payday = source.get("regularPayDay", "")
                if regular_payday and regular_payday != "None":
                    # The semimonthly patterns should be processed without errors
                    next_payday = source.get("nextPayDay")
                    assert (
                        next_payday != "None"
                    ), f"Should predict next payday for semimonthly pattern: {regular_payday}"

    # Optional: Save results for analysis
    if SAVE_RESULTS_TO_NOTEBOOKS:
        save_test_result(json_file, output_dict)


def save_test_result(json_file, output_dict):
    """Save individual test result to notebooks folder for analysis."""
    try:
        # Determine frequency type based on file path
        if "Monthly" in json_file:
            notebooks_dir = os.path.join(config.ROOT_DIR, "notebooks", "monthly_payday_test_results")
            prefix = "monthly_result_"
        elif "Biweekly" in json_file:
            notebooks_dir = os.path.join(config.ROOT_DIR, "notebooks", "biweekly_payday_test_results")
            prefix = "biweekly_result_"
        elif "Weekly" in json_file:
            notebooks_dir = os.path.join(config.ROOT_DIR, "notebooks", "weekly_payday_test_results")
            prefix = "weekly_result_"
        elif "Semimonthly" in json_file:
            notebooks_dir = os.path.join(config.ROOT_DIR, "notebooks", "semimonthly_payday_test_results")
            prefix = "semimonthly_result_"
        else:
            notebooks_dir = os.path.join(config.ROOT_DIR, "notebooks", "payday_test_results")
            prefix = "result_"

        os.makedirs(notebooks_dir, exist_ok=True)

        filename = os.path.basename(json_file).replace(".json", "").replace("result_", "")
        result_file = os.path.join(notebooks_dir, f"{prefix}{filename}.json")

        with open(result_file, "w") as f:
            json.dump(output_dict, f, indent=2, default=str)

    except Exception as e:
        print(f"Error saving result for {json_file}: {str(e)}")


def run_single_file(file_path):
    """
    Run a single income file for debugging purposes.

    Args:
        file_path (str): Full path to the JSON file to process
    """
    if not os.path.exists(file_path):
        print(f"File not found: {file_path}")
        return

    filename = os.path.basename(file_path)
    print(f"Processing file: {filename}")

    # Load the JSON data
    with open(file_path, "r") as f:
        input_data = json.load(f)

    # Run the complete model pipeline
    output = run_model(input_data, TimeFrame.ALL)

    # Parse the output to extract income source information
    output_dict = json.loads(output)

    # Extract and display payday prediction results
    income_sources = output_dict.get("incomeSources", [])

    print(f"Found {len(income_sources)} income sources:")

    for i, source in enumerate(income_sources, 1):
        print(f"\n  Income Source {i}:")
        print(f"    Source ID: {source.get('sourceID')}")
        print(f"    Income Source: {source.get('incomeSource')}")
        print(f"    Frequency: {source.get('frequency')}")
        print(f"    Regular Pay Day: {source.get('regularPayDay')}")
        print(f"    Last Pay Day: {source.get('lastPayDay')}")
        print(f"    Next Pay Day: {source.get('nextPayDay')}")
        print(f"    Payment Near Holiday: {source.get('paymentNearHoliday')}")
        print(f"    Next Pay Day On Holiday: {source.get('nextPayDayOnHoliday')}")
        print(f"    Monthly Amount: {source.get('monthlyAmount')}")

    print(f"\n✓ Successfully processed {filename}")


if __name__ == "__main__":
    # Run a single file for testing when script is executed directly
    file_path = os.path.join(
        os.path.realpath(os.path.join(config.ROOT_DIR, "..", "tests", "data", "by_freq", "Weekly")), "220781.json"
    )
    print("=== Testing Monthly File ===")
    # run_single_file(file_path)
    test_weekly_income_file(file_path)
    print("finished")
