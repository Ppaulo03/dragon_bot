from app.core.interfaces import MessageData, MediaType
from .schemas import EvolutionWebhook
from .client import EvolutionClient
from .parser import parse_message_content


def process_evolution_message(data: EvolutionWebhook) -> MessageData:
    data_message = {**(data.data.message or {}), "messageType": data.data.message_type}
    tipo_str, body = parse_message_content(data_message)

    tipo_map = {
        "conversation": MediaType.TEXT,
        "extendedTextMessage": MediaType.TEXT,
        "imageMessage": MediaType.IMAGE,
        "audioMessage": MediaType.AUDIO,
        "stickerMessage": MediaType.STICKER,
    }
    tipo_final = tipo_map.get(tipo_str, MediaType.TEXT)

    msg_keys = data.data.key
    remote_jid = msg_keys.remote_jid

    is_group = "@g.us" in remote_jid
    numero = remote_jid if is_group else remote_jid.split("@")[0]

    return MessageData(
        message_id=msg_keys.id,
        nome=data.data.push_name or "",
        numero=numero,
        tipo=tipo_final,
        body=body,
        is_group=is_group,
        instance=data.instance,
        client=EvolutionClient(),
        mentioned=False,
    )
