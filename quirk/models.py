from utils import Base
from sqlalchemy import Column, String, Boolean, SmallInteger, ForeignKey

def uuidGet():
    return str(uuid4())

class User(Base):
    __tablename__ = 'users'
    id = Column(String(255), primary_key=True)
    name = Column(String(255))
    age = Column(SmallInteger())
    def serialize(self):
        return {
            'id': self.id,
            'name': self.name,
            'age': self.age
        }

class Quirk(Base):
    __tablename__ = 'quirks'
    id = Column(String(36), primary_key=True, default=uuidGet)
    quirk = Column(String(140))
    userId = Column(String(255), ForeignKey('users.id'))
    def serialize(self):
        return {
            'id': self.id,
            'quirk': self.quirk,
            'user_id': self.userId
        }

class UserLike(Base):
    __tablename__ = 'user_likes'
    likerId = Column(String(255), ForeignKey('users.id'), primary_key=True)
    likeeId = Column(String(255), ForeignKey('users.id'), primary_key=True)
    liked = Column(Boolean())
    def serialize(self):
        return {
            'liker_id': self.likerId,
            'likee_id': self.likeeId,
            'liked': self.liked
        }

class QuirkLike(Base):
    __tablename__ = 'quirk_likes'
    userId = Column(String(255), ForeignKey('users.id'), primary_key=True)
    quirkId = Column(String(36), ForeignKey('quirks.id'), primary_key=True)
    liked = Column(Boolean())
    def serialize(self):
        return {
            'user_id': self.userId,
            'quirk_id': self.quirkId,
            'liked': self.liked
        }

class Photo(Base):
    __tablename__ = 'photos'
    id = Column(String(36), primary_key=True, default=uuidGet)
    userId = Column(String(255), ForeignKey('users.id'))

class Match(Base):
    __tablename__ = 'matches'
    userOneId = Column(String(255), ForeignKey('users.id'), primary_key=True)
    userTwoId = Column(String(255), ForeignKey('users.id'), primary_key=True)
