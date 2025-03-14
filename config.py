from dataclasses import dataclass
from os import environ
from dotenv import load_dotenv


res = load_dotenv()

@dataclass
class Config:
    BOT_TOKEN = environ['BOT_TOKEN']
    DJANGO_PATH = environ['DJANGO_PATH']
    LOG_FILE = environ.get('LOG_FILE', 'log.log')
    MANAGER_LINK = environ.get('MANAGER_LINK', '+79679580207')
    DJANGO_HOST = environ.get('DJANGO_HOST', 'https://bashni.pro')
    REGION = environ.get('REGION', 'Asia/Vladivostok')
    DEBUG = bool(environ.get('DEBUG', 0))
    DISPATCH_TIME = environ.get('DISPATCH_TIME', '16:20')
