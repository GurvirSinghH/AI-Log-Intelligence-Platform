def search_logs(data_frame, search_term):
    """Case-insensitive substring filter over the ``message`` column.

    ``regex=False`` keeps special characters (``(``, ``[``, ``*`` ...) safe, so
    typing them in the search box filters literally instead of crashing.
    """
    if not search_term or not search_term.strip():
        return data_frame

    mask = data_frame["message"].str.contains(
        search_term, case=False, na=False, regex=False
    )
    return data_frame[mask]
