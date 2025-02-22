from aiogram import Router, F, types

from app import text, Markup, log


router = Router()

@log
@router.message(F.text == text.Btn.FLATS.value)
async def flats(msg: types.Message):
    await msg.answer(
        text.flats, 
        reply_markup = Markup.bottom_buttons([ [types.KeyboardButton(text = text.Btn.BACK.value)] ])
    )

@log
@router.message(F.text == text.Btn.OFFICES.value)
async def offices(msg: types.Message):
    await msg.answer(
        text.offices, 
        reply_markup = Markup.bottom_buttons([ [types.KeyboardButton(text = text.Btn.BACK.value)] ])
    )