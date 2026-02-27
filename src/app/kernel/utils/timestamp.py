from datetime import datetime


def format_timestamp(ts):
    if not ts:
        return ""
    try:
        ts_float = float(ts)
        if ts_float > 32503680000:
            ts_float /= 1000
        return datetime.fromtimestamp(ts_float).strftime("%d/%m/%Y %H:%M")
    except (ValueError, OSError, OverflowError):
        return "Data Inválida"
