import pandas as pd
from sklearn.preprocessing import LabelEncoder

CATEGORICAL_COLUMNS = ["process", "module", "host"]
FEATURE_COLUMNS = ["process", "module", "host", "pid", "message_length", "hour"]


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
    features = encode_categorical_features(df)
    features["message_length"] = df["message"].str.len()
    features["hour"] = (
        pd.to_datetime(df["time"], format="%H:%M:%S", errors="coerce").dt.hour.fillna(0).astype(int)
    )
    features["pid"] = pd.to_numeric(df["pid"], errors="coerce").fillna(0).astype(int)
    return features[FEATURE_COLUMNS]
