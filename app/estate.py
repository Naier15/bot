from aiogram import Router, F, types
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from .menu import App
from .utils import form_buttons, log


router = Router()

class Page(StatesGroup):
    estate = State()

@log
@router.message(F.text == App.NEW_SUBSCRIPTION)
async def estate_start(msg: types.Message, state: FSMContext):
    await msg.answer(
        f'На новости какого ЖК вы хотите подписаться:', 
        reply_markup = form_buttons([
            [types.KeyboardButton(text = App.BACK)]
        ])
    )