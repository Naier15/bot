from aiogram import Router, F, types
from aiogram.fsm.context import FSMContext

from telegrambot.app import text, Markup, CityRepository, log, App


router = Router()

# Раздел Каталог квартир
@router.message(F.text == text.Btn.FLATS.value)
@log
async def flats(msg: types.Message, state: FSMContext):
    cities = await CityRepository().get()
    city_name = [f'<a href="{city['url']}">{city['name']}</a>' for city in cities]
    await msg.answer(
        f'{text.flats}\n{'\n'.join(city_name)}', 
        reply_markup = App.menu()
    )

# Раздел Помещения для офиса
@router.message(F.text == text.Btn.OFFICES.value)
@log
async def offices(msg: types.Message, state: FSMContext):
    await msg.answer(
        text.offices, 
        reply_markup = App.menu()
    )
