from aiogram import Router, F, types
from aiogram.fsm.context import FSMContext

from telegrambot.app import text, Markup, App, log


router = Router()
    
@router.message(F.text == text.Btn.PROFILE.value)
@log
async def main(msg: types.Message, state: FSMContext): 
    '''Раздел Профиль'''  
    async with App(state) as app:
        await app.user.sync(msg.chat.id)
        await msg.answer(
            f'ВАШ ПРОФИЛЬ:\n{app.user.get_data()}',
            reply_markup = Markup.bottom_buttons([
                [types.KeyboardButton(text = text.Btn.TO_MENU.value)]
            ])
        )