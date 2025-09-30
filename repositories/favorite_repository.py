from django.contrib.auth.models import User

from internal import to_async, Config
from cabinet.models import FavoritesFlats, FavoritesCommercial, UserSubscription
from property.models import Flats
from property.templatetags.view_price import price


# Слой доступа к данным для взаимодействия с базой данными
config = Config()


class FavoriteRepository:

    async def get_favorites_by_user(self, user: User) -> list[dict]:
        '''Сбор обновлений по квартирам и коммерции в ЛК пользователя'''
        news = []

        flats = await to_async(FavoritesFlats.objects.filter(user = user).all)()
        for fav_flat in flats:
            flat = fav_flat.property_pk

            # print(f'{flat.fk_building.fk_property.name} №{flat.fk_building.num_dom} has last price={flat.price} and new price={flat.property_pk.price_history.first().current_price}')
            if (not fav_flat.price) or (not flat.price_history.first()):
                continue

            if fav_flat.price != flat.price_history.first().current_price:
                flat_number = flat.fl_num or '-'
                floor = flat.floor
                flat_type = next(x[1] for x in Flats.FLAT_CHOICES if x[0] == flat.fl_type)
                zhk_name = flat.fk_property.name
                current_price = flat.price_history.first().current_price
                text = (
                    f'{ flat_type }, №{ flat_number }, на { floor }-м этаже в ЖК { zhk_name }\n'
                    f'Цена при добавлении в избранное: { price(str(fav_flat.price)) } руб.\n'
                    f'Текущая стоимость: { price(str(current_price)) } руб.'
                )
                news.append({
                    'id': f'flat_{ fav_flat.id }', 
                    'text': text
                })

        commercials = await to_async(FavoritesCommercial.objects.filter(user = user).all)()
        for fav_commercial in commercials:
            commercial = fav_commercial.commercial_pk
            if (not fav_commercial.price) or (not commercial.commercial_history.first()):
                continue

            if fav_commercial.price != commercial.commercial_history.first().current_price:
                current_price = commercial.commercial_history.first().current_price
                zhk_name = commercial.fk_property.name
                square = commercial.commercial_sq
                text = (
                    f'Коммерция в ЖК { zhk_name }, площадь { square }м2.\n'
                    f'Цена при добавлении в избранное: { price(str(fav_commercial.price)) } руб.\n'
                    f'Текущая стоимость: { price(str(current_price)) } руб.'
                )
                news.append({
                    'id': f'com_{ fav_commercial.id }',
                    'text': text
                })
        return news

    async def get_all_favorites(self) -> list[UserSubscription]:
        return await to_async(UserSubscription.objects.filter(
            subscription_type = 'favorites', 
            telegram_subscription = True
        ).all)()

    async def remove_user_favorites_flat(self, obj_id: str) -> None:
        fav = await to_async(FavoritesFlats.objects.filter(pk=obj_id).first)()
        if fav:
            await fav.adelete()

    async def remove_user_favorites_commercial(self, obj_id: str) -> None:
        fav = await to_async(FavoritesCommercial.objects.filter(pk=obj_id).first)()
        if fav:
            await fav.adelete()