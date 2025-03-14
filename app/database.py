from typing import Optional
import secrets, string

from config import Config
from .utils import connect_django
connect_django(Config().DJANGO_PATH)

from django.contrib.auth.models import User as DjUser
from authapp.models import UserProfile
from property.models import City, Property, Buildings, CheckTermsPassKeys, BuildMonths, BuildingPhotos
from bot.models import TgUser, SeenPhoto


# Все запросы к базе данных
class Database:
    # Получение городов
    async def get_cities(self) -> list[dict]:
        cities = []
        async for x in City.objects.filter(event = False).order_by('city_name'):
            cities.append({
                'id': str(x.id),
                'name': x.city_name,
                'url': f'{Config().DJANGO_HOST}property/{x.city_slug}/'
            })
        return cities

    # Получение ЖК по городу
    async def get_properties(self, city_id: str) -> list:
        properties = []
        async for x in Property.objects.filter(city_id = int(city_id)).order_by('name'):
            properties.append({
                'id': str(x.id),
                'name': x.name
            })
        return properties
    
    # Получение зданий по ЖК
    async def get_buildings(self, property_id: str) -> list:
        buildings = []
        async for x in Buildings.objects.filter(fk_property = int(property_id)).order_by('num_dom'):
            buildings.append({
                'id': str(x.id),
                'name': x.num_dom
            })
        return buildings
    
    # Данные по подписке на здание
    async def get_subscription_data(self, building_id: str) -> dict:
        building = await Buildings.objects.aget(id = int(building_id))
        property_id = building.fk_property.pk
        property_name = building.fk_property.name
        slug = building.fk_property.slug
        city = building.fk_property.city.city_slug
        pass_keys = CheckTermsPassKeys.objects.filter(fk_object = building).first()
        
        last_month = BuildMonths.objects.filter(fk_building = building).order_by('-build_date').first()
        last_photos = [BuildingPhotos.objects.filter(fk_month = last_month).last()]
        photos = [(photo.id, f'{Config().DJANGO_HOST}{photo.build_img.url}', last_month.build_month) for photo in last_photos]

        stage = building.build_stage
        if stage == 'b':
            stage = 'Строится'
        elif stage == 'p':
            stage = 'Сдан'
        elif stage == 'd':
            stage = 'Долгострой'
        
        return {
            'id': building_id,
            'property_name': property_name,
            'house_number': building.num_dom,
            'url': f'{Config().DJANGO_HOST}/property/{city}/{property_id}/{slug}/',
            'photo_url': f'{Config().DJANGO_HOST}/property/{city}/{property_id}/format/#building_photo',
            'photos': photos,
            'stage': stage,
            'date_realise': pass_keys.changed_date if pass_keys else 'Не указано',
            'date_info': pass_keys.note if pass_keys else 'Не указано'
        }
    
    # Отметить, что фото было уже просмотрено в ежедневной рассылке
    async def make_photo_seen(self, chat_id: str, building_id: int, photo_id: int) -> None:
        building = await Buildings.objects.aget(id = building_id)
        photo = await BuildingPhotos.objects.aget(id = photo_id)
        seen_photo = await SeenPhoto.objects.acreate(photo = photo, building = building)
        user = await TgUser.objects.aget(chat_id = chat_id)
        await user.seen_photos.aadd(seen_photo)

    # Отфильтровать еще не просмотренные фото
    async def filter_unseen_photos(self, chat_id: str, building_id: str, photos: list[int]) -> list[str]:
        user = await TgUser.objects.aget(chat_id = chat_id)
        seen_photos = user.seen_photos.filter(building__id = building_id) & user.seen_photos.filter(photo__id__in = photos)
        for photo in seen_photos:
            while photo.photo.id in photos:
                photos.remove(photo.photo.id)
        return photos
    
    # Получить временную запись пользователя
    async def has_temp_user(self, chat_id: str) -> bool:
        try:
            user = await TgUser.objects.aget(chat_id = chat_id)
            return True if user else False
        except TgUser.DoesNotExist:
            return False
        
    # Создать временного пользователя, чтобы связать с UserProfile
    async def create_temp_user(self, chat_id: str, phone_number: str) -> None:
        alphabet = string.ascii_letters + string.digits
        temp_login = 'temp_' + ''.join(secrets.choice(alphabet) for _ in range(16))
        user = DjUser.objects.create_user(
            username = temp_login,
            password = temp_login
        )
        profile = await UserProfile.objects.acreate(tel = phone_number, user = user)
        await TgUser.objects.acreate(chat_id = chat_id, user_profile = profile)

    # Проверка, что сможем добавить нового пользователя
    async def is_user_valid(self, username: str) -> bool:
        users = DjUser.objects.filter(username = username).all()
        if len(users) > 0:
            return False
        return True
        
    # Создание постоянного пользователя
    async def create_user(self, chat_id: str, login: str, password: str, email: Optional[str]) -> None:
        tg_user = await TgUser.objects.aget(chat_id = chat_id)
        tg_user.user_profile.user.username = login
        tg_user.is_registed = True
        if email:
            tg_user.user_profile.user.email = email
        tg_user.user_profile.user.set_password(password)
        await tg_user.user_profile.user.asave()
        await tg_user.asave()
    
    # Получение постоянного пользователя
    async def get_user(self, chat_id: str) -> Optional[TgUser]:
        tg_user = await TgUser.objects.aget(chat_id = chat_id)
        return tg_user
    
    # Сохранить подписку пользователя
    async def save_subscription(self, chat_id: str, building_id: str) -> None:
        tg_user = await TgUser.objects.aget(chat_id = chat_id)
        if not tg_user:
            return
        building = await Buildings.objects.aget(id = building_id)
        if await tg_user.building.acontains(building):
            return
        await tg_user.building.aadd(building)
        await tg_user.asave()

    # Удалить подписку у пользователя
    async def remove_subscription(self, chat_id: str, building_id: str) -> None:
        tg_user = await TgUser.objects.aget(chat_id = chat_id)
        if not tg_user:
            return
        building = await Buildings.objects.aget(id = building_id)
        if not await tg_user.building.acontains(building):
            return
        await tg_user.building.aremove(building)
        await tg_user.asave()
        
    # Ежедневная рассылка пользователям новостей
    async def clients_dispatch(self) -> list[int]:
        users = []
        async for user in TgUser.objects.all():
            users.append(user.chat_id)
        return users