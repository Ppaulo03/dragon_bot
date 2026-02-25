import re
from typing import Dict, Any
from app.core.interfaces import MessageData

PADRAO_DONO = r"(?i)(?:quem (?:é|e) o dono de|de quem (?:é|e))\s+(.+)"
PADRAO_PRONOME = (
    r"^(o|a|os|as|esse|essa|esses|essas|este|esta|estes|estas|"
    r"aquele|aquela|aqueles|aquelas|isso|isto|aquilo)\s+(.*)"
)

MAPA_PRONOME = {
    "o": "do",
    "a": "da",
    "os": "dos",
    "as": "das",
    "esse": "desse",
    "essa": "dessa",
    "esses": "desses",
    "essas": "dessas",
    "este": "deste",
    "esta": "desta",
    "estes": "destes",
    "estas": "destas",
    "aquele": "daquele",
    "aquela": "daquela",
    "aqueles": "daqueles",
    "aquelas": "daquelas",
    "isso": "disso",
    "isto": "disto",
    "aquilo": "daquilo",
}


def get_meme_name(msg: str) -> str:
    """Extrai e formata o nome para o meme do 'João Dono'."""
    match = re.search(PADRAO_DONO, msg)
    if not match:
        return ""

    item = match.group(1).strip().replace("?", "")
    match_artigo = re.match(PADRAO_PRONOME, item, re.IGNORECASE)

    if match_artigo:
        artigo = match_artigo.group(1).lower()
        resto_da_frase = match_artigo.group(2)
        preposicao = MAPA_PRONOME.get(artigo, "de")
        return f"João Dono {preposicao} {resto_da_frase}".title()

    return f"João Dono de {item}".title()


async def meme_contact(msg_data: MessageData, *args) -> Dict[str, Any]:
    """Cria um objeto de contato fake baseado na mensagem recebida."""
    name = get_meme_name(msg_data.body)
    if not name:
        return {}
    clean_name = name.lower().replace(" ", "")

    return {
        "fullName": name,
        "wuid": "556496188380",
        "phoneNumber": "+55 64 96188-380",
        "organization": f"{name} LTDA",
        "email": f"{clean_name}@gmail.com",
        "url": f"https://{clean_name}.com",
    }
