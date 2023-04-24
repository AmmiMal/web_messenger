import datetime
import sqlalchemy
from sqlalchemy import orm
from .db_session import SqlAlchemyBase


class Message(SqlAlchemyBase):
    __tablename__ = 'message'

    message_id = sqlalchemy.Column(sqlalchemy.Integer,
                           primary_key=True, autoincrement=True)
    chat_id = sqlalchemy.Column(sqlalchemy.Integer, nullable=False)
    user_id = sqlalchemy.Column(sqlalchemy.Integer,
                                sqlalchemy.ForeignKey("users.id"))
    content = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    created_date = sqlalchemy.Column(sqlalchemy.Time,
                                     default=datetime.datetime.now().time())
    user = orm.relationship('User')

    def __repr__(self):
        return f'<Message_id:> {self.message_id} <Chat_id:> {self.chat_id} <User_id:> {self.user_id} <Content:> {self.content} <Create_date:> {self.created_date}'
