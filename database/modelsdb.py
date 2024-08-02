import sqlalchemy as sq
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


class User(Base):
    __tablename__ = "user"

    id = sq.Column(sq.Integer, primary_key=True, autoincrement=False)

    def __str__(self):
        return f"User {self.id}"


class Word(Base):
    __tablename__ = "word"

    id = sq.Column(sq.Integer, primary_key=True)
    word = sq.Column(sq.String, unique=True)
    translate = sq.Column(sq.String, unique=True)

    def __str__(self):
        return f"Word {self.id} -> {self.word} -> {self.translate}"


class UserWord(Base):
    __tablename__ = "user_word"

    id = sq.Column(sq.Integer, primary_key=True)
    user_id = sq.Column(sq.Integer, sq.ForeignKey("user.id"), nullable=False)
    word_id = sq.Column(sq.Integer, sq.ForeignKey("word.id"), nullable=False)

    user = relationship(User, backref="user_words")
    word = relationship(Word, backref="user_words")

    def __str__(self):
        return f"UserWord {self.id}"


def create_tables(engine):
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)