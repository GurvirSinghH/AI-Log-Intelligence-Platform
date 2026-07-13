import pandas as pd
import re
def parse_logs(logs):
    """
    This function is responsible for parsing the input data and extracting relevant information.
    It processes the data according to predefined rules and returns a structured output.
    """
    parsed_logs = []

    pattern=re.compile(r'(?P<month>Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec) (?P<day>\d{1,2}) (?P<time>\d{2}:\d{2}:\d{2}) (?P<host>\S+) (?P<process>.*?): (?P<message>.+)')
    matches = []
    for lines in logs.splitlines():
        matches.extend(pattern.finditer(lines))
    for match in matches:
        parsed_logs.append({
            "month": match.group("month"),
            "day": match.group("day"),
            "time": match.group("time"),
            "host": match.group("host"),
            "process": match.group("process"),
            "message": match.group("message")
        })
    
    return pd.DataFrame(parsed_logs)