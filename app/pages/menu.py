from aiogram import Router, F, types
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext

from .. import text
from ..utils import form_buttons, log
from ..entities import App, Page


router = Router()

@log
@router.message(CommandStart())
async def start(msg: types.Message, state: FSMContext):
    await App.clear_history(state)
    # buttons = Page().make_page(1)
    # if buttons:
    #     await msg.answer('Выберете чат:', reply_markup = buttons)
    await msg.answer(
        text.introduction,
        reply_markup = form_buttons([ [types.KeyboardButton(text = 'Разрешить') ]])#, request_contact = True)] ])
    )
    # await get_menu(msg, state)

# @log
# @router.callback_query(F.data.in_(['next', 'back']))
# async def change_page(call: types.CallbackQuery):
#     buttons = None
#     page = App.page
#     if call.data == 'next':
#         buttons = page.make_page(page.current_page + 1)
#     elif call.data == 'back':
#         buttons = page.make_page(page.current_page - 1)

#     if buttons:
#         await call.message.edit_reply_markup(reply_markup = buttons)

@log
@router.message(F.contact)
async def get_contact(msg: types.Message, state: FSMContext):
    phone = msg.contact.phone_number.strip().replace('-', '')
    if phone.startswith('8'):
        phone = f'+7{phone[1:]}'
    if len(phone) == 12:
        App.user.id = msg.from_user.id
        App.user.phone = phone
        await get_menu(msg, state)
    else:
        await msg.answer(
            f'Не похоже на номер телефона, попробуйте еще раз', 
            reply_markup = form_buttons([ [types.KeyboardButton(text = App.BACK)] ])
        )

@log
@router.message(F.text == App.HELP)
async def help(msg: types.Message):
    await msg.answer(
        text.help, 
        reply_markup = form_buttons([ [types.KeyboardButton(text=App.BACK)] ])
    )

@log
@router.message(F.text.in_([App.BACK, App.SKIP]))
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
    print('menu')
    await App.clear_history(state)
    await msg.answer(
        App.MENU, 
        reply_markup = App.menu()
    )