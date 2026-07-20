from sklearn.preprocessing import LabelEncoder
import pandas as pd

def encode_categorical_features(df):
    features = df.copy()

    process_encoder = LabelEncoder()
    module_encoder = LabelEncoder()
    host_encoder = LabelEncoder()
    features['process'] = process_encoder.fit_transform(features['process'])
    features['module'] = module_encoder.fit_transform(features['module'])
    features['host'] = host_encoder.fit_transform(features['host'])
    return features

def create_features(df):
    features = encode_categorical_features(df)
    features['message_length'] = features['message'].apply(len)
    features['hour'] = pd.to_datetime(features['time'], format="%H:%M:%S").dt.hour
    features['pid'] = features['pid'].astype(int)
    return features[['process', 'module', 'host','pid' ,'message_length', 'hour']]