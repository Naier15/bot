from aiogram import Router, F, types
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from .menu import get_menu
from app import text, log, App, Subscription, Database


router = Router()

class Page(StatesGroup):
    find_property = State()
    find_building = State()
    finished = State()

@log
@router.message(F.text == text.Btn.NEW_SUBSCRIPTION.value)
async def property_start(msg: types.Message, state: FSMContext):
    App.subscription = Subscription()

    cities = await Database.get_cities()
    buttons = App.page.using(cities).get_page(1)

    if not buttons:
        return
    
    await msg.answer(
        text.choose_city, 
        reply_markup = buttons
    )
    await App.set_state(Page.find_property, state)

@log
@router.callback_query(F.data.in_(['next', 'back', 'page', 'menu']))
async def property_search(call: types.CallbackQuery, state: FSMContext):
    buttons = None
    page = App.page
    if call.data == 'menu':
        await get_menu(call.message, state)
    elif call.data == 'next':
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
    if not await App.subscription.set_city(call.data):
        return
    
    properties = await Database.get_properties()
    buttons = App.page.using(properties).get_page(1)
    if not buttons:
        return
    
    await call.message.answer(
        text.choose_property, 
        reply_markup = buttons
    )
    await App.replace_state(Page.find_building, state)

@log
@router.message(Page.find_building, F.text)
async def property_error(msg: types.Message, state: FSMContext):
    await msg.answer(text.choose_property_error)

@log
@router.callback_query(Page.find_building, F.data)
async def choose_building(call: types.CallbackQuery, state: FSMContext):
    if not await App.subscription.set_property(call.data):
        return await call.message.answer(text.choose_property_error)
    
    buildings = await Database.get_buildings()
    if len(buildings) == 0:
        return
    elif len(buildings) == 1:
        if not await App.subscription.set_building(buildings[0]['id']):
            return
        await success(call, state)
    else:
        buttons = App.page.using(buildings).get_page(1)    
        await call.message.answer(
            text.choose_house, 
            reply_markup = buttons
        )
        await App.replace_state(Page.finished, state)

@log
@router.message(Page.finished, F.text)
async def buidling_error(msg: types.Message):
    await msg.answer(text.choose_house_error)

@log
@router.callback_query(Page.finished, F.data)
async def building(call: types.CallbackQuery, state: FSMContext):
    if not await App.subscription.set_building(call.data):
        return
    await success(call, state)

async def success(call: types.CallbackQuery, state: FSMContext):
    await call.message.answer(text.subscription_success)
    App.save_subscription()
    await get_menu(call.message, state)