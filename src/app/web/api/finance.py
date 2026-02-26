import re

from fastapi import APIRouter, Form, Depends, status
from fastapi.responses import RedirectResponse, JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from app.infrastructure.database.postgrees_client import get_db_session
from src.app.infrastructure.database.models import User

router = APIRouter(prefix="/finance", tags=["Finance API"])


@router.post("/users")
async def api_add_user(
    name: str = Form(...),
    jid: str = Form(...),
    db: AsyncSession = Depends(get_db_session),
):
    clean_id = re.sub(r"\D", "", jid)

    try:
        existing = await db.get(User, clean_id)
        if existing:
            raise ValueError(
                f"O número {clean_id} já está vinculado ao perfil '{existing.name}'."
            )

        new_user = User(id=clean_id, name=name)
        db.add(new_user)
        await db.commit()
        return RedirectResponse(url="/finance", status_code=status.HTTP_303_SEE_OTHER)
    except ValueError as e:
        return RedirectResponse(
            url=f"/finance?error={str(e)}", status_code=status.HTTP_303_SEE_OTHER
        )


@router.delete("/users/{user_id}")
async def api_delete_user(user_id: str, db: AsyncSession = Depends(get_db_session)):
    """API para deletar usuário"""
    user = await db.get(User, user_id)
    if user:
        await db.delete(user)
        await db.commit()
        return {"message": "Usuário removido"}
    return JSONResponse(status_code=404, content={"message": "Não encontrado"})
