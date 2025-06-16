from aiogram import Router, F, types
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from .menu import get_menu, reload_handler
from telegrambot.app import text, Markup, App, log, UserRepository, \
    get_favorites_subscr, remove_user_favorites_flat, remove_user_favorites_commercial
from telegrambot.models import TgUser


router = Router()

class SubscriptionPage(StatesGroup):
    menu = State()
    remove = State()

# Раздел Подписки - главное меню
@router.message(F.text == text.Btn.SUBSCRIPTION.value)
async def menu(msg: types.Message, state: FSMContext):
    log(menu) 
    async with App(state) as app:
        await app.set_state(SubscriptionPage.menu, state)
        if not app.user.is_registed:
            await app.user.sync(msg.chat.id)

        if not app.user.is_registed:
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
    log(list) 
    async with App(state) as app:
        subscription_btns = await app.user.form_subscriptions_as_buttons()
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
    log(remove) 
    async with App(state) as app:
        subscription_btns = await app.user.form_subscriptions_as_buttons()
        if len(subscription_btns) == 0:
            return await msg.answer(text.subscription_empty, reply_markup = Markup.current())
        
        await msg.answer(
            text.subscription_remove, 
            reply_markup = Markup.inline_buttons(
                subscription_btns + 
                [[types.InlineKeyboardButton(text = text.Btn.BACK.value, callback_data = 'back')]]
            )
        )
        await app.set_state(SubscriptionPage.remove, state)

# Ошибка удаления подписки
@router.message(SubscriptionPage.remove, F.text)
async def remove_error(msg: types.Message, state: FSMContext):
    log(remove_error)
    if await reload_handler(msg, state):
        return
    await msg.answer(text.choose_property_error)

# Удаление подписки и возвращение в главное меню раздела Подписки
@router.callback_query(SubscriptionPage.remove, F.data)
async def remove_result(call: types.CallbackQuery, state: FSMContext):
    log(remove_result)
    async with App(state) as app:
        if call.data == 'back':
            await app.go_back(state)
            return await menu(call.message, state)
        
        for sub in app.user.subscriptions:
            if sub.building_id == call.data:
                await sub.remove(app.user.id)
                app.user.subscriptions.remove(sub)
                break
        else:
            return await call.message.answer(text.choose_property_error)
        
        await call.message.answer(text.subscription_remove_success)
        await app.go_back(state)
        await menu(call.message, state)

# Карточка подписки ЖК
@router.callback_query(SubscriptionPage.menu)
async def subscription_card(call: types.CallbackQuery, state: FSMContext):
    log(subscription_card)
    async with App(state) as app:
        if call.data == 'back': 
            return await menu(call.message, state)
        else:
            subscription = [x for x in app.user.subscriptions if x.building_id == call.data][0]
            await subscription.send_info(call.message.chat.id)

# Выбор кнопок меню
@router.message(SubscriptionPage.menu)
async def choice(msg: types.Message, state: FSMContext):
    log(choice)
    if await reload_handler(msg, state):
        return
    
    if msg.text == text.Btn.TO_MENU.value:
        return await get_menu(msg, state)
    elif msg.text == text.Btn.NEW_SUBSCRIPTION.value:
        from .property import start
        return await start(msg, state)
    elif msg.text == text.Btn.BACK.value:
        return await menu(msg, state)
    elif msg.text == text.Btn.EDIT.value:
        from .profile import ProfilePage, edit_login
        
        async with App(state) as app:
            await app.go_back(state)
            await app.set_state(ProfilePage.start, state)
        return await edit_login(msg, state)

# отправка уведомлений об изменении цен в избранном
async def send_favorites_obj():
    get_favorites = await get_favorites_subscr()
    for user_subscr in get_favorites:
        res_user_obj = await UserRepository().get_favorites_obj(user_subscr.user)
        for text_item in res_user_obj:
            if user_subscr.user.telegramchat_set.first():
                await App().bot.send_message(chat_id=user_subscr.user.telegramchat_set.first().telegram_id,
                                             text='<strong>Уведомление об изменение цен в избранном в вашем личном '
                                                  'кабинете</strong>\n\n' + text_item['text'], parse_mode='html',
                                             reply_markup=Markup.inline_buttons(
                [[types.InlineKeyboardButton(text = 'Удалить', callback_data = f'delete_{text_item["id"]}')]]))
            else:
                try:
                    user_profile = user_subscr.user.profile
                    if user_profile:
                        tg_user = TgUser.objects.filter(user_profile=user_profile).first()
                        if tg_user:
                            await App().bot.send_message(chat_id=tg_user.chat_id,
                                                         text='<strong>Уведомление об изменение цен в избранном в вашем личном '
                                                          'кабинете</strong>\n\n' + text_item['text'], parse_mode='html',
                                                     reply_markup=Markup.inline_buttons(
                        [[types.InlineKeyboardButton(text = 'Удалить', callback_data = f'delete_{text_item["id"]}')]]))
                except Exception as e:
                    print('err = ', e)


# Удаление из избранного квартир и коммерции, добавленных в личном кабинете (Callback func при отправке уведомлений
# об изменении цен в избранном)
@router.callback_query(F.data.startswith('delete_'))
async def remove_result(call: types.CallbackQuery):
    obj_id = call.data.split('_')[-1]
    if call.data.startswith('delete_flat'):
        await remove_user_favorites_flat(obj_id)
    elif call.data.startswith('delete_com'):
        await remove_user_favorites_commercial(obj_id)
    await call.answer()
    await call.message.answer('Объект удален из избранного')
