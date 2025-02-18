from . import text
from .utils import form_buttons, log, connect_django
from .config import Config
from .entities import App, User
from .pages.menu import router as menu_router
from .pages.buildings import router as buildings_router
from .pages.profile import router as profile_router
from .pages.subscription import router as subscription_router
from .pages.property import router as property_router