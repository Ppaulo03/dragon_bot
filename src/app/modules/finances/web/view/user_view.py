from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession

# Imports internos
from app.modules.finances.database import get_db_session
from app.modules.finances.database.models import User

router = APIRouter()


@router.get("/user/{user_id}/edit", response_class=HTMLResponse)
async def edit_user_view(
    request: Request, user_id: str, db: AsyncSession = Depends(get_db_session)
):
    user = await db.get(User, user_id)
    if not user:
        return RedirectResponse(url="/finance?error=Usuário não encontrado")

    templates = request.app.state.templates
    return templates.TemplateResponse(
        "finance/user_edit.j2", {"request": request, "user": user, "options": {}}
    )
