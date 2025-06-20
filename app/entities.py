from dataclasses import dataclass
from typing import Optional, Self
import re, datetime, logging

from aiogram import Bot, types
from aiogram.fsm.state import State
from aiogram.fsm.context import FSMContext
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from asgiref.sync import sync_to_async

from .repository import SubscriptionRepository, PhotoRepository, UserRepository
from .utils import Markup, Tempfile
from . import text
from config import Config


config = Config()

# Подписка
@dataclass
class Subscription:
    def __init__(self,
        city_id: Optional[str] = None, 
        property_id: Optional[str] = None, 
        building_id: Optional[str] = None
    ) -> Self:
        self.city_id: str = city_id
        self.property_id: str = property_id
        self.building_id: str = building_id
        self.url: Optional[str] = None
        self.photo_url: Optional[str] = None
        self.send_keys: str = 'Неизвестно'
        self.property_name: Optional[str] = None
        self.house_num: Optional[str] = None
        self.photos: list[tuple[int, str, str]] = []
        self.stage: Optional[str] = None
        self.date_release: Optional[str] = None
        self.date_info: Optional[str] = None
        self.subscription_repository: SubscriptionRepository = SubscriptionRepository()
        self.photo_repository: PhotoRepository = PhotoRepository()

    def __eq__(self, other: 'Subscription') -> bool:
        if not isinstance(other, Subscription):
            raise TypeError('Вы сравниваете не с подпиской')
        return self.building_id == other.building_id

    def __repr__(self) -> str:
        return f'\nSubscription(\n\tname = {self.property_name}, \n\thouse_number = {self.house_num}\n\tcity = {self.city_id}, \n\tproperty = {self.property_id}, \n\tbuilding = {self.building_id}\n)\n'
        
    # Добавление информации
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
    
    # Сохранение подписки
    async def save(self, chat_id: str, user_repository: UserRepository) -> None:
        await self.sync()
        await user_repository.save_subscription(chat_id, self.building_id)

    # Удаление подписки
    async def remove(self, chat_id: str, user_repository: UserRepository) -> None:
        await user_repository.remove_subscription(chat_id, self.building_id)

    # Подтягивание всех данных из базы данных
    async def sync(self) -> bool:
        if not self.building_id:
            return False
        data = await self.subscription_repository.get_subscription_data(self.building_id)
        self.url = data['url']
        self.photo_url = data['photo_url']
        self.property_name = data['property_name']
        self.house_num = data['house_number']
        self.photos = data['photos']
        self.stage = data['stage']
        self.date_release = data['date_release']
        self.date_info = data['date_info']
        return True
    
    # Формирование и отправка сообщения ежедневной подписки
    async def send_info(self, chat_id: int, is_dispatch: bool = False) -> None:
        await self.sync()

        photo_ids = [id for id, _, _ in self.photos]
        if is_dispatch:
            unseen_photos = await self.photo_repository.filter_unseen_photos(chat_id, self.building_id, photo_ids) 
            [await self.photo_repository.make_photo_seen(chat_id, self.building_id, photo_id) for photo_id in photo_ids]
        else:
            unseen_photos = photo_ids

        photos_to_show = [photo for photo in self.photos if photo[0] in unseen_photos]   

        if len(photos_to_show) > 0:
            answer = (
                f'{self.property_name}, дом {self.house_num}'
                f'\n<a href="{self.url}">Сайт ЖК</a>'
                f'\nСтадия строительства: {self.stage}'
                f'\nСдача дома: {self.date_release}'
                f'\nПеренос сроков: {self.date_info}'
                f'\nВсе фото и видео по <b><a href="{self.photo_url}">ссылке</a></b>'
            )
            if config.DEBUG:
                answer += f'\nСсылка на фото: {[photo[1] for photo in photos_to_show]}'
                    
            await App.bot.send_message(
                chat_id, 
                answer, 
                reply_markup = App.menu() if is_dispatch else Markup.bottom_buttons([ [types.KeyboardButton(text = text.Btn.BACK.value)] ])
            )
            exception = None
            try:
                for id, url, month in photos_to_show:
                    photo = types.InputMediaPhoto(
                        media = url,
                        caption = month
                    )
                    await App.bot.send_media_group(chat_id, [photo])
            except Exception as ex:
                exception = ex
                try:
                    for id, url, month in photos_to_show: 
                        ext = url.split('.')[-1]
                        async with Tempfile(f'{id}.{ext}', url) as tempfile:
                            photo = types.InputMediaPhoto(
                                media = types.FSInputFile(tempfile),
                                caption = month
                            )
                            await App.bot.send_media_group(chat_id, [photo])
                except Exception as ex:
                    logging.error(f"Couldn't send photo. Error 1:\n{exception}\nError 2:\n{ex}")

