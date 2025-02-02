from aiogram import Router, F, types
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from .menu import App
from .utils import form_buttons, log
from .menu import get_menu


router = Router()

class Page(StatesGroup):
    menu = State()
    app = State()

@log
@router.message(F.text == App.SUBSCRIPTION)
async def subscription_menu(msg: types.Message, state: FSMContext):
    await msg.answer(
        'Действующие подписки:', 
        reply_markup = form_buttons([
            [types.KeyboardButton(text = 'Город - ЖК - Дом')],
            [types.KeyboardButton(text = App.NEW_SUBSCRIPTION)], 
            [types.KeyboardButton(text = App.TO_MENU)]
        ])
    )
    await App.set_state(Page.menu, state)

@log
@router.message(Page.menu)
async def subscription_app(msg: types.Message, state: FSMContext):
    if msg.text == App.TO_MENU:
        return await get_menu(msg, state)
    elif msg.text == App.BACK:
        return await subscription_menu(msg, state)
    
    await msg.answer(
        'Сайт ЖК (url):', 
        reply_markup = form_buttons([ [types.KeyboardButton(text = App.BACK)] ])
    )