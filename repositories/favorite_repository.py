from internal import to_async
from config import Config
from cabinet.models import FavoritesFlats, FavoritesCommercial, UserSubscription
from property.templatetags.view_price import price


# Слой доступа к данным для взаимодействия с базой данными
config = Config()


class FavoriteRepository:

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

                    text_list.append({
                        'id': f'flat_{fav_flat.id}', 
                        'text':text
                    })

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

    async def get_favorites_subscr(self):
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