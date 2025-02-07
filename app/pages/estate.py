from aiogram import Router, F, types
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from ..entities import App, Subscription
from ..utils import form_buttons, log
from .menu import get_menu


router = Router()

class Page(StatesGroup):
    find_estate = State()
    find_house = State()
    finish = State()

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
@router.message(F.text == App.NEW_SUBSCRIPTION)
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
        f'Выберете город:', 
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
@router.callback_query(Page.find_estate)
async def estate(call: types.CallbackQuery, state: FSMContext):
    if not await set_city(call.data):
        return
    buttons = App.page.using([
        {
            'title': 'ЖК Атмосфера',
            'id': 'ЖК Атмосфера'
        }, 
        {
            'title': 'ЖК Горизонт',
            'id': 'ЖК Горизонт'
        },
        {
            'title': 'ЖК Зеленый бульвар',
            'id': 'ЖК Зеленый бульвар'
        }
    ]).get_page(1)
    if not buttons:
        return
    
    await call.message.answer(
        f'На новости какого ЖК вы хотите подписаться:', 
        reply_markup = buttons
    )
    await App.replace_state(Page.find_house, state)

@log
@router.callback_query(Page.find_house)
async def house(call: types.CallbackQuery, state: FSMContext):
    if not await set_estate(call.data):
        return
    buttons = App.page.using([
        {
            'title': 'Дом №1',
            'id': 'Дом №1'
        }, 
        {
            'title': 'Дом №2',
            'id': 'Дом №2'
        },
        {
            'title': 'Дом №3',
            'id': 'Дом №3'
        }
    ]).get_page(1)
    if not buttons:
        return
    
    await call.message.answer(
        f'Выберите дом:', 
        reply_markup = buttons
    )
    await App.replace_state(Page.finish, state)

@log
@router.callback_query(Page.finish)
async def house(call: types.CallbackQuery, state: FSMContext):
    if not await set_house(call.data):
        return
    await call.message.answer('<b>Подписка оформлена успешно!</b>\nПросматривать подписки можно во вкладке Подписка')
    App.user.subscriptions.append(App.subscription)
    App.subscription = None
    await get_menu(call.message, state)





