from django.db.models import Q

from property.models import Buildings, BuildingPhotos
from telegrambot.models import TgUser, SeenPhoto


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