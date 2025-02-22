from aiogram import Router, F, types

from app import text, log, form_buttons


router = Router()

@log
@router.message(F.text == text.Btn.FLATS.value)
async def flats(msg: types.Message):
    markup = form_buttons([
        [types.KeyboardButton(text = text.Btn.BACK.value)]
    ])
    await msg.answer(text.flats, reply_markup = markup)

@log
@router.message(F.text == text.Btn.OFFICES.value)
async def offices(msg: types.Message):
    markup = form_buttons([
        [types.KeyboardButton(text = text.Btn.BACK.value)]
    ])
    await msg.answer(text.offices, reply_markup=markup)