import asyncio, datetime, logging, os, sys
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
from router import send_favorites_obj


config = Config()

formatter = logging.Formatter('%(asctime)s -- %(name)s -- %(levelname)s -- %(message)s')
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

for handler in logger.handlers:
    logger.removeHandler(handler)

# Логи в файл
file_handler = logging.FileHandler(
    filename=os.path.abspath(os.path.join(os.path.dirname(__file__), config.LOG_FILE)),
    encoding='utf-8'
)
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

# Логи в консоль
console = logging.StreamHandler(sys.stdout)
console.setFormatter(formatter)
logger.addHandler(console)

@log
async def main():
    app = App()
    await app.bot.delete_webhook(drop_pending_updates = True)  
    if config.TO_SET_COMMANDS:
        commands = [ types.BotCommand(command = 'menu', description = 'В меню') ]
        await app.bot.set_my_commands(commands, types.BotCommandScopeDefault())
    scheduler = AsyncIOScheduler(timezone = config.REGION)
    if config.DEBUG:
        # scheduler.add_job(
        #     app.dispatch_to_clients, 
        #     trigger = 'cron', 
        #     day_of_week = '0,1,2,3,4,5,6',
        #     minute = '*',
        #     start_date = datetime.datetime.now()
        # )
        pass
    else:
        scheduler.add_job(
            app.dispatch_to_clients, 
            trigger = 'cron', 
            day_of_week = '0,1,2,3,4,5,6',
            hour = int(config.DISPATCH_TIME.split(':')[0]), 
            minute = int(config.DISPATCH_TIME.split(':')[1]),
            start_date = datetime.datetime.now()
        )
        scheduler.add_job(
            send_favorites_obj,
            trigger='cron',
            day_of_week='0,1,2,3,4,5,6',
            hour=14,
            minute=50,
            start_date=datetime.datetime.now()
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
