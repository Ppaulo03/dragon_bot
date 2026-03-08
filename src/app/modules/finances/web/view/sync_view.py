from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
import json
from app.kernel import settings

router = APIRouter()


@router.get("/sync", response_class=HTMLResponse)
async def sync_qr_view(request: Request):
    # Hardcoded temp_token as per user request
    temp_token = "convite-123"
    api_url = settings.SYNC_API_URL.rstrip("/") + "/api/internal/finance"

    qr_payload = {"url": api_url, "temp_token": temp_token}

    payload_json = json.dumps(qr_payload)

    templates = request.app.state.templates
    return templates.TemplateResponse(
        "finances/sync/sync_page.j2",
        {"request": request, "payload": payload_json, "api_url": api_url},
    )
