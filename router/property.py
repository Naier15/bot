from aiogram import Router, F, types
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

import fuzzywuzzy
import fuzzywuzzy.process

from telegrambot.app import text, PageBuilder, App, log, \
    CityRepository, PropertyRepository, BuildingRepository
from .menu import reload, require_auth
from .subscription import menu, SubscriptionPage


router = Router()

class PropertyPage(StatesGroup):
    city = State()
    property = State()
    building = State()

@router.message(F.text == text.Btn.NEW_SUBSCRIPTION.value)
@require_auth()
@log
async def start(msg: types.Message, state: FSMContext):
    '''Раздел Новая подписка - выбор города'''
    async with App(state) as app:
        await app.user.new_subscription()
        cities = await CityRepository().get()
        buttons = PageBuilder.using(cities).current() 
        if not buttons:
            return
        
        await msg.answer(
            text.choose_city, 
            reply_markup = buttons
        )
        await app.set_state(PropertyPage.city, state)

@router.callback_query(F.data.in_(['next', 'prev', 'page', 'menu', 'back']))
@log
async def navigation(call: types.CallbackQuery, state: FSMContext):
    '''Кнопки навигации - влево, вправо, в меню, назад '''
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

@router.message(PropertyPage.city, F.text)
@reload
@log
async def city_error(msg: types.Message, state: FSMContext):
    '''Ошибка выбора города'''
    await msg.answer(text.choose_city_error)

@router.callback_query(PropertyPage.city, F.data)
@log
async def city(call: types.CallbackQuery, state: FSMContext):
    '''Сохранение города и выбор ЖК'''
    async with App(state) as app:
        city_id = app.user.added_subscription.city_id if call.data == 'back' else call.data
        if not await app.user.added_subscription.set(city_id = city_id):
            return
    
        properties = await PropertyRepository().get(app.user.added_subscription.city_id)
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

@router.message(PropertyPage.property, F.text)
@reload
@log
async def property_error(msg: types.Message, state: FSMContext): 
    '''Ошибка выбора ЖК'''
    async with App(state) as app:
        properties = await PropertyRepository().get(app.user.added_subscription.city_id)
        results = fuzzywuzzy.process.extract(msg.text, properties, limit = 6)
        if len(results) == 0:
            return await msg.answer(text.choose_property_error)
        results = [result[0] for result in results]
        buttons = PageBuilder.using(results).current()
        await msg.answer(
            text.choose_exact_property, 
            reply_markup = buttons
        )

@router.callback_query(PropertyPage.property, F.data)
@log
async def property(call: types.CallbackQuery, state: FSMContext):
    '''Сохранение ЖК и выбор дома (если домов в ЖК более одного)'''
    async with App(state) as app:
        if not await app.user.added_subscription.set(property_id = call.data):
            return await call.message.answer(text.choose_property_error)
    
        buildings = await BuildingRepository().get(app.user.added_subscription.property_id)
        if len(buildings) == 0:
            return
        elif len(buildings) == 1:
            if not await app.user.added_subscription.set(building_id = buildings[0]['id']):
                return
            await success(call, state)
        else:
            buttons = PageBuilder.using(buildings).current()    
            await call.message.answer(
                text.choose_house, 
                reply_markup = buttons
            )
            await app.set_state(PropertyPage.building, state)

@router.message(PropertyPage.building, F.text)
@reload
@log
async def buidling_error(msg: types.Message, state: FSMContext):
    '''Ошибка выбора дома'''
    await msg.answer(text.choose_house_error)

@router.callback_query(PropertyPage.building, F.data)
@log
async def building(call: types.CallbackQuery, state: FSMContext):
    '''Сохранение дома'''
    async with App(state) as app:
        if not await app.user.added_subscription.set(building_id = call.data):
            return
    await success(call, state)

async def success(call: types.CallbackQuery, state: FSMContext):
    '''Завершение подписки'''
    async with App(state) as app:
        await call.message.answer(text.subscription_success)
        await app.user.save_subscription()
        await app.clear_history()
    await menu(call.message, state) 
