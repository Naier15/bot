from aiogram import Dispatcher, types
from aiogram.fsm.storage.memory import MemoryStorage
from apscheduler.schedulers.asyncio import AsyncIOScheduler
import asyncio, logging

from app import App, menu_router, buildings_router, profile_router, subscription_router, estate_router
from app.utils import log


# logging.basicConfig(
#     filename = f'./log.log',
#     level = logging.INFO, 
#     format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
#     encoding = 'utf-8'
# )


from aiogram import Router, F, types
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from dataclasses import dataclass
from typing import Optional, Self
from aiogram import Bot
from aiogram.fsm.state import State

from app import form_buttons, log, text


# router = Router()

# @log
# @router.message(CommandStart())
# async def start(msg: types.Message, state: FSMContext):
#     await msg.answer(
#         'Hello'
#     )
    
# @router.message(F.text)
# async def start2(msg: types.Message, state: FSMContext):
#     print(msg.text)
#     await msg.edit_text

@log
async def main():
	await App.bot.delete_webhook(drop_pending_updates = True)
      
	commands = [
        types.BotCommand(command = 'start', description = 'Старт'),
		types.BotCommand(command = 'menu', description = 'В меню'),
        types.BotCommand(command = 'state', description = 'Состояние')
    ]
	await App.bot.set_my_commands(commands, types.BotCommandScopeDefault())
	
	scheduler = AsyncIOScheduler(timezone = 'Asia/Vladivostok')
    
	dp = Dispatcher(storage = MemoryStorage())
	dp.include_router(buildings_router)
	dp.include_router(profile_router)
	dp.include_router(subscription_router)
	dp.include_router(estate_router)
	dp.include_router(menu_router)
	print('Start')
	await dp.start_polling(App.bot, allowed_updates = dp.resolve_used_update_types())


if __name__ == '__main__':
    asyncio.run(main())