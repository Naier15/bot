from typing import Optional
import secrets, string

from .utils import connect_django, to_async, log
from config import Config
config = Config()
connect_django(config.DJANGO_PATH)
from authapp.models import UserProfile
from property.models import City, Property, Buildings, CheckTermsPassKeys, BuildingPhotos
from telegrambot.models import TgUser, SeenPhoto
from cabinet.models import FavoritesFlats, FavoritesCommercial, UserSubscription
from property.templatetags.view_price import price

from django.db.models import Q
from django.contrib.auth.models import User as DjUser
from django.db import transaction


# Слой доступа к данным для взаимодействия с базой данными

class CityRepository:
    async def get(self) -> list[dict]:
        '''Получение городов'''
        cities = []
        async for x in City.objects.filter(event = False) \
                .values('id', 'city_name', 'city_slug') \
                .order_by('city_name'):
            cities.append({
                'id': str(x['id']),
                'name': x['city_name'],
                'url': f'{config.DJANGO_HOST}/property/{x['city_slug']}/'
            })
        return cities
    
class PropertyRepository:
    async def get(self, city_id: str) -> list:
        '''Получение ЖК по городу'''
        properties = []
        async for x in Property.objects.filter(city_id = int(city_id)) \
                .values('id', 'name') \
                .order_by('name'):
            x['id'] = str(x['id'])
            properties.append(x)
        return properties
    
class BuildingRepository:
    async def get(self, property_id: str) -> list:
        '''Получение зданий по ЖК'''
        buildings = []
        async for x in Buildings.objects.filter(fk_property = int(property_id)) \
                .values('id', 'num_dom') \
                .order_by('num_dom'):
            buildings.append({
                'id': str(x['id']),
                'name': x['num_dom']
            })
        return buildings
    
class SubscriptionRepository:
    async def get(self, building_id: str) -> dict:
        '''Данные по подписке на здание'''
        building = await to_async(
            Buildings.objects.select_related('fk_property', 'fk_property__city') \
            .filter(id = int(building_id))\
            .values(
                'id',
                'fk_property__pk', \
                'fk_property__name', \
                'fk_property__slug', \
                'fk_property__city__city_name', \
                'build_stage', \
                'operation_term', \
                'num_dom'
            ).first
        )()
        property_id = building['fk_property__pk']
        property_name = building['fk_property__name']
        slug = building['fk_property__slug']
        city = building['fk_property__city__city_name']
        pass_keys = await to_async(CheckTermsPassKeys.objects.filter(fk_object = building['id']).first)()
        last_photos = [ 
            await to_async(
                BuildingPhotos.objects.select_related('fk_month') \
                    .filter(Q(fk_month__fk_building = building['id']) & Q(build_img__isnull = False))
                    .order_by('-fk_month__build_date')
                    .first
            )()
        ] 
        photos = [ 
            (photo.id, f'{config.DJANGO_HOST}{photo.build_img.url}', photo.fk_month.build_month) 
            for photo in last_photos 
        ]

        stage = building['build_stage']
        if stage == 'b':
            stage = 'Строится'
        elif stage == 'p':
            stage = 'Сдан'
        elif stage == 'd':
            stage = 'Долгострой'

        if pass_keys:
            date_release = pass_keys.changed_date
            date_info = pass_keys.note
        elif building['operation_term']:
            date_release = building['operation_term']
            date_info = 'Без изменений'
        else:
            date_release = 'Не указано'
            date_info = 'Не указано'
        
        return {
            'id': building_id,
            'property_name': property_name,
            'house_number': building['num_dom'],
            'url': f'{config.DJANGO_HOST}/property/{city}/{property_id}/{slug}/',
            'photo_url': f'{config.DJANGO_HOST}/property/{city}/{property_id}/{slug}/#building_photo',
            'photos': photos,
            'stage': stage,
            'date_release': date_release,
            'date_info': date_info
        }
    
class PhotoRepository:
    async def make_photo_seen(self, user: TgUser, building_id: int, photo_id: int) -> None:
        '''Отметить, что фото было уже просмотрено в ежедневной рассылке'''
        building = await Buildings.objects.aget(id = building_id)
        photo = await BuildingPhotos.objects.aget(id = photo_id)
        seen_photo = await SeenPhoto.objects.acreate(photo = photo, building = building)
        await user.seen_photos.aadd(seen_photo)

    async def filter_unseen_photos(self, user: TgUser, building_id: str, photos: list[int]) -> list[str]:
        '''Отфильтровать еще не просмотренные фото'''
        seen_photos = user.seen_photos.filter(Q(building__id = building_id) & Q(photo__id__in = photos))
        for photo in seen_photos:
            while photo.photo.id in photos:
                photos.remove(photo.photo.id)
        return photos
    
class UserRepository:

    async def create_user(self, chat_id: str, login: str, phone_number: str, email: Optional[str] = None) -> bool:
        '''Создать пользователя'''
        with transaction.atomic():
            alphabet = string.ascii_letters + string.digits
            password = ''.join(secrets.choice(alphabet) for _ in range(16))
            user = await to_async(DjUser.objects.create_user)(
                username = login,
                password = password,
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
    
    async def get_user(self, chat_id: Optional[str] = None, name: Optional[str] = None) -> Optional[TgUser]:
        '''Получение пользователя'''
        if (chat_id is not None and name is not None) or (chat_id is None and name is None):
            raise Exception('UserRepository.get_user() requires one parameter at least')
        try:
            if chat_id is not None:
                return await TgUser.objects.select_related('user_profile__user').aget(chat_id = chat_id)
            elif name is not None:
                return await TgUser.objects.select_related('user_profile__user').aget(
                    user_profile__user__username = name
                )
        except TgUser.DoesNotExist:
            return None

    async def save_subscription(self, chat_id: str, building_id: str) -> None:
        '''Сохранить подписку пользователя'''
        tg_user = await self.get_user(chat_id = chat_id)
        if not tg_user:
            return
        building = await Buildings.objects.aget(id = building_id)
        if await tg_user.building.acontains(building):
            return
        await tg_user.building.aadd(building)
        await tg_user.asave()

    async def remove_subscription(self, chat_id: str, building_id: str) -> None:
        '''Удалить подписку у пользователя'''
        tg_user = await self.get_user(chat_id = chat_id)
        if not tg_user:
            return
        building = await Buildings.objects.aget(id = building_id)
        if not await tg_user.building.acontains(building):
            return
        await tg_user.building.aremove(building)
        await tg_user.asave()
        
    async def get_dispatch_list(self) -> list[int]:
        '''Получить список пользователей для ежедневной рассылки новостей'''
        return await to_async(TgUser.objects.values_list)('chat_id', flat = True)

    async def get_favorites_obj(self, subscr_user) -> list[str]:
        '''Избранное квартир и коммерции в ЛК'''
        fav_flats = await to_async(FavoritesFlats.objects.filter(user=subscr_user).all)()
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

        fav_commercial = await to_async(FavoritesCommercial.objects.filter(user=subscr_user).all)()
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
    subscribers = await to_async(UserSubscription.objects.filter(subscription_type='favorites', telegram_subscription=True).all)()
    return subscribers

async def remove_user_favorites_flat(obj_id: str) -> None:
    fav = await to_async(FavoritesFlats.objects.filter(pk=obj_id).first)()
    if fav:
        await fav.adelete()

async def remove_user_favorites_commercial(obj_id: str) -> None:
    fav = await to_async(FavoritesCommercial.objects.filter(pk=obj_id).first)()
    if fav:
        await fav.adelete()
