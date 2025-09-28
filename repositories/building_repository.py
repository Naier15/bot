from property.models import Buildings  # type: ignore


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