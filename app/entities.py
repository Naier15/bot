from dataclasses import dataclass
from typing import Optional, Self
import regex

from aiogram import Bot, types
from aiogram.fsm.state import State
from aiogram.fsm.context import FSMContext
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from .database import Database
from .utils import Markup, log_it
from . import text
from config import Config


# Подписка
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
        self.url: Optional[str] = None
        self.send_keys: str = 'Неизвестно'
        self.property_name: Optional[str] = None
        self.photos: list[types.InputMediaPhoto] = []
        self.stage: Optional[str] = None
        self.date_realise: Optional[str] = None
        self.date_info: Optional[str] = None

    def __str__(self) -> str:
        return f'Subscription(city = {self.city_id}, property = {self.property_id}, building = {self.building_id})'
        
    # Сохранение подписки
    async def save(self, chat_id: str) -> None:
        await self.sync()
        await self.database.save_subscription(chat_id, self.building_id)

    # Удаление подписки
    async def remove(self, chat_id: str) -> None:
        await self.database.remove_subscription(chat_id, self.building_id)
        App.user.subscriptions.remove(self)

    # Подтягивание всех данных из базы данных
    async def sync(self) -> bool:
        if not self.building_id:
            return False
        data = await self.database.get_subscription_data(self.building_id)
        self.url = data['url']
        self.property_name = data['property_name']
        self.photos = data['photos']
        self.stage = data['stage']
        self.date_realise = data['date_realise']
        self.date_info = data['date_info']
        return True
    
    # Формирование и отправка сообщения ежедневной подписки
    async def send_info(self, chat_id: int, is_dispatch: bool = False) -> None:
        answer = (
            f'{self.property_name}'
            f'\n<a href="{self.url}">Сайт ЖК</a>'
            f'\nСтадия строительства: {self.stage}'
            f'\nСдача дома: {self.date_realise}'
            f'\nПеренос сроков: {self.date_info}'
            # f'\nВсе фото и видео по <a href="">ссылке</a>'
        )

        photo_ids = [id for id, _ in self.photos]
        if is_dispatch:
            unseen_photos = await self.database.filter_unseen_photos(chat_id, self.building_id, photo_ids) 
            [await self.database.make_photo_seen(chat_id, self.building_id, photo_id) for photo_id in photo_ids]
        else:
            unseen_photos = photo_ids
        photos_to_show = [url for id, url in self.photos if id in unseen_photos]        
        photos_to_show = [types.InputMediaPhoto(media = f'{Config().DJANGO_HOST}media/{url}') for url in photos_to_show]

        if len(photos_to_show) > 0:
            await App.bot.send_message(
                chat_id, 
                answer, 
                reply_markup = App.menu() if is_dispatch else Markup.bottom_buttons([ [types.KeyboardButton(text = text.Btn.BACK.value)] ])
            )
            try:
                await App.bot.send_media_group(chat_id, photos_to_show)
            except:
                pass

# Пользователь
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

    # Формирование сообщения в профиле
    def get_data(self) -> str:
        res = (
            f'{f'- ЛОГИН 😉 <b><code>{self.login}</code></b>\n' if self.is_registed and self.login else ''}'
            f'{f'- ТЕЛЕФОН 📞 <b><code>{self.phone}</code></b>\n' if self.phone else ''}'
            f'{f'- EMAIL 📧 <b><code>{self.email}</code></b>\n' if self.is_registed and self.email else ''}'
            '\n<i>🔹 Нажмите на логин, email или телефон, чтобы их скопировать</i>'
        )
        return res if res else 'Нет данных'
     
    # Добавление и валидация номера телефона
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
        
    # Добавление и валидация логина
    async def set_login(self, msg: types.Message) -> bool:
        login = msg.text.strip()
        await msg.delete()
        if len(login) > 5 and len(login) < 16:
            self.login = login
            return True
        else:
            return False
        
    # Добавление и валидация пароля
    async def set_password(self, msg: types.Message) -> bool:
        password = msg.text.strip()
        await msg.delete()
        if len(password) > 7:
            self.password = password
            return True
        else:
            return False
        
    # Добавление и валидация email
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
        
    # Сохранение в базе временного и постоянного пользователя
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
    
    # Подтягивание данных пользователя
    async def sync(self, chat_id: int) -> None:
        if self.is_sync:
            return
        if not self.id:
            self.id = chat_id

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
        App.log = log_it(self.user.id)

    # Отчистка данных
    async def clear_data(self) -> None:
        self.login = None
        self.password = None
        self.email = None

# Логика приложения
class App:
    history: list[State] = []
    bot: Bot = Bot(
        token = Config().BOT_TOKEN, 
        default = DefaultBotProperties(parse_mode = ParseMode.HTML)
    )
    database: Database = Database()
    user: User = User(database)
    subscription: Optional[Subscription]
    log = log_it(user.id)

    # Создание новой пустой подписки
    @staticmethod
    def new_subscription() -> Subscription:
        App.subscription = Subscription(database = App.database)
        return App.subscription

    # Добавление текущей подписки в список подписок пользователя
    @staticmethod
    async def save_subscription() -> None:
        found_subscription = [
            True for sub in App.user.subscriptions 
            if sub.building_id == App.subscription.building_id
        ]
        if not found_subscription:
            await App.subscription.save(App.user.id)
            App.user.subscriptions += [App.subscription]
        App.subscription = None
    
    # Кнопки главного меню
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
    
    # Отчистка истории страниц
    @staticmethod
    async def clear_history(state: FSMContext):
        App.user.password = None
        App.history.clear()
        await state.clear()

    # Добавление нового состояния в историю
    @staticmethod
    async def set_state(page: State, state: FSMContext) -> None:
        if len(App.history) > 0 and App.history[-1] == page:
            return
        App.history.append(page)
        await state.set_state(page)
        # print(f'--History {App.history}--')

    # Откат последнего состояния и возвращение предыдущего
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
    
    # Рассылка клиентам
    @staticmethod
    async def dispatch_to_clients() -> None:
        chats = await App.database.clients_dispatch()
        for chat_id in chats:
            user = User(database = App.database)
            await user.sync(chat_id)

            for subscription in user.subscriptions:
                await subscription.send_info(user.id, is_dispatch = True)