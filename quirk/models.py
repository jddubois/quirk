from utils import Base
from utils import dbGetSession
from sqlalchemy import String, Boolean, SmallInteger, Text, Float
from sqlalchemy import Column, ForeignKey

def uuidGet():
    return str(uuid4())

class User(Base):
    __tablename__ = 'users'
    id = Column(String(255), primary_key=True)
    name = Column(String(255))
    age = Column(SmallInteger())
    bio = Column(Text())
    radius = Column(SmallInteger())
    latitude = Column(Float())
    longitude = Column(Float())
    min_age = Column(SmallInteger())
    max_age = Column(SmallInteger())

    # TODO
        # Notification settings
        # Gender
        # Miles vs kilometers?

    def set(self, newUser):
        fields = self.__dict__.keys()
        immutableFields = ['id', 'name', 'age']
        for field in fields:
            if field in newUser and not field in immutableFields:
                setattr(self, field, newUser[field])

    def serialize(self):
        dbSession = dbGetSession()
        userQuirks = dbSession.query(Quirk).filter(Quirk.user_id == self.id).all()
        dbSession.close()
        return {
            'id': self.id,
            'name': self.name,
            'age': self.age,
            'bio': self.bio,
            'quirks': userQuirks
        }

class Quirk(Base):
    __tablename__ = 'quirks'
    id = Column(String(36), primary_key=True, default=uuidGet)
    quirk = Column(String(140))
    user_id = Column(String(255), ForeignKey('users.id'))
    def serialize(self):
        return {
            'id': self.id,
            'quirk': self.quirk,
            'user_id': self.user_id
        }

class UserLike(Base):
    __tablename__ = 'user_likes'
    liker_id = Column(String(255), ForeignKey('users.id'), primary_key=True)
    likee_id = Column(String(255), ForeignKey('users.id'), primary_key=True)
    liked = Column(Boolean())
    def serialize(self):
        return {
            'liker_id': self.liker_id,
            'likee_id': self.likee_id,
            'liked': self.liked
        }

class QuirkLike(Base):
    __tablename__ = 'quirk_likes'
    likee_id = Column(String(255), ForeignKey('users.id'), primary_key=True)
    liker_id = Column(String(255), ForeignKey('users.id'), primary_key=True)
    quirk_id = Column(String(36), ForeignKey('quirks.id'), primary_key=True)
    liked = Column(Boolean())
    def serialize(self):
        return {
            'likee_id': self.likee_id,
            'liker_id': self.liker_id,
            'quirk_id': self.quirk_id,
            'liked': self.liked
        }

class Photo(Base):
    __tablename__ = 'photos'
    id = Column(String(36), primary_key=True, default=uuidGet)
    user_id = Column(String(255), ForeignKey('users.id'))

class Match(Base):
    __tablename__ = 'matches'
    user_one_id = Column(String(255), ForeignKey('users.id'), primary_key=True)
    user_two_id = Column(String(255), ForeignKey('users.id'), primary_key=True)

