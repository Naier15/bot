from dependency_injector import containers, providers, schema
from typing import Iterable, Optional
import math


class App:
    def __init__(self):
        self.current_page: int = 1
        self.chats_counter: int = 0
        self.items_per_page: int = 10
        self.chats: Iterable[dict] = self.generate_chats(1000)

    def generate_chats(self, quantity: int) -> Iterable[dict]:
        self.chats_counter = 0
        chats = []
        for idx in range(quantity):
            chats.append({'title': f'Чат №{idx}', 'id': f'{idx}'})
            self.chats_counter += 1
        return chats
    
    def make_page(self, page: int) -> Optional[types.InlineKeyboardMarkup]:
        if page < 1 or math.ceil(self.chats_counter / self.items_per_page) <= page:
            return
       
        self.current_page = page   
        index = (self.current_page - 1) * self.items_per_page
        chats_to_show = self.chats[index:index+self.items_per_page]
        
        if len(chats_to_show) == 0:
            return
        buttons = types.InlineKeyboardMarkup()
        items = []
        for chat in chats_to_show:
            items.append(types.InlineKeyboardButton(text=chat['title'], callback_data=chat['id']))
        buttons.add(*items, row_width=1)
        buttons.add(*[
            types.InlineKeyboardButton(text='<', callback_data='back'),
            types.InlineKeyboardButton(text=f' {self.current_page}/{math.ceil(self.chats_counter / self.items_per_page)} '.center(12, '-'), callback_data='page'),
            types.InlineKeyboardButton(text='>', callback_data='next')
        ], row_width=3)
        return buttons