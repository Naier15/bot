from dataclasses import dataclass
from os import environ

from dotenv import load_dotenv


# res = load_dotenv()

@dataclass
class Config:
    BOT_TOKEN = environ['BOT_TOKEN']