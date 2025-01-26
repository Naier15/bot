from app.context import Context
from aiogram import Router, F, types
import emoji
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext


class Page(StatesGroup):
    menu = State()
    flats = State()
    offices = State()
    profile = State()
    subscription = State()
    help = State()
    none = State()

class App:
    MENU = emoji.emojize(':white_circle:Меню')
    FLATS = emoji.emojize(':house_with_garden:Каталог квартир')
    OFFICES = emoji.emojize(':office_building:Помещения для бизнеса')
    PROFILE = emoji.emojize(':bust_in_silhouette:Мой профиль')
    SUBSCRIPTION = emoji.emojize(':check_mark_button:Подписка')
    HELP = emoji.emojize(':speech_balloon:Помощь')
    BACK = emoji.emojize(':left_arrow:Назад')
    history = []
    
    @staticmethod
    def menu() -> types.ReplyKeyboardMarkup:
        btns = [
            [
                types.KeyboardButton(text=App.FLATS),
                types.KeyboardButton(text=App.PROFILE)
            ],
            [
                types.KeyboardButton(text=App.OFFICES),
                types.KeyboardButton(text=App.SUBSCRIPTION)
            ],
            [types.KeyboardButton(text=App.HELP)]
        ]
        return types.ReplyKeyboardMarkup(
            keyboard=btns, 
            resize_keyboard=True, 
            one_time_keyboard=True, 
            input_field_placeholder='Выберете действие:'
        )
    
    @staticmethod
    async def set_state(state: Page, context: FSMContext) -> None:
        if len(App.history) == 0 or App.history[-1] != state:
            App.history.append(state)
            await context.set_state(state)
            print(App.history)

    @staticmethod
    async def go_back(context: FSMContext) -> None:
        App.history.pop()
        state = App.history[-1]
        await context.set_state(state)
        print(App.history)
