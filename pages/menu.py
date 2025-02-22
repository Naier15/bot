from aiogram import Router, F, types
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext

from app import text, form_buttons, log, App


router = Router()

@log
@router.message(CommandStart())
async def start(msg: types.Message, state: FSMContext):
    await App.clear_history(state)
    await msg.answer(
        text.introduction,
        reply_markup = form_buttons([ [types.KeyboardButton(text = 'Разрешить', request_contact = True)] ])
    )
    # await get_menu(msg, state)

@log
@router.message(F.contact)
async def get_contact(msg: types.Message, state: FSMContext):
    if App.user.set_phone(msg):
        await get_menu(msg, state)
    else:
        await msg.answer(
            text.phone_error, 
            reply_markup = form_buttons([ [types.KeyboardButton(text = text.Btn.BACK.value)] ])
        )

@log
@router.message(F.text == text.Btn.HELP.value)
async def help(msg: types.Message):
    await msg.answer(
        text.help, 
        reply_markup = form_buttons([ [types.KeyboardButton(text = text.Btn.BACK.value)] ])
    )

@log
@router.message(F.text.in_([text.Btn.BACK.value, text.Btn.SKIP.value]))
async def back(msg: types.Message, state: FSMContext):
    next_page = await App.go_back(state)
    if not next_page:
        await get_menu(msg, state)

@log
@router.message(Command('state'))
async def get_state(msg: types.Message):
    print('History:', App.history, '\nUser:', App.user.username, '\nSubscription:', App.user.subscriptions[0])

@log
@router.message(Command('menu'))
@router.message(F.text)
async def get_menu(msg: types.Message, state: FSMContext):
    print(App.history)
    await App.clear_history(state)
    await msg.answer(
        text.Btn.MENU.value, 
        reply_markup = App.menu()
    )