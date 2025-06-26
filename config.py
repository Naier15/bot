from dataclasses import dataclass
from os import environ
from dotenv import load_dotenv
from sys import path
import logging, os, sys

import django.conf, django


res = load_dotenv()

def connect_django(path_to_django: str):
    '''Подключение к Django'''
    path.append(path_to_django)
    environ.setdefault('DJANGO_SETTINGS_MODULE', 'bashni.settings')
    if not django.conf.settings.configured:
        django.setup()
        logging.debug(f'--- Connected to Django models - {django.conf.settings.configured} ---')

def init_log(log_file: str):
    formatter = logging.Formatter('%(asctime)s -- %(name)s -- %(levelname)s -- %(message)s')
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)

    for handler in logger.handlers:
        logger.removeHandler(handler)

    # Логи в файл
    file_handler = logging.FileHandler(
        filename=os.path.abspath(os.path.join(os.path.dirname(__file__), log_file)),
        encoding='utf-8'
    )
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    # Логи в консоль
    console = logging.StreamHandler(sys.stdout)
    console.setFormatter(formatter)
    logger.addHandler(console)

@dataclass
class Config:
    BOT_TOKEN = environ['BOT_TOKEN']
    DJANGO_PATH = environ['DJANGO_PATH']
    TO_SET_COMMANDS = environ.get('TO_SET_COMMANDS', 0)
    LOG_FILE = environ.get('LOG_FILE', 'log.log')
    MANAGER_LINK = environ.get('MANAGER_LINK', '+79679580207')
    DJANGO_HOST = environ.get('DJANGO_HOST', 'https://bashni.pro')
    REGION = environ.get('REGION', 'Asia/Vladivostok')
    DEBUG = bool(environ.get('DEBUG', 0))
    DISPATCH_TIME = environ.get('DISPATCH_TIME', '16:20')