from aiogram import Router, F, types
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from .menu import get_menu
from app import text, Markup, App


router = Router()

class SubscriptionPage(StatesGroup):
    menu = State()
    list = State()
    remove = State()

# Раздел Подписки - главное меню
@router.message(F.text == text.Btn.SUBSCRIPTION.value)
async def menu(msg: types.Message, state: FSMContext):
    App.log(menu) 
    await App.set_state(SubscriptionPage.menu, state)
    if not App.user.is_registed:
        await App.user.sync(msg.from_user.id)
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
    
# Список всех подписок
@router.message(SubscriptionPage.menu, F.text == text.Btn.SUBSCRIPTION_LIST.value)
async def list(msg: types.Message, state: FSMContext):
    App.log(list) 
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

# Удаление подписки
@router.message(SubscriptionPage.menu, F.text == text.Btn.REMOVE_SUBSCRIPTION.value)
async def remove(msg: types.Message, state: FSMContext):
    App.log(remove) 
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

# Ошибка удаления подписки
@router.message(SubscriptionPage.remove, F.text)
async def remove_error(msg: types.Message, state: FSMContext):
    App.log(remove_error)
    await msg.answer(text.choose_property_error)

# Удаление подписки и возвращение в главное меню раздела Подписки
@router.callback_query(SubscriptionPage.remove, F.data)
async def remove_result(call: types.CallbackQuery, state: FSMContext):
    App.log(remove_result)
    if call.data == 'back':
        await App.go_back(state)
        return await menu(call.message, state)
    for sub in App.user.subscriptions:
        if sub.building_id == call.data:
            await sub.remove(App.user.id)
            break
    else:
        return await call.message.answer(text.choose_property_error)
    
    await call.message.answer(text.subscription_remove_success)
    await App.go_back(state)
    await menu(call.message, state)

# Карточка подписки ЖК
@router.callback_query(SubscriptionPage.menu)
async def subscription_card(call: types.CallbackQuery, state: FSMContext):
    App.log(subscription_card)
    if call.data == 'back':
        return await menu(call.message, state)
    else:
        subscription = [x for x in App.user.subscriptions if x.building_id == call.data][0]
        await subscription.send_info(call.from_user.id)

# Выбор кнопок меню
@router.message(SubscriptionPage.menu)
async def choice(msg: types.Message, state: FSMContext):
    App.log(choice)
    if msg.text == text.Btn.TO_MENU.value:
        return await get_menu(msg, state)
    elif msg.text == text.Btn.NEW_SUBSCRIPTION.value:
        from .property import start
        return await start(msg, state)
    elif msg.text == text.Btn.BACK.value:
        return await menu(msg, state)
    elif msg.text == text.Btn.EDIT.value:
        from .profile import ProfilePage, edit_login
        
        await App.go_back(state)
        await App.set_state(ProfilePage.start, state)
        return await edit_login(msg, state)