import telebot
from telebot import types
import socket
import threading as t

#G_BOI_BOT
bot = telebot.TeleBot('1228811646:AAHi2uByEsCDx0Ly70zwY0mIEr-6a0m4spE')
HOST = "127.0.0.1"
PORT = 65432

@bot.message_handler(content_types=['text'])
def mess(message: types.Message):
    msg = message.text.strip().lower()
    chat_id = message.chat.id
    print(chat_id, msg)
    process = t.Thread(target=server, args=(chat_id, msg), daemon=True)
    process.start()
    bot.send_message(message.chat.id, 'Отправлено', parse_mode='html')
    process.join()


@bot.message_handler(commands=['start'])
def start(message):
    CHAT_ID = message.chat.id
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    btn1 = types.KeyboardButton ("1")
    btn2 = types.KeyboardButton ("2")
    markup.add(btn1, btn2)
    send_mess = f"Привет, {message.from_user.first_name}!\nПогнали?"
    bot.send_message(message.chat.id, send_mess, parse_mode='html', reply_markup=markup)


def server(chat_id, message):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((HOST, PORT))
        s.sendall(f"{chat_id} | {message}".encode())
    #   data = s.recv(1024).decode()
    # print(f"Received {data!r}")

if __name__ == '__main__':
    bot.polling(none_stop=True)
  
  