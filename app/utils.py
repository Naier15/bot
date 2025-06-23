from functools import partial, wraps
from time import perf_counter

import aiofiles.os
from aiogram import types
from PIL import Image
from io import BytesIO
from typing import Optional, Self, Coroutine
import logging, inspect, math, os, sys, django, aiohttp, aiofiles
import django.conf
from asgiref.sync import sync_to_async


to_async = partial(sync_to_async, thread_sensitive = False)

class Markup:
    '''Помощник создания markup и inline кнопок'''
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
    
class PageBuilder:
    '''Помощник создания inline редактора для выбора города, жк и дома'''
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
    
def connect_django(path_to_django: str):
    '''Подключение к Django'''
    sys.path.append(path_to_django)
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'bashni.settings')
    if not django.conf.settings.configured:
        django.setup()
        logging.debug(f'--- Connected to Django models - {django.conf.settings.configured} ---')

def log(coro: Coroutine) -> Coroutine:
    '''Декоратор для логгирования'''
    @wraps(coro)
    async def wrapper(*args, **kwargs):
        logger = logging.getLogger(os.path.abspath(inspect.getfile(coro)))
        logger.debug(os.path.abspath(inspect.getfile(coro)), coro.__name__)
        try:
            result = await coro(*args, **kwargs)
        except Exception as ex:
            logger.error(f'{coro.__name__} - {ex}')
        else:
            logger.debug(coro.__name__)
            return result
    return wrapper

def time(coro: Coroutine) -> Coroutine:
    '''Декоратор для отображения времени отработки функции'''
    @wraps(coro)
    async def wrapper(*args, **kwargs):
        start = perf_counter()
        result = await coro(*args, **kwargs)
        print(f'[{coro.__name__}] takes {perf_counter() - start} seconds')
        return result
    return wrapper

class Tempfile:
    def __init__(self, temp_name: str, url: str) -> Self:
        self._temp_path = os.path.abspath(os.path.join(os.path.dirname(__file__), 'temp'))
        self._temp_name = temp_name
        self._url = url

    async def __aenter__(self) -> str:
        bytes = None
        if not os.path.exists(self._temp_path):
            os.mkdir(self._temp_path)
        self._temp_file = os.path.join(self._temp_path, self._temp_name)
        async with aiohttp.ClientSession() as session:
            async with session.get(self._url) as response:
                bytes = await response.content.read()
        if not bytes:
            return self._temp_file
        img = Image.open(BytesIO(bytes))
        img = img.resize((img.size[0] // 3,img.size[1] // 3))
        img.save(self._temp_file, optimize = True, quality = 70)
        return self._temp_file
    
    async def __aexit__(self, type, value, traceback) -> None:
        await aiofiles.os.remove(self._temp_file)