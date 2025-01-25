from django.contrib.auth import authenticate, login, update_session_auth_hash



def create_chats():
	chats = []
	for idx in range(5):
		chats.append({'title': f'Чат №{idx}'})
	return chats

chats = create_chats()

current_page = 2
items_per_page = len(chats)
index = (current_page - 1) * items_per_page
# chats[current_page:*page]
print(index)


# bot.edit_message_text('Хотел другой текст', message.chat.id, msg.message_id)
# bot.delete_messages(message.chat.id, [msg.message_id, msg2.message_id])


# if last_message:
# 	bot.delete_messages(message.chat.id, [last_message])