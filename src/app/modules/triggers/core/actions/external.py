import random
from typing import Optional
from app.kernel.infrastructure import translate_service, external_api
from app.kernel.utils import url_to_b64
from app.kernel.config import settings


async def _safe_translate(text: Optional[str]) -> str:
    if not text:
        return ""
    try:
        return await translate_service.translate(
            text, target_lang=settings.TRANSLATE_TARGET_LANG
        )
    except Exception:
        return text


async def cat_api(*args) -> str:
    """Busca um fato sobre gatos."""
    url = "https://meowfacts.herokuapp.com/?lang=por-br"
    res = await external_api.fetch(url)
    return await _safe_translate(res.get("data", [""])[0] if res else "Miau!")


async def breaking_bad_api(*args) -> str:
    """Busca e traduz uma frase de Breaking Bad."""
    url = "https://api.breakingbadquotes.xyz/v1/quotes"
    res = await external_api.fetch(url)
    if not res or not isinstance(res, list):
        return ""

    quote = res[0]
    text_pt = await _safe_translate(quote.get("quote"))
    return f'"{text_pt}"\n— {quote.get("author")}'


async def chuck_norris_api(*args) -> str:
    url = "https://api.chucknorris.io/jokes/random"
    res = await external_api.fetch(url)
    return await _safe_translate(res.get("value")) if res else ""


async def get_advice(*args) -> str:
    url = "https://api.adviceslip.com/advice"
    res = await external_api.fetch(url)
    if not res:
        return ""
    return await _safe_translate(res.get("slip", {}).get("advice"))


async def motivacional_api(*args) -> str:
    """Busca uma frase motivacional de um repositório JSON e traduz."""
    url = "https://raw.githubusercontent.com/devmatheusguerra/frasesJSON/master/frases.json"
    data = await external_api.fetch(url)

    if not data or not isinstance(data, list):
        return ""

    choice = random.choice(data)
    frase = await _safe_translate(choice.get("frase"))
    autor = choice.get("autor", "Desconhecido")

    return f'"{frase}"\n— {autor}'


async def anime_api(*args) -> str:
    """Busca uma frase de anime com tratamento para JSON aninhado."""
    url = "https://api.animechan.io/v1/quotes/random"
    res = await external_api.fetch(url)

    data = res.get("data", {}) if res and isinstance(res, dict) else {}
    if not data:
        return ""

    quote = await _safe_translate(data.get("content"))
    character = data.get("character", {}).get("name", "Desconhecido")
    anime = data.get("anime", {}).get("name", "Anime")

    return f'"{quote}"\n— {character} ({anime})'


async def cat_photo_api(*args) -> str:
    url = "https://cataas.com/cat?json=true"
    res = await external_api.fetch(url)
    if not res:
        return ""
    img_path = res.get("url", "")
    if img_path and not img_path.startswith("http"):
        img_path = f"https://cataas.com/{img_path.lstrip('/')}"

    if img_path:
        try:
            b64 = await url_to_b64(img_path)
            return f";base64,{b64}" if b64 else img_path
        except Exception:
            return img_path
    return img_path or ""


async def get_dog(*args) -> str:
    url = "https://dog.ceo/api/breeds/image/random"
    res = await external_api.fetch(url)
    return res.get("message", "") if res and res.get("status") == "success" else ""


async def waifu_pics_helper(category: str) -> str:
    url = f"https://api.waifu.pics/sfw/{category}"
    res = await external_api.fetch(url)
    return res.get("url", "") if res else ""


async def get_bonk(*args) -> str:
    return await waifu_pics_helper("bonk")


async def get_smile(*args) -> str:
    return await waifu_pics_helper("smile")
