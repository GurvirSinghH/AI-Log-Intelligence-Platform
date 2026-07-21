from sklearn.ensemble import IsolationForest


def detect_anomalies(features, contamination=0.05, random_state=42):
    """Flag anomalous log rows with an Isolation Forest.

    Returns a *copy* of ``features`` with an added ``anomaly`` column
    (1 = anomaly, 0 = normal). The input frame is never mutated, which keeps
    the function safe to memoize with Streamlit's cache.
    """
    result = features.copy()

    model = IsolationForest(
        n_estimators=100,
        contamination=contamination,
        random_state=random_state,
        n_jobs=-1,
    )
    # Isolation Forest returns -1 for anomalies and 1 for normal points.
    predictions = model.fit_predict(features)
    result["anomaly"] = (predictions == -1).astype(int)

    return result
