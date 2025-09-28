from typing import Optional
from django.contrib.auth.models import User as DjUser
from django.db import transaction
import secrets

from internal import to_async
from authapp.models import UserProfile  # type: ignore
from property.models import Buildings  # type: ignore
from telegrambot.models import TgUser  # type: ignore


class UserRepository:

    async def create_user(self, chat_id: str, login: str, phone_number: str, email: Optional[str] = None) -> bool:
        '''Создать пользователя'''
        async with transaction.atomic():
            user = await to_async(DjUser.objects.create_user)(
                username = login,
                password = secrets.token_urlsafe(16),
                email = email
            )
            profile = await UserProfile.objects.acreate(
                tel = phone_number, 
                user = user
            )
            await TgUser.objects.acreate(
                chat_id = chat_id, 
                user_profile = profile,
                is_registed = True
            )
            return True
        return False

    async def set_email(self, chat_id: str, email: str) -> bool:
        '''Добавление email'''
        user = await self.get_user(chat_id = chat_id)
        if not user:
            return False
        await DjUser.objects.filter(id = user.user_profile.user.id).aupdate(email = email)
        return True
    
    async def get_user(self, chat_id: Optional[int] = None, name: Optional[str] = None) -> Optional[TgUser]:
        '''Получение пользователя'''
        if (chat_id is not None and name is not None) or (chat_id is None and name is None):
            raise ValueError('UserRepository.get_user() requires exactly one parameter: chat_id or name')
        try:
            qs = await to_async(TgUser.objects.select_related)('user_profile__user')
            if chat_id:
                return await qs.aget(chat_id = chat_id)
            return await qs.aget(user_profile__user__username = name)
        except TgUser.DoesNotExist:
            return None

    async def save_subscription(self, chat_id: str, building_id: str) -> None:
        '''Сохранить подписку пользователя'''
        tg_user = await self.get_user(chat_id = chat_id)
        if not tg_user:
            return
        building = await Buildings.objects.aget(id = building_id)
        if not await tg_user.building.acontains(building):
            await tg_user.building.aadd(building)

    async def remove_subscription(self, chat_id: int, building_id: str) -> None:
        '''Удалить подписку у пользователя'''
        tg_user = await self.get_user(chat_id = chat_id)
        if not tg_user:
            return
        building = await Buildings.objects.aget(id = building_id)
        if await tg_user.building.acontains(building):
            await tg_user.building.aremove(building)
        
        
    async def get_dispatch_list(self) -> list[int]:
        '''Получить список пользователей для ежедневной рассылки новостей'''
        return await to_async(TgUser.objects.values_list)('chat_id', flat = True)