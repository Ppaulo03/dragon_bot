from fastapi import APIRouter, HTTPException
from fastapi.responses import HTMLResponse
from .client import evolution_client
from pathlib import Path

router = APIRouter(prefix="/evolution", tags=["Evolution Provider"])
html_path = Path(__file__).parent / "template" / "status_page.html"


@router.get("")
async def evolution_root():
    html_content = html_path.read_text()
    return HTMLResponse(content=html_content, media_type="text/html")


@router.get("/status")
async def get_evolution_status():
    try:
        status = await evolution_client.check_status()
        if status == "open":
            return {"connected": True}

        qrcode_data = await evolution_client.get_qrcode()
        # Assume que qrcode_data vem como base64 ou URL
        return {"connected": False, "qrcode": qrcode_data}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/disconnect")
async def disconnect():
    await evolution_client.logout()
    return {"status": "success"}
