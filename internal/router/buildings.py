from aiogram import Router, F, types
from aiogram.fsm.context import FSMContext

from internal import text, log
from internal.entities import App
from internal.repositories import CityRepository
from .menu import require_auth


router = Router()

@router.message(F.text == text.Btn.FLATS.value)
@require_auth()
@log
async def flats(msg: types.Message, state: FSMContext):
    '''Раздел Каталог квартир'''
    cities = await CityRepository().get()
    city_name = [f'<a href="{city['url']}">{city['name']}</a>' for city in cities]
    city_name = '\n'.join(city_name)
    await msg.answer(
        f'{text.flats}\n{city_name}',
        reply_markup = App.menu()
    )

@router.message(F.text == text.Btn.OFFICES.value)
@require_auth()
@log
async def offices(msg: types.Message, state: FSMContext):
    '''Раздел Помещения для офиса'''
    await msg.answer(
        text.offices, 
        reply_markup = App.menu()
    )