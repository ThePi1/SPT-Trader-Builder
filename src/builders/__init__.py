"""Plain-Python builders for the JSON that SPT reads.

Nothing in here imports Qt: each function takes already-extracted values and returns
the dict (or list) to export, so the output can be tested without opening a window.
The windows only read their widgets and call these.
"""
