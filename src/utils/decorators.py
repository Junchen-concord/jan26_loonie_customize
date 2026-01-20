from datetime import datetime

from config import config
from config.settings import PRINT_TIMESTAMPS_THRESHOLD


def timer(func):
    """
    Decorator to time a function, printing when the time taken exceeds a certain threshold.
    """

    def wrapper(*args, **kwargs):
        start_time = datetime.now()
        result = func(*args, **kwargs)
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds() * 1000  # duration in milliseconds
        if config.PRINT_TIMESTAMPS and (duration > PRINT_TIMESTAMPS_THRESHOLD):
            print(f"'{func.__name__}' took {duration:.2f} ms to execute")

        return result

    return wrapper
