from aiogram import Router, F, types

from .menu import App
from .utils import log, form_buttons
from . import text


router = Router()

@log
@router.message(F.text == App.FLATS)
async def flats(msg: types.Message):
    markup = form_buttons([
        [types.KeyboardButton(text=App.BACK)]
    ])
    await msg.answer(text.flats, reply_markup=markup)

@log
@router.message(F.text == App.OFFICES)
async def offices(msg: types.Message):
    markup = form_buttons([
        [types.KeyboardButton(text=App.BACK)]
    ])
    await msg.answer(text.offices, reply_markup=markup)