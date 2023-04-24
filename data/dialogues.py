import datetime
import sqlalchemy
from sqlalchemy import orm
from .db_session import SqlAlchemyBase


class Chat(SqlAlchemyBase):
    __tablename__ = 'chat'

    chat_id = sqlalchemy.Column(sqlalchemy.Integer,
                           primary_key=True, autoincrement=True)
    user1 = sqlalchemy.Column(sqlalchemy.Integer, nullable=False)
    user2 = sqlalchemy.Column(sqlalchemy.Integer, nullable=False)

    def __repr__(self):
        return f'<Chat_id:> {self.chat_id} <User1:> {self.user1} <User2:> {self.user2}'
