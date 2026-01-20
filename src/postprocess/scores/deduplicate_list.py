def deduplicate_list(alert_list: list[str]) -> list[str]:
    x = list(set(alert_list))
    if "None" in x:
        x.remove("None")
    if (
        "Increased Default Risk: No Active Income Detected" in x
        and "Customer tends to keep a low balance over time" in x
    ):
        x.remove("Customer tends to keep a low balance over time")
    return x
