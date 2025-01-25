from aiogram import Dispatcher, types
from aiogram.fsm.storage.memory import MemoryStorage
from apscheduler.schedulers.asyncio import AsyncIOScheduler
import asyncio, datetime

from app.router import router
from app.app import Context, App



# @bot.callback_query_handler(func=lambda call: call.data in ('next', 'back'))
# def next(call: types.CallbackQuery):
# 	buttons = None
# 	if call.data == 'next':
# 		buttons = app.make_page(app.current_page + 1)
# 	elif call.data == 'back':
# 		buttons = app.make_page(app.current_page - 1)
	
# 	if buttons:
# 		bot.send_message(call.message.chat.id, 'Выберете чат:', reply_markup=buttons)

# @bot.callback_query_handler(func=lambda call: True)
# def other(call: types.CallbackQuery):
# 	print(f'Message recieved {call.data}')


# @bot.message_handler(commands=['start'])
# def start(message: types.Message):
# 	markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
# 	btn1 = types.KeyboardButton ("Каталог квартир")
# 	btn2 = types.KeyboardButton ("Каталог коммерции")
# 	btn3 = types.KeyboardButton ("Мой профиль")
# 	btn4 = types.KeyboardButton ("Фотоотчеты")
# 	btn5 = types.KeyboardButton ("Помощь")
# 	markup.add(btn1, btn2, btn3, btn4, btn5)
# 	send_mess = f"Привет, {message.from_user.first_name}!\nПогнали?"
# 	bot.send_message(message.chat.id, send_mess, reply_markup=markup)


# @bot.message_handler(content_types=['text'])
# def mess(message: types.Message):
# 	buttons = app.make_page(1)
# 	if buttons:
# 		bot.send_message(message.chat.id, 'Выберете чат:', reply_markup=buttons)


async def main():
	context = Context()
	config = context.config()

	app = App()

	bot = context.bot()
	await bot.delete_webhook(drop_pending_updates = True)
      
	commands = [
        types.BotCommand(command='start', description='Старт'),
		types.BotCommand(command='menu', description='В меню'),
		types.BotCommand(command='help', description='Помощь')
    ]
	await bot.set_my_commands(commands, types.BotCommandScopeDefault())
	
	scheduler = AsyncIOScheduler(timezone = 'Asia/Vladivostok')
	# scheduler.add_job(
    #     app.dispatch_to_users, 
    #     trigger = 'cron', 
    #     # day_of_week = '1,4', 
    #     # hour = 16, 
    #     # minute = 20,
    #     minute = '*',    #testing
    #     start_date = datetime.datetime.now()
    # )
	# scheduler.start()
    
	dp = Dispatcher(storage=MemoryStorage())
	dp.include_router(router)
	await dp.start_polling(bot, allowed_updates = dp.resolve_used_update_types())
	await app.run(bot)


if __name__ == '__main__':
    asyncio.run(main())