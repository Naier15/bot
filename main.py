from aiogram import Dispatcher, types
from aiogram.fsm.storage.memory import MemoryStorage
from apscheduler.schedulers.asyncio import AsyncIOScheduler
import asyncio, logging

from app import App, menu_router, buildings_router, profile_router, subscription_router, estate_router
from app.utils import log


logging.basicConfig(
    filename = f'./log.log',
    level = logging.INFO, 
    format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    encoding = 'utf-8'
)

@log
async def main():
	bot = App.bot
	await bot.delete_webhook(drop_pending_updates = True)
      
	commands = [
        types.BotCommand(command = 'start', description = 'Старт'),
		types.BotCommand(command = 'menu', description = 'В меню'),
        types.BotCommand(command = 'state', description = 'Состояние')
    ]
	await bot.set_my_commands(commands, types.BotCommandScopeDefault())
	
	scheduler = AsyncIOScheduler(timezone = 'Asia/Vladivostok')
    
	dp = Dispatcher(storage = MemoryStorage())
	dp.include_router(buildings_router)
	dp.include_router(profile_router)
	dp.include_router(subscription_router)
	dp.include_router(estate_router)
	dp.include_router(menu_router)
	print('Start')
	await dp.start_polling(bot, allowed_updates = dp.resolve_used_update_types())


if __name__ == '__main__':
    asyncio.run(main())