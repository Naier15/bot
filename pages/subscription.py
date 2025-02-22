from aiogram import Router, F, types
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from .menu import get_menu
from .property import property_start
from app import text, App, form_buttons, log, form_inline_buttons, Database, CurrentBtns


router = Router()

class Page(StatesGroup):
    menu = State()
    list = State()
    remove = State()


@log
@router.message(F.text == text.Btn.SUBSCRIPTION.value)
async def subscription_menu(msg: types.Message, state: FSMContext):
    await msg.answer(
        text.subscription_menu, 
        reply_markup = form_buttons([
            [types.KeyboardButton(text = text.Btn.SUBSCRIPTION_LIST.value)],
            [
                types.KeyboardButton(text = text.Btn.NEW_SUBSCRIPTION.value), 
                types.KeyboardButton(text = text.Btn.REMOVE_SUBSCRIPTION.value)
            ], 
            [types.KeyboardButton(text = text.Btn.TO_MENU.value)]
        ])
    )
    await App.set_state(Page.menu, state)

@router.message(Page.menu, F.text == text.Btn.SUBSCRIPTION_LIST.value)
async def subscription_list(msg: types.Message, state: FSMContext):
    subscription_btns = []
    if len(App.user.subscriptions) > 0:
        print(App.user.subscriptions[0])
        for sub in App.user.subscriptions:
            data = await Database.get_building(sub.building)
            subscription_btns.append([types.InlineKeyboardButton(text = data['text'], callback_data = data['id'])])
        await msg.answer(
            text.subscriptions, 
            reply_markup = form_inline_buttons([
                *subscription_btns,
                [types.InlineKeyboardButton(text = text.Btn.BACK.value, callback_data = 'back')]
            ])
        )
    else:
        await msg.answer(
            text.subscription_empty,
            reply_markup = CurrentBtns.get()
        )

@log
@router.message(Page.menu, F.text == text.Btn.REMOVE_SUBSCRIPTION.value)
async def subscription_remove(msg: types.Message, state: FSMContext):
    subscription_btns = []
    for sub in App.user.subscriptions:
        data = await Database.get_building(sub.building)
        subscription_btns.append([types.InlineKeyboardButton(text = data, callback_data = sub.building)])
    if len(subscription_btns) == 0:
        await msg.answer(
            text.subscription_empty,
            reply_markup = CurrentBtns.get()
        )
    else:
        await msg.answer(
            text.subscription_remove, 
            reply_markup = form_inline_buttons(subscription_btns)
        )
        await App.set_state(Page.remove, state)

@log
@router.message(Page.remove, F.text)
async def subscription_remove_error(msg: types.Message, state: FSMContext):
    await msg.answer(text.choose_property_error)

@log
@router.callback_query(Page.remove, F.data)
async def subscription_remove(call: types.CallbackQuery, state: FSMContext):
    for sub in App.user.subscriptions:
        if sub.building == call.data:
            App.user.subscriptions.remove(sub)
            break
    else:
        return await call.message.answer(text.choose_property_error)
    
    await call.message.answer(text.subscription_remove_success)
    await get_menu(call.message, state)

@log
@router.callback_query(Page.menu)
async def subscription_inline_choice(call: types.CallbackQuery, state: FSMContext):
    if call.data == 'back':
        return await subscription_menu(call.message, state)
    else:
        building = await Database.get_building(call.data)
        await call.message.answer(
            f'<a href="{building.url}">Сайт ЖК</a>', 
            reply_markup = form_buttons([ [types.KeyboardButton(text = text.Btn.BACK.value)] ])
        )

@log
@router.message(Page.menu)
async def subscription_choice(msg: types.Message, state: FSMContext):
    if msg.text == text.Btn.TO_MENU.value:
        return await get_menu(msg, state)
    elif msg.text == text.Btn.NEW_SUBSCRIPTION.value:
        return await property_start(msg, state)
    elif msg.text == text.Btn.BACK.value:
        return await subscription_menu(msg, state)
    else:
        await msg.answer(
            f'<a href="{App.user.subscriptions[0].url}">Сайт ЖК</a>', 
            reply_markup = form_buttons([ [types.KeyboardButton(text = text.Btn.BACK.value)] ])
        )