from aiogram import Router, F, types
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from .menu import get_menu
from .estate import estate_start
from ..utils import form_buttons, log
from ..entities import App


router = Router()

class Page(StatesGroup):
    app = State()

@log
@router.message(F.text == App.SUBSCRIPTION)
async def subscription_menu(msg: types.Message, state: FSMContext):
    subscription_btns = [
        [types.KeyboardButton(text = f'{sub.city} - {sub.estate} - {sub.house}')] for sub in App.user.subscriptions
    ]
    await msg.answer(
        'Действующие подписки:', 
        reply_markup = form_buttons([
            *subscription_btns,
            [types.KeyboardButton(text = App.NEW_SUBSCRIPTION)], 
            [types.KeyboardButton(text = App.TO_MENU)]
        ])
    )
    await App.set_state(Page.app, state)

@log
@router.message(Page.app)
async def subscription_app(msg: types.Message, state: FSMContext):
    if msg.text == App.TO_MENU:
        return await get_menu(msg, state)
    elif msg.text == App.NEW_SUBSCRIPTION:
        return await estate_start(msg, state)
    elif msg.text == App.BACK:
        return await subscription_menu(msg, state)
    
    await msg.answer(
        f'Сайт ЖК ({App.user.subscriptions[0].url}):', 
        reply_markup = form_buttons([ [types.KeyboardButton(text = App.BACK)] ])
    )