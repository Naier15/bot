from aiogram import Router, F, types
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from .menu import get_menu
from .property import property_start
from app import text, form_buttons, log, App


router = Router()

class Page(StatesGroup):
    login = State()
    password = State()
    email = State()
    finish = State()
    

@log
@router.message(F.text == text.Btn.PROFILE.value)
async def profile_main(msg: types.Message, state: FSMContext):    
    await msg.answer(
        f'ВАШ ПРОФИЛЬ:\n{App.user.get_data()}{'' if App.user.login else '\nВы можете отредактировать профиль и получить доступ к новостным обновлениям по ЖК'}', 
        reply_markup = form_buttons([
            [types.KeyboardButton(text = text.Btn.EDIT.value)], 
            [types.KeyboardButton(text = text.Btn.TO_MENU.value)]
        ])
    )
    await App.set_state(Page.login, state)

@log
@router.message(Page.login, F.text == text.Btn.EDIT.value)
async def profile_edit_start(msg: types.Message):
    await msg.answer(
        f'{text.login_preview}\nВведите ваш логин:\n{text.login_tip}', 
        reply_markup = form_buttons([ [types.KeyboardButton(text = text.Btn.TO_MENU.value)] ])
    )

@log
@router.message(Page.login)
async def profile_edit_login(msg: types.Message, state: FSMContext):
    if msg.text == text.Btn.TO_MENU.value:
        return await get_menu(msg, state)
    
    if not await App.user.set_login(msg):
        return
    await msg.answer(
        f'Введите пароль:\n{text.password_tip}{text.password_disclaimer}', 
        reply_markup = types.ReplyKeyboardRemove()
    )
    await App.set_state(Page.password, state)

@log
@router.message(Page.password)
async def profile_edit_password(msg: types.Message, state: FSMContext):
    if msg.text == text.Btn.TO_MENU.value:
        return await get_menu(msg, state)
    
    if not await App.user.set_password(msg):
        return
    await msg.answer(
        text.choose_email, 
        reply_markup = form_buttons([
            [types.KeyboardButton(text = text.Btn.SKIP.value)],
            [types.KeyboardButton(text = text.Btn.TO_MENU.value)]
        ])
    )
    await App.set_state(Page.email, state)

@log
@router.message(Page.email)
async def profile_edit_email(msg: types.Message, state: FSMContext):
    if msg.text == text.Btn.TO_MENU.value:
        return await get_menu(msg, state)
    if msg.text != text.Btn.SKIP.value:
        if not await App.user.set_email(msg):
            return
    await msg.answer(f'ВАШ ПРОФИЛЬ:\n{App.user.get_data()}')
    await msg.answer(
        text.auth_finished, 
        reply_markup = form_buttons([ 
            [types.KeyboardButton(text = text.Btn.SUBSCRIBE.value)],
            [types.KeyboardButton(text = text.Btn.SKIP.value)]
        ])
    )
    await App.set_state(Page.finish, state)

@log
@router.message(Page.finish)
async def profile_finish(msg: types.Message, state: FSMContext):   
    await App.clear_history(state)
    if msg.text == text.Btn.SUBSCRIBE.value:
        return await property_start(msg, state)
    else:
        return await get_menu(msg, state)