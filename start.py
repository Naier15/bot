import asyncio
from aiogram import Dispatcher, types
from aiogram.fsm.storage.memory import MemoryStorage
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from internal.config import Config
config = Config()
config.setup()

from entities import App, Dispatch
from internal import log
from router import menu_router # Страница главного меню и раздел помощь
from router import buildings_router # Разделы квартир и офисов
from router import subscription_router # Раздел подписок - просмотр, удаление
from router import property_router # Раздел добавления новой подписки


@log
async def main():
    app = App()
    await app.bot.delete_webhook(drop_pending_updates = True)  
    if config.TO_SET_COMMANDS:
        commands = [ types.BotCommand(command = 'menu', description = 'В меню') ]
        await app.bot.set_my_commands(commands, types.BotCommandScopeDefault())
    scheduler = AsyncIOScheduler(timezone = config.REGION)
    Dispatch().setup(scheduler)
    scheduler.start()
    
    dp = Dispatcher(storage = MemoryStorage())
    [dp.include_router(router) for router in (
		buildings_router,
		subscription_router,
		property_router,
		menu_router
	)]
    await dp.start_polling(app.bot, allowed_updates = dp.resolve_used_update_types())

if __name__ == '__main__':
    asyncio.run(main())