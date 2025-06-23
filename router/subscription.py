import logging

from aiogram import Router, F, types
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from .menu import get_menu, reload
from telegrambot.app import text, Markup, App, log, UserRepository, \
    get_favorites_subscr, remove_user_favorites_flat, remove_user_favorites_commercial
from telegrambot.models import TgUser


router = Router()

class SubscriptionPage(StatesGroup):
    menu = State()
    remove = State()

@router.message(F.text == text.Btn.SUBSCRIPTION.value)
@log
async def menu(msg: types.Message, state: FSMContext):
    '''Раздел Подписки - главное меню'''
    async with App(state) as app:
        await app.set_state(SubscriptionPage.menu, state)
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
@log
async def list(msg: types.Message, state: FSMContext):
    '''Список всех подписок'''
    async with App(state) as app:
        subscription_btns = await app.user.form_subscriptions_as_buttons()
        if len(subscription_btns) == 0:
            return await msg.answer(
                text.subscription_empty, 
                reply_markup = Markup.current()
            )
        await msg.answer(
            text.subscriptions, 
            reply_markup = Markup.inline_buttons(
                subscription_btns +
                [[types.InlineKeyboardButton(text = text.Btn.BACK.value, callback_data = 'back')]]
            ) 
        )

@router.message(SubscriptionPage.menu, F.text == text.Btn.REMOVE_SUBSCRIPTION.value)
@log
async def remove(msg: types.Message, state: FSMContext):
    '''Удаление подписки'''
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

@router.message(SubscriptionPage.remove, F.text)
@log
@reload
async def remove_error(msg: types.Message, state: FSMContext):
    '''Ошибка удаления подписки'''
    await msg.answer(text.choose_property_error)

@router.callback_query(SubscriptionPage.remove, F.data)
@log
async def remove_result(call: types.CallbackQuery, state: FSMContext):
    '''Удаление подписки и возвращение в главное меню раздела Подписки'''
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

@router.callback_query(SubscriptionPage.menu)
@log
async def subscription_card(call: types.CallbackQuery, state: FSMContext):
    '''Карточка подписки ЖК'''
    async with App(state) as app:
        if call.data == 'back': 
            return await menu(call.message, state)
        else:
            subscription = [x for x in app.user.subscriptions if x.building_id == call.data][0]
            await subscription.send_info(call.message.chat.id)

@router.message(SubscriptionPage.menu)
@log
@reload
async def choice(msg: types.Message, state: FSMContext):
    '''Выбор кнопок меню'''
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

async def send_favorites_obj():
    '''Отправка уведомлений об изменении цен в избранном'''
    get_favorites = await get_favorites_subscr()
    for user_subscr in get_favorites:
        res_user_obj = await UserRepository().get_favorites_obj(user_subscr.user)
        for text_item in res_user_obj:
            if user_subscr.user.telegramchat_set.first():
                await App.bot.send_message(chat_id=user_subscr.user.telegramchat_set.first().telegram_id,
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
                            await App.bot.send_message(chat_id=tg_user.chat_id,
                                                         text='<strong>Уведомление об изменение цен в избранном в вашем личном '
                                                          'кабинете</strong>\n\n' + text_item['text'], parse_mode='html',
                                                     reply_markup=Markup.inline_buttons(
                        [[types.InlineKeyboardButton(text = 'Удалить', callback_data = f'delete_{text_item["id"]}')]]))
                except Exception as e:
                    logging.error('err = ', e)


@router.callback_query(F.data.startswith('delete_'))
@log
async def remove_result(call: types.CallbackQuery):
    '''Удаление из избранного квартир и коммерции, добавленных в личном кабинете 
    (Callback func при отправке уведомлений об изменении цен в избранном)'''
    obj_id = call.data.split('_')[-1]
    if call.data.startswith('delete_flat'):
        await remove_user_favorites_flat(obj_id)
    elif call.data.startswith('delete_com'):
        await remove_user_favorites_commercial(obj_id)
    await call.answer()
    await call.message.answer('Объект удален из избранного')