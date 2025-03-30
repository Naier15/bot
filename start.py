import asyncio, datetime, logging, os
from aiogram import Dispatcher, types
from aiogram.fsm.storage.memory import MemoryStorage
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from config import Config
from app import App, log
from router import menu_router # Страница главного меню и раздел помощь
from router import buildings_router # Разделы квартир и офисов
from router import profile_router # Раздел профиля, его создания и редактирования
from router import subscription_router # Раздел подписок - просмотр, удаление
from router import property_router # Раздел добавления новой подписки


config = Config()
logging.basicConfig(
    filename = os.path.abspath(os.path.join(os.path.dirname(__file__), config.LOG_FILE)),
    level = logging.INFO, 
    format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    encoding = 'utf-8'
)

async def main():
    log(main)
    app = App()
    await app.bot.delete_webhook(drop_pending_updates = True)  
    if config.TO_SET_COMMANDS:
        commands = [ types.BotCommand(command = 'menu', description = 'В меню') ]
        await app.bot.set_my_commands(commands, types.BotCommandScopeDefault())
    scheduler = AsyncIOScheduler(timezone = config.REGION)
    if config.DEBUG:
        scheduler.add_job(
            app.dispatch_to_clients, 
            trigger = 'cron', 
            day_of_week = '0,1,2,3,4,5,6',
            minute = '*',
            start_date = datetime.datetime.now()
        )
    else:
        scheduler.add_job(
            app.dispatch_to_clients, 
            trigger = 'cron', 
            day_of_week = '0,1,2,3,4,5,6',
            hour = int(config.DISPATCH_TIME.split(':')[0]), 
            minute = int(config.DISPATCH_TIME.split(':')[1]),
            start_date = datetime.datetime.now()
        )
    scheduler.start()
    
    dp = Dispatcher(storage = MemoryStorage())
    [dp.include_router(router) for router in (
		buildings_router,
		profile_router,
		subscription_router,
		property_router,
		menu_router
	)]
    print('Start')
    await dp.start_polling(app.bot, allowed_updates = dp.resolve_used_update_types())


if __name__ == '__main__':
    asyncio.run(main())