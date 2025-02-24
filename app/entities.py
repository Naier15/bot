from dataclasses import dataclass
from typing import Optional, Self
import math, regex

from aiogram import Bot, types
from aiogram.fsm.state import State
from aiogram.fsm.context import FSMContext
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from .database import Database
from .utils import Markup
from . import text
from config import Config


class Page:
    def __init__(self):
        self.current_page: int = 1
        self.quantity: int = 0
        self.items_per_page: int = 8
        self.choices: list[str]

    def using(self, choices: list[str]) -> Self:
        self.quantity = len(choices)
        self.choices = choices
        return self
    
    def get_page(self, page_number: Optional[int] = None) -> Optional[types.InlineKeyboardMarkup]:
        if not page_number:
            page_number = self.current_page
        if page_number < 1 or math.ceil(self.quantity / self.items_per_page) < page_number:
            return
        
        self.current_page = page_number
        index = (self.current_page - 1) * self.items_per_page
        chunk = self.choices[index:index+self.items_per_page]
        if len(chunk) == 0:
            return
        buttons = []
        for choice in chunk:
            buttons.append([types.InlineKeyboardButton(
                text = choice['text'], 
                callback_data = choice['id']
            )])
        buttons += [[
            types.InlineKeyboardButton(text = '<', callback_data = 'back'),
            types.InlineKeyboardButton(text = f' {self.current_page}/{math.ceil(self.quantity / self.items_per_page)} '.center(12, '-'), callback_data = 'page'),
            types.InlineKeyboardButton(text = '>', callback_data = 'next')
        ]]
        buttons += [[types.InlineKeyboardButton(text = 'В меню', callback_data = 'menu')]]
        return Markup.inline_buttons(buttons)


@dataclass
class Subscription:
    def __init__(self,
        database: Database,
        city_id: Optional[str] = None, 
        property_id: Optional[str] = None, 
        building_id: Optional[str] = None
    ) -> Self:
        self.database: Database = database
        self.city_id: str = city_id
        self.property_id: str = property_id
        self.building_id: str = building_id
        self.url: str = None
        self.send_keys: str = 'Неизвестно'
        self.address: str = None
        self.photos: list = []

    def __str__(self) -> str:
        return f'Subscription(city = {self.city_id}, property = {self.property_id}, building = {self.building_id})'
        
    async def set(self, 
        city_id: Optional[str] = None, 
        property_id: Optional[str] = None, 
        building_id: Optional[str] = None
    ) -> bool:
        if city_id and len(city_id) > 0:
            self.city_id = city_id
            return True
        if property_id and len(property_id) > 0:
            self.property_id = property_id
            return True
        if building_id and len(building_id) > 0:
            self.building_id = building_id
            return True
        return False
        
    async def save(self, chat_id: str) -> None:
        await self.sync()
        await self.database.save_subscription(chat_id, self.building_id)

    async def remove(self, chat_id: str) -> None:
        await self.database.remove_subscription(chat_id, self.building_id)

    async def sync(self) -> bool:
        if not self.building_id:
            return False
        data = await self.database.get_subscription_data(self.building_id)
        self.url = data['url']
        self.address = data['text']
        self.send_keys = data['send_keys']
        self.photos = data['photos']
        return True


