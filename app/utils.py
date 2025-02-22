from aiogram import types
from typing import Callable, Any, Optional
import logging, inspect, os, sys, django
import django.conf


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
    
def connect_django(path_to_django: str):
	sys.path.append(path_to_django)
	os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'bashni.settings')
	django.setup()
	print(f'--- Connected to Django models - {django.conf.settings.configured} ---')

def log(func: Callable):
    def inner(*args: tuple, **kwargs: dict) -> Any:
        # logging.getLogger(os.path.abspath(inspect.getfile(func))).info(func.__name__)
        print(os.path.abspath(inspect.getfile(func)), func.__name__)
        return func(*args, **kwargs)
    return inner