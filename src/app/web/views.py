from typing import List
from fastapi import APIRouter, BackgroundTasks, Depends, Request, UploadFile
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from pathlib import Path
from app.core.services.config_service import config_service
from app.config import settings
from app.infrastructure import storage
from app.utils.text import add_uuid_to_filename
from app.utils.image import calculate_phash
from app.web.utils.RuleFormParser import RuleFormParser, TriggerRule

templates = Jinja2Templates(directory=str(Path(__file__).parent / "templates"))
router = APIRouter(tags=["Interface Visual"])


@router.get("/trigger-config", response_class=HTMLResponse)
async def trigger_config_page(request: Request):
    data = config_service.load_triggers_data()
    constants = config_service.get_constants()
    return templates.TemplateResponse(
        "trigger_config.j2",
        {
            "request": request,
            "triggers": data["triggers"],
            "no_triggers": data["no_triggers"],
            "options": constants,
            "storage_url": f"http://localhost:9000/{settings.BUCKET_NAME}/",
        },
    )


@router.post("/trigger-config")
async def save_config(
    background_tasks: BackgroundTasks,
    request: Request,
    parser: RuleFormParser = Depends(),
):
    rules: List[TriggerRule] = await parser(request)
    triggers = []
    no_triggers = []

    used_files = set()
    for rule in rules:
        if rule.matcher == "image_similarity":
            if rule.trigger_upload:

                rule.params.pattern = await upload_to_storage(
                    rule.trigger_upload, "triggers"
                )
                await rule.trigger_upload.seek(0)
                rule.params.hash = calculate_phash(await rule.trigger_upload.read())
            used_files.add(rule.params.pattern)

        for f in rule.new_files:
            path = await upload_to_storage(f, "assets")
            rule.existing_files.append(path)

        used_files.update(rule.existing_files)
        if rule.matcher == "always":
            no_triggers.append(rule.dict_for_yaml())
        else:
            triggers.append(rule.dict_for_yaml())

    config_service.save_triggers_data(
        {"triggers": triggers, "no_triggers": no_triggers}
    )
    background_tasks.add_task(cleanup_unused_files, used_files)
    return RedirectResponse(url="/trigger-config", status_code=303)


async def upload_to_storage(file: UploadFile, folder: str = "assets"):
    if not file or not file.filename:
        return None
    filename = add_uuid_to_filename(file.filename)
    path = f"{folder}/{filename}"
    await storage.upload_file(path, file.file, content_type=file.content_type)
    return path


async def cleanup_unused_files(used_files: set):
    asset_files = await storage.list_all_files("assets")
    trigger_files = await storage.list_all_files("triggers")
    all_files = set(asset_files + trigger_files)
    for f in all_files:
        if f not in used_files:
            await storage.delete_file(f)
