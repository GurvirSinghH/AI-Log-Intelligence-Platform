import re

import pandas as pd

# Compiled once at import time instead of on every call / Streamlit rerun.
LOG_PATTERN = re.compile(
    r'(?P<month>Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+'
    r'(?P<day>\d{1,2})\s+'
    r'(?P<time>\d{2}:\d{2}:\d{2})\s+'
    r'(?P<host>\S+)\s+'
    r'(?P<process>[^(]+)\((?P<module>[^)]+)\)\[(?P<pid>\d+)\]:\s+'
    r'(?P<message>.+)'
)

COLUMNS = ["month", "day", "time", "host", "process", "module", "pid", "message"]


def parse_logs(logs):
    """Parse raw syslog text into a structured DataFrame.

    Each line is scanned exactly once and matched at most once; lines that do
    not fit the syslog pattern are skipped. Always returns a DataFrame with the
    expected columns (empty if nothing matched) so downstream code can rely on
    the schema.
    """
    parsed_logs = [
        match.groupdict()
        for line in logs.splitlines()
        if (match := LOG_PATTERN.search(line))
    ]
    return pd.DataFrame(parsed_logs, columns=COLUMNS)
