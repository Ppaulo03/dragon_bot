from app.kernel import MessageData, BaseModule
from .database import client, Base
from .web import web_router


class FinanceModule(BaseModule):
    @property
    def name(self):
        return "finance"

    def register_routes(self):
        return web_router

    async def handle_message(self, message: MessageData):
        pass

    async def startup(self, app):
        await client.setup_database(Base.metadata)

    async def shutdown(self, app):
        await client.close()
