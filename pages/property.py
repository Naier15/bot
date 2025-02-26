from aiogram import Router, F, types
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

import fuzzywuzzy
import fuzzywuzzy.process

from app import text, PageBuilder, App, log
from .subscription import menu, SubscriptionPage


router = Router()

class PropertyPage(StatesGroup):
    city = State()
    property = State()
    building = State()

@log
@router.message(F.text == text.Btn.NEW_SUBSCRIPTION.value)
async def start(msg: types.Message, state: FSMContext):
    App.new_subscription()

    cities = await App.database.get_cities()
    buttons = PageBuilder.using(cities).current()

    if not buttons:
        return
    
    await msg.answer(
        text.choose_city, 
        reply_markup = buttons
    )
    await App.set_state(PropertyPage.city, state)

@log
@router.callback_query(F.data.in_(['next', 'prev', 'page', 'menu', 'back']))
async def navigation(call: types.CallbackQuery, state: FSMContext):
    buttons = None
    if call.data == 'menu':
        await menu(call.message, state)
    elif call.data == 'back':
        prev_state = await App.go_back(state)
        if prev_state == SubscriptionPage.menu:
            await menu(call.message, state)
        elif prev_state == PropertyPage.city:
            await start(call.message, state)
        elif prev_state == PropertyPage.property:
            await property(call, state)
    elif call.data == 'next':
        PageBuilder.next()
        buttons = PageBuilder.current()
    elif call.data == 'prev':
        PageBuilder.previous()
        buttons = PageBuilder.current()
    elif call.data == 'page':
        pass

    if buttons:
        await call.message.edit_reply_markup(reply_markup = buttons)

@log
@router.message(PropertyPage.city, F.text)
async def city_error(msg: types.Message, state: FSMContext):
    await msg.answer(text.choose_city_error)

@log
@router.callback_query(PropertyPage.city, F.data)
async def city(call: types.CallbackQuery, state: FSMContext):
    city_id = App.subscription.city_id if call.data == 'back' else call.data
    if not await App.subscription.set(city_id = city_id):
        return
    
    properties = await App.database.get_properties(App.subscription.city_id)
    if len(properties) == 0:
        await App.go_back(state)
        await call.message.answer(text.no_property)
        return await start(call.message, state)

    buttons = PageBuilder.using(properties).current()
    if not buttons:
        return
    
    await call.message.answer(
        text.choose_property, 
        reply_markup = buttons
    )
    await App.set_state(PropertyPage.property, state)

@log
@router.message(PropertyPage.property, F.text)
async def property_error(msg: types.Message, state: FSMContext):
    properties = await App.database.get_properties(App.subscription.city_id)
    results = fuzzywuzzy.process.extract(msg.text, properties, limit = 6)
    if len(results) == 0:
        return await msg.answer(text.choose_property_error)
    results = [result[0] for result in results]
    buttons = PageBuilder.using(results).current()
    await msg.answer(
        text.choose_exact_property, 
        reply_markup = buttons
    )

@log
@router.callback_query(PropertyPage.property, F.data)
async def property(call: types.CallbackQuery, state: FSMContext):
    if not await App.subscription.set(property_id = call.data):
        return await call.message.answer(text.choose_property_error)
    
    buildings = await App.database.get_buildings(App.subscription.property_id)
    if len(buildings) == 0:
        return
    elif len(buildings) == 1:
        if not await App.subscription.set(building_id = buildings[0]['id']):
            return
        await success(call, state)
    else:
        buttons = PageBuilder.using(buildings).current()    
        await call.message.answer(
            text.choose_house, 
            reply_markup = buttons
        )
        await App.set_state(PropertyPage.building, state)

@log
@router.message(PropertyPage.building, F.text)
async def buidling_error(msg: types.Message):
    await msg.answer(text.choose_house_error)

@log
@router.callback_query(PropertyPage.building, F.data)
async def building(call: types.CallbackQuery, state: FSMContext):
    if not await App.subscription.set(building_id = call.data):
        return
    await success(call, state)

async def success(call: types.CallbackQuery, state: FSMContext):
    await call.message.answer(text.subscription_success)
    await App.save_subscription()
    await App.clear_history(state)
    await menu(call.message, state)