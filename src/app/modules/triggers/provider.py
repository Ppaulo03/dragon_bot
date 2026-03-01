from app.kernel import MessageData, BaseModule
from .manager import trigger_manager
from .web import web_router
from .core.services.factory import service_factory


class TriggersModule(BaseModule):
    @property
    def name(self):
        return "triggers"

    def register_routes(self):
        return web_router

    async def handle_message(self, message: MessageData):
        await trigger_manager.process(message)

    async def startup(self, app):
        triggers, no_triggers = await service_factory.load_triggers()
        trigger_manager.primary_triggers = triggers
        trigger_manager.fallback_triggers = no_triggers

    async def shutdown(self, app):
        pass
