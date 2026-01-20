from utils.utils import TimeFrame


def handle_timeframe(timeframe_str):
    try:
        timeframe = timeframe_str.upper()
        timeframe = TimeFrame(timeframe)
        return timeframe, None
    except ValueError:
        return None, (
            {
                "status": 400,
                "message": "Invalid timeframe specified. Use one of the following: 'all', 'one_month', 'two_month', 'three_month', 'four_month', 'five_month', 'six_month'.",
            }
        )
