from sklearn.cluster import KMeans

def cluster_logs(features):
    anomaly_features = features[features['anomaly'] == 1]
    training_data = anomaly_features.drop(columns=["anomaly"])
    
    if len(training_data) < 2:
        features['cluster'] = -1
        return features
    else:
        kmeans = KMeans(n_clusters=2, random_state=42)
        kmeans.fit(training_data)
    anomaly_features = anomaly_features.copy()
    anomaly_features['cluster'] = kmeans.labels_
    features.loc[anomaly_features.index, 'cluster'] = anomaly_features['cluster']
    
    return features
