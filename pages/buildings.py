from aiogram import Router, F, types
from aiogram.fsm.context import FSMContext

from telegrambot.app import text, Markup, App, log


router = Router()

# Раздел Каталог квартир
@router.message(F.text == text.Btn.FLATS.value)
async def flats(msg: types.Message, state: FSMContext):
    log(flats)
    async with App(state) as app:
        cities = await app.database.get_cities()
        # city_name = [f'<a href="{city['url']}">{city['name']}</a>' for city in cities]
        city_name = [f"<a href=f'{city['url']}'>{city['name']}</a>" for city in cities]
        city_name = '\n'.join(city_name)
        await msg.answer(
            f'{text.flats}\n{city_name}',
            reply_markup = Markup.bottom_buttons([ [types.KeyboardButton(text = text.Btn.BACK.value)] ])
        )

# Раздел Помещения для офиса
@router.message(F.text == text.Btn.OFFICES.value)
async def offices(msg: types.Message, state: FSMContext):
    log(offices)
    await msg.answer(
        text.offices, 
        reply_markup = Markup.bottom_buttons([ [types.KeyboardButton(text = text.Btn.BACK.value)] ])
    )