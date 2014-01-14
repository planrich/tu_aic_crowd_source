import sqlalchemy
import sqlalchemy.ext.declarative
import sqlalchemy.orm
import settings
from sqlalchemy import Table, Column, Integer, ForeignKey, String, DateTime, Boolean
from sqlalchemy.orm import relationship, backref
from sqlalchemy.ext.declarative import declarative_base
import datetime as dt
from contextlib import contextmanager

engine = sqlalchemy.create_engine(settings.DB_URL)

Session = sqlalchemy.orm.sessionmaker(bind=engine)
Base = sqlalchemy.ext.declarative.declarative_base()

@contextmanager
def session_scope():
    session = Session()
    try:
        yield session
        session.commit()
    except:
        session.rollback()
        raise
    finally:
        session.close()

class OpenTask(Base):
    __tablename__ = 'open_tasks'
    id = Column(sqlalchemy.String, primary_key=True)
    datetime = Column(DateTime)
    task_description = Column(String)
    task_text = Column(String)
    answer_possibility = Column(String) # hacky
    callback_link = Column(String)
    solved = Column(Boolean)
    price = Column(sqlalchemy.Float)
    price_bonus = Column(sqlalchemy.Float)


    def __init__(self, id, desc, text, answer, link, cents):
        self.id = id
        self.task_description = desc
        self.task_text = text
        self.answer_possibility = answer
        self.callback_link = link
        self.price = cents
        self.datetime = dt.datetime.now()
        self.solved = False
        self.price_bonus = 0

    def answer_options(self):
        return self.answer_possibility.split("|")

Base.metadata.create_all(engine)

