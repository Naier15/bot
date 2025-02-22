from dataclasses import dataclass
from typing import Optional, Self
import math, regex, secrets, string

from aiogram import Bot, types
from aiogram.fsm.state import State
from aiogram.fsm.context import FSMContext
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from app import text, form_buttons #, Config


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
            print(choice['text'])
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
        return types.InlineKeyboardMarkup(inline_keyboard = buttons)

@dataclass
class Subscription:
    city: Optional[str]
    property: Optional[str]
    building: Optional[str]
    url: Optional[str]

    def __init__(self, 
        city: Optional[str] = None, 
        property: Optional[str] = None, 
        building: Optional[str] = None, 
        url: Optional[str] = None
    ) -> Self:
        self.city = city
        self.property = property
        self.building = building
        self.url = url

    def __str__(self) -> str:
        return f'Subscription(city = {self.city}, property  = {self.property}, building = {self.building})'
    
    async def set_city(self, city: str) -> bool:
        if len(city) > 0:
            self.city = city
            return True
        else:
            return False
        
    async def set_property(self, property: str) -> bool:
        if len(property) > 0:
            self.property = property
            return True
        else:
            return False
        
    async def set_building(self, building: str) -> bool:
        if len(building) > 0:
            self.building = building
            return True
        else:
            return False

class User:
    id: Optional[int] = 31313131
    username: Optional[str] = 'Роман'
    phone: Optional[str] = ''
    login: Optional[str] = 'naier'
    password: Optional[str]
    email: Optional[str] = 'grv1510@mail.ru'
    subscriptions: list[Subscription] = [Subscription('1', '576', '3609')]

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
            '\n<i>Нажмите на логин, email или телефон, чтобы их скопировать</i>'
        )
        return res if res else 'Нет данных'
     
    async def set_phone(self, msg: types.Message) -> bool:
        phone = msg.contact.phone_number.strip().replace('-', '')
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
            await msg.answer(f' ЛОГИН: {login} '.center(40, '-'))
            return True
        else:
            await msg.answer(text.login_tip)
            return False
        
    async def set_password(self, msg: types.Message) -> bool:
        password = msg.text.strip()
        await msg.delete()
        if len(password) > 7:
            self.password = password
            await msg.answer(f' ПАРОЛЬ: {'*' * len(password)} '.center(40, '-'))
            return True
        else:
            await msg.answer(text.password_tip)      
            return False
        
    async def set_email(self, msg: types.Message):
        email = msg.text.strip()
        await msg.delete()
        if regex.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email):
            self.email = email
            await msg.answer(f' EMAIL: {email} '.center(40, '-'))
            return True
        else:
            await msg.answer(text.email_tip)      
            return False
        
    async def save(temporary: bool = False):
        pass


class App:
    history: list[State] = []
    user: User = User()
    bot: Bot = Bot(
        # token = Config().BOT_TOKEN, 
        token = '1291275643:AAHIk28uq57pVT5ZZz-IEQllgQhP5_mwx7s',
        default = DefaultBotProperties(parse_mode=ParseMode.HTML)
    )
    page: Page = Page()
    subscription: Optional[Subscription]

    @staticmethod
    def save_subscription() -> None:
        App.user.subscriptions += [App.subscription]
        App.subscription = None
    
    @staticmethod
    def menu() -> types.ReplyKeyboardMarkup:
        btns = [
            [
                types.KeyboardButton(text=text.Btn.FLATS.value),
                types.KeyboardButton(text=text.Btn.PROFILE.value)
            ],
            [
                types.KeyboardButton(text=text.Btn.OFFICES.value),
                types.KeyboardButton(text=text.Btn.SUBSCRIPTION.value)
            ],
            [types.KeyboardButton(text=text.Btn.HELP.value)]
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
    
class Database:        

    @staticmethod
    async def get_cities() -> list[dict]:
        from property.models import City
        cities = [{
            'id': str(x.id),
            'text': x.city_name
        } async for x in City.objects.all()]
        cities.sort(key = lambda x: x['text'])
        return cities

    @staticmethod
    async def get_properties() -> list:
        from property.models import Property
        properties = [{
            'id': str(x.id),
            'text': x.name
        } async for x in Property.objects.filter(city_id = int(App.subscription.city))]
        properties.sort(key = lambda x: x['text'])
        return properties
    
    @staticmethod
    async def get_buildings() -> list:
        from property.models import Buildings
        buildings = [{
            'id': str(x.id),
            'text': x.num_dom
        } async for x in Buildings.objects.filter(fk_property = int(App.subscription.property))]
        buildings.sort(key = lambda x: x['text'])
        return buildings
    
    @staticmethod
    async def get_building(id: str) -> dict:
        from property.models import Buildings
        building = [{
            'id': str(x.id),
            'text': x.addr,
            'url': None
        } async for x in Buildings.objects.filter(id = int(id))]
        return building[0]
    
    @staticmethod
    async def create_temp_user(id: str, phone_number: str) -> None:
        from django.contrib.auth.models import User
        from authapp.models import UserProfile

        alphabet = string.ascii_letters + string.digits
        temp_login = 'temp_' + ''.join(secrets.choice(alphabet) for _ in range(16))
        user = User.objects.create_user(
            username = temp_login,
            password = temp_login
        )
        profile = UserProfile.objects.create(tel = phone_number, user = user)

    @staticmethod
    async def get_user() -> None:
        from django.contrib.auth.models import User
        from authapp.models import UserProfile

        # UserProfile.objects.filter(tel = phone_number, user = user)