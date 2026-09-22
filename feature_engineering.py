import pandas as pd
from sklearn.preprocessing import LabelEncoder

from template_miner import mine_templates

CATEGORICAL_COLUMNS = ["process", "module", "host"]
FEATURE_COLUMNS = [
    "process",
    "module",
    "host",
    "pid",
    "message_length",
    "hour",
    "template_frequency",
]


def add_templates(df):
    """Add Drain template columns ('template_id' and 'template') to the parsed logs.

    Safe to call more than once: if the columns already exist, it does nothing.
    """
    if "template" in df.columns:
        return df
    df = df.copy()
    template_ids, templates = mine_templates(df["message"].fillna("").astype(str))
    df["template_id"] = template_ids
    df["template"] = templates
    return df


def encode_categorical_features(df):
    features = df.copy()
    for column in CATEGORICAL_COLUMNS:
        features[column] = LabelEncoder().fit_transform(features[column].astype(str))
    return features


def create_features(df):
    """Turn parsed logs into a purely numeric feature matrix for the models.

    Time and PID parsing are error-tolerant: malformed values become 0 instead
    of raising, so a single bad line can never take down the whole pipeline.
    """
    df = add_templates(df)
    features = encode_categorical_features(df)
    features["message_length"] = df["message"].str.len()
    features["hour"] = (
        pd.to_datetime(df["time"], format="%H:%M:%S", errors="coerce").dt.hour.fillna(0).astype(int)
    )
    features["pid"] = pd.to_numeric(df["pid"], errors="coerce").fillna(0).astype(int)

    # How common is each line's template? Rare templates are suspicious.
    template_share = df["template"].map(df["template"].value_counts(normalize=True))
    features["template_frequency"] = template_share
    return features[FEATURE_COLUMNS]