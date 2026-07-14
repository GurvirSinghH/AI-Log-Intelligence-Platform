import pandas as pd

def analyze_log(data_frame):
    """
    Analyzes the log data and returns a summary.

    Parameters:
    data_frame (pd.DataFrame): The DataFrame containing the parsed log data.

    Returns:
    dict: A dictionary containing summary statistics of the log data.
    """
    statistics = {
        "Total Logs": len(data_frame),
        "Uniques hosts": data_frame['host'].nunique(),
        "Unique processes": data_frame['process'].nunique(),
        "Unique messages": data_frame['message'].nunique(),
        "Most common process": data_frame['process'].mode()[0] if not data_frame['process'].mode().empty else None,
        "Most common message": data_frame['message'].mode()[0] if not data_frame['message'].mode().empty else None,
        "Logs per host": data_frame.groupby('host').size().to_dict(),
        "Logs per process": data_frame.groupby('process').size().to_dict()
    }
    
    return statistics