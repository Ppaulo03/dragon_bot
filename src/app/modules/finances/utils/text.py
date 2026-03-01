import re


def clean_phone_number(jid: str) -> str:
    """Remove caracteres não numéricos de um JID ou número."""
    return re.sub(r"\D", "", jid)
