from pathlib import Path
from fastapi import FastAPI
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from app.kernel.core.registry import module_registry


def setup_views(app: FastAPI) -> Jinja2Templates:
    base_dir = Path("src/app")
    template_dirs = [str(base_dir / "templates")]

    app.mount(
        "/static/global",
        StaticFiles(directory=str(base_dir / "static")),
        name="static_global",
    )

    for module in module_registry.get_all():
        module.setup_resources(app, template_dirs)
    return Jinja2Templates(directory=template_dirs)
