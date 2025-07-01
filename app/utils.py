from functools import partial, wraps
from time import perf_counter
from typing import Optional, Self, Coroutine
from aiogram import types
from PIL import Image
from io import BytesIO
from asgiref.sync import sync_to_async
import logging, inspect, math, os, aiohttp, aiofiles, aiofiles.os


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

def log(coro: Coroutine) -> Coroutine:
    '''Декоратор для логгирования'''
    @wraps(coro)
    async def wrapper(*args, **kwargs):
        logger = logging.getLogger(os.path.abspath(inspect.getfile(coro)))

        if len(args) > 0 and isinstance(args[0], types.Message):
            username = f'{args[0].chat.username}({args[0].chat.id})'
        elif len(args) > 0 and isinstance(args[0], types.CallbackQuery):
            username = f'{args[0].message.chat.username}({args[0].message.chat.id})'
        else:
            username = 'x'

        logger.info(f'{coro.__name__} - {username}')
        try:
            return await coro(*args, **kwargs)
        except Exception as ex:
            logger.error(f'{coro.__name__} - {ex}', exc_info=True)
    return wrapper

def time(coro: Coroutine) -> Coroutine:
    '''Декоратор для отображения времени отработки функции'''
    @wraps(coro)
    async def wrapper(*args, **kwargs):
        start = perf_counter()
        result = await coro(*args, **kwargs)
        logging.info(f'[{coro.__name__}] takes {perf_counter() - start} seconds')
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