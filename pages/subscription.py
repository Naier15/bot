from aiogram import Router, F, types
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.utils.media_group import MediaGroupBuilder

import os

from .menu import get_menu
from app import text, Markup, App, log


router = Router()

class SubscriptionPage(StatesGroup):
    menu = State()
    list = State()
    remove = State()

@log
@router.message(F.text == text.Btn.SUBSCRIPTION.value)
async def subscription_menu(msg: types.Message, state: FSMContext):
    await App.set_state(SubscriptionPage.menu, state)
    if not App.user.is_registed:
        return await msg.answer(
            text.please_login, 
            reply_markup = Markup.bottom_buttons([
                [types.KeyboardButton(text = text.Btn.EDIT.value)],
                [types.KeyboardButton(text = text.Btn.TO_MENU.value)]
            ])
        )
    await msg.answer(
        text.subscription_menu, 
        reply_markup = Markup.bottom_buttons([
            [types.KeyboardButton(text = text.Btn.SUBSCRIPTION_LIST.value)],
            [
                types.KeyboardButton(text = text.Btn.NEW_SUBSCRIPTION.value), 
                types.KeyboardButton(text = text.Btn.REMOVE_SUBSCRIPTION.value)
            ], 
            [types.KeyboardButton(text = text.Btn.TO_MENU.value)]
        ])
    )
    
@router.message(SubscriptionPage.menu, F.text == text.Btn.SUBSCRIPTION_LIST.value)
async def subscription_list(msg: types.Message, state: FSMContext):
    subscription_btns = [
        [types.InlineKeyboardButton(text = sub.property_name, callback_data = sub.building_id)]
        for sub in App.user.subscriptions
    ]
    if len(subscription_btns) == 0:
        return await msg.answer(text.subscription_empty, reply_markup = Markup.current())
    await msg.answer(
        text.subscriptions, 
        reply_markup = Markup.inline_buttons(
            subscription_btns +
            [[types.InlineKeyboardButton(text = text.Btn.BACK.value, callback_data = 'back')]]
        )
    )

@log
@router.message(SubscriptionPage.menu, F.text == text.Btn.REMOVE_SUBSCRIPTION.value)
async def subscription_remove(msg: types.Message, state: FSMContext):
    subscription_btns = [
        [types.InlineKeyboardButton(text = sub.property_name, callback_data = sub.building_id)]
        for sub in App.user.subscriptions
    ]
    if len(subscription_btns) == 0:
        return await msg.answer(text.subscription_empty, reply_markup = Markup.current())
    
    await msg.answer(
        text.subscription_remove, 
        reply_markup = Markup.inline_buttons(
            subscription_btns + 
            [[types.InlineKeyboardButton(text = text.Btn.BACK.value, callback_data = 'back')]]
        )
    )
    await App.set_state(SubscriptionPage.remove, state)

@log
@router.message(SubscriptionPage.remove, F.text)
async def subscription_remove_error(msg: types.Message, state: FSMContext):
    await msg.answer(text.choose_property_error)

@log
@router.callback_query(SubscriptionPage.remove, F.data)
async def subscription_remove(call: types.CallbackQuery, state: FSMContext):
    for sub in App.user.subscriptions:
        if sub.building_id == call.data:
            await sub.remove(App.user.id)
            App.user.subscriptions.remove(sub)
            break
    else:
        return await call.message.answer(text.choose_property_error)
    
    await call.message.answer(text.subscription_remove_success)
    await App.go_back(state)
    await subscription_menu(call.message, state)

@log
@router.callback_query(SubscriptionPage.menu)
async def subscription_inline_choice(call: types.CallbackQuery, state: FSMContext):
    if call.data == 'back':
        return await subscription_menu(call.message, state)
    else:
        subscription = [x for x in App.user.subscriptions if x.building_id == call.data][0]
        await call.message.answer(
            (
                f'<a href="{subscription.url}">{subscription.property_name}</a>'
                f'\nСдача ключей: {subscription.send_keys}'
            ),
            reply_markup = Markup.bottom_buttons([ [types.KeyboardButton(text = text.Btn.BACK.value)] ])
        )
        photos = ['C:/Users/User/Desktop/bashni/static/img/Yulia.png']
        media = [types.InputMediaPhoto(media = photo) for photo in photos]
        await call.message.answer_media_group(media = media)

@log
@router.message(SubscriptionPage.menu)
async def subscription_choice(msg: types.Message, state: FSMContext):
    if msg.text == text.Btn.TO_MENU.value:
        return await get_menu(msg, state)
    elif msg.text == text.Btn.NEW_SUBSCRIPTION.value:
        from .property import property_start
        return await property_start(msg, state)
    elif msg.text == text.Btn.BACK.value:
        return await subscription_menu(msg, state)
    elif msg.text == text.Btn.EDIT.value:
        from .profile import ProfilePage, profile_edit_start
        
        await App.go_back(state)
        await App.set_state(ProfilePage.login, state)
        return await profile_edit_start(msg, state)