import asyncio, datetime
from aiogram import Dispatcher, types
from aiogram.fsm.storage.memory import MemoryStorage
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from config import Config
from app import log, App
from pages import menu_router # Страница главного меню и раздел помощь
from pages import buildings_router # Разделы квартир и офисов
from pages import profile_router # Раздел профиля, его создания и редактирования
from pages import subscription_router # Раздел подписок - просмотр, удаление
from pages import property_router # Раздел добавления новой подписки


# logging.basicConfig(
#     filename = f'./log.log',
#     level = logging.INFO, 
#     format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
#     encoding = 'utf-8'
# )

@log
async def main():
    await App.bot.delete_webhook(drop_pending_updates = True)  
    commands = [
		types.BotCommand(command = 'start', description = 'Старт'),
		types.BotCommand(command = 'menu', description = 'В меню'),
        types.BotCommand(command = 'state', description = 'Состояние')
    ]
    await App.bot.set_my_commands(commands, types.BotCommandScopeDefault())
	
    scheduler = AsyncIOScheduler(timezone = Config().REGION)
    # scheduler.add_job(
    #     App.dispatch_to_clients, 
    #     trigger = 'cron', 
    #     day_of_week = '0,1,2,3,4,5,6', 
    #     # hour = 16, 
    #     # minute = 20,
    #     minute = '*',    # testing
    #     start_date = datetime.datetime.now()
    # )
    # scheduler.start()
    
    dp = Dispatcher(storage = MemoryStorage())
    [dp.include_router(router) for router in (
		buildings_router,
		profile_router,
		subscription_router,
		property_router,
		menu_router
	)]
    print('Start')
    await dp.start_polling(App.bot, allowed_updates = dp.resolve_used_update_types())


if __name__ == '__main__':
    asyncio.run(main())