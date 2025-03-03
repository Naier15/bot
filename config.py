from dataclasses import dataclass
from os import environ
from dotenv import load_dotenv


res = load_dotenv()

@dataclass
class Config:
    BOT_TOKEN = environ['BOT_TOKEN']
    DJANGO_PATH = environ['DJANGO_PATH']
    MANAGER_BOT_LINK = environ.get('MANAGER_BOT_LINK', 'https://t.me/bashnipro_bot')
    DJANGO_HOST = environ.get('DJANGO_HOST', 'https://bashni.pro/')
    REGION = environ.get('REGION', 'Asia/Vladivostok')