# Пользователь
class User:
    def __init__(self, user_repository: UserRepository) -> Self:
        self.user_repository = user_repository
        self.id: Optional[int] = None
        self.phone: Optional[str] = None
        self.is_registed: bool = False
        self.is_sync: bool = False
        self.login: Optional[str] = None
        self.password: Optional[str] = None
        self.email: Optional[str] = None
        self.archive: list[str, str, str] = []
        self.subscriptions: list[Subscription] = []
        self.added_subscription: Optional[Subscription] = None

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
        try:
            phone = msg.contact.phone_number.strip().replace(' ', '').replace('-', '')
            if len(phone) == 11 and phone.startswith('7'):
                phone = f'8{phone[1:]}'
            elif len(phone) == 12 and phone.startswith('+7'):
                phone = f'8{phone[2:]}'

            if len(phone) == 11:
                self.id = msg.chat.id
                self.phone = phone
                return True
            else:
                return False
        except Exception as ex:
            return False
        
    # Добавление и валидация логина
    async def set_login(self, msg: types.Message) -> bool:
        login = msg.text.strip()
        await msg.delete()
        if len(login) > 5 and len(login) < 16 and re.match(r'^[a-zA-Z0-9_]*$', login):
            self.login = login
            return True
        else:
            return False
        
    async def is_valid_login(self) -> bool:
        if not self.login:
            raise ValueError('У пользователя еще нет логина')
        return await self.user_repository.is_user_valid(self.login)
        
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
        if re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email):
            self.email = email
            await msg.answer(f' EMAIL: {email} '.center(40, '-'))
            return True
        else:
            await msg.answer(text.email_tip)      
            return False
        
    # Сохранение в базе временного и постоянного пользователя
    async def save(self, temporary: bool = False) -> Optional[str]:
        if temporary:
            if not await self.user_repository.has_temp_user(self.id):
                await self.user_repository.create_temp_user(self.id, self.phone)
        else:
            is_valid = await self.user_repository.is_user_valid(self.login)
            if is_valid:
                await self.user_repository.create_user(self.id, self.login, self.password, self.email)
                self.is_registed = True
            else:
                return text.Error.user_exists.value
    
    # Подтягивание данных пользователя
    async def sync(self, chat_id: int) -> bool:
        if self.is_sync:
            return True
        if not self.id:
            self.id = chat_id
            
        tg_user = await self.user_repository.get_user(self.id) 
        if not tg_user:
            return False
        
        self.is_registed = True if tg_user.is_registed else False
        if not self.phone:
            self.phone = tg_user.user_profile.tel

        self.login = tg_user.user_profile.user.username
        self.email = tg_user.user_profile.user.email if tg_user.user_profile.user.email else None
        self.subscriptions = [
            Subscription(building_id = str(building.id)) 
            for building in await sync_to_async(tg_user.building.all)()
        ]
        [await x.sync() for x in self.subscriptions]
        [x.photos for x in self.subscriptions]
        self.is_sync = True
        return True
    
    # Создание новой пустой подписки
    async def new_subscription(self) -> Subscription:
        self.added_subscription = Subscription()
        return self.added_subscription

    # Добавление текущей подписки в список подписок пользователя
    async def save_subscription(self) -> None:
        found_subscription = [
            True for sub in self.subscriptions 
            if sub.building_id == self.added_subscription.building_id
        ]
        if not found_subscription:
            await self.added_subscription.save(self.id, self.user_repository)
            self.subscriptions += [self.added_subscription]
        self.added_subscription = None
    
    # Сохранение данных пользователя перед редактированием профиля
    async def push_to_archive(self) -> None:
        self.archive = [self.login, self.password, self.email]

    # Если в архиве есть данные пользователя и редактирование прервалось, возвращаем данные из архива
    async def pop_from_archive(self) -> None:
        if len(self.archive) > 0:
            self.login = self.archive[0]
            self.password = self.archive[1]
            self.email = self.archive[2]
            self.archive.clear()

    # Отчистка данных
    async def clear_data(self) -> None:
        self.password = None

    # Формирование подписок как inline кнопок
    async def form_subscriptions_as_buttons(self) -> list:
        return [
            [types.InlineKeyboardButton(text = f'{sub.property_name}, дом {sub.house_num}', callback_data = sub.building_id)]
            for sub in self.subscriptions
        ]
    

# Логика приложения
class App:
    bot: Bot = None

    def __init__(self, state: Optional[FSMContext] = None) -> Self:
        if not App.bot:
            App.bot: Bot = Bot(
                token = config.BOT_TOKEN, 
                default = DefaultBotProperties(parse_mode = ParseMode.HTML)
            )
        self.history: list[State] = []
        self.user: User = User(UserRepository())
        self.instance: Optional[Self] = None
        self.state = state

    async def __aenter__(self) -> Self:
        self.instance = await App.new(self.state)
        return self.instance
    
    async def __aexit__(self, exc_type, exc, tb) -> None:
        await self.instance.save(self.state)
        
    # Получение экземпляра App пользователя
    @staticmethod
    async def new(state: FSMContext) -> Self:
        data = await state.get_data()
        app = data.get('app')
        if not app:
            app = App()
            await app.save(state)
        return app
    
    # Сохранение экземпляра App пользователя
    async def save(self, state: FSMContext) -> None:
        await state.update_data(app = self)

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
    async def clear_history(self, state: FSMContext, with_user: bool = False):
        if with_user:
            self.user = User(UserRepository())
        self.history.clear()
        await state.clear()

    # Добавление нового состояния в историю
    async def set_state(self, page: State, state: FSMContext) -> None:
        if len(self.history) > 0 and self.history[-1] == page:
            return
        self.history.append(page)
        await state.set_state(page)
        # print(f'--History {self.history}--')

    # Откат последнего состояния и возвращение предыдущего
    async def go_back(self, state: FSMContext) -> State:
        if len(self.history) > 0:
            self.history.pop()  # Шаг назад

        page = None
        if len(self.history) > 0:
            page = self.history[-1] # Получение предыдущего состояния
            await state.set_state(page)
            self.history.pop() # Удаляем и предыдущего состояние, поскольку оно добавится в следующем обработчике
        return page
    
    # Рассылка клиентам
    async def dispatch_to_clients(self) -> None:
        logging.info(f'{datetime.datetime.now()} DISPATCHING')
        user_repository = UserRepository()
        chats = await user_repository.clients_dispatch()
        async for chat_id in chats:
            user = User(user_repository)
            await user.sync(chat_id)

            for subscription in user.subscriptions:
                await subscription.send_info(user.id, is_dispatch = True)