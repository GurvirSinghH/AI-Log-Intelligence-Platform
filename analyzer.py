def analyze_log(data_frame):
    """Return a flat dictionary of scalar summary statistics for the logs.

    Per-host / per-process breakdowns are intentionally left out here because
    they are already rendered as charts by the visualizer module.
    """
    if data_frame.empty:
        return {}

    process_mode = data_frame["process"].mode()
    message_mode = data_frame["message"].mode()

    return {
        "Total Logs": len(data_frame),
        "Unique Hosts": data_frame["host"].nunique(),
        "Unique Processes": data_frame["process"].nunique(),
        "Unique Messages": data_frame["message"].nunique(),
        "Most Common Process": process_mode.iloc[0] if not process_mode.empty else "N/A",
        "Most Common Message": message_mode.iloc[0] if not message_mode.empty else "N/A",
    }
