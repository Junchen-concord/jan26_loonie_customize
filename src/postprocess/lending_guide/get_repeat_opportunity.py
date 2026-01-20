from config import config


def get_repeat_opportunity(repeat_score: int) -> str:
    if repeat_score >= config.REPEAT_MODEL_HIGH_THRESHOLD:
        return "High"
    elif repeat_score >= config.REPEAT_MODEL_LOW_THRESHOLD:
        return "Medium"
    else:
        return "Low"
