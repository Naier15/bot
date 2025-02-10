from typing import Optional, Self, Iterable
import math

from aiogram import Bot, types
from aiogram.fsm.state import State
from aiogram.fsm.context import FSMContext
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from .text import Btn
from .config import Config
from .utils import form_buttons


class Page:
    def __init__(self):
        self.current_page: int = 1
        self.chats_counter: int = 0
        self.items_per_page: int = 8
        self.chats: Iterable[dict[str, str]]

    def using(self, items: Iterable[dict[str, str]]) -> Self:
        self.chats_counter = len(items)
        self.chats = items
        return self
    
    def get_page(self, page: int) -> Optional[types.InlineKeyboardMarkup]:
        if page < 1 or math.ceil(self.chats_counter / self.items_per_page) < page:
            return
        
        self.current_page = page
        index = (self.current_page - 1) * self.items_per_page
        chats_to_show = self.chats[index:index+self.items_per_page]
        if len(chats_to_show) == 0:
            return
        buttons = []
        for chat in chats_to_show:
            buttons.append([types.InlineKeyboardButton(text = chat['title'], callback_data = chat['id'])])
        buttons += [[
            types.InlineKeyboardButton(text = '<', callback_data = 'back'),
            types.InlineKeyboardButton(text = f' {self.current_page}/{math.ceil(self.chats_counter / self.items_per_page)} '.center(12, '-'), callback_data = 'page'),
            types.InlineKeyboardButton(text = '>', callback_data = 'next')
        ]]
        return types.InlineKeyboardMarkup(inline_keyboard = buttons)

class Subscription:
    city: Optional[str]
    estate: Optional[str]
    house: Optional[str]
    url: Optional[str]

    def __init__(self, 
        city: Optional[str] = None, 
        estate: Optional[str] = None, 
        house: Optional[str] = None, 
        url: Optional[str] = None
    ) -> Self:
        self.city = city
        self.estate = estate
        self.house = house
        self.url = url

class User:
    id: Optional[int] = 31313131
    username: Optional[str] = 'Роман'
    phone: Optional[str] = ''
    login: Optional[str] = 'naier'
    password: Optional[str]
    email: Optional[str] = 'grv1510@mail.ru'
    subscriptions: list[Subscription] = []

    def to_dict(self) -> dict:
        return self.__dict__
    
    @staticmethod
    def from_dict(data: dict) -> Self:
        return User(**data)

    def get_data(self) -> str:
        res = (
            f'{f'- ЛОГИН 😉 <b><code>{self.login}</code></b>\n' if self.login else ''}'
            f'{f'- ТЕЛЕФОН 📞 <b><code>{self.phone}</code></b>\n' if self.phone else ''}'
            f'{f'- EMAIL 📧 <b><code>{self.email}</code></b>\n' if self.email else ''}'
        )
        return res if res else 'Нет данных'

class App:
    history: list[State] = []
    user: User = User()
    bot: Bot = Bot(
        token = Config().BOT_TOKEN, 
        default = DefaultBotProperties(parse_mode=ParseMode.HTML)
    )
    page: Page = Page()
    subscription: Optional[Subscription]
    
    @staticmethod
    def menu() -> types.ReplyKeyboardMarkup:
        btns = [
            [
                types.KeyboardButton(text=Btn.FLATS.value),
                types.KeyboardButton(text=Btn.PROFILE.value)
            ],
            [
                types.KeyboardButton(text=Btn.OFFICES.value),
                types.KeyboardButton(text=Btn.SUBSCRIPTION.value)
            ],
            [types.KeyboardButton(text=Btn.HELP.value)]
        ]
        return form_buttons(btns)
    
    @staticmethod
    async def clear_history(state: FSMContext):
        App.history.clear()
        await state.clear()
    
    @staticmethod
    async def replace_state(page: State, state: FSMContext) -> None:
        if len(App.history) > 0 and App.history[-1] == page:
            return
        App.history[-1] = page
        await state.set_state(page)
        print('History: ', App.history)

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