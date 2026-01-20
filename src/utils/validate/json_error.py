from app_utils import logger
from utils.validate.raise_error import raise_error


class JsonError:
    """
    Class for JSON validation errors. This class is used to check if the JSON file is valid.
    It currently checks if the JSON file is empty or if it contains only one record.
    """

    @classmethod
    def validate_json(cls, data):
        """Runs all json validation checks on the input data."""
        try:
            cls.check_empty_json(data)
            cls.check_single_record(data)
        except Exception as e:
            logger.error("JSON error:")
            return e, True
        return data, False

    @staticmethod
    def check_empty_json(data):
        """Check if the JSON data is empty."""
        if not data:
            logger.error("Empty JSON file")
            raise raise_error(401, "Empty JSON file")

    @staticmethod
    def check_single_record(data):
        """Check if the JSON contains only one record."""
        if len(data) == 1:
            raise raise_error(301, "JSON file contains only one record")
        if len(data) == 1:
            raise raise_error(301, "JSON file contains only one record")
