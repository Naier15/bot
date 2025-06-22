from functools import wraps
from typing import Coroutine

from aiogram import Router, F, types
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from telegrambot.app import text, Markup, App, log


router = Router()

class MenuPage(StatesGroup):
    phone = State()


# Декоратор для возвращения в главное меню - использовать в обработчиках в каком-то состоянии (StatesGroup)
def reload(coro: Coroutine):
    @wraps(coro)
    async def wrapper(msg: types.Message, state: FSMContext):
        async with App(state) as app:
            if msg.text == text.Btn.START.value:
                await app.clear_history(with_user = True)
                return await start(msg, state)
        return await coro(msg, state)
    return wrapper

# Начало 
@router.message(CommandStart())
@log
async def start(msg: types.Message, state: FSMContext):
    async with App(state) as app:
        await app.clear_history(with_user = True)
        await msg.answer(
            text.introduction,
            reply_markup = Markup.bottom_buttons([ 
                [types.KeyboardButton(text = text.phone_button, request_contact = True)] 
            ])
        )
        await app.set_state(MenuPage.phone, state)

# Регистрация пользователя
@router.message(MenuPage.phone, F.contact | F.text)
@log
@reload
async def get_contact(msg: types.Message, state: FSMContext):
    async with App(state) as app:
        if await app.user.set_phone(msg.contact.phone_number.strip().replace(' ', '').replace('-', '')):
            await app.user.set_id(msg.chat.id)
            await app.user.set_login(msg.from_user.username)
            if not await app.user.is_exist():
                saved = await app.user.save()
                if not saved:
                    return await msg.answer(text.error, reply_markup = Markup.no_buttons())
            await app.go_back(state)
            await get_menu(msg, state)
        else:
            await msg.answer(
                text.phone_error, 
                reply_markup = Markup.bottom_buttons([ 
                    [types.KeyboardButton(text = text.phone_button, request_contact = True)] 
                ])
            )

# Раздел Помощь
@router.message(F.text == text.Btn.HELP.value)
@log
async def help(msg: types.Message):
    await msg.answer(
        text.help, 
        reply_markup = Markup.bottom_buttons([ [types.KeyboardButton(text = text.Btn.BACK.value)] ])
    )

# Триггер на кнопки Назад и Пропустить
@router.message(F.text.in_([text.Btn.BACK.value, text.Btn.SKIP.value]))
@log
async def back(msg: types.Message, state: FSMContext):
    async with App(state) as app:
        next_page = await app.go_back(state)
        if not next_page:
            await get_menu(msg, state)

# Команда меню и другие непонятные запросы
@router.message(Command('menu'))
@router.message(F.text)
@log
async def get_menu(msg: types.Message, state: FSMContext):
    async with App(state) as app:
        await app.clear_history()
        if not await app.user.sync(msg.chat.id):
            return
    await msg.answer(
        text.Btn.MENU.value, 
        reply_markup = App.menu()
    )