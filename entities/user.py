from typing import Optional, Self
from aiogram import types
import re

from .subscription import Subscription
from repositories import UserRepository
from internal import to_async
from internal.config import Config
from telegrambot.models import TgUser # type: ignore


config = Config()

class User:
    '''Пользователь'''
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
    
    async def set_id(self, id: int) -> bool:
        '''Добавление id'''
        self.id = id
        return True
     
    async def set_phone(self, phone: str) -> bool:
        '''Добавление и валидация номера телефона'''
        try:
            if len(phone) == 11 and phone.startswith('7'):
                phone = f'8{phone[1:]}'
            elif len(phone) == 12 and phone.startswith('+7'):
                phone = f'8{phone[2:]}'

            if len(phone) == 11:
                self.phone = phone
                return True
            else:
                return False
        except Exception as ex:
            return False

    async def set_login(self, login: str) -> bool:
        '''Добавление логина'''
        if len(login) > 5 and len(login) < 16 and re.match(r'^[a-zA-Z0-9_]*$', login):
            self.login = login
            return True
        else:
            return False
        
    async def set_password(self, password: str) -> bool:
        '''Добавление и валидация пароля'''
        if len(password) > 7:
            self.password = password
            return True
        else:
            return False
        
    async def set_email(self, email: str) -> bool:
        '''Добавление и валидация email'''
        if re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email):
            self.email = email
            success = await self.user_repository.set_email(self.id, self.email)
            if not success:
                return False
            return True
        else:    
            return False
        
    async def is_exist(self) -> bool:
        '''Проверка существования пользователя'''
        user = await self.user_repository.get_user(chat_id = self.id)
        return True if user else False
        
    async def save(self) -> bool:
        '''Сохранение пользователя'''
        result = await self.user_repository.create_user(self.id, self.login, self.phone, self.email)
        if result:
            self.is_registed = True
            return True
        else:
            return False
        
    async def get(self, chat_id: Optional[int] = None) -> TgUser:
        '''Получение пользователя'''
        if not self.id:
            if chat_id is None:
                raise Exception('User.get() User should be synced or required chat_id parameter')
            self.id = chat_id
        return await self.user_repository.get_user(chat_id = self.id) 
    
    async def sync(self, chat_id: int) -> bool:
        '''Подтягивание данных пользователя'''
        if self.is_sync:
            return True
        
        tg_user = await self.get(chat_id)
        if not tg_user:
            return False

        self.is_registed = True if tg_user.is_registed else False

        if not self.phone:
            self.phone = tg_user.user_profile.tel

        self.login = tg_user.user_profile.user.username
        self.email = tg_user.user_profile.user.email if tg_user.user_profile.user.email else None
        self.subscriptions = [
            Subscription(building_id = str(building.id)) 
            for building in await to_async(tg_user.building.all)()
        ]
        [await x.sync() for x in self.subscriptions]
        self.is_sync = True
        return True
    
    async def new_subscription(self) -> Subscription:
        '''Создание новой пустой подписки'''
        self.added_subscription = Subscription()
        return self.added_subscription

    async def save_subscription(self) -> None:
        '''Добавление текущей подписки в список подписок пользователя'''
        found_subscription = [
            True for sub in self.subscriptions 
            if sub.building_id == self.added_subscription.building_id
        ]
        if not found_subscription:
            await self.added_subscription.save(self.id, self.user_repository)
            self.subscriptions += [self.added_subscription]
        self.added_subscription = None

    async def remove_subscription(self, subscription: Subscription) -> None:
        '''Удаление текущей подписки из списка подписок пользователя'''
        await subscription.remove(self.id, self.user_repository)

    async def form_subscriptions_as_buttons(self) -> list:
        '''Формирование подписок как inline кнопок'''
        return [
            [types.InlineKeyboardButton(text = f'{sub.property_name}, дом {sub.house_num}', callback_data = sub.building_id)]
            for sub in self.subscriptions
        ]