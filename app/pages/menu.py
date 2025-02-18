from aiogram import Router, F, types
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext

from .. import text
from ..text import Btn
from ..utils import form_buttons, log
from ..entities import App

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
    phone = msg.contact.phone_number.strip().replace('-', '')
    if (phone.startswith('7') or phone.startswith('8')) and len(phone) == 11:
        phone = f'+7{phone[1:]}'

    if len(phone) == 12:
        App.user.id = msg.from_user.id
        App.user.phone = phone
        await get_menu(msg, state)
    else:
        await msg.answer(
            text.phone_error, 
            reply_markup = form_buttons([ [types.KeyboardButton(text = Btn.BACK.value)] ])
        )

@log
@router.message(F.text == Btn.HELP.value)
async def help(msg: types.Message):
    await msg.answer(
        text.help, 
        reply_markup = form_buttons([ [types.KeyboardButton(text=Btn.BACK.value)] ])
    )

@log
@router.message(F.text.in_([Btn.BACK.value, Btn.SKIP.value]))
async def back(msg: types.Message, state: FSMContext):
    next_page = await App.go_back(state)
    if not next_page:
        await get_menu(msg, state)

@log
@router.message(Command('state'))
async def get_state(msg: types.Message):
    print('History:', App.history, '\nUser:', App.user.username)

@log
@router.message(Command('menu'))
@router.message(F.text)
async def get_menu(msg: types.Message, state: FSMContext):
    print(App.history)
    print('menu')
    await App.clear_history(state)
    await msg.answer(
        Btn.MENU.value, 
        reply_markup = App.menu()
    )