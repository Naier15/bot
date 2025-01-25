from app.context import Context
from aiogram import Router, F, types


MENU = 'Меню'
FLATS = 'Каталог квартир'
OFFICES = 'Помещения для бизнеса'
PROFILE = 'Мой профиль'
PHOTO = 'Фотоотчеты'
HELP = 'Помощь'
BACK = 'Назад'

class App:
    
    @staticmethod
    def menu() -> types.ReplyKeyboardMarkup:
        btns = [
            [
                types.KeyboardButton(text=FLATS),
                types.KeyboardButton(text=PROFILE)
            ],
            [
                types.KeyboardButton(text=OFFICES),
                types.KeyboardButton(text=PHOTO)
            ],
            [types.KeyboardButton(text=HELP)]
        ]
        return types.ReplyKeyboardMarkup(keyboard=btns, resize_keyboard=True, one_time_keyboard=True, input_field_placeholder='Выберете действие:')