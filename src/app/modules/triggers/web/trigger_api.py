from fastapi import APIRouter, HTTPException
from app.modules.triggers.core.services.config_service import config_service

router = APIRouter(prefix="/api/internal", tags=["Trigger Config API"])


@router.get("/constants")
async def get_constants():
    return config_service.get_constants()


@router.get("/config")
async def get_config():
    return config_service.load_triggers_data()


@router.post("/config")
async def update_config(data: dict):
    success = config_service.save_triggers_data(data)
    if not success:
        raise HTTPException(status_code=500, detail="Erro ao salvar configuração")
    return {"status": "success"}
