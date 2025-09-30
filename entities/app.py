from typing import Optional, Self
import logging

from aiogram import Bot, types
from aiogram.exceptions import TelegramForbiddenError
from aiogram.fsm.state import State
from aiogram.fsm.context import FSMContext
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from .user import User
from repositories import UserRepository
from internal import Markup, log, Tempfile, text, Config
from telegrambot.models import TgUser
    

config = Config()

class App:
    '''Логика приложения'''
    bot: Bot = None

    def __init__(self, state: Optional[FSMContext] = None) -> Self:
        if not App.bot:
            App.bot: Bot = Bot(
                token = config.BOT_TOKEN, 
                default = DefaultBotProperties(parse_mode = ParseMode.HTML)
            )
        self.history: list[State] = []
        self.user: User = User(UserRepository())
        self.instance: Optional[Self] = None
        self.state = state

    async def __aenter__(self) -> Self:
        data = await self.state.get_data()
        if 'app' not in data:
            await self.state.update_data(app = self)
            data = await self.state.get_data()
        self.instance = data.get('app')
        return self.instance
    
    async def __aexit__(self, exc_type, exc, tb) -> None:
        await self.state.update_data(app = self.instance)

    @staticmethod
    def menu() -> types.ReplyKeyboardMarkup:
        '''Кнопки главного меню'''
        btns = [
            [
                types.KeyboardButton(text = text.Btn.FLATS.value),
                types.KeyboardButton(text = text.Btn.SUBSCRIPTION.value)
            ],
            [
                types.KeyboardButton(text = text.Btn.OFFICES.value),
                types.KeyboardButton(text = text.Btn.AUTH.value)
            ],
            [
                types.KeyboardButton(text = text.Btn.HELP.value)
            ]
        ]
        return Markup.bottom_buttons(btns)
    
    @staticmethod
    def subscription_menu() -> types.ReplyKeyboardMarkup:
        '''Кнопки меню управления подписками'''
        btns = [
            [
                types.KeyboardButton(text = text.Btn.SUBSCRIPTION_LIST.value)
            ],
            [
                types.KeyboardButton(text = text.Btn.NEW_SUBSCRIPTION.value), 
                types.KeyboardButton(text = text.Btn.REMOVE_SUBSCRIPTION.value)
            ], 
            [
                types.KeyboardButton(text = text.Btn.TO_MENU.value)
            ]
        ]
        return Markup.bottom_buttons(btns)
    
    async def clear_history(self, with_user: bool = False):
        '''Отчистка истории страниц'''
        if with_user:
            self.user = User(UserRepository())
        self.history.clear()
        await self.state.clear()

    async def set_state(self, page: State, state: FSMContext) -> None:
        '''Добавление нового состояния в историю'''
        if len(self.history) > 0 and self.history[-1] == page:
            return
        self.history.append(page)
        await state.set_state(page)
        # print(f'--History {self.history}--')

    async def go_back(self, state: FSMContext) -> State:
        '''Откат последнего состояния и возвращение предыдущего'''
        if len(self.history) > 0:
            self.history.pop()  # Шаг назад

        page = None
        if len(self.history) > 0:
            page = self.history[-1] # Получение предыдущего состояния
            await state.set_state(page)
            self.history.pop() # Удаляем и предыдущего состояние, поскольку оно добавится в следующем обработчике
        return page
    
    @log
    @staticmethod
    async def send_msg(
        chat_id: int, 
        text: str, 
        markup: Optional[types.InlineKeyboardMarkup | types.ReplyKeyboardMarkup | types.ReplyKeyboardRemove]
    ) -> bool:
        if config.DEBUG and chat_id != '341461613':
            return False
        await App.bot.send_message(
            chat_id         = chat_id,
            text            = text, 
            parse_mode      = 'html',
            reply_markup    = markup
        )
        return True
    
    @log
    async def send_news(self, user: TgUser, answer: str, photos_to_show: list[tuple[int, str, str]], is_dispatch: bool) -> None:        
        try:
            success = await App.send_msg(
                user.chat_id, 
                answer, 
                App.menu() if is_dispatch else App.subscription_menu()
            )
            if not success:
                return
        except TelegramForbiddenError:
            return

        exception = None
        try:
            for id, url, month in photos_to_show:
                photo = types.InputMediaPhoto(
                    media = url,
                    caption = month
                )
                await App.bot.send_media_group(user.chat_id, [photo])
        except Exception as ex:
            exception = ex
            try:
                for id, url, month in photos_to_show: 
                    ext = url.split('.')[-1]
                    async with Tempfile(f'{id}.{ext}', url) as tempfile:
                        photo = types.InputMediaPhoto(
                            media = types.FSInputFile(tempfile),
                            caption = month
                        )
                        await App.bot.send_media_group(user.chat_id, [photo])
            except Exception as ex:
                logging.error(f"Couldn't send photo. Error 1:\n{exception}\nError 2:\n{ex}")