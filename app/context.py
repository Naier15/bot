from dependency_injector import containers, providers
from aiogram import Bot

from app.config import Config


class Context(containers.DeclarativeContainer):
    config = providers.Singleton(Config)
    bot = providers.Singleton(
        Bot,
        token=config().BOT_TOKEN
    )