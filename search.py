import pandas as pd

def search_logs(data_frame, search_term):

    if search_term is None or search_term.strip() == "":
        return data_frame
    filtered_logs = data_frame[data_frame['message'].str.contains(search_term, case=False, na=False)]
    return filtered_logs
