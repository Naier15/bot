from aiogram import types
from typing import Callable, Any
import logging, inspect, os


def log(func: Callable):
    def inner(*args: tuple, **kwargs: dict) -> Any:
        # logging.getLogger(os.path.abspath(inspect.getfile(func))).info(func.__name__)
        print(os.path.abspath(inspect.getfile(func)), func.__name__)
        return func(*args, **kwargs)
    return inner

def form_buttons(btn: list, input_prompt: str = 'Выберете действие:') -> types.ReplyKeyboardMarkup:
    return types.ReplyKeyboardMarkup(
        keyboard = btn, 
        resize_keyboard = True, 
        one_time_keyboard = True, 
        input_field_placeholder = input_prompt
    )