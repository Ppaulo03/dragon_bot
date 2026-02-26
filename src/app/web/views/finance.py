from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pathlib import Path
from app.infrastructure.database.postgrees_client import get_db_session
from src.app.infrastructure.database.models import User

templates = Jinja2Templates(directory=str(Path(__file__).parent / "templates"))
router = APIRouter(prefix="/finance", tags=["Finance Management"])


@router.get("", response_class=HTMLResponse)
async def users_view(
    request: Request, error: str = None, db: AsyncSession = Depends(get_db_session)
):
    """Página de Seleção de Usuário (Navegador)"""
    result = await db.execute(select(User))
    users = result.scalars().all()
    return templates.TemplateResponse(
        "finance/users_list.j2",
        {"request": request, "users": users, "error": error},
    )
