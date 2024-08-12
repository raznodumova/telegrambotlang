import sqlalchemy
from sqlalchemy.orm import sessionmaker
from database.modelsdb import create_tables, User, Word, UserWord
import random
from configparser import ConfigParser


def load_config():
    config = ConfigParser()
    config.read('configdb.ini')
    return config['database']


class Connection():
    db_config = load_config()

    def __init__(self):
        self.engine = sqlalchemy.create_engine(f"{self.db_config['dialect']}://{self.db_config['username']}:{self.db_config['password']}@{self.db_config['host']}:{self.db_config['port']}/{self.db_config['database']}")
        self.Session = sessionmaker(bind=self.engine)
        self.session = self.Session()

    def add_base_words(self):
        base_words = {
            'mouse': 'мышь',
            'cat': 'кот',
            'dog': 'собака',
            'car': 'машина',
            'book': 'книга',
            'table': 'стол',
            'sun': 'солнце',
            'carrot': 'морковка',
            'banana': 'банан',
            'apple': 'яблоко'
        }
        create_tables(engine=self.engine)
        for i in base_words.items():
            self.session.add(Word(word=i[0], translate=i[1]))
            self.session.commit()

    def session_close(self):
        self.session.close()


if __name__ == '__main__':
    db = Connection()
    db.add_base_words()
    db.session_close()


