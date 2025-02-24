from aiogram import Router, F, types
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from app import text, PageBuilder, App, log
from .subscription import subscription_menu, SubscriptionPage


router = Router()

class PropertyPage(StatesGroup):
    find_property = State()
    find_building = State()
    finished = State()

@log
@router.message(F.text == text.Btn.NEW_SUBSCRIPTION.value)
async def property_start(msg: types.Message, state: FSMContext):
    App.new_subscription()

    cities = await App.database.get_cities()
    buttons = PageBuilder.using(cities).current()

    if not buttons:
        return
    
    await msg.answer(
        text.choose_city, 
        reply_markup = buttons
    )
    await App.set_state(PropertyPage.find_property, state)

@log
@router.callback_query(F.data.in_(['next', 'prev', 'page', 'menu', 'back']))
async def property_search(call: types.CallbackQuery, state: FSMContext):
    buttons = None
    if call.data == 'menu':
        await subscription_menu(call.message, state)
    elif call.data == 'back':
        prev_state = await App.go_back(state)
        if prev_state == SubscriptionPage.menu:
            await subscription_menu(call.message, state)
        elif prev_state == PropertyPage.find_property:
            await property_start(call.message, state)
        elif prev_state == PropertyPage.find_building:
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
@router.message(PropertyPage.find_property, F.text)
async def city_error(msg: types.Message, state: FSMContext):
    await msg.answer(text.choose_city_error)

@log
@router.callback_query(PropertyPage.find_property, F.data)
async def property(call: types.CallbackQuery, state: FSMContext):
    city_id = App.subscription.city_id if call.data == 'back' else call.data
    if not await App.subscription.set(city_id = city_id):
        return
    
    properties = await App.database.get_properties(App.subscription.city_id)
    if len(properties) == 0:
        await App.go_back(state)
        await call.message.answer(text.no_property)
        return await property_start(call.message, state)

    buttons = PageBuilder.using(properties).current()
    if not buttons:
        return
    
    await call.message.answer(
        text.choose_property, 
        reply_markup = buttons
    )
    await App.set_state(PropertyPage.find_building, state)

@log
@router.message(PropertyPage.find_building, F.text)
async def property_error(msg: types.Message, state: FSMContext):
    await msg.answer(text.choose_property_error)

@log
@router.callback_query(PropertyPage.find_building, F.data)
async def choose_building(call: types.CallbackQuery, state: FSMContext):
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
        await App.set_state(PropertyPage.finished, state)

@log
@router.message(PropertyPage.finished, F.text)
async def buidling_error(msg: types.Message):
    await msg.answer(text.choose_house_error)

@log
@router.callback_query(PropertyPage.finished, F.data)
async def building(call: types.CallbackQuery, state: FSMContext):
    if not await App.subscription.set(building_id = call.data):
        return
    await success(call, state)

async def success(call: types.CallbackQuery, state: FSMContext):
    await call.message.answer(text.subscription_success)
    await App.save_subscription()
    await App.clear_history(state)
    await subscription_menu(call.message, state)