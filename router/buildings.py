from aiogram import Router, F, types
from aiogram.fsm.context import FSMContext

from app import text, Markup, log, CityRepository


router = Router()

# Раздел Каталог квартир
@router.message(F.text == text.Btn.FLATS.value)
async def flats(msg: types.Message, state: FSMContext):
    log(flats)
    cities = await CityRepository().get()
    city_name = [f'<a href="{city['url']}">{city['name']}</a>' for city in cities]
    await msg.answer(
        f'{text.flats}\n{'\n'.join(city_name)}', 
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