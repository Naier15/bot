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