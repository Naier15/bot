from aiogram import Router, F, types
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from .menu import get_menu
from .estate import estate_start
from .. import text
from ..text import Btn
from ..utils import form_buttons, log, form_inline_buttons
from ..entities import App


router = Router()

class Page(StatesGroup):
    app = State()
    remove = State()

@log
@router.message(F.text == Btn.SUBSCRIPTION.value)
async def subscription_menu(msg: types.Message, state: FSMContext):
    subscription_btns = [
        [types.KeyboardButton(text = f'{sub.city} - {sub.estate} - {sub.house}')] for sub in App.user.subscriptions
    ]
    await msg.answer(
        text.subscriptions, 
        reply_markup = form_buttons([
            *subscription_btns,
            [
                types.KeyboardButton(text = Btn.NEW_SUBSCRIPTION.value), 
                types.KeyboardButton(text = Btn.REMOVE_SUBSCRIPTION.value)
            ], 
            [types.KeyboardButton(text = Btn.TO_MENU.value)]
        ])
    )
    await App.set_state(Page.app, state)

@log
@router.message(Page.app, F.text == Btn.REMOVE_SUBSCRIPTION.value)
async def subscription_remove(msg: types.Message, state: FSMContext):
    subscription_btns = [
        [types.InlineKeyboardButton(text = f'{sub.city} - {sub.estate} - {sub.house}', callback_data = f'{sub.house}')] 
        for sub in App.user.subscriptions
    ]
    await msg.answer(
        text.subscription_remove, 
        reply_markup = form_inline_buttons(subscription_btns)
    )
    await App.set_state(Page.remove, state)

@log
@router.message(Page.remove, F.text)
async def subscription_remove_error(msg: types.Message, state: FSMContext):
    await msg.answer(text.choose_estate_error)

@log
@router.callback_query(Page.remove, F.data)
async def subscription_remove(call: types.CallbackQuery, state: FSMContext):
    for sub in App.user.subscriptions:
        if sub.house == call.data:
            App.user.subscriptions.remove(sub)
            break
    else:
        return await call.message.answer(text.choose_estate_error)
    
    await call.message.answer(text.subscription_remove_success)
    await get_menu(call.message, state)

@log
@router.message(Page.app)
async def subscription_app(msg: types.Message, state: FSMContext):
    if msg.text == Btn.TO_MENU.value:
        return await get_menu(msg, state)
    elif msg.text == Btn.NEW_SUBSCRIPTION.value:
        return await estate_start(msg, state)
    elif msg.text == Btn.BACK.value:
        return await subscription_menu(msg, state)
    
    await msg.answer(
        f'<a href="{App.user.subscriptions[0].url}">Сайт ЖК</a>', 
        reply_markup = form_buttons([ [types.KeyboardButton(text = Btn.BACK.value)] ])
    )