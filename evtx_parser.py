import calendar
import os
import re
import sys
import tempfile
import xml.etree.ElementTree as ET

import pandas as pd
from Evtx.Evtx import Evtx

from log_parser import COLUMNS

NS = {"e": "http://schemas.microsoft.com/win/2004/08/events/event"}

# Readable names for the most commonly analysed Windows event IDs
EVENT_NAMES = {
    "1102": "Audit log cleared",
    "4616": "System time changed",
    "4624": "Successful logon",
    "4625": "Failed logon",
    "4634": "Logoff",
    "4647": "User-initiated logoff",
    "4648": "Logon with explicit credentials",
    "4672": "Special privileges assigned",
    "4688": "Process created",
    "4689": "Process exited",
    "4720": "User account created",
    "4722": "User account enabled",
    "4724": "Password reset attempt",
    "4728": "Member added to global group",
    "4732": "Member added to local group",
    "4740": "Account locked out",
    "4768": "Kerberos TGT requested",
    "4769": "Kerberos service ticket requested",
    "4776": "Credential validation",
    "4798": "User's local group membership enumerated",
    "4799": "Local group membership enumerated",
    "5379": "Credential Manager credentials read",
    "5058": "Key file operation",
    "5059": "Key migration operation",
    "5061": "Cryptographic operation",
    "5382": "Vault credentials read",
}

AUDIT_SUCCESS = 0x20000000000000
AUDIT_FAILURE = 0x10000000000000
LEVELS = {"1": "Critical", "2": "Error", "3": "Warning", "4": "Information", "5": "Verbose"}

TIME_PATTERN = re.compile(r"(\d{4})-(\d{2})-(\d{2})[ T](\d{2}:\d{2}:\d{2})")

# Safety cap so a huge log can't freeze the app
MAX_EVENTS = 20000


def parse_evtx_bytes(data):
    """Parse an uploaded .evtx file (raw bytes) into the canonical schema."""
    with tempfile.NamedTemporaryFile(suffix=".evtx", delete=False) as tmp:
        tmp.write(data)
        path = tmp.name
    try:
        return parse_evtx_file(path)
    finally:
        os.remove(path)


def parse_evtx_file(path, max_events=MAX_EVENTS):
    """Parse a .evtx file on disk into the canonical schema.

    Damaged records are skipped instead of stopping the whole parse.
    """
    rows = []
    with Evtx(path) as log:
        for record in log.records():
            if len(rows) >= max_events:
                break
            try:
                row = _record_to_row(record.xml())
            except Exception:
                continue
            if row:
                rows.append(row)
    return pd.DataFrame(rows, columns=COLUMNS)


def _record_to_row(xml_text):
    # Remove any <?xml ...?> header so ElementTree can read it
    xml_text = re.sub(r"^\s*<\?xml[^>]*\?>", "", xml_text)
    root = ET.fromstring(xml_text)

    system = root.find("e:System", NS)
    if system is None:
        return None

    event_id = _text(system.find("e:EventID", NS))
    time_node = system.find("e:TimeCreated", NS)
    timestamp = time_node.get("SystemTime", "") if time_node is not None else ""
    execution = system.find("e:Execution", NS)
    pid = execution.get("ProcessID") if execution is not None else None

    month, day, time = _split_time(timestamp)
    name = EVENT_NAMES.get(event_id, "Windows event")
    details = _event_data(root)
    message = f"{name} (EventID {event_id})"
    if details:
        message += ": " + details

    return {
        "month": month,
        "day": day,
        "time": time,
        "host": _text(system.find("e:Computer", NS)),
        "process": event_id,
        "module": _outcome(system),
        "pid": pid,
        "message": message,
    }


def _text(node):
    if node is None or node.text is None:
        return ""
    return node.text.strip()


def _event_data(root):
    """Turn the event's <Data> fields into 'Name=Value' pairs."""
    parts = []
    for data in root.iter(f"{{{NS['e']}}}Data"):
        value = "_".join((data.text or "").split()) or "-"
        name = data.get("Name")
        parts.append(f"{name}={value}" if name else value)
    return " ".join(parts)


def _outcome(system):
    """Audit Success / Audit Failure for security events, otherwise the level."""
    keywords = _text(system.find("e:Keywords", NS))
    try:
        value = int(keywords, 16)
        if value & AUDIT_SUCCESS:
            return "Audit Success"
        if value & AUDIT_FAILURE:
            return "Audit Failure"
    except ValueError:
        pass
    level = _text(system.find("e:Level", NS))
    return LEVELS.get(level, "Information")


def _split_time(timestamp):
    """Turn '2026-09-21 14:03:22.123+00:00' into ('Sep', '21', '14:03:22')."""
    match = TIME_PATTERN.search(timestamp)
    if not match:
        return "", "", ""
    _year, month, day, clock = match.groups()
    return calendar.month_abbr[int(month)], str(int(day)), clock


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python evtx_parser.py <path-to-file.evtx>")
        sys.exit(1)

    df = parse_evtx_file(sys.argv[1])
    print(f"Parsed {len(df):,} events")
    print("\nTop event IDs:")
    print(df["process"].value_counts().head(10).to_string())
    print("\nOutcomes:")
    print(df["module"].value_counts().to_string())