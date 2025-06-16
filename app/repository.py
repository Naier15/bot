from typing import Optional
import secrets, string

from config import Config
config = Config()
from .utils import connect_django
connect_django(config.DJANGO_PATH)

from django.db.models import Q
from asgiref.sync import sync_to_async
from django.contrib.auth.models import User as DjUser
from authapp.models import UserProfile
from property.models import City, Property, Buildings, CheckTermsPassKeys, BuildingPhotos
from telegrambot.models import TgUser, SeenPhoto
from cabinet.models import FavoritesFlats, FavoritesCommercial, UserSubscription
from property.templatetags.view_price import price


# Слой доступа к данным для взаимодействия с базой данными

class CityRepository:
    # Получение городов
    async def get(self) -> list[dict]:
        cities = []
        async for x in City.objects.filter(event = False).order_by('city_name'):
            cities.append({
                'id': str(x.id),
                'name': x.city_name,
                'url': f'{config.DJANGO_HOST}/property/{x.city_slug}/'
            })
        return cities
    
class PropertyRepository:
    # Получение ЖК по городу
    async def get(self, city_id: str) -> list:
        properties = []
        async for x in Property.objects.filter(city_id = int(city_id)).order_by('name'):
            properties.append({
                'id': str(x.id),
                'name': x.name
            })
        return properties
    
class BuildingRepository:
    # Получение зданий по ЖК
    async def get(self, property_id: str) -> list:
        buildings = []
        async for x in Buildings.objects.filter(fk_property = int(property_id)).order_by('num_dom'):
            buildings.append({
                'id': str(x.id),
                'name': x.num_dom
            })
        return buildings
    
class SubscriptionRepository:
    # Данные по подписке на здание
    async def get_subscription_data(self, building_id: str) -> dict:
        building = await Buildings.objects.aget(id = int(building_id))
        property_id = building.fk_property.pk
        property_name = building.fk_property.name
        slug = building.fk_property.slug
        city = building.fk_property.city.city_slug
        pass_keys = await sync_to_async(CheckTermsPassKeys.objects.filter(fk_object = building).first)()
        last_photos = [ 
            await sync_to_async(
                BuildingPhotos.objects.filter(Q(fk_month__fk_building = building) & Q(build_img__isnull = False))
                    .order_by('-fk_month__build_date')
                    .first)() 
        ] 
        photos = [ 
            (photo.id, f'{config.DJANGO_HOST}{photo.build_img.url}', photo.fk_month.build_month) 
            for photo in last_photos 
        ]

        stage = building.build_stage
        if stage == 'b':
            stage = 'Строится'
        elif stage == 'p':
            stage = 'Сдан'
        elif stage == 'd':
            stage = 'Долгострой'

        if pass_keys:
            date_release = pass_keys.changed_date
            date_info = pass_keys.note
        elif building.operation_term:
            date_release = building.operation_term
            date_info = 'Без изменений'
        else:
            date_release = 'Не указано'
            date_info = 'Не указано'
        
        return {
            'id': building_id,
            'property_name': property_name,
            'house_number': building.num_dom,
            'url': f'{config.DJANGO_HOST}/property/{city}/{property_id}/{slug}/',
            'photo_url': f'{config.DJANGO_HOST}/property/{city}/{property_id}/{slug}/#building_photo',
            'photos': photos,
            'stage': stage,
            'date_release': date_release,
            'date_info': date_info
        }
    
class PhotoRepository:
    # Отметить, что фото было уже просмотрено в ежедневной рассылке
    async def make_photo_seen(self, chat_id: str, building_id: int, photo_id: int) -> None:
        building = await Buildings.objects.aget(id = building_id)
        photo = await BuildingPhotos.objects.aget(id = photo_id)
        seen_photo = await SeenPhoto.objects.acreate(photo = photo, building = building)
        tg_user = await self.get_user(chat_id)
        await tg_user.seen_photos.aadd(seen_photo)

    # Отфильтровать еще не просмотренные фото
    async def filter_unseen_photos(self, chat_id: str, building_id: str, photos: list[int]) -> list[str]:
        tg_user = await self.get_user(chat_id)
        seen_photos = tg_user.seen_photos.filter(Q(building__id = building_id) & Q(photo__id__in = photos))
        for photo in seen_photos:
            while photo.photo.id in photos:
                photos.remove(photo.photo.id)
        return photos
    
