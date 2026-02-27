import re
import os
import uuid


def sanitize_name(name: str) -> str:
    name = re.sub(r"[^\w\s-]", "", name).strip().lower()
    name = re.sub(r"[-\s]+", "-", name)
    return name


def add_uuid_to_filename(filename: str) -> str:
    short_id = uuid.uuid4().hex[:4]
    ext = os.path.splitext(filename)[1]
    name = sanitize_name(os.path.splitext(filename)[0])
    unique_name = f"{name}_{short_id}{ext}"
    return unique_name
