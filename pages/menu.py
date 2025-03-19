from aiogram import Router, F, types
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from app import text, Markup, App, log


router = Router()

class MenuPage(StatesGroup):
    phone = State()

# Начало 
@router.message(CommandStart())
async def start(msg: types.Message, state: FSMContext):
    log(start)
    async with App(state) as app:
        await app.clear_history(state, with_user = True)
        await msg.answer(
            text.introduction,
            reply_markup = Markup.bottom_buttons([ 
                [types.KeyboardButton(text = text.phone_button, request_contact = True)] 
            ])
        )
        await app.set_state(MenuPage.phone, state)

# Получение номера телефона 
@router.message(MenuPage.phone, F.contact | F.text)
async def get_contact(msg: types.Message, state: FSMContext):
    log(get_contact)
    if await reload_handler(msg, state):
        return
    async with App(state) as app:
        if await app.user.set_phone(msg):
            await app.user.save(temporary = True)
            await app.go_back(state)
            await get_menu(msg, state)
        else:
            await msg.answer(
                text.phone_error, 
                reply_markup = Markup.bottom_buttons([ 
                    [types.KeyboardButton(text = text.phone_button, request_contact = True)] 
                ])
            )

# Раздел Помощь
@router.message(F.text == text.Btn.HELP.value)
async def help(msg: types.Message):
    log(help)
    await msg.answer(
        text.help, 
        reply_markup = Markup.bottom_buttons([ [types.KeyboardButton(text = text.Btn.BACK.value)] ])
    )

# Триггер на кнопки Назад и Пропустить
@router.message(F.text.in_([text.Btn.BACK.value, text.Btn.SKIP.value]))
async def back(msg: types.Message, state: FSMContext):
    log(back)
    async with App(state) as app:
        next_page = await app.go_back(state)
        if not next_page:
            await get_menu(msg, state)

# Команда меню и другие непонятные запросы
@router.message(Command('menu'))
@router.message(F.text)
async def get_menu(msg: types.Message, state: FSMContext):
    log(get_menu)
    async with App(state) as app:
        await app.clear_history(state)
        if not await app.user.sync(msg.chat.id):
            return
    await msg.answer(
        text.Btn.MENU.value, 
        reply_markup = App.menu()
    )

async def reload_handler(msg: types.Message, state: FSMContext) -> bool:
    async with App(state) as app:
        if msg.text == text.Btn.START.value:
            await app.clear_history(state, with_user = True)
            await start(msg, state)
            return True
    return False