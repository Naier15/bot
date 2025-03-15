from aiogram import Router, F, types
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

import fuzzywuzzy
import fuzzywuzzy.process

from app import text, PageBuilder, App, log
from .menu import reload_handler
from .subscription import menu, SubscriptionPage


router = Router()

class PropertyPage(StatesGroup):
    city = State()
    property = State()
    building = State()

# Раздел Новая подписка - выбор города
@router.message(F.text == text.Btn.NEW_SUBSCRIPTION.value)
async def start(msg: types.Message, state: FSMContext):
    log(start) 
    async with App(state) as app:
        app.new_subscription()
        cities = await app.database.get_cities()
        buttons = PageBuilder.using(cities).current() 
        if not buttons:
            return
        
        await msg.answer(
            text.choose_city, 
            reply_markup = buttons
        )
        await app.set_state(PropertyPage.city, state)

# Кнопки навигации - влево, вправо, в меню, назад 
@router.callback_query(F.data.in_(['next', 'prev', 'page', 'menu', 'back']))
async def navigation(call: types.CallbackQuery, state: FSMContext):
    log(navigation)
    buttons = None
    if call.data == 'menu':
        await menu(call.message, state)
    elif call.data == 'back':
        async with App(state) as app:
            prev_state = await app.go_back(state)
        if prev_state == SubscriptionPage.menu:
            await menu(call.message, state)
        elif prev_state == PropertyPage.city:
            await start(call.message, state)
        elif prev_state == PropertyPage.property:
            await city(call, state)
        else:
            await menu(call.message, state)
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

# Ошибка выбора города
@router.message(PropertyPage.city, F.text)
async def city_error(msg: types.Message, state: FSMContext):
    log(city_error) 
    if await reload_handler(msg, state):
        return
    await msg.answer(text.choose_city_error)

# Сохранение города и выбор ЖК
@router.callback_query(PropertyPage.city, F.data)
async def city(call: types.CallbackQuery, state: FSMContext):
    log(city) 
    async with App(state) as app:
        city_id = app.subscription.city_id if call.data == 'back' else call.data
        if not await app.subscription.set(city_id = city_id):
            return
    
        properties = await app.database.get_properties(app.subscription.city_id)
        if len(properties) == 0:
            await app.go_back(state)
            await call.message.answer(text.no_property)
            return await start(call.message, state)

        buttons = PageBuilder.using(properties).current()
        if not buttons:
            return
        
        await call.message.answer(
            text.choose_property, 
            reply_markup = buttons
        )
        await app.set_state(PropertyPage.property, state)

# Ошибка выбора ЖК
@router.message(PropertyPage.property, F.text)
async def property_error(msg: types.Message, state: FSMContext):
    log(property_error)
    if await reload_handler(msg, state):
        return  
    async with App(state) as app:
        properties = await app.database.get_properties(app.subscription.city_id)
        results = fuzzywuzzy.process.extract(msg.text, properties, limit = 6)
        if len(results) == 0:
            return await msg.answer(text.choose_property_error)
        results = [result[0] for result in results]
        buttons = PageBuilder.using(results).current()
        await msg.answer(
            text.choose_exact_property, 
            reply_markup = buttons
        )

# Сохранение ЖК и выбор дома (если домов в ЖК более одного)
@router.callback_query(PropertyPage.property, F.data)
async def property(call: types.CallbackQuery, state: FSMContext):
    log(property) 
    async with App(state) as app:
        if not await app.subscription.set(property_id = call.data):
            return await call.message.answer(text.choose_property_error)
    
        buildings = await app.database.get_buildings(app.subscription.property_id)
        if len(buildings) == 0:
            return
        elif len(buildings) == 1:
            if not await app.subscription.set(building_id = buildings[0]['id']):
                return
            await success(call, state)
        else:
            buttons = PageBuilder.using(buildings).current()    
            await call.message.answer(
                text.choose_house, 
                reply_markup = buttons
            )
            await app.set_state(PropertyPage.building, state)

# Ошибка выбора дома
@router.message(PropertyPage.building, F.text)
async def buidling_error(msg: types.Message, state: FSMContext):
    log(buidling_error)
    if await reload_handler(msg, state):
        return
    await msg.answer(text.choose_house_error)

# Сохранение дома
@router.callback_query(PropertyPage.building, F.data)
async def building(call: types.CallbackQuery, state: FSMContext):
    log(building) 
    async with App(state) as app:
        if not await app.subscription.set(building_id = call.data):
            return
    await success(call, state)

# Завершение подписки
async def success(call: types.CallbackQuery, state: FSMContext):
    async with App(state) as app:
        await call.message.answer(text.subscription_success)
        await app.save_subscription()
        await app.clear_history(state)
    await menu(call.message, state) 