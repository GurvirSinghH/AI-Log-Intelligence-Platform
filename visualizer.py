import pandas as pd
import plotly.express as px 


def plot_process_distribution(data_frame):
    df_counts = data_frame['process'].value_counts().reset_index()
    fig = px.bar(df_counts, x='process', y='count', title='Process Distribution')
    return fig

def plot_host_distribution(data_frame):
    df_counts = data_frame['host'].value_counts().reset_index()
    fig = px.bar(df_counts, x='host', y='count', title='Host Distribution')
    return fig

def plot_message_distribution(data_frame):
    df_counts = data_frame['message'].value_counts().reset_index()
    df_counts["short_message"] = df_counts["message"].str[:50] + "..."
    fig = px.bar(df_counts, x='count', y='short_message', title='Message Distribution')
    return fig