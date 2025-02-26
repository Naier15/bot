from aiogram import types
from typing import Callable, Any, Optional, Self
import logging, inspect, math, os, sys, django
import django.conf


# Помощник создания markup и inline кнопок
class Markup:
    __btns: Optional[types.ReplyKeyboardMarkup | types.InlineKeyboardMarkup] = None

    @staticmethod
    def current() -> Optional[types.ReplyKeyboardMarkup | types.InlineKeyboardMarkup]:
        return Markup.__btns
    
    @staticmethod
    def set(btns: types.ReplyKeyboardMarkup | types.InlineKeyboardMarkup) -> types.ReplyKeyboardMarkup | types.InlineKeyboardMarkup:
        Markup.__btns = btns
        return Markup.__btns
    
    @staticmethod
    def bottom_buttons(btn: list, input_prompt: str = 'Выберете действие:') -> types.ReplyKeyboardMarkup:
        return Markup.set(
            types.ReplyKeyboardMarkup(
                keyboard = btn, 
                resize_keyboard = True, 
                one_time_keyboard = True, 
                input_field_placeholder = input_prompt
            )
        )

    @staticmethod
    def inline_buttons(btn: list) -> types.InlineKeyboardMarkup:
        return Markup.set(
            types.InlineKeyboardMarkup(
                inline_keyboard = btn
            )
        )
    
    @staticmethod
    def no_buttons() -> types.ReplyKeyboardRemove:
        return types.ReplyKeyboardRemove()
    
# Помощник создания inline редактора для выбора города, жк и дома
class PageBuilder:
    current_page: int = 1
    quantity: int = 0
    items_per_page: int = 8
    choices: list[str] = []

    @classmethod
    def using(cls, choices: list[dict]) -> Self:
        cls.quantity = len(choices)
        cls.choices = choices
        cls.current_page = 1
        return cls
    
    @classmethod
    def next(cls) -> None:
        if math.ceil(cls.quantity / cls.items_per_page) < cls.current_page + 1:
            return
        cls.current_page += 1
    
    @classmethod
    def previous(cls) -> None:
        if cls.current_page - 1 < 1:
            return
        cls.current_page -= 1
    
    @classmethod
    def current(cls) -> Optional[types.InlineKeyboardMarkup]:
        if cls.quantity == 0:
            return
        index = (cls.current_page - 1) * cls.items_per_page
        chunk = cls.choices[index:index+cls.items_per_page]
        if len(chunk) == 0:
            return
        buttons = []
        for choice in chunk:
            buttons.append([types.InlineKeyboardButton(
                text = choice['name'], 
                callback_data = choice['id']
            )])
        buttons += [[
            types.InlineKeyboardButton(text = '<', callback_data = 'prev'),
            types.InlineKeyboardButton(text = f' {cls.current_page}/{math.ceil(cls.quantity / cls.items_per_page)} '.center(12, '-'), callback_data = 'page'),
            types.InlineKeyboardButton(text = '>', callback_data = 'next')
        ]]
        bottom_btns = [[
            types.InlineKeyboardButton(text = 'В меню', callback_data = 'menu'),
            types.InlineKeyboardButton(text = 'Назад', callback_data = 'back')
        ]]
        buttons += bottom_btns
         
        return Markup.inline_buttons(buttons)
    
# Подключение к Django
def connect_django(path_to_django: str):
	sys.path.append(path_to_django)
	os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'bashni.settings')
	django.setup()
	print(f'--- Connected to Django models - {django.conf.settings.configured} ---')

# Логгирование
def log(func: Callable):
    def inner(*args: tuple, **kwargs: dict) -> Any:
        # logging.getLogger(os.path.abspath(inspect.getfile(func))).info(func.__name__)
        print(os.path.abspath(inspect.getfile(func)), func.__name__)
        try:
            return func(*args, **kwargs)
        except Exception as ex:
            print(ex)
    return inner