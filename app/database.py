from typing import Optional
import secrets, string

from .utils import connect_django
connect_django('..')

from django.contrib.auth.models import User as DjUser
from authapp.models import UserProfile
from property.models import City, Property, Buildings, MainPhotos
from bot.models import TgUser

class Database:

    async def get_cities(self) -> list[dict]:
        cities = []
        async for x in City.objects.all():
            cities.append({
                'id': str(x.id),
                'text': x.city_name
            })
        cities.sort(key = lambda x: x['text'])
        return cities

    async def get_properties(self, city_id: str) -> list:
        properties = []
        async for x in Property.objects.filter(city_id = int(city_id)):
            properties.append({
                'id': str(x.id),
                'text': x.name
            })
        properties.sort(key = lambda x: x['text'])
        return properties
    
    async def get_buildings(self, property_id: str) -> list:
        buildings = []
        async for x in Buildings.objects.filter(fk_property = int(property_id)):
            buildings.append({
                'id': str(x.id),
                'text': x.num_dom
            })
        buildings.sort(key = lambda x: x['text'])
        return buildings
    
    async def get_subscription_data(self, id: str) -> dict:
        building = Buildings.objects.filter(id = int(id)).first()
        property_id = building.fk_property.pk
        property_name = building.fk_property.name
        slug = building.fk_property.slug
        city = building.fk_property.city.city_slug
        photos = MainPhotos.objects.filter(fk_building_id = int(id)).order_by('-id')[:3]
        building = {
            'id': str(building.id),
            'property_name': property_name,
            'url': f'https://bashni.pro/property/{city}/{property_id}/{slug}/',
            'send_keys': building.send_keys.strftime('%d.%m.%Y'),
            'photos': photos
        }
        return building
    
    async def get_temp_user(self, chat_id: str) -> Optional[TgUser]:
        return TgUser.objects.filter(chat_id = chat_id).first()
    
    async def create_temp_user(self, chat_id: str, phone_number: str) -> None:
        alphabet = string.ascii_letters + string.digits
        temp_login = 'temp_' + ''.join(secrets.choice(alphabet) for _ in range(16))
        user = DjUser.objects.create_user(
            username = temp_login,
            password = temp_login
        )
        profile = await UserProfile.objects.acreate(tel = phone_number, user = user)
        await TgUser.objects.acreate(chat_id = chat_id, user_profile = profile)

    async def is_user_valid(self, username: str) -> bool:
        users = DjUser.objects.filter(username = username).all()
        if len(users) > 0:
            return False
        elif len(users) == 0:
            return True
        
    async def create_user(self, chat_id: str, login: str, password: str, email: Optional[str]) -> None:
        tg_user = TgUser.objects.filter(chat_id = chat_id).first()
        tg_user.user_profile.user.username = login
        tg_user.is_registed = True
        if email:
            tg_user.user_profile.user.email = email
        tg_user.user_profile.user.set_password(password)
        await tg_user.user_profile.user.asave()
        await tg_user.asave()
    
    async def get_user(self, chat_id: str) -> Optional[TgUser]:
        tg_user = TgUser.objects.filter(chat_id = chat_id).first()
        return tg_user
    
    async def save_subscription(self, chat_id: str, building_id: str) -> None:
        tg_user = TgUser.objects.filter(chat_id = chat_id).first()
        if not tg_user:
            return
        building = Buildings.objects.filter(id = building_id).first()
        if await tg_user.building.acontains(building):
            return
        await tg_user.building.aadd(building)
        await tg_user.asave()

    async def remove_subscription(self, chat_id: str, building_id: str) -> None:
        tg_user = TgUser.objects.filter(chat_id = chat_id).first()
        if not tg_user:
            return
        building = Buildings.objects.filter(id = building_id).first()
        if not await tg_user.building.acontains(building):
            return
        await tg_user.building.aremove(building)
        await tg_user.asave()
        
    async def clients_dispatch(self) -> list[int]:
        users = []
        async for user in TgUser.objects.all():
            users.append(user.chat_id)
        return users

        