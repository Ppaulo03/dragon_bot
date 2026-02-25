import json
import re
from typing import Any, Callable, Dict, Tuple


def _get_media_body(
    message: Dict[str, Any], msg_key: str, caption_key: str = "caption"
) -> str:
    """Helper para padronizar o formato URL |&&| CAPTION."""
    url = message.get("mediaUrl", "")
    content = message.get(msg_key, {})
    caption = content.get(caption_key, "") if isinstance(content, dict) else ""
    return f"{url} |&&| {caption}".strip(" |&&| ")


def live_location_message_handler(message: Dict[str, Any]) -> Tuple[str, str]:
    loc = message.get("liveLocationMessage", {})
    body = f"{loc.get('degreesLatitude', 0.0)} | {loc.get('degreesLongitude', 0.0)}"
    return "real_location", body


def location_message_handler(message: Dict[str, Any]) -> Tuple[str, str]:
    loc = message.get("locationMessage", {})
    body = f"{loc.get('degreesLatitude', 0.0)} | {loc.get('degreesLongitude', 0.0)} | {loc.get('name', '')}"
    return "location", body


def contacts_message_handler(message: Dict[str, Any]) -> Tuple[str, str]:
    if "contactsArrayMessage" in message:
        contacts_raw = message["contactsArrayMessage"].get("contacts", [])
    else:
        contacts_raw = [message.get("contactMessage", {})]

    contacts = []
    for contact in contacts_raw:
        vcard = contact.get("vcard", "")
        waid = re.search(r"waid=(\d+)", vcard)
        phone = waid.group(1) if waid else ""
        contacts.append(
            {
                "name": {"formatted_name": contact.get("displayName", "")},
                "phones": [{"phone": phone}],
            }
        )
    return "contacts", json.dumps(contacts)


def document_message_handler(msg: Dict[str, Any]) -> Tuple[str, str]:
    return "document", _get_media_body(msg, "documentMessage", "fileName")


def image_message_handler(msg: Dict[str, Any]) -> Tuple[str, str]:
    return "image", _get_media_body(msg, "imageMessage")


def video_message_handler(msg: Dict[str, Any]) -> Tuple[str, str]:
    return "video", _get_media_body(msg, "videoMessage")


def sticker_message_handler(msg: Dict[str, Any]) -> Tuple[str, str]:
    return "sticker", _get_media_body(msg, "stickerMessage")


def audio_message_handler(msg: Dict[str, Any]) -> Tuple[str, str]:
    return "audio", msg.get("mediaUrl", "")


def text_message_handler(msg: Dict[str, Any]) -> Tuple[str, str]:
    # Unifica conversation e extendedTextMessage
    body = (
        msg.get("conversation") or msg.get("extendedTextMessage", {}).get("text") or ""
    )
    return "text", body


TREAT_DICT: Dict[str, Callable[[Dict[str, Any]], Tuple[str, str]]] = {
    "liveLocationMessage": live_location_message_handler,
    "locationMessage": location_message_handler,
    "contactMessage": contacts_message_handler,
    "contactsArrayMessage": contacts_message_handler,
    "documentMessage": document_message_handler,
    "imageMessage": image_message_handler,
    "videoMessage": video_message_handler,
    "stickerMessage": sticker_message_handler,
    "audioMessage": audio_message_handler,
    "extendedTextMessage": text_message_handler,
    "conversation": text_message_handler,
}


def parse_message_content(data: Dict[str, Any]) -> Tuple[str, str]:
    """Extrai o tipo e o conteúdo textual/url de uma mensagem da Evolution API."""
    tipo_original = str(data.get("messageType", "unknown"))
    handler = TREAT_DICT.get(tipo_original)

    if handler:
        return handler(data)

    return "unknown", "Conteúdo não suportado"
