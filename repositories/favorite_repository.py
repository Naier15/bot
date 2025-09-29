from internal import to_async
from internal.config import Config
from cabinet.models import FavoritesFlats, FavoritesCommercial, UserSubscription  # type: ignore
from property.templatetags.view_price import price  # type: ignore
from django.contrib.auth.models import User


# Слой доступа к данным для взаимодействия с базой данными
config = Config()


class FavoriteRepository:

    async def get_favorites_by_user(self, user: User) -> list[dict]:
        '''Сбор обновлений по квартирам и коммерции в ЛК пользователя'''
        news = []

        fav_flats = await to_async(FavoritesFlats.objects.filter(user = user).all)()
        for fav_flat in fav_flats:
            # if fav_flat.user.id != 1:
            #     return []
            # print(f'{fav_flat.property_pk.fk_building.fk_property.name} №{fav_flat.property_pk.fk_building.num_dom} has last price={fav_flat.price} and new price={fav_flat.property_pk.price_history.first().current_price}')
            if (not fav_flat.price) or (not fav_flat.property_pk.price_history.first()):
                continue

            if fav_flat.price != fav_flat.property_pk.price_history.first().current_price:
                if fav_flat.property_pk.fl_type == '0':
                    fl = 'Студия'
                elif fav_flat.property_pk.fl_type in '12345678':
                    fl = f'{fav_flat.property_pk.fl_type}-комн. кв.'

                if fav_flat.property_pk.fl_num:
                    num_fl = fav_flat.property_pk.fl_num
                else:
                    num_fl = '-'

                floor = fav_flat.property_pk.floor
                zhk = fav_flat.property_pk.fk_property.name
                cur_price = fav_flat.property_pk.price_history.first().current_price
                text = (
                    f'{fl}, №{num_fl}, на {floor}-м этаже в ЖК {zhk}\n'
                    f'Цена при добавлении в избранное: {price(str(fav_flat.price))} руб.\n'
                    f'Текущая стоимость: {price(str(cur_price))} руб.'
                )
                news.append({
                    'id': f'flat_{fav_flat.id}', 
                    'text': text
                })

        fav_commercial = await to_async(FavoritesCommercial.objects.filter(user = user).all)()
        for fav_com in fav_commercial:
            if (not fav_com.price) or (not fav_com.commercial_pk.commercial_history.first()):
                continue

            if fav_com.price != fav_com.commercial_pk.commercial_history.first().current_price:
                cur_price = fav_com.commercial_pk.commercial_history.first().current_price
                zhk = fav_com.commercial_pk.fk_property.name
                sq = fav_com.commercial_pk.commercial_sq
                text = (
                    f'Коммерция в ЖК {zhk}, площадь {sq}м2.\n'
                    f'Цена при добавлении в избранное: {price(str(fav_com.price))} руб.\n'
                    f'Текущая стоимость: {price(str(cur_price))} руб.'
                )
                news.append({
                    'id': f'com_{fav_com.id}',
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