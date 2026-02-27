from datetime import datetime
from pathlib import Path
from fastapi.templating import Jinja2Templates


def format_timestamp(ts):
    if not ts:
        return ""
    try:
        ts_float = float(ts)
        # Ajuste para milissegundos
        if ts_float > 32503680000:
            ts_float /= 1000
        return datetime.fromtimestamp(ts_float).strftime("%d/%m/%Y %H:%M")
    except (ValueError, OSError, OverflowError):
        return "Data Inválida"


TEMPLATE_DIR = Path(__file__).parent.parent / "templates"
templates = Jinja2Templates(directory=str(TEMPLATE_DIR))
templates.env.filters["timestamp_to_date"] = format_timestamp
