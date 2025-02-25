from aiogram import Router, F, types

from app import text, Markup, App, log


router = Router()

@log
@router.message(F.text == text.Btn.FLATS.value)
async def flats(msg: types.Message):
    cities = await App.database.get_cities()
    city_name = [f'<a href="{city['url']}">{city['name']}</a>' for city in cities]
    await msg.answer(
        f'{text.flats}\n{'\n'.join(city_name)}', 
        reply_markup = Markup.bottom_buttons([ [types.KeyboardButton(text = text.Btn.BACK.value)] ])
    )

@log
@router.message(F.text == text.Btn.OFFICES.value)
async def offices(msg: types.Message):
    await msg.answer(
        {text.offices}, 
        reply_markup = Markup.bottom_buttons([ [types.KeyboardButton(text = text.Btn.BACK.value)] ])
    )