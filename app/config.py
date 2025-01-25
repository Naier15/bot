from dotenv import load_dotenv
from dataclasses import dataclass
from os import environ


res = load_dotenv()

@dataclass
class Config:
    BOT_TOKEN = environ['BOT_TOKEN']