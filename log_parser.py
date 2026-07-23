import re

import pandas as pd

# ---------------------------------------------------------------------------
# Linux syslog / auth.log  (existing format — unchanged)
# ---------------------------------------------------------------------------
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

# ---------------------------------------------------------------------------
# Linux syslog  (new — general system logs without the auth.log PAM module)
# ---------------------------------------------------------------------------
# Example lines this matches:
#   Jan 15 10:42:13 server1 systemd[1]: Started Daily Cleanup.
#   Jan 15 10:42:20 server1 kernel: USB device connected.          (no pid)
#   Jan 15 10:42:25 server1 CRON[2201]: (root) CMD (/usr/bin/backup.sh)
#
# The program token forbids '(' so a PAM-tagged auth.log line (e.g.
# "sshd(pam_unix)[1234]:") can never match here -- that keeps this pattern
# mutually exclusive with LOG_PATTERN and stops the two from being confused.
SYSLOG_GENERAL_PATTERN = re.compile(
    r'(?P<month>Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+'
    r'(?P<day>\d{1,2})\s+'
    r'(?P<time>\d{2}:\d{2}:\d{2})\s+'
    r'(?P<host>\S+)\s+'
    r'(?P<process>[^\s:\[\(]+)'          # program name (no PAM "(module)" tag)
    r'(?:\[(?P<pid>\d+)\])?'             # optional [pid]
    r':\s+'
    r'(?P<message>.+)'
)

# ---------------------------------------------------------------------------
# Apache access log  (new — Common Log Format / Combined Log Format)
# ---------------------------------------------------------------------------
# Example lines this matches:
#   127.0.0.1 - frank [10/Oct/2000:13:55:36 -0700] "GET /index.html HTTP/1.1" 200 2326
#   192.168.1.10 - - [15/Jul/2026:14:31:20 +0000] "POST /login HTTP/1.1" 401 721 "https://example.com" "Mozilla/5.0"
#
# The trailing referrer / user-agent pair is optional so the same pattern
# handles both Common (no pair) and Combined (with pair) log formats.
APACHE_PATTERN = re.compile(
    r'^(?P<ip>\S+)\s+\S+\s+\S+\s+'                       # client IP, identd, user
    r'\[(?P<timestamp>[^\]]+)\]\s+'                       # [day/Mon/Year:HH:MM:SS +ZZZZ]
    r'"(?P<method>[A-Z]+)\s+(?P<url>\S+)'                 # "METHOD URL
    r'(?:\s+(?P<http_version>HTTP/\d(?:\.\d)?))?"\s+'     #  HTTP/x.y" (version optional)
    r'(?P<status>\d{3})\s+'                               # status code
    r'(?P<size>\d+|-)'                                    # response size (or - when unknown)
    r'(?:\s+"(?P<referrer>[^"]*)")?'                      # optional "referrer"
    r'(?:\s+"(?P<user_agent>[^"]*)")?'                    # optional "user agent"
)

# Canonical columns first (consumed unchanged by the rest of the app), then the
# Apache-only fields that have no canonical home.
APACHE_COLUMNS = COLUMNS + ["url", "http_version", "referrer", "user_agent"]

# ---------------------------------------------------------------------------
# Apache error log  (new — handles both the 2.2 and 2.4 line formats)
# ---------------------------------------------------------------------------
# Example lines this matches:
#   [Wed Oct 11 14:32:52 2000] [error] [client 127.0.0.1] client denied ...
#   [Fri Sep 09 10:42:29.902022 2011] [core:error] [pid 35708:tid 4328636416] [client 72.15.99.187:64834] AH00126: Invalid URI ...
#
# The [pid ...] and [client ...] blocks are optional (2.2 omits pid; server
# level messages omit client), and 2.4 prefixes the level with a module.
APACHE_ERROR_PATTERN = re.compile(
    r'^\[(?P<timestamp>[^\]]+)\]\s+'                          # [DoW Mon DD HH:MM:SS[.us] YYYY]
    r'\[(?:(?P<module>[^\]:]+):)?(?P<level>[^\]]+)\]\s*'      # [level] or [module:level]
    r'(?:\[pid\s+(?P<pid>\d+)(?::tid\s+\d+)?\]\s*)?'          # optional [pid N:tid M]
    r'(?:\[client\s+(?P<client>[^\]]+)\]\s*)?'                # optional [client IP:port]
    r'(?P<message>.*)$'                                       # free-text error message
)

