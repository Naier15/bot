from aiogram import Router, F, types
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from .menu import get_menu
from .. import text
from ..text import Btn
from ..entities import App, Subscription
from ..utils import log
# from ..db import get_cities


router = Router()

class Page(StatesGroup):
    find_property = State()
    find_house = State()
    finished = State()

async def set_city(msg: str) -> bool:
    if len(msg) > 0:
        App.subscription.city = msg
        return True
    else:
        return False
    
async def set_property(msg: str) -> bool:
    if len(msg) > 0:
        App.subscription.property = msg
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
async def property_start(msg: types.Message, state: FSMContext):
    App.subscription = Subscription()

    from property.models import City
    cities = [x.city_name async for x in City.objects.all()]
    cities.sort()
    buttons = App.page.using(cities).get_page(1)

    if not buttons:
        return
    
    await msg.answer(
        text.choose_city, 
        reply_markup = buttons
    )
    await App.set_state(Page.find_property, state)

@log
@router.callback_query(F.data.in_(['next', 'back', 'page']))
async def property_search(call: types.CallbackQuery):
    buttons = None
    page = App.page
    if call.data == 'next':
        buttons = page.get_page(page.current_page + 1)
    elif call.data == 'back':
        buttons = page.get_page(page.current_page - 1)
    elif call.data == 'page':
        pass

    if buttons:
        await call.message.edit_reply_markup(reply_markup = buttons)

@log
@router.message(Page.find_property, F.text)
async def city_error(msg: types.Message, state: FSMContext):
    await msg.answer(text.choose_city_error)

@log
@router.callback_query(Page.find_property, F.data)
async def property(call: types.CallbackQuery, state: FSMContext):
    if not await set_city(call.data):
        return
    
    from property.models import Property
    properties = [x.name async for x in Property.objects.all()]
    properties.sort()
    buttons = App.page.using(properties).get_page(1)
    if not buttons:
        return
    
    await call.message.answer(
        text.choose_property, 
        reply_markup = buttons
    )
    await App.replace_state(Page.find_house, state)

@log
@router.message(Page.find_house, F.text)
async def property_error(msg: types.Message, state: FSMContext):
    await msg.answer(text.choose_property_error)

@log
@router.callback_query(Page.find_house, F.data)
async def choose_house(call: types.CallbackQuery, state: FSMContext):
    if not await set_property(call.data):
        return await call.message.answer(text.choose_property_error)
    
    from property.models import Buildings
    buildings = [x.addr async for x in Buildings.objects.all()]
    buildings.sort()
    buttons = App.page.using(buildings).get_page(1)
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
    App.save_subscription()
    await get_menu(call.message, state)