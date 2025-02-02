from typing import Iterable, Optional
from aiogram import types
import math


class App:
    def __init__(self):
        self.current_page: int = 1
        self.chats_counter: int = 0
        self.items_per_page: int = 10
        self.chats: Iterable[dict] = self.generate_chats(1000)

    def generate_chats(self, quantity: int) -> Iterable[dict]:
        self.chats_counter = 0
        chats = []
        for idx in range(quantity):
            chats.append({'title': f'Чат №{idx}', 'id': f'{idx}'})
            self.chats_counter += 1
        return chats
    
    def make_page(self, page: int) -> Optional[types.InlineKeyboardMarkup]:
        if page < 1 or math.ceil(self.chats_counter / self.items_per_page) <= page:
            return
       
        self.current_page = page   
        index = (self.current_page - 1) * self.items_per_page
        chats_to_show = self.chats[index:index+self.items_per_page]
        
        if len(chats_to_show) == 0:
            return
        buttons = types.InlineKeyboardMarkup()
        items = []
        for chat in chats_to_show:
            items.append(types.InlineKeyboardButton(text=chat['title'], callback_data=chat['id']))
        buttons.add(*items, row_width=1)
        buttons.add(*[
            types.InlineKeyboardButton(text='<', callback_data='back'),
            types.InlineKeyboardButton(text=f' {self.current_page}/{math.ceil(self.chats_counter / self.items_per_page)} '.center(12, '-'), callback_data='page'),
            types.InlineKeyboardButton(text='>', callback_data='next')
        ], row_width=3)
        return buttons
    
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
