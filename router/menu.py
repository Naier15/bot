from functools import wraps
from typing import Coroutine, Callable
from os import name as os_name
from aiogram import Router, F, types
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from django.core.cache import cache

from entities import App
from internal import text, Markup, log


router = Router()

class MenuPage(StatesGroup):
    phone = State()
    email = State()


def reload(coro: Coroutine) -> Coroutine:
    '''Декоратор для возвращения в главное меню - использовать для обработчиков в каком-то состоянии (StatesGroup)'''
    @wraps(coro)
    async def wrapper(msg: types.Message, state: FSMContext):
        async with App(state) as app:
            if msg.text == text.Btn.START.value:
                await app.clear_history(with_user = True)
                return await start(msg, state)
            elif msg.text == text.Btn.TO_MENU.value:
                await app.clear_history()
                return await get_menu(msg, state)
        return await coro(msg, state)
    return wrapper

def require_auth(clear_history: bool = False) -> Callable:
    '''Декоратор для автоматической авторизации или переходу к регистрации'''
    def wrapper(coro: Coroutine):
        @wraps(coro)
        async def inner(msg: types.Message, state: FSMContext):
            nonlocal clear_history
            async with App(state) as app:
                if clear_history:
                    await app.clear_history()
                if not await app.user.sync(msg.chat.id):
                    return await start(msg, state)
            return await coro(msg, state)
        return inner
    return wrapper

@router.message(CommandStart())
@log
async def start(msg: types.Message, state: FSMContext):
    '''Начало'''
    async with App(state) as app:
        await app.clear_history(with_user = True)
        await msg.answer(
            text.introduction,
            reply_markup = Markup.bottom_buttons([ 
                [types.KeyboardButton(text = text.phone_button, request_contact = True)] 
            ])
        )
        await app.set_state(MenuPage.phone, state)

@router.message(MenuPage.phone, F.contact | F.text)
@reload
@log
async def get_contact(msg: types.Message, state: FSMContext):
    '''Регистрация пользователя'''
    async with App(state) as app:
        if msg.contact and await app.user.set_phone(msg.contact.phone_number.strip().replace(' ', '').replace('-', '')):
            await app.user.set_id(msg.chat.id)
            await app.user.set_login(msg.from_user.username or msg.chat.id)
            if not await app.user.is_exist():
                saved = await app.user.save()
                if not saved:
                    return await msg.answer(text.error, reply_markup = Markup.no_buttons())
                await msg.answer(text.choose_email, reply_markup = Markup.no_buttons())
                await app.set_state(MenuPage.email, state)
                return
            await app.go_back(state)
            await get_menu(msg, state)
        else:
            await msg.answer(
                text.phone_error, 
                reply_markup = Markup.bottom_buttons([ 
                    [types.KeyboardButton(text = text.phone_button, request_contact = True)] 
                ])
            )

@router.message(MenuPage.email, F.text)
@reload
@log
async def get_email(msg: types.Message, state: FSMContext):
    '''Регистрация email'''
    async with App(state) as app:
        if await app.user.set_email(msg.text.strip()):
            await app.go_back(state) 
            await get_menu(msg, state)
        else:
            await msg.answer(text.email_tip, reply_markup = Markup.no_buttons())

@router.message(F.text == text.Btn.AUTH.value)
@require_auth()
@log
async def auth(msg: types.Message, state: FSMContext):
    '''Авторизация на сайте'''
    async with App(state) as app:
        tg_user = await app.user.get(msg.chat.id)
        if os_name == 'posix': 
            cache.set('telegram_user', tg_user.user_profile.user, 120)
        await msg.answer(
            text.auth, 
            reply_markup = Markup.inline_buttons([ 
                [types.InlineKeyboardButton(text = text.auth_btn, url = 'https://bashni.pro')]
            ])
        )
        await get_menu(msg, state)

@router.message(F.text == text.Btn.HELP.value)
@require_auth()
@log
async def help(msg: types.Message, state: FSMContext):
    '''Раздел Помощь'''
    await msg.answer(
        text.help, 
        reply_markup = App.menu()
    )

@router.message(F.text.in_([text.Btn.BACK.value, text.Btn.SKIP.value]))
@log
async def back(msg: types.Message, state: FSMContext):
    '''Триггер на кнопки Назад и Пропустить'''
    async with App(state) as app:
        next_page = await app.go_back(state)
        if not next_page:
            await get_menu(msg, state)

@router.message(Command('menu'))
@router.message(F.text)
@require_auth(clear_history = True)
@log
async def get_menu(msg: types.Message, state: FSMContext):
    '''Команда меню и другие непонятные запросы'''
    async with App(state) as app:
        if not app.user.email:
            await msg.answer(text.choose_email, reply_markup = Markup.no_buttons())
            await app.set_state(MenuPage.email, state)
            return
    await msg.answer(
        text.Btn.MENU.value, 
        reply_markup = App.menu()
    )

@router.callback_query(F.data == 'to_menu')
async def get_menu_callback(call: types.CallbackQuery, state: FSMContext):
    '''Прокси в get_menu для Inline кнопок'''
    await get_menu(call.message, state) 