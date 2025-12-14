from django.db.models import Q

from internal import to_async
from internal.config import Config
from property.models import Buildings, CheckTermsPassKeys, BuildingPhotos


config = Config()

class SubscriptionRepository:
    async def get(self, building_id: str) -> dict:
        '''Данные по подписке на здание'''
        building = await to_async(
            Buildings.objects.select_related('fk_property', 'fk_property__city')
            .filter(id = int(building_id))
            .values(
                'id',
                'fk_property__pk',
                'fk_property__name',
                'fk_property__slug',
                'fk_property__city__city_name',
                'build_stage',
                'operation_term',
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
                BuildingPhotos.objects.select_related('fk_month')
                    .filter(Q(fk_month__fk_building = building['id']) & Q(build_img__isnull = False))
                    .order_by('-fk_month__build_date')
                    .values(
                        'id',
                        'build_img',
                        'fk_month__build_month'
                    )
                    .first
            )()
        ]
        photos = [ 
            (photo['id'], f'{config.DJANGO_HOST}/{photo['build_img']}', photo['fk_month__build_month']) 
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