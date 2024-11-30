import telebot
from telebot import types
import socket
import threading as t

bot = telebot.TeleBot('1291275643:AAHIk28uq57pVT5ZZz-IEQllgQhP5_mwx7s')
HOST = "127.0.0.1"
PORT = 65432
CHAT_ID = None

@bot.message_handler(content_types=['text'])
def mess(message):
  CHAT_ID = message.chat.id
  print(CHAT_ID)
  markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
  btn1 = types.KeyboardButton ("Под мобильные телефоны")
  btn2 = types.KeyboardButton ("Виртуальная реальность")
  markup.add(btn1, btn2)
  bot.send_message(message.chat.id, 'Ку-ку', parse_mode='html', reply_markup=markup)


@bot.message_handler(commands=['start'])
def start(message):
  CHAT_ID = message.chat.id
  markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
  btn1 = types.KeyboardButton ("1")
  btn2 = types.KeyboardButton ("2")
  markup.add(btn1, btn2)
  send_mess = f"Привет, {message.from_user.first_name}!\nПогнали?"
  bot.send_message(message.chat.id, send_mess, parse_mode='html', reply_markup=markup)


def server():
  CHAT_ID = 341461613
  with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.bind((HOST, PORT))
    s.listen()
    while True:
      conn, addr = s.accept()
      with conn:
          print(f"Connected by {addr}")
          while True:
              data = conn.recv(1024).decode()
              if not data:
                  break
              chat_id, message = data.split(' | ')
              bot.send_message(int(chat_id), message, parse_mode='html')
              print(data)

if __name__ == '__main__':
  process = t.Thread(target=server, daemon=True)
  process.start()
  bot.polling(none_stop=True)
  process.join()
  
  