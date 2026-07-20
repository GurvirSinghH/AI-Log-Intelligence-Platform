from sklearn.ensemble import IsolationForest

def detect_anomalies(features):

    model =  IsolationForest(n_estimators=100, contamination=0.05, random_state=42)
    model.fit(features)

    features['anomaly'] = model.predict(features)
    features['anomaly'] = features['anomaly'].map({1: 0, -1: 1})  

    return features