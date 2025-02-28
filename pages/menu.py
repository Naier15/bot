from aiogram import Router, F, types
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext

from app import text, Markup, App


router = Router()

@router.message(CommandStart())
async def start(msg: types.Message, state: FSMContext):
    App.log(start)
    await App.clear_history(state)
    await msg.answer(
        text.introduction,
        reply_markup = Markup.bottom_buttons([ [types.KeyboardButton(text = 'Разрешить', request_contact = True)] ])
    )

@router.message(F.contact)
async def get_contact(msg: types.Message, state: FSMContext):
    App.log(get_contact)
    if await App.user.set_phone(msg):
        await App.user.save(temporary = True)
        await get_menu(msg, state)
    else:
        await msg.answer(
            text.phone_error, 
            reply_markup = Markup.bottom_buttons([ [types.KeyboardButton(text = 'Разрешить', request_contact = True)] ])
        )

@router.message(F.text == text.Btn.HELP.value)
async def help(msg: types.Message):
    App.log(help)
    await msg.answer(
        text.help, 
        reply_markup = Markup.bottom_buttons([ [types.KeyboardButton(text = text.Btn.BACK.value)] ])
    )

@router.message(F.text.in_([text.Btn.BACK.value, text.Btn.SKIP.value]))
async def back(msg: types.Message, state: FSMContext):
    App.log(back)
    next_page = await App.go_back(state)
    if not next_page:
        await get_menu(msg, state)

@router.message(Command('menu'))
@router.message(F.text)
async def get_menu(msg: types.Message, state: FSMContext):
    App.log(get_menu)
    # print(App.history)
    await App.clear_history(state)
    await App.user.sync(msg.from_user.id)
    await msg.answer(
        text.Btn.MENU.value, 
        reply_markup = App.menu()
    ) 