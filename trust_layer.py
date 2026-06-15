def validate(report: str):
    keywords = ["flood", "traffic", "outage", "accident", "fire"]
    return any(k in report.lower() for k in keywords)
