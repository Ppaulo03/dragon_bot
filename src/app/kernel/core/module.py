from abc import ABC, abstractmethod
from pathlib import Path
from fastapi import FastAPI, APIRouter
from fastapi.staticfiles import StaticFiles
from typing import Optional, List
from .interfaces import MessageData


class BaseModule(ABC):
    """Contrato que define o que é um Módulo no Dragon Bot."""

    @property
    @abstractmethod
    def name(self) -> str:
        pass

    @property
    def module_path(self) -> Path:
        """Retorna o caminho da pasta do módulo"""
        import sys

        module_file = sys.modules[self.__class__.__module__].__file__
        return Path(module_file).parent

    def setup_resources(self, app: FastAPI, template_dirs: List[Path]):
        t_dir = self.module_path / "templates"
        if t_dir.exists():
            template_dirs.append(str(t_dir))

        s_dir = self.module_path / "static"
        if s_dir.exists():
            app.mount(
                f"/static/{self.name}",
                StaticFiles(directory=str(s_dir)),
                name=f"static_{self.name}",
            )

    @abstractmethod
    def register_routes(self) -> Optional[APIRouter]:
        pass

    @abstractmethod
    async def handle_message(self, message: MessageData):
        pass

    @abstractmethod
    async def startup(self, app: FastAPI):
        pass

    @abstractmethod
    async def shutdown(self, app: FastAPI):
        pass
