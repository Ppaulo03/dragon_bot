from fastapi import APIRouter, Form, Request, Depends
from fastapi.responses import HTMLResponse
from sqlalchemy.ext.asyncio import AsyncSession


from app.modules.finances.database import get_db_session
from app.modules.finances.repository import UserRepository


router = APIRouter()


@router.get("/", response_class=HTMLResponse)
async def users_view(
    request: Request, error: str = None, db: AsyncSession = Depends(get_db_session)
):
    repo = UserRepository(db)
    users = await repo.list()

    templates = request.app.state.templates
    context = {"request": request, "users": users, "error": error}

    if request.headers.get("HX-Request"):
        return templates.TemplateResponse(
            "finances/index/partials/user_items.j2", context
        )

    return templates.TemplateResponse(
        "finances/index/index.j2",
        context,
    )


@router.post("/")
async def api_add_user(
    request: Request,
    name: str = Form(...),
    jid: str = Form(...),
    db: AsyncSession = Depends(get_db_session),
):
    repo = UserRepository(db)
    try:
        await repo.add(name=name, jid=jid)
        users = await repo.list()
        return request.app.state.templates.TemplateResponse(
            "finances/index/partials/user_items.j2",
            {"request": request, "users": users},
        )
    except ValueError as e:
        return request.app.state.templates.TemplateResponse(
            "finances/index/partials/err.j2",
            {"request": request, "message": str(e)},
            # status_code=200,
            headers={"HX-Retarget": "#error-container"},
        )
