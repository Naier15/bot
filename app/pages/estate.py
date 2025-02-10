from aiogram import Router, F, types
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from .menu import get_menu
from .. import text
from ..text import Btn
from ..entities import App, Subscription
from ..utils import log


router = Router()

class Page(StatesGroup):
    find_estate = State()
    find_house = State()
    finished = State()

async def set_city(msg: str) -> bool:
    if len(msg) > 0:
        App.subscription.city = msg
        return True
    else:
        return False
    
async def set_estate(msg: str) -> bool:
    if len(msg) > 0:
        App.subscription.estate = msg
        return True
    else:
        return False
    
async def set_house(msg: str) -> bool:
    if len(msg) > 0:
        App.subscription.house = msg
        return True
    else:
        return False


@log
@router.message(F.text == Btn.NEW_SUBSCRIPTION.value)
async def estate_start(msg: types.Message, state: FSMContext):
    App.subscription = Subscription()
    buttons = App.page.using([
        {
            'title': 'Владивосток',
            'id': 'Владивосток'
        }, 
        {
            'title': 'Уссурийск',
            'id': 'Уссурийск'
        },
        {
            'title': 'Находка',
            'id': 'Находка'
        }
    ]).get_page(1)

    if not buttons:
        return
    
    await msg.answer(
        text.choose_city, 
        reply_markup = buttons
    )
    await App.set_state(Page.find_estate, state)

@log
@router.callback_query(F.data.in_(['next', 'back']))
async def estate_search(call: types.CallbackQuery):
    buttons = None
    page = App.page
    if call.data == 'next':
        buttons = page.get_page(page.current_page + 1)
    elif call.data == 'back':
        buttons = page.get_page(page.current_page - 1)

    if buttons:
        await call.message.edit_reply_markup(reply_markup = buttons)

@log
@router.message(Page.find_estate, F.text)
async def city_error(msg: types.Message, state: FSMContext):
    await msg.answer(text.choose_city_error)

@log
@router.callback_query(Page.find_estate, F.data)
async def estate(call: types.CallbackQuery, state: FSMContext):
    if not await set_city(call.data):
        return
    buttons = App.page.using([
        {
            'title': 'Атмосфера',
            'id': 'Атмосфера'
        }, 
        {
            'title': 'Горизонт',
            'id': 'Горизонт'
        },
        {
            'title': 'Зеленый бульвар',
            'id': 'Зеленый бульвар'
        },
                {
            'title': 'Атмосфера2',
            'id': 'Атмосфера2'
        }, 
        {
            'title': 'Горизонт2',
            'id': 'Горизонт2'
        },
        {
            'title': 'Зеленый бульвар2',
            'id': 'Зеленый бульвар2'
        },
                {
            'title': 'Атмосфера3',
            'id': 'Атмосфера3'
        }, 
        {
            'title': 'Горизонт3',
            'id': 'Горизонт3'
        },
        {
            'title': 'Зеленый бульвар3',
            'id': 'Зеленый бульвар3'
        },
                {
            'title': 'Атмосфера4',
            'id': 'Атмосфера4'
        }, 
        {
            'title': 'Горизонт4',
            'id': 'Горизонт4'
        },
        {
            'title': 'Зеленый бульвар4',
            'id': 'Зеленый бульвар4'
        },
                {
            'title': 'Атмосфера5',
            'id': 'Атмосфера5'
        }, 
        {
            'title': 'Горизонт5',
            'id': 'Горизонт5'
        },
        {
            'title': 'Зеленый бульвар5',
            'id': 'Зеленый бульвар5'
        }
    ]).get_page(1)
    if not buttons:
        return
    
    await call.message.answer(
        text.choose_estate, 
        reply_markup = buttons
    )
    await App.replace_state(Page.find_house, state)

@log
@router.message(Page.find_house, F.text)
async def estate_error(msg: types.Message, state: FSMContext):
    await msg.answer(text.choose_estate_error)

@log
@router.callback_query(Page.find_house, F.data)
async def choose_house(call: types.CallbackQuery, state: FSMContext):
    if not await set_estate(call.data):
        return await call.message.answer(text.choose_estate_error)
    buttons = App.page.using([
        {
            'title': '1',
            'id': '1'
        }, 
        {
            'title': '2',
            'id': '2'
        },
        {
            'title': '3',
            'id': '3'
        }
    ]).get_page(1)
    if not buttons:
        return
    
    await call.message.answer(
        text.choose_house, 
        reply_markup = buttons
    )
    await App.replace_state(Page.finished, state)

@log
@router.message(Page.finished, F.text)
async def house_error(msg: types.Message):
    await msg.answer(text.choose_house_error)

@log
@router.callback_query(Page.finished, F.data)
async def house(call: types.CallbackQuery, state: FSMContext):
    if not await set_house(call.data):
        return
    await call.message.answer(text.subscription_success)
    App.user.subscriptions += [App.subscription]
    App.subscription = None
    await get_menu(call.message, state)