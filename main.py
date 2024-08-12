import random

from sqlalchemy import func, or_
from telebot import types, TeleBot, custom_filters
from telebot.storage import StateMemoryStorage
from database.modelsdb import User, Word, UserWord
# from database.connectdb import Connection
from sqlalchemy.orm import sessionmaker
import sqlalchemy
from configparser import ConfigParser
import configparser
from commands import Command
from mystates import MyStates


def load_config():
    config = ConfigParser()
    config.read(r'C:\Users\doc21\PycharmProjects\НАЧИНАЕМ ВСЕ СНАЧАЛА ТЕЛЕГА\database\configdb.ini')
    return config['database']


db_config = load_config()

engine = sqlalchemy.create_engine(f"{db_config['dialect']}://{db_config['username']}:{db_config['password']}@{db_config['host']}:{db_config['port']}/{db_config['database']}")
Session = sessionmaker(bind=engine)
session = Session()


print('Start telegram bot...')

state_storage = StateMemoryStorage()
config = configparser.ConfigParser()
config.read('configtg.ini')
token_tg = config['TELEGRAM']['token']
token_bot = token_tg
bot = TeleBot(token_bot, state_storage=state_storage)

userStep = {}
buttons = []


def show_hint(*lines):
    return '\n'.join(lines)


def show_target(data):
    return f"{data['target_word']} -> {data['translate_word']}"


def get_user_step(uid):
    if uid in userStep:
        return userStep[uid]
    else:
        user = User(id=uid)
        userStep[uid] = 0
        print("New user detected, who hasn't used \"/start\" yet")
        return 0


def add_user(user_id):  # не проверяю наличие пользователя в бд
    user = User(id=user_id)
    session.add(user)
    session.commit()


def add_user_word(user_id, word_id):
    user_word = UserWord(user_id=user_id, word_id=word_id)
    session.add(user_word)
    session.commit()


@bot.message_handler(commands=['cards', 'start'])
def create_cards(message):
    cid = message.chat.id
    user = session.query(User).filter(User.id == cid).first()  # больше нет запроса в блоке if
    if user is None:
        add_user(cid)
        userStep[cid] = 0
        bot.send_message(cid, "Hello, stranger, let study English...")

    markup = types.ReplyKeyboardMarkup(row_width=2)
    others = (
        session.query(Word.word, Word.translate)
        .join(UserWord, isouter=True)
        .where(or_(
            UserWord.user_id == None,
            UserWord.user_id == cid,
        ))
        .order_by(func.random())
        .limit(4)
        .all()
    )   # большое спасибо за наводку по запросу, использовала ее
    target_word = random.choice(others)
    target_word_txt = target_word.word
    translate = target_word.translate

    other_words_btns = [types.KeyboardButton(word.word) for word in others if word.word != target_word_txt]
    random_others = random.sample(other_words_btns, min(3, len(other_words_btns)))
    target_word_btn = types.KeyboardButton(target_word_txt)
    buttons = random_others + [target_word_btn]
    random.shuffle(buttons)

    next_btn = types.KeyboardButton(Command.NEXT)
    add_word_btn = types.KeyboardButton(Command.ADD_WORD)
    delete_word_btn = types.KeyboardButton(Command.DELETE_WORD)
    buttons.extend([next_btn, add_word_btn, delete_word_btn])

    markup.add(*buttons)

    greeting = f"Выбери перевод слова:\n🇷🇺 {translate}"
    bot.send_message(message.chat.id, greeting, reply_markup=markup)

    bot.set_state(message.from_user.id, MyStates.target_word, message.chat.id)
    with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
        data['target_word'] = target_word_txt
        data['translate_word'] = translate
        data['other_words'] = [word.word for word in others]


@bot.message_handler(func=lambda message: message.text == Command.NEXT)
def next_cards(message):
    create_cards(message)


@bot.message_handler(func=lambda message: message.text == Command.ADD_WORD)
def add_word(message):  # не проверяю пользователя в БД
    cid = message.chat.id
    userStep[cid] = 1
    bot.send_message(message.chat.id, "Введите слово и его перевод в формате: слово: перевод")


@bot.message_handler(func=lambda message: userStep.get(message.chat.id) == 1)
def save_word(message):
    cid = message.chat.id
    word, translate = message.text.split(':')
    word = word.strip()
    translate = translate.strip()

    session = Session()
    new_word = Word(word=word, translate=translate)
    session.add(new_word)
    session.commit()
    word_id = new_word.id
    add_user_word(cid, word_id)
    session.commit()
    session.close()

    bot.send_message(cid, f"Слово '{word}' успешно добавлено!")
    userStep[cid] = 0


@bot.message_handler(func=lambda message: message.text == Command.DELETE_WORD)
def delete_word(message):
    cid = message.chat.id
    userStep[cid] = 2
    bot.send_message(cid, "Введите слово для удаления")


@bot.message_handler(func=lambda message: userStep.get(message.chat.id) == 2)   # теперь пользователь может удалять только свои слова
def confirm_delete_word(message):
    cid = message.chat.id
    word_to_delete = message.text.strip()

    session = Session()

    word_record = session.query(Word).filter(Word.word == word_to_delete).first()
    if word_record:
        if word_record.id > 10:
            user_word_records = session.query(UserWord).filter(UserWord.word_id == word_record.id).all()

            for user_word in user_word_records:
                session.delete(user_word)
            session.delete(word_record)
            session.commit()

            bot.send_message(cid, f"Слово '{word_to_delete}' удалено)")
        else:
            bot.send_message(cid, f"Слово '{word_to_delete}' невозможно удалить(")
    else:
        bot.send_message(cid, f"Слово '{word_to_delete}' не найдено(")

    session.close()
    userStep[cid] = 0


@bot.message_handler(func=lambda message: True, content_types=['text'])
def message_reply(message):
    text = message.text
    markup = types.ReplyKeyboardMarkup(row_width=2)
    with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
        target_word = data['target_word']
        if text == target_word:
            hint = show_target(data)
            hint_text = ["Отлично!❤️", hint]
            next_btn = types.KeyboardButton(Command.NEXT)
            add_word_btn = types.KeyboardButton(Command.ADD_WORD)
            delete_word_btn = types.KeyboardButton(Command.DELETE_WORD)
            buttons = [next_btn, add_word_btn, delete_word_btn]
            hint = show_hint(*hint_text)
        else:
            buttons = []
            for btn in buttons:
                if btn.text == text:
                    btn.text = text + '❌'
                    buttons.append(btn)
                    break
            hint = show_hint("Допущена ошибка!",
                             f"Попробуй ещё раз вспомнить слово 🇷🇺{data['translate_word']}")

    markup.add(*buttons)
    bot.send_message(message.chat.id, hint, reply_markup=markup)


bot.add_custom_filter(custom_filters.StateFilter(bot))

bot.infinity_polling(skip_pending=True)
