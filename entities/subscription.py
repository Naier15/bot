from dataclasses import dataclass
from typing import Optional, Self

from repositories import SubscriptionRepository, PhotoRepository, UserRepository
from internal.config import Config
from telegrambot.models import TgUser # type: ignore


config = Config()

@dataclass
class Subscription:
    '''Подписка'''
    def __init__(self,
        city_id: Optional[str] = None, 
        property_id: Optional[str] = None, 
        building_id: Optional[str] = None
    ) -> Self:
        self.city_id: str = city_id
        self.property_id: str = property_id
        self.building_id: str = building_id
        self.url: Optional[str] = None
        self.photo_url: Optional[str] = None
        self.send_keys: str = 'Неизвестно'
        self.property_name: Optional[str] = None
        self.house_num: Optional[str] = None
        self.photos: list[tuple[int, str, str]] = []
        self.stage: Optional[str] = None
        self.date_release: Optional[str] = None
        self.date_info: Optional[str] = None
        self.subscription_repository: SubscriptionRepository = SubscriptionRepository()
        self.photo_repository: PhotoRepository = PhotoRepository()

    def __eq__(self, other: 'Subscription') -> bool:
        if not isinstance(other, Subscription):
            raise TypeError('Вы сравниваете не с подпиской')
        return self.building_id == other.building_id

    def __repr__(self) -> str:
        return f'\nSubscription(\n\tname = {self.property_name}, \n\thouse_number = {self.house_num}\n\tcity = {self.city_id}, \n\tproperty = {self.property_id}, \n\tbuilding = {self.building_id}\n)\n'
        
    async def set(self, 
        city_id: Optional[str] = None, 
        property_id: Optional[str] = None, 
        building_id: Optional[str] = None
    ) -> bool:
        '''Добавление информации'''
        if city_id and len(city_id) > 0:
            self.city_id = city_id
            return True
        if property_id and len(property_id) > 0:
            self.property_id = property_id
            return True
        if building_id and len(building_id) > 0:
            self.building_id = building_id
            return True
        return False
    
    async def save(self, chat_id: str, user_repository: UserRepository) -> None:
        '''Сохранение подписки'''
        await self.sync()
        await user_repository.save_subscription(chat_id, self.building_id)

    async def remove(self, chat_id: int, user_repository: UserRepository) -> None:
        '''Удаление подписки'''
        await user_repository.remove_subscription(chat_id, self.building_id)

    async def sync(self) -> bool:
        '''Подтягивание всех данных из базы данных'''
        if not self.building_id:
            return False
        data = await self.subscription_repository.get(self.building_id)
        self.url = data['url']
        self.photo_url = data['photo_url']
        self.property_name = data['property_name']
        self.house_num = data['house_number']
        self.photos = data['photos']
        self.stage = data['stage']
        self.date_release = data['date_release']
        self.date_info = data['date_info']
        return True
    
    async def form_news(self, user: TgUser, is_dispatch: bool = False) -> Optional[tuple[str, list[tuple[int, str, str]]]]:
        '''Формирование и отправка сообщения ежедневной подписки'''
        await self.sync()

        photo_ids = [id for id, _, _ in self.photos]
        if is_dispatch:
            unseen_photos = await self.photo_repository.filter_unseen_photos(user, self.building_id, photo_ids) 
            [await self.photo_repository.make_photo_seen(user, self.building_id, photo_id) for photo_id in photo_ids]
        else:
            unseen_photos = photo_ids

        photos_to_show = [photo for photo in self.photos if photo[0] in unseen_photos]   

        if len(photos_to_show) > 0:
            answer = (
                f'{self.property_name}, дом {self.house_num}'
                f'\n<a href="{self.url}">Сайт ЖК</a>'
                f'\nСтадия строительства: {self.stage}'
                f'\nСдача дома: {self.date_release}'
                f'\nПеренос сроков: {self.date_info}'
                f'\nВсе фото и видео по <b><a href="{self.photo_url}">ссылке</a></b>'
            )
            if config.DEBUG:
                answer += f'\nСсылка на фото: {[photo[1] for photo in photos_to_show]}'
            return (answer, photos_to_show)