# Number of leading non-empty lines inspected to auto-detect the format.
_DETECTION_SAMPLE = 20


def parse_logs(logs):
    """Detect the log format and dispatch to the matching parser.

    Detection is automatic (the user never picks a type): a sample of the first
    lines is matched against each known format (Linux auth.log, Linux syslog,
    Apache access, Apache error) and the best match wins. Anything not recognised
    falls through to the auth.log parser, which returns an empty frame for
    unsupported input — preserving today's behaviour.

    Always returns a DataFrame; downstream code can rely on the canonical
    ``COLUMNS`` being present regardless of the detected format.
    """
    log_format = _detect_format(logs)
    if log_format == "apache_access":
        return _parse_apache(logs)
    if log_format == "apache_error":
        return _parse_apache_error(logs)
    if log_format == "syslog_general":
        return _parse_syslog_general(logs)
    return _parse_syslog(logs)


def _parse_syslog(logs):
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


def _parse_syslog_general(logs):
    """Parse general Linux syslog lines into the canonical schema.

    Handles the standard ``Mon DD HH:MM:SS host program[pid]: message`` form
    used by systemd, kernel, CRON, NetworkManager, etc. This is deliberately
    kept separate from the auth.log parser: auth.log carries a PAM ``(module)``
    tag that this format does not, so ``module`` has no equivalent here and is
    set to None; ``pid`` is None when the ``[pid]`` block is absent.
    """
    rows = []
    for line in logs.splitlines():
        match = SYSLOG_GENERAL_PATTERN.search(line)
        if not match:
            continue

        fields = match.groupdict()
        rows.append(
            {
                "month": fields["month"],
                "day": fields["day"],
                "time": fields["time"],
                "host": fields["host"],
                "process": fields["process"],
                "module": None,
                "pid": fields["pid"],
                "message": fields["message"],
            }
        )

    df = pd.DataFrame(rows, columns=COLUMNS)
    # Absent optional fields must read back as literal None, not NaN.
    for column in ("module", "pid"):
        df[column] = df[column].astype(object).where(df[column].notna(), None)
    return df


def _parse_apache(logs):
    """Parse Apache access logs (Common / Combined Log Format).

    Apache fields are mapped onto the canonical schema so the existing pipeline
    keeps working without modification:

        IP Address    -> host        HTTP Method   -> process
        Status Code   -> module      Response Size -> pid
        Timestamp     -> month/day/time

    URL, HTTP version, referrer and user agent are kept in their own columns.
    Missing optional fields become ``None`` instead of raising.
    """
    rows = []
    for line in logs.splitlines():
        match = APACHE_PATTERN.search(line)
        if not match:
            continue

        fields = match.groupdict()
        month, day, time = _split_apache_timestamp(fields["timestamp"])
        size = None if fields["size"] in (None, "-") else fields["size"]

        rows.append(
            {
                "month": month,
                "day": day,
                "time": time,
                "host": fields["ip"],
                "process": fields["method"],
                "module": fields["status"],
                "pid": size,
                "message": _build_apache_message(fields, size),
                "url": fields["url"],
                "http_version": fields["http_version"],
                "referrer": _clean_optional(fields["referrer"]),
                "user_agent": _clean_optional(fields["user_agent"]),
            }
        )

    df = pd.DataFrame(rows, columns=APACHE_COLUMNS)
    # pandas coerces absent object values to NaN on construction; the optional
    # fields are required to read back as literal None.
    for column in ("http_version", "referrer", "user_agent"):
        df[column] = df[column].astype(object).where(df[column].notna(), None)
    return df


