from aiogram import Router, F, types

from .. import text
from ..text import Btn
from ..utils import log, form_buttons


router = Router()

@log
@router.message(F.text == Btn.FLATS.value)
async def flats(msg: types.Message):
    markup = form_buttons([
        [types.KeyboardButton(text=Btn.BACK.value)]
    ])
    await msg.answer(text.flats, reply_markup=markup)

@log
@router.message(F.text == Btn.OFFICES.value)
async def offices(msg: types.Message):
    markup = form_buttons([
        [types.KeyboardButton(text=Btn.BACK.value)]
    ])
    await msg.answer(text.offices, reply_markup=markup)