import regex

from aiogram import Router, F, types
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from .menu import get_menu
from .property import property_start
from .. import text
from ..text import Btn
from ..utils import form_buttons, log
from ..entities import App


router = Router()

class Page(StatesGroup):
    login = State()
    password = State()
    email = State()
    finish = State()
    
async def set_login(msg: types.Message) -> bool:
    login = msg.text.strip()
    await msg.delete()
    if len(login) > 5 and len(login) < 16:
        App.user.login = login
        await msg.answer(f' ЛОГИН: {login} '.center(40, '-'))
        return True
    else:
        await msg.answer(text.login_tip)
        return False

async def set_password(msg: types.Message) -> bool:
    password = msg.text.strip()
    await msg.delete()
    if len(password) > 7:
        App.user.password = password
        await msg.answer(f' ПАРОЛЬ: {'*' * len(password)} '.center(40, '-'))
        return True
    else:
        await msg.answer(text.password_tip)      
        return False

async def set_email(msg: types.Message):
    email = msg.text.strip()
    await msg.delete()
    if regex.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email):
        App.user.email = email
        await msg.answer(f' EMAIL: {email} '.center(40, '-'))
        return True
    else:
        await msg.answer(text.email_tip)      
        return False
    

@log
@router.message(F.text == Btn.PROFILE.value)
async def profile_main(msg: types.Message, state: FSMContext):    
    await msg.answer(
        f'ВАШ ПРОФИЛЬ:\n{App.user.get_data()}', 
        reply_markup = form_buttons([
            [types.KeyboardButton(text = Btn.EDIT.value)], 
            [types.KeyboardButton(text = Btn.TO_MENU.value)]
        ])
    )
    await App.set_state(Page.login, state)

@log
@router.message(Page.login, F.text == Btn.EDIT.value)
async def profile_edit_start(msg: types.Message):
    await msg.answer(
        f'Введите ваш логин:\n{text.login_tip}', 
        reply_markup = form_buttons([ [types.KeyboardButton(text = Btn.TO_MENU.value)] ])
    )

@log
@router.message(Page.login)
async def profile_edit_login(msg: types.Message, state: FSMContext):
    if msg.text == Btn.TO_MENU.value:
        return await get_menu(msg, state)
    
    if not await set_login(msg):
        return
    await msg.answer(
        f'Введите пароль:\n{text.password_tip}{text.password_disclaimer}', 
        reply_markup = types.ReplyKeyboardRemove()
    )
    await App.set_state(Page.password, state)

@log
@router.message(Page.password)
async def profile_edit_password(msg: types.Message, state: FSMContext):
    if msg.text == Btn.TO_MENU.value:
        return await get_menu(msg, state)
    
    if not await set_password(msg):
        return
    await msg.answer(
        text.choose_email, 
        reply_markup = form_buttons([
            [types.KeyboardButton(text = Btn.SKIP.value)],
            [types.KeyboardButton(text = Btn.TO_MENU.value)]
        ])
    )
    await App.set_state(Page.email, state)

@log
@router.message(Page.email)
async def profile_edit_email(msg: types.Message, state: FSMContext):
    if msg.text == Btn.TO_MENU.value:
        return await get_menu(msg, state)
    if msg.text != Btn.SKIP.value:
        if not await set_email(msg):
            return
    await msg.answer(f'ВАШ ПРОФИЛЬ:\n{App.user.get_data()}')
    await msg.answer(
        text.auth_finished, 
        reply_markup = form_buttons([ 
            [types.KeyboardButton(text = Btn.SUBSCRIBE.value)],
            [types.KeyboardButton(text = Btn.SKIP.value)]
        ])
    )
    await App.set_state(Page.finish, state)

@log
@router.message(Page.finish)
async def profile_finish(msg: types.Message, state: FSMContext):   
    await App.clear_history(state)
    if msg.text == Btn.SUBSCRIBE.value:
        return await property_start(msg, state)
    else:
        return await get_menu(msg, state)