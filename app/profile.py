from aiogram import Router, F, types
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from .utils import form_buttons, log
from . import text
from .estate import Page as estate_page
from .menu import get_menu, App


router = Router()

class Page(StatesGroup):
    login = State()
    password = State()
    email = State()
    finish = State()
    
async def set_login(msg: types.Message) -> bool:
    login = msg.text.strip()
    if len(login) > 5 and len(login) < 16:
        App.user.login = login
        return True
    else:
        await msg.answer(
            text.login_tip, 
            reply_markup = form_buttons([ [types.KeyboardButton(text = App.TO_MENU)] ])
        )
        return False

async def set_password(msg: types.Message) -> bool:
    password = msg.text.strip()
    if len(password) > 7:
        App.user.password = password
        password = '*' * len(password)
        print(password)
        await App.bot.edit_message_text(password, message_id = msg.message_id, chat_id = msg.from_user.id)
        return True
    else:
        await msg.answer(
            text.password_tip, 
            reply_markup = form_buttons([ [types.KeyboardButton(text = App.TO_MENU)] ])
        )      
        return False

async def set_email(msg: types.Message):
    App.user.email = msg.text.strip()

@log
@router.message(F.text == App.PROFILE)
async def profile_main(msg: types.Message, state: FSMContext):    
    await msg.answer(
        f'Ваш профиль: {App.user.get_data()}', 
        reply_markup = form_buttons([
            [types.KeyboardButton(text = App.EDIT)], 
            [types.KeyboardButton(text = App.TO_MENU)]
        ])
    )
    await App.set_state(Page.login, state)

@log
@router.message(Page.login, F.text == App.EDIT)
async def profile_edit_start(msg: types.Message):
    await msg.answer(
        f'Введите ваш логин:\n' + text.login_tip, 
        reply_markup = form_buttons([ [types.KeyboardButton(text = App.TO_MENU)] ], 'Ожидаем...')
    )

@log
@router.message(Page.login)
async def profile_edit_login(msg: types.Message, state: FSMContext):
    if msg.text == App.TO_MENU:
        return await get_menu(msg, state)
    
    if not await set_login(msg):
        return
    await msg.answer(
        f'Введите пароль:\nПАРОЛЬ ОБЯЗАТЕЛЬНО НУЖНО ЗАПОМНИТЬ!\n' + text.password_tip, 
        reply_markup = form_buttons([ [types.KeyboardButton(text = App.TO_MENU)] ], 'Ожидаем...')
    )
    await App.set_state(Page.password, state)

@log
@router.message(Page.password)
async def profile_edit_password(msg: types.Message, state: FSMContext):
    if msg.text == App.TO_MENU:
        return await get_menu(msg, state)
    
    if not await set_password(msg):
        return
    await msg.answer(
        f'Введите адрес электронной почты:', 
        reply_markup = form_buttons([
            [types.KeyboardButton(text = App.SKIP)],
            [types.KeyboardButton(text = App.TO_MENU)]
        ], 'Ожидаем...')
    )
    await App.set_state(Page.email, state)

@log
@router.message(Page.email)
async def profile_edit_email(msg: types.Message, state: FSMContext):
    if msg.text == App.TO_MENU:
        return await get_menu(msg, state)
    if msg.text != App.SKIP:
        await set_email(msg)

    await msg.answer(
        text.auth_finished, 
        reply_markup = form_buttons([ 
            [types.KeyboardButton(text = App.SUBSCRIBE)],
            [types.KeyboardButton(text = App.SKIP)]
        ], 'Ожидаем...')
    )
    await App.set_state(Page.finish, state)

@log
@router.message(Page.finish)
async def profile_finish(msg: types.Message, state: FSMContext):   
    await App.clear_history(state)
    if msg.text == App.SUBSCRIBE:
        await App.set_state(estate_page.estate, state)
    else:
        await msg.answer(f'Ваш профиль: {App.user.get_data()}')
        await get_menu(msg, state)