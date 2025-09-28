from property.models import Property  # type: ignore


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