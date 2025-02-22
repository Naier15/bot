import asyncio
from aiogram import Dispatcher, types
from aiogram.fsm.storage.memory import MemoryStorage
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from app import connect_django, log, App
connect_django('..')
from pages import menu_router, buildings_router, profile_router, subscription_router, property_router


from django.contrib.auth.models import User
from authapp.models import UserProfile

# alphabet = string.ascii_letters + string.digits
# temp_login = 'temp_' + ''.join(secrets.choice(alphabet) for _ in range(16))
# user = User.objects.create_user(
#     username = temp_login,
#     password = temp_login
# )
# profile = UserProfile.objects.create(tel = '89147166183', user = user)


# profile = UserProfile.objects.filter(tel = '89147166183').first()
# user = profile.user
# user.username = 'Roman'
# user.email = ''
# user.set_password('123456')
# user.save()


# logging.basicConfig(
#     filename = f'./log.log',
#     level = logging.INFO, 
#     format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
#     encoding = 'utf-8'
# )

@log
async def main():
	await App.bot.delete_webhook(drop_pending_updates = True)
      
	commands = [
        types.BotCommand(command = 'start', description = 'Старт'),
		types.BotCommand(command = 'menu', description = 'В меню'),
        types.BotCommand(command = 'state', description = 'Состояние')
    ]
	await App.bot.set_my_commands(commands, types.BotCommandScopeDefault())
	
	# scheduler = AsyncIOScheduler(timezone = 'Asia/Vladivostok')
    
	dp = Dispatcher(storage = MemoryStorage())
	[dp.include_router(router) for router in (
		buildings_router,
		profile_router,
		subscription_router,
		property_router,
		menu_router
	)]
	print('Start')
	await dp.start_polling(App.bot, allowed_updates = dp.resolve_used_update_types())


if __name__ == '__main__':
    asyncio.run(main())