def _parse_apache_error(logs):
    """Parse Apache error logs (both the 2.2 and 2.4 line formats).

    Error-log fields are mapped onto the canonical schema so the existing
    pipeline keeps working without modification:

        Client IP -> host        Log Level -> process
        Module    -> module      PID       -> pid
        Timestamp -> month/day/time        Message   -> message

    Optional fields (module, pid, client) become ``None`` when absent rather
    than raising.
    """
    rows = []
    for line in logs.splitlines():
        match = APACHE_ERROR_PATTERN.search(line)
        if not match:
            continue

        fields = match.groupdict()
        month, day, time = _split_apache_error_timestamp(fields["timestamp"])

        rows.append(
            {
                "month": month,
                "day": day,
                "time": time,
                "host": _client_ip(fields["client"]),
                "process": (fields["level"] or "").strip(),
                "module": _clean_optional(fields["module"]),
                "pid": fields["pid"],
                "message": (fields["message"] or "").strip(),
            }
        )

    df = pd.DataFrame(rows, columns=COLUMNS)
    # Absent optional fields must read back as literal None, not NaN.
    for column in ("host", "module", "pid"):
        df[column] = df[column].astype(object).where(df[column].notna(), None)
    return df


def _detect_format(logs):
    """Return the detected format.

    One of 'apache_access', 'apache_error', 'syslog_general' or 'auth'.

    Detection is by match-count voting over a sample of lines. The auth.log and
    general-syslog patterns are mutually exclusive by construction (auth.log
    requires a PAM ``(module)`` tag that general syslog forbids), so their counts
    never overlap. An Apache format is chosen only when it *strictly* beats the
    syslog family, and 'auth' stays the default fall-back for ties and
    unsupported input — exactly as before this parser gained more formats.
    """
    sample = _sample_lines(logs)
    if not sample:
        return "auth"

    access = _count_matches(sample, APACHE_PATTERN)
    error = _count_matches(sample, APACHE_ERROR_PATTERN)
    auth = _count_matches(sample, LOG_PATTERN)
    syslog_general = _count_matches(sample, SYSLOG_GENERAL_PATTERN)
    syslog_family = max(auth, syslog_general)

    if error > syslog_family and error > access:
        return "apache_error"
    if access > syslog_family and access > 0:
        return "apache_access"
    if syslog_general > auth:
        return "syslog_general"
    return "auth"


def _count_matches(lines, pattern):
    """Count how many of ``lines`` match ``pattern`` (used for format voting)."""
    return sum(1 for line in lines if pattern.search(line))


def _sample_lines(logs, limit=_DETECTION_SAMPLE):
    """Return up to ``limit`` leading non-empty lines used for format detection."""
    sample = []
    for line in logs.splitlines():
        if line.strip():
            sample.append(line)
            if len(sample) >= limit:
                break
    return sample


def _split_apache_timestamp(timestamp):
    """Split ``10/Oct/2000:13:55:36 -0700`` into (month, day, time).

    ``time`` is returned as ``HH:MM:SS`` so feature engineering can extract the
    hour exactly as it does for syslog. Malformed timestamps degrade to empty
    strings rather than raising.
    """
    try:
        date_part = timestamp.split()[0]              # 10/Oct/2000:13:55:36
        day, month, rest = date_part.split("/", 2)    # 10 | Oct | 2000:13:55:36
        time = rest.split(":", 1)[1]                  # 13:55:36
        return month, day, time
    except (ValueError, IndexError):
        return "", "", ""


def _build_apache_message(fields, size):
    """Build a readable request line used for search, charts and the LLM report."""
    parts = [fields["method"], fields["url"]]
    if fields["http_version"]:
        parts.append(fields["http_version"])
    parts.append(fields["status"])
    parts.append(size if size is not None else "-")
    return " ".join(parts)


def _split_apache_error_timestamp(timestamp):
    """Split ``Wed Oct 11 14:32:52 2000`` / ``Fri Sep 09 10:42:29.902022 2011``
    into (month, day, time).

    ``time`` is returned as ``HH:MM:SS`` (microseconds dropped) so feature
    engineering can extract the hour exactly as it does for syslog. Malformed
    timestamps degrade to empty strings rather than raising.
    """
    try:
        _weekday, month, day, clock, _year = timestamp.split()
        time = clock.split(".", 1)[0]                  # drop optional microseconds
        return month, day, time
    except (ValueError, IndexError):
        return "", "", ""


def _client_ip(client):
    """Return the bare client IP, stripping the ``:port`` that Apache 2.4 adds."""
    if client is None:
        return None
    ip, separator, port = client.rpartition(":")
    if separator and port.isdigit():
        return ip
    return client


def _clean_optional(value):
    """Normalise absent optional fields (missing, empty, or ``-``) to None."""
    if value in (None, "", "-"):
        return None
    return value
