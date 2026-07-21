from sklearn.cluster import KMeans


def cluster_logs(features, n_clusters=2, random_state=42):
    """Group the anomalous rows into clusters with KMeans.

    Returns a copy of ``features`` with an added ``cluster`` column. Normal
    rows (and the case where there are too few anomalies to cluster) get
    ``cluster = -1``. The input frame is never mutated.
    """
    result = features.copy()
    result["cluster"] = -1

    anomalies = result[result["anomaly"] == 1]
    training_data = anomalies.drop(columns=["anomaly", "cluster"])

    # Cannot form k clusters from fewer than k points.
    n_clusters = min(n_clusters, len(training_data))
    if n_clusters < 2:
        return result

    kmeans = KMeans(n_clusters=n_clusters, random_state=random_state, n_init=10)
    labels = kmeans.fit_predict(training_data)
    result.loc[anomalies.index, "cluster"] = labels

    return result
