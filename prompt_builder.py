"""
prompt_builder.py

This file builds the text prompt that we send to the LLM.

We do NOT send the raw log file to the LLM. Instead we send a short summary
made from results we have already calculated:
  - basic statistics
  - anomaly detection results
  - clustering results
  - a few example log messages

Keeping this in its own file makes it easy to see (and explain) exactly what
information the LLM receives.
"""


def build_prompt(stats, display_df, anomalies_df):
    """Build one text prompt from the analysis results and return it as a string.

    Parameters:
        stats        : dictionary returned by analyzer.analyze_log()
        display_df   : DataFrame of parsed logs plus 'anomaly' and 'cluster' columns
        anomalies_df : rows of display_df where anomaly == 1
    """
    total_logs = len(display_df)
    num_anomalies = len(anomalies_df)

    # We build the prompt line by line and join it at the end.
    # This is easier to read than one huge string.
    lines = []

    # Instructions for the LLM.
    lines.append("You are a helpful system administrator assistant.")
    lines.append("Write a short incident report using ONLY the summary below.")
    lines.append("")

    # 1) Basic statistics
    lines.append("=== LOG STATISTICS ===")
    lines.append(f"Total logs: {total_logs}")
    lines.append(f"Unique hosts: {stats['Unique Hosts']}")
    lines.append(f"Unique processes: {stats['Unique Processes']}")
    lines.append(f"Most common process: {stats['Most Common Process']}")
    lines.append(f"Most common message: {stats['Most Common Message']}")
    lines.append("")

    # 2) Anomaly detection results
    lines.append("=== ANOMALY DETECTION (Isolation Forest) ===")
    lines.append(f"Anomalies found: {num_anomalies} out of {total_logs}")
    lines.append("")

    # 3) Clustering results
    lines.append("=== ANOMALY CLUSTERS (KMeans) ===")
    clustered = display_df[display_df["cluster"] != -1]
    if clustered.empty:
        lines.append("No clusters were formed (too few anomalies).")
    else:
        cluster_sizes = clustered["cluster"].value_counts().sort_index()
        for cluster_id, size in cluster_sizes.items():
            lines.append(f"Cluster {int(cluster_id)}: {size} anomalies")
    lines.append("")

    # 4) A few representative (example) anomalous messages.
    # We only take the first 5 so the prompt stays short.
    lines.append("=== EXAMPLE ANOMALOUS LOG MESSAGES ===")
    example_messages = anomalies_df["message"].head(5).tolist()
    if example_messages:
        for message in example_messages:
            # Cut very long messages so the prompt does not get too big.
            short_message = str(message)[:200]
            lines.append(f"- {short_message}")
    else:
        lines.append("No anomalous messages to show.")
    lines.append("")

    # Final instruction: tell the LLM what the report should contain.
    lines.append("Write the report with three parts:")
    lines.append("1. A short summary of what happened.")
    lines.append("2. The key findings.")
    lines.append("3. Two or three recommended actions.")

    # Join all the lines into one string separated by new lines.
    prompt = "\n".join(lines)
    return prompt
