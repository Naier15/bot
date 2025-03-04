from aiogram import Router, F, types
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from .menu import get_menu
from .property import start
from app import text, Markup, App, log


router = Router()

class ProfilePage(StatesGroup):
    start = State()
    login = State()
    password = State()
    email = State()
    
# Раздел Профиль - Главное меню
@router.message(F.text == text.Btn.PROFILE.value)
async def main(msg: types.Message, state: FSMContext):   
    log(main) 
    async with App(state) as app:
        await msg.answer(
            f'ВАШ ПРОФИЛЬ:\n{app.user.get_data()}\n{'' if app.user.is_registed else text.login_empty}', 
            reply_markup = Markup.bottom_buttons([
                [types.KeyboardButton(text = text.Btn.EDIT.value)], 
                [types.KeyboardButton(text = text.Btn.TO_MENU.value)]
            ])
        )
        await app.set_state(ProfilePage.start, state)

# Создание профиля и запрос логина
@router.message(ProfilePage.start, F.text == text.Btn.EDIT.value)
async def edit_login(msg: types.Message, state: FSMContext):
    log(edit_login) 
    await msg.answer(
        f'{text.login_preview}\nПридумайте логин:\n{text.login_tip}', 
        reply_markup = Markup.bottom_buttons(
            [ [types.KeyboardButton(text = text.Btn.TO_MENU.value)] ],
            'Напишите логин:'
        )
    )

# Сохранение логина и запрос пароля
@router.message(ProfilePage.start)
async def edit_password(msg: types.Message, state: FSMContext):
    log(edit_password) 
    async with App(state) as app:
        if msg.text == text.Btn.TO_MENU.value:
            await app.user.clear_data()
            return await get_menu(msg, state)
        
        res = await app.user.set_login(msg)
        if not res:
            await msg.answer(text.login_tip)
            return

        await msg.answer(f' ЛОГИН: {app.user.login} '.center(40, '-'))
        await msg.answer(
            f'Придумайте пароль:\n{text.password_tip}{text.password_disclaimer}', 
            reply_markup = Markup.bottom_buttons(
                [ [types.KeyboardButton(text = text.Btn.TO_MENU.value)] ],
                'Напишите пароль:'
            )
        )
        await app.set_state(ProfilePage.login, state)

# Сохранение пароля и запрос email или пропустить
@router.message(ProfilePage.login)
async def edit_email(msg: types.Message, state: FSMContext):
    log(edit_email) 
    async with App(state) as app:
        if msg.text == text.Btn.TO_MENU.value:
            await app.user.clear_data()
            return await get_menu(msg, state)
        
        if not await app.user.set_password(msg):
            await msg.answer(text.password_tip)      
            return

        await msg.answer(f' ПАРОЛЬ: {'*' * len(app.user.password)} '.center(40, '-'))
        await msg.answer(
            text.choose_email, 
            reply_markup = Markup.bottom_buttons([
                [types.KeyboardButton(text = text.Btn.SKIP.value)],
                [types.KeyboardButton(text = text.Btn.TO_MENU.value)]
            ], 'Напишите email:')
        )
        await app.set_state(ProfilePage.password, state)

# Предложение подписки или заверщение регистрации
@router.message(ProfilePage.password)
async def subscribe_or_finish(msg: types.Message, state: FSMContext):
    log(subscribe_or_finish)
    async with App(state) as app:
        if msg.text == text.Btn.TO_MENU.value:
            await app.user.clear_data()
            return await get_menu(msg, state)
        if msg.text != text.Btn.SKIP.value:
            if not await app.user.set_email(msg):
                return
        error = await app.user.save(temporary = False)
        if error:
            await app.clear_history(state)
            return await msg.answer(f'{error}\n{text.error}', reply_markup = App.menu()) 

        await msg.answer(f'ВАШ ПРОФИЛЬ:\n{app.user.get_data()}')
        await msg.answer(
            text.auth_finished, 
            reply_markup = Markup.bottom_buttons([ 
                [types.KeyboardButton(text = text.Btn.SUBSCRIBE.value)],
                [types.KeyboardButton(text = text.Btn.SKIP.value)]
            ])
        )
        await app.set_state(ProfilePage.email, state)

# Завершение регистрации
@router.message(ProfilePage.email)
async def finish(msg: types.Message, state: FSMContext):  
    log(finish)  
    async with App(state) as app:
        await app.clear_history(state)
    if msg.text == text.Btn.SUBSCRIBE.value:
        return await start(msg, state)
    else:
        return await get_menu(msg, state)