import pandas as pd
import plotly.express as px

TOP_N = 15


def plot_process_distribution(data_frame):
    counts = data_frame["process"].value_counts().head(TOP_N).reset_index()
    fig = px.bar(
        counts, x="process", y="count",
        title=f"Top {len(counts)} Processes by Log Volume",
    )
    fig.update_layout(template="plotly_white", xaxis_title="", yaxis_title="Count")
    return fig


def plot_host_distribution(data_frame):
    counts = data_frame["host"].value_counts().head(TOP_N).reset_index()
    fig = px.bar(
        counts, x="host", y="count",
        title=f"Top {len(counts)} Hosts by Log Volume",
    )
    fig.update_layout(template="plotly_white", xaxis_title="", yaxis_title="Count")
    return fig


def plot_message_distribution(data_frame):
    counts = data_frame["message"].value_counts().head(TOP_N).reset_index()
    counts["short_message"] = counts["message"].str.slice(0, 60)
    fig = px.bar(
        counts, x="count", y="short_message", orientation="h",
        title=f"Top {len(counts)} Messages by Frequency",
    )
    fig.update_layout(
        template="plotly_white",
        yaxis={"categoryorder": "total ascending"},
        xaxis_title="Count", yaxis_title="",
    )
    return fig


def plot_anomaly_scatter(scored_features, max_points=5000):
    """Scatter of message length vs hour, colored by anomaly flag.

    On large frames the normal points are sampled down (all anomalies kept)
    so the chart stays responsive.
    """
    data = scored_features
    if len(data) > max_points:
        anomalies = data[data["anomaly"] == 1]
        normals = data[data["anomaly"] == 0]
        n_normal = max(0, max_points - len(anomalies))
        if len(normals) > n_normal:
            normals = normals.sample(n_normal, random_state=42)
        data = pd.concat([normals, anomalies])

    labels = data["anomaly"].map({0: "Normal", 1: "Anomaly"})
    fig = px.scatter(
        data, x="hour", y="message_length", color=labels,
        title="Anomalies by Hour and Message Length",
        color_discrete_map={"Normal": "#4C78A8", "Anomaly": "#E45756"},
        opacity=0.7,
    )
    fig.update_layout(
        template="plotly_white",
        legend_title_text="Type",
        xaxis_title="Hour of Day", yaxis_title="Message Length",
    )
    return fig