class User:
    id: Optional[int] = None
    phone: Optional[str] = None
    is_registed: bool = False
    is_sync: bool = False
    login: Optional[str] = None
    password: Optional[str]
    email: Optional[str] = None
    subscriptions: list[Subscription] = []

    def __init__(self, database: Database) -> Self:
        self.database = database

    def to_dict(self) -> dict:
        return self.__dict__
    
    @staticmethod
    def from_dict(data: dict) -> Self:
        return User(**data)

    def get_data(self) -> str:
        res = (
            f'{f'- ЛОГИН 😉 <b><code>{self.login}</code></b>\n' if self.is_registed and self.login else ''}'
            f'{f'- ТЕЛЕФОН 📞 <b><code>{self.phone}</code></b>\n' if self.phone else ''}'
            f'{f'- EMAIL 📧 <b><code>{self.email}</code></b>\n' if self.is_registed and self.email else ''}'
            '\n<i>🔹 Нажмите на логин, email или телефон, чтобы их скопировать</i>'
        )
        return res if res else 'Нет данных'
     
    async def set_phone(self, msg: types.Message) -> bool:
        phone = msg.contact.phone_number.strip().replace(' ', '').replace('-', '')
        if len(phone) == 11 and phone.startswith('7'):
            phone = f'8{phone[1:]}'
        elif len(phone) == 12 and phone.startswith('+7'):
            phone = f'8{phone[2:]}'

        if len(phone) == 11:
            self.id = msg.from_user.id
            self.phone = phone
            return True
        else:
            return False
        
    async def set_login(self, msg: types.Message) -> bool:
        login = msg.text.strip()
        await msg.delete()
        if len(login) > 5 and len(login) < 16:
            self.login = login
            return True
        else:
            return False
        
    async def set_password(self, msg: types.Message) -> bool:
        password = msg.text.strip()
        await msg.delete()
        if len(password) > 7:
            self.password = password
            return True
        else:
            return False
        
    async def set_email(self, msg: types.Message) -> bool:
        email = msg.text.strip()
        await msg.delete()
        if regex.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email):
            self.email = email
            await msg.answer(f' EMAIL: {email} '.center(40, '-'))
            return True
        else:
            await msg.answer(text.email_tip)      
            return False
        
    async def save(self, temporary: bool = False) -> Optional[str]:
        if temporary:
            tg_user = await self.database.get_temp_user(self.id)
            if not tg_user:
                await self.database.create_temp_user(self.id, self.phone)
        else:
            is_valid = await self.database.is_user_valid(self.login)
            if is_valid:
                await self.database.create_user(self.id, self.login, self.password, self.email)
                self.is_registed = True
            else:
                return text.Error.user_exists.value
    
    async def sync(self, msg: types.Message) -> None:
        if not self.id:
            self.id = msg.from_user.id

        tg_user = await self.database.get_user(self.id)
        if not tg_user:
            return
        self.is_registed = True if tg_user.is_registed else False
        
        if not self.phone:
            self.phone = tg_user.user_profile.tel
        self.login = tg_user.user_profile.user.username
        self.email = tg_user.user_profile.user.email if tg_user.user_profile.user.email else None
        self.subscriptions = [
            Subscription(database = App.database, building_id = str(building.id)) 
            for building in tg_user.building.all()
        ]
        [await x.sync() for x in self.subscriptions]
        [x.photos for x in self.subscriptions]
        self.is_sync = True

    async def clear_data(self) -> None:
        self.login = None
        self.password = None
        self.email = None


class App:
    is_debug: bool = True
    history: list[State] = []
    bot: Bot = Bot(
        token = Config().BOT_TOKEN, 
        default = DefaultBotProperties(parse_mode = ParseMode.HTML)
    )
    page: Page = Page()
    database: Database = Database()
    user: User = User(database)
    subscription: Optional[Subscription]

    @staticmethod
    def new_subscription() -> Subscription:
        App.subscription = Subscription(database = App.database)
        return App.subscription

    @staticmethod
    async def save_subscription() -> None:
        await App.subscription.save(App.user.id)
        App.user.subscriptions += [App.subscription]
        App.subscription = None
    
    @staticmethod
    def menu() -> types.ReplyKeyboardMarkup:
        btns = [
            [
                types.KeyboardButton(text = text.Btn.FLATS.value),
                types.KeyboardButton(text = text.Btn.PROFILE.value)
            ],
            [
                types.KeyboardButton(text = text.Btn.OFFICES.value),
                types.KeyboardButton(text = text.Btn.SUBSCRIPTION.value)
            ],
            [types.KeyboardButton(text = text.Btn.HELP.value)]
        ]
        return Markup.bottom_buttons(btns)
    
    @staticmethod
    async def clear_history(state: FSMContext):
        App.user.password = None
        App.history.clear()
        await state.clear()
    
    @staticmethod
    async def replace_state(page: State, state: FSMContext) -> None:
        if len(App.history) > 0 and App.history[-1] == page:
            return
        App.history[-1] = page
        await state.set_state(page)

    @staticmethod
    async def set_state(page: State, state: FSMContext) -> None:
        if len(App.history) > 0 and App.history[-1] == page:
            return
        App.history.append(page)
        await state.set_state(page)

    @staticmethod
    async def get_state() -> Optional[State]:
        if len(App.history) == 0:
            return
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
        return page