class UserRepository:
    # Получить временную запись пользователя
    async def has_temp_user(self, chat_id: str) -> bool:
        try:
            tg_user = await self.get_user(chat_id)
            return True if tg_user else False
        except TgUser.DoesNotExist:
            return False
        
    # Создать временного пользователя, чтобы связать с UserProfile
    async def create_temp_user(self, chat_id: str, phone_number: str) -> None:
        alphabet = string.ascii_letters + string.digits
        temp_login = 'temp_' + ''.join(secrets.choice(alphabet) for _ in range(16))
        user = await sync_to_async(DjUser.objects.create_user)(
            username = temp_login,
            password = temp_login
        )
        try:
            profile = await UserProfile.objects.acreate(tel=phone_number, user=user)
            await TgUser.objects.acreate(chat_id=chat_id, user_profile=profile)
        except Exception:
            profile = await sync_to_async(UserProfile.objects.filter(tel=phone_number).first)()
            if profile:
                tg_user = await sync_to_async(TgUser.objects.filter(user_profile=profile).first)()
                if not tg_user:
                    await TgUser.objects.acreate(chat_id=chat_id, user_profile=profile)


    # Проверка, что сможем добавить нового пользователя
    async def is_user_valid(self, username: str) -> bool:
        users = await sync_to_async(DjUser.objects.filter(username = username).all)()
        if len(users) > 0:
            return False
        return True
        
    # Создание постоянного пользователя
    async def create_user(self, chat_id: str, login: str, password: str, email: Optional[str]) -> None:
        tg_user = await self.get_user(chat_id)
        tg_user.user_profile.user.username = login
        tg_user.is_registed = True
        if email:
            tg_user.user_profile.user.email = email
        tg_user.user_profile.user.set_password(password)
        await tg_user.user_profile.user.asave()
        await tg_user.asave()
    
    # Получение постоянного пользователя
    async def get_user(self, chat_id: str) -> Optional[TgUser]:
        try:
            return await TgUser.objects.aget(chat_id = chat_id)
        except TgUser.DoesNotExist:
            return None

    # Сохранить подписку пользователя
    async def save_subscription(self, chat_id: str, building_id: str) -> None:
        tg_user = await self.get_user(chat_id)
        if not tg_user:
            return
        building = await Buildings.objects.aget(id = building_id)
        if await tg_user.building.acontains(building):
            return
        await tg_user.building.aadd(building)
        await tg_user.asave()

    # Удалить подписку у пользователя
    async def remove_subscription(self, chat_id: str, building_id: str) -> None:
        tg_user = await self.get_user(chat_id)
        if not tg_user:
            return
        building = await Buildings.objects.aget(id = building_id)
        if not await tg_user.building.acontains(building):
            return
        await tg_user.building.aremove(building)
        await tg_user.asave()
        
    # Ежедневная рассылка пользователям новостей
    async def clients_dispatch(self) -> list[int]:
        return await sync_to_async(TgUser.objects.values_list)('chat_id', flat = True)

    # Избранное квартир и коммерции в ЛК
    async def get_favorites_obj(self, subscr_user) -> list[str]:
        fav_flats = await sync_to_async(FavoritesFlats.objects.filter(user=subscr_user).all)()
        text_list = []
        for fav_flat in fav_flats:
            if fav_flat.price and fav_flat.property_pk.price_history.first():
                if fav_flat.price != fav_flat.property_pk.price_history.first().current_price:
                    fl: str
                    if fav_flat.property_pk.fl_type == '0':
                        fl = 'Студия'
                    elif fav_flat.property_pk.fl_type == '1':
                        fl = '1-комн. кв.'
                    elif fav_flat.property_pk.fl_type == '2':
                        fl = '2-комн. кв.'
                    elif fav_flat.property_pk.fl_type == '3':
                        fl = '3-комн. кв.'
                    elif fav_flat.property_pk.fl_type == '4':
                        fl = '4-комн. кв.'
                    elif fav_flat.property_pk.fl_type == '5':
                        fl = '5-комн. кв.'
                    elif fav_flat.property_pk.fl_type == '6':
                        fl = '6-комн. кв.'
                    elif fav_flat.property_pk.fl_type == '7':
                        fl = '7-комн. кв.'
                    elif fav_flat.property_pk.fl_type == '8':
                        fl = '8-комн. кв.'
                    if fav_flat.property_pk.fl_num:
                        num_fl = fav_flat.property_pk.fl_num
                    else:
                        num_fl = '-'
                    floor = fav_flat.property_pk.floor
                    zhk = fav_flat.property_pk.fk_property.name
                    cur_price = fav_flat.property_pk.price_history.first().current_price
                    text = (f'{fl}, №{num_fl}, на {floor}-м этаже в ЖК {zhk}\nЦена при добавлении в избранное: '
                            f'{price(str(fav_flat.price))} руб.\nТекущая стоимость: {price(str(cur_price))} руб.')

                    text_list.append({'id': f'flat_{fav_flat.id}', 'text':text})

        fav_commercial = await sync_to_async(FavoritesCommercial.objects.filter(user=subscr_user).all)()
        for fav_com in fav_commercial:
            if fav_com.price and fav_com.commercial_pk.commercial_history.first():
                if fav_com.price != fav_com.commercial_pk.commercial_history.first().current_price:
                    cur_price = fav_com.commercial_pk.commercial_history.first().current_price
                    zhk = fav_com.commercial_pk.fk_property.name
                    sq = fav_com.commercial_pk.commercial_sq
                    text = (f'Коммерция в ЖК {zhk}, площадь {sq}м2.\nЦена при добавлении в избранное: {price(str(fav_com.price))} '
                            f'руб.\nТекущая стоимость: {price(str(cur_price))} руб.')
                    text_list.append({'id': f'com_{fav_com.id}','text': text})
        return text_list


async def get_favorites_subscr():
    subscribers = await sync_to_async(UserSubscription.objects.filter(subscription_type='favorites', telegram_subscription=True).all)()
    return subscribers

async def remove_user_favorites_flat(obj_id: str) -> None:
    fav = await sync_to_async(FavoritesFlats.objects.filter(pk=obj_id).first)()
    if fav:
        await fav.adelete()

async def remove_user_favorites_commercial(obj_id: str) -> None:
    fav = await sync_to_async(FavoritesCommercial.objects.filter(pk=obj_id).first)()
    if fav:
        await fav.adelete()
