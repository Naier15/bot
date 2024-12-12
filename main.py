from typing import Iterable
import webbrowser
import telebot, math
from telebot import types

from telebot.util import async_dec


# bot = telebot.AsyncTeleBot('1291275643:AAHIk28uq57pVT5ZZz-IEQllgQhP5_mwx7s')
bot = telebot.TeleBot('1291275643:AAHIk28uq57pVT5ZZz-IEQllgQhP5_mwx7s')
current_page: int = 1
chats_counter: int = 0
items_per_page: int = 10
last_message: int = None

@async_dec()
def generate_chats() -> Iterable[dict]:
	global chats_counter
	chats_counter = 0
	chats = []
	for idx in range(10000):
		chats.append({'title': f'Чат №{idx}', 'id': f'{idx}{idx}'})
		chats_counter += 1
	return chats

@async_dec()
def make_page(message: types.Message, current_page: int) -> Iterable:
	global items_per_page, last_message
	# if last_message:
	# 	bot.delete_messages(message.chat.id, [last_message])

	chats = generate_chats()
	
	index = (current_page - 1) * items_per_page
	chats_to_show = chats[index:index+items_per_page]
	
	if len(chats_to_show) == 0:
		return
	items = []
	for chat in chats_to_show:
		items.append(types.InlineKeyboardButton(text=chat['title'], callback_data=chat['id']))
	buttons = types.InlineKeyboardMarkup()
	buttons.add(*items, row_width=1)
	buttons.add(*[
		types.InlineKeyboardButton(text='<', callback_data='back'),
		types.InlineKeyboardButton(text=f' {current_page}/{math.ceil(chats_counter / items_per_page)} '.center(12, '-'), callback_data='page'),
		types.InlineKeyboardButton(text='>', callback_data='next')
	], row_width=3)

	if last_message:
		msg = bot.edit_message_text('Выберете чат:', message.chat.id, last_message, reply_markup=buttons)
	else:
		msg = bot.send_message(message.chat.id, 'Выберете чат:', reply_markup=buttons)
	last_message = msg.message_id
	print('hi')


@bot.callback_query_handler(func=lambda call: call.data in ('next', 'back'))
@async_dec()
def next(call: types.CallbackQuery):
	global current_page
	if call.data == 'next':
		if math.ceil(chats_counter / items_per_page) <= current_page:
			return
		current_page += 1
		make_page(call.message, current_page)
	elif call.data == 'back':
		if current_page == 1:
			return
		current_page -= 1
		make_page(call.message, current_page)

@bot.callback_query_handler(func=lambda call: True)
@async_dec()
def other(call: types.CallbackQuery):
	print(f'Message recieved {call.data}')


@bot.message_handler(commands=['start'])
@async_dec()
def start(message: types.Message):
	markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
	btn1 = types.KeyboardButton ("Каталог квартир")
	btn2 = types.KeyboardButton ("Каталог коммерции")
	btn3 = types.KeyboardButton ("Мой профиль")
	btn4 = types.KeyboardButton ("Фотоотчеты")
	btn5 = types.KeyboardButton ("Помощь")
	markup.add(btn1, btn2, btn3, btn4, btn5)
	send_mess = f"Привет, {message.from_user.first_name}!\nПогнали?"
	bot.send_message(message.chat.id, send_mess, reply_markup=markup)

@bot.message_handler(content_types=['text'])
@async_dec()
def mess(message: types.Message):
	print('start')
	global current_page
	make_page(message, current_page)
	
	# bot.edit_message_text('Хотел другой текст', message.chat.id, msg.message_id)
	# bot.delete_messages(message.chat.id, [msg.message_id, msg2.message_id])




if __name__ == '__main__':
	bot.polling(none_stop=True)
  