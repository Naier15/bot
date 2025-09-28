from property.models import City  # type: ignore
from internal.config import Config


config = Config()

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
                'url': f'{config.DJANGO_HOST}/property/{x['city_slug']}/flats/'
            })
        return cities