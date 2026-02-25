from base64 import b64decode, b64encode
from io import BytesIO

import httpx
from imagehash import ImageHash, hex_to_hash, phash
from loguru import logger
from PIL import Image


async def url_to_b64(url: str):
    try:
        url = url.replace("minio-storage", "localhost").split("?")[0]
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(url)
            response.raise_for_status()
            encoded_string = b64encode(response.content).decode("utf-8")
            return encoded_string
    except Exception as e:
        logger.error(f"Erro ao baixar imagem da URL {url}: {e}")
        return None


def calculate_phash(file_bytes: bytes) -> str:
    """Recebe os bytes de uma imagem e retorna o pHash como string."""
    img = Image.open(BytesIO(file_bytes))
    hash_value = phash(img)
    return str(hash_value)


def get_hash_from_b64(b64_str: str) -> ImageHash:
    if len(b64_str) == 16:
        return hex_to_hash(b64_str)
    else:
        img = Image.open(BytesIO(b64decode(b64_str))).convert("RGB")
        return phash(img)
