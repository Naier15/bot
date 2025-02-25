from dataclasses import dataclass
from os import environ

from dotenv import load_dotenv


# res = load_dotenv()

@dataclass
class Config:
    BOT_TOKEN = environ.get('BOT_TOKEN', '1291275643:AAHIk28uq57pVT5ZZz-IEQllgQhP5_mwx7s')
    MANAGER_BOT_LINK = environ.get('MANAGER_BOT_LINK', 'https://t.me/bashnipro_bot')
    DJANGO_HOST = environ.get('DJANGO_HOST', 'https://bashni.pro/')
    REGION = environ.get('REGION', 'Asia/Vladivostok')
