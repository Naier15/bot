import datetime
from aiogram import types
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from repositories import UserRepository, FavoriteRepository
from internal import Markup, log, Config
from .user import User
from .app import App
from telegrambot.models import TgUser 


config = Config()

class Dispatch:
    '''Задания по расписанию'''
    @log
    async def dispatch_news(self) -> None:
        '''Рассылка клиентам'''
        user_repository = UserRepository()
        chats = await user_repository.get_dispatch_list()
        async for chat_id in chats:    
            user = User(user_repository)
            await user.sync(chat_id)

            for subscription in user.subscriptions:
                tg_user = await user.get()
                news = await subscription.form_news(tg_user, is_dispatch = True)
                if news:
                    answer, photos_to_show = news
                    await self.send_news(tg_user, answer, photos_to_show, True)

    @log
    async def dispatch_favorites(self) -> None:
        '''Отправка уведомлений об изменении цен в избранном'''
        favorites_repository = FavoriteRepository()
        user_repository = UserRepository()
        all_favorites = await favorites_repository.get_all_favorites()
        for subscription in all_favorites:
            # print(
            #     '\nUSER = ', subscription.user.username, 
            #     '\tTgUser = ', subscription.user.username, await user_repository.get_user(name = subscription.user.username),
            #     '\tTelegramchat_set = ', subscription.user.telegramchat_set.first()
            # )
            user_favorites = await favorites_repository.get_favorites_by_user(subscription.user)
            for news in user_favorites:
                if subscription.user.telegramchat_set.first():
                    await App.send_msg(
                        subscription.user.telegramchat_set.first().telegram_id,
                        '<strong>Уведомление об изменение цен в избранном в вашем личном '
                            'кабинете</strong>\n\n' + news['text'],
                        Markup.inline_buttons(
                            [ [types.InlineKeyboardButton(text = 'Удалить', callback_data = f'delete_{news["id"]}')] ]
                        )
                    )
                else:
                    tg_user = await user_repository.get_user(name = subscription.user.username)
                    if tg_user:
                        await App.send_msg(
                            tg_user.chat_id,
                            '<strong>Уведомление об изменение цен в избранном в вашем личном '
                                'кабинете</strong>\n\n' + news['text'],
                            Markup.inline_buttons(
                                [ [types.InlineKeyboardButton(text = 'Удалить', callback_data = f'delete_{news["id"]}')] ]
                            )
                        )

    @log
    async def setup(self, scheduler: AsyncIOScheduler) -> None:
        scheduler.add_job(
            self.dispatch_news, 
            trigger = 'cron', 
            day_of_week = '0,1,2,3,4,5,6',
            hour = int(config.DISPATCH_TIME.split(':')[0]) if config.DISPATCH_TIME != '*' else '*', 
            minute = int(config.DISPATCH_TIME.split(':')[1]) if config.DISPATCH_TIME != '*' else '*',
            start_date = datetime.datetime.now()
        )
        scheduler.add_job(
            self.dispatch_favorites,
            trigger = 'cron',
            day_of_week = '0,1,2,3,4,5,6',
            hour = int(config.CHANGE_PRICES_TIME.split(':')[0]) if config.CHANGE_PRICES_TIME != '*' else '*',
            minute = int(config.CHANGE_PRICES_TIME.split(':')[1]) if config.CHANGE_PRICES_TIME != '*' else '*',
            start_date = datetime.datetime.now()
        ) 