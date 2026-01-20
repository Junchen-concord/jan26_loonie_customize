import math


def transform_score(pred_res: float, odds: int) -> int:
    score = pred_res * 1000
    pdo = 100
    point = 850
    d = pred_res / (1 - pred_res)
    factor = pdo / math.log(2)
    offset = point - (factor * math.log(odds))
    score = offset + factor * math.log(d)
    return int(score)
