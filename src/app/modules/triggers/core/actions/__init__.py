from .external import (
    cat_api,
    cat_photo_api,
    breaking_bad_api,
    motivacional_api,
    chuck_norris_api,
    get_dog,
    get_advice,
    get_bonk,
    get_smile,
    anime_api,
)
from .local import meme_contact


ACTION_REGISTRY = {
    # Ações de API (Externas)
    "cat_api": cat_api,
    "cat_photo_api": cat_photo_api,
    "breaking_bad": breaking_bad_api,
    "motivacional": motivacional_api,
    "chuck_norris": chuck_norris_api,
    "dog_api": get_dog,
    "advice": get_advice,
    "bonk": get_bonk,
    "smile": get_smile,
    "anime_quote": anime_api,
    # Lógica Local (Meme)
    "meme_contact": meme_contact,
}

__all__ = ["ACTION_REGISTRY"]
