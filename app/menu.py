from aiogram import Router, F, types
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from dataclasses import dataclass
from typing import Optional, Self
from aiogram import Bot
from aiogram.fsm.state import State

from .config import Config
from . import text
from .utils import form_buttons, log


router = Router()

@dataclass
class User:
    id: Optional[int] = None
    phone: Optional[str] = None
    login: Optional[str] = None
    username: Optional[str] = None
    password: Optional[str] = None
    email: Optional[str] = None
    city: Optional[str] = None
    estate: Optional[str] = None
    house: Optional[str] = None

    def to_dict(self) -> dict:
        return self.__dict__
    
    @staticmethod
    def from_dict(data: dict) -> Self:
        return User(**data)
    
    def get_data(self) -> str:
        res = (
            f'{f'📞 {self.phone}\n' if self.phone else ''}'
            f'{f'🆔 {self.login}\n' if self.login else ''}'
            f'{f'✉ {self.email}\n' if self.email else ''}'
            f'{f'🏠 {self.estate}\n' if self.estate else ''}'
        )
        return res if res else 'Нет данных'


class App:
    MENU = '⚪Меню'
    FLATS = '🏡Каталог квартир'
    OFFICES = '🏢Помещения для бизнеса'
    PROFILE = '👤Мой профиль'
    SUBSCRIPTION = '✅Подписка'
    HELP = '💬Помощь'
    BACK = '🔙Назад'
    EDIT = '✏Редактировать анкету'
    SKIP = '⏩Пропустить'
    SUBSCRIBE = '⭐Подписаться'
    NEW_SUBSCRIPTION = '+ Новая подписка'
    TO_MENU = '🔙В главное меню'
    history: list[State] = []
    user: User = User()
    bot: Bot = Bot(token=Config().BOT_TOKEN)
    
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
    async def clear_history(state: FSMContext):
        App.history.clear()
        await state.clear()
    
    @staticmethod
    async def set_state(page: State, state: FSMContext) -> None:
        if len(App.history) > 0 and App.history[-1] == page:
            return
        App.history.append(page)
        await state.set_state(page)
        print('History: ', App.history)

    @staticmethod
    async def get_state() -> Optional[State]:
        if len(App.history) == 0:
            return
        print('History: ', App.history)
        return App.history[-1]

    @staticmethod
    async def go_back(state: FSMContext) -> State:
        if len(App.history) > 0:
            App.history.pop()  # Шаг назад

        page = None
        if len(App.history) > 0:
            page = App.history[-1] # Получение предыдущего состояния
            await state.set_state(page)
            App.history.pop() # Удаляем и предыдущего состояние, поскольку оно добавится в следующем обработчике
        print('History: ', App.history, 'page: ', page)
        return page

@log
@router.message(CommandStart())
async def start(msg: types.Message, state: FSMContext):
    await App.clear_history(state)
    await msg.answer(
        text.introduction, 
        reply_markup = form_buttons([ [types.KeyboardButton(text = 'Разрешить', request_contact = True)] ])
    )
    # await get_menu(msg, state)

@log
@router.message(F.contact)
async def get_contact(msg: types.Message, state: FSMContext):
    phone = msg.contact.phone_number.strip().replace('-', '')
    if phone.startswith('8'):
        phone = f'+7{phone[1:]}'
    if len(phone) == 12:
        App.user.id = msg.from_user.id
        App.user.phone = phone
        await get_menu(msg, state)
    else:
        await msg.answer(
            f'Не похоже на номер телефона, попробуйте еще раз', 
            reply_markup = form_buttons([ [types.KeyboardButton(text = App.BACK)] ])
        )

@log
@router.message(F.text == App.HELP)
async def help(msg: types.Message):
    await msg.answer(
        text.help, 
        reply_markup = form_buttons([ [types.KeyboardButton(text=App.BACK)] ])
    )

@log
@router.message(F.text.in_([App.BACK, App.SKIP]))
async def back(msg: types.Message, state: FSMContext):
    next_page = await App.go_back(state)
    if not next_page:
        await get_menu(msg, state)

@log
@router.message(Command('state'))
async def get_state(msg: types.Message):
    print('History:', App.history, '\nUser:', App.user.username)

@log
@router.message(Command('menu'))
async def get_menu(msg: types.Message, state: FSMContext):
    await App.clear_history(state)
    await msg.answer(
        App.MENU, 
        reply_markup = App.menu()
    )