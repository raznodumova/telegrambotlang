from telebot.handler_backends import State, StatesGroup

class MyStates(StatesGroup):
    target_word = State()
    translate_word = State()
    another_words = State()