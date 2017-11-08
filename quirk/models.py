from utils import Base
from utils import dbGetSession
from sqlalchemy import String, Boolean, SmallInteger, Text, Float, Integer
from sqlalchemy import Column, ForeignKey
from sqlalchemy.ext.hybrid import hybrid_method
from uuid import uuid4
from flask import current_app as app
from math import sin, acos, cos, radians

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
    gender = Column(SmallInteger())
    seeking = Column(SmallInteger())
    reports = Column(SmallInteger(), default=0)
    # TODO
        # Notification settings
        # Come up with plan for storing nonbinary genders
        # Miles vs kilometers?
    # NOTE
        # Gender = 0 means male
        # Gender = 1 means female
        # Seeking = 0 means seeking male
        # Seeking = 1 means seeking female
        # Seeking = 2 means seeking male and female

    def isGenderCompatible(self, other):
        # Other is interested
        if self.gender == other.seeking or other.seeking == 2:
            # User is interested
            if self.seeking == other.gender or self.seeking == 2:
                return True
        return False

    def getDistance(self, other):
        radius = 3959
        return acos(
            sin(radians(other.latitude)) * sin(radians(self.latitude)) + cos(radians(other.latitude)) * cos(radians(self.latitude)) * cos(radians(self.longitude - other.longitude))
        ) * radius

    def set(self, newUser):
        fields = self.__dict__.keys()
        immutableFields = ['id', 'name', 'age']
        for field in fields:
            if field in newUser and not field in immutableFields:
                setattr(self, field, newUser[field])

    def serialize(self):
        dbSession = dbGetSession()
        userQuirks = dbSession.query(Quirk).filter(Quirk.user_id == self.id).all()
        userPhotos = dbSession.query(Photo).filter(Photo.user_id == self.id, Photo.thumbnail == False).all()
        userThumbnail = dbSession.query(Photo).filter(Photo.user_id == self.id, Photo.thumbnail == True).one_or_none()

        thumbnailUrl = None
        if not userThumbnail is None:
            thumbnailUrl = userThumbnail.getUrl()

        dbSession.close()

        return {
            'id': self.id,
            'name': self.name,
            'age': self.age,
            'bio': self.bio,
            'thumbnail': thumbnailUrl,
            'photos': [photo.getUrl() for photo in userPhotos],
            'quirks': [quirk.serialize() for quirk in userQuirks]
        }

class Quirk(Base):
    __tablename__ = 'quirks'
    id = Column(String(36), primary_key=True, default=uuidGet)
    quirk = Column(String(140))
    user_id = Column(String(255), ForeignKey('users.id', ondelete="CASCADE"))
    def serialize(self):
        return {
            'id': self.id,
            'quirk': self.quirk,
            'user_id': self.user_id
        }

class UserLike(Base):
    __tablename__ = 'user_likes'
    liker_id = Column(String(255), ForeignKey('users.id', ondelete="CASCADE"), primary_key=True)
    likee_id = Column(String(255), ForeignKey('users.id', ondelete="CASCADE"), primary_key=True)
    liked = Column(Boolean())
    def serialize(self):
        return {
            'liker_id': self.liker_id,
            'likee_id': self.likee_id,
            'liked': self.liked
        }

class QuirkLike(Base):
    __tablename__ = 'quirk_likes'
    likee_id = Column(String(255), ForeignKey('users.id', ondelete="CASCADE"), primary_key=True)
    liker_id = Column(String(255), ForeignKey('users.id', ondelete="CASCADE"), primary_key=True)
    quirk_id = Column(String(36), ForeignKey('quirks.id', ondelete="CASCADE"), primary_key=True)
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
    ext = Column(String(3))
    user_id = Column(String(255), ForeignKey('users.id', ondelete="CASCADE"))
    thumbnail = Column(Boolean())

    def getUrl(self):
        return '{}/{}.{}'.format(app.config['PHOTO_BASE_URL'], self.id, self.ext)

class Match(Base):
    __tablename__ = 'matches'
    user_one_id = Column(String(255), ForeignKey('users.id', ondelete="CASCADE"), primary_key=True)
    user_two_id = Column(String(255), ForeignKey('users.id', ondelete="CASCADE"), primary_key=True)
    def serialize(self, user, dbSession):
        otherId = self.user_two_id if self.user_one_id == user else self.user_one_id
        print(otherId)
        otherUser = dbSession.query(User).filter(User.id == otherId).one_or_none()
        photo = dbSession.query(Photo).filter(Photo.user_id == otherId, Photo.thumbnail == True).one_or_none()
        return {
            'name': otherUser.name,
            'photo': photo.getUrl()
        }

class Priority(Base):
    __tablename__ = 'priorities'
    user_one_id = Column(String(255), ForeignKey('users.id', ondelete="CASCADE"), primary_key=True)
    user_two_id = Column(String(255), ForeignKey('users.id', ondelete="CASCADE"), primary_key=True)
    priority = Column(SmallInteger(), default=0)

class Business(Base):
    __tablename__ = 'business'
    id = Column(String(36), primary_key=True, default=uuidGet)
    email = Column(String(255))
    password = Column(Text)
    business_name = Column(String(255))
    def serialize(self):
        return {
            'id': self.id,
            'email': self.email,
            'business_name': self.business_name
    }

class Deal(Base):
    __tablename__ = 'deals'
    id = Column(String(36), primary_key=True, default=uuidGet)
    latitude = Column(Float())
    longitude = Column(Float())
    business_name = Column(String(255))
    business_id = Column(String(36), ForeignKey('business.id'))
    deal_name = Column(String(255))
    deal_text = Column(String(255))
    photo_id = Column(String(36), default="images/no_picture.jpg")
    def serialize(self):
        return {
            'id': self.id,
            'latitude': self.latitude,
            'longitude': self.longitude,
            'business_name': self.business_name,
            'business_id': self.business_id,
            'deal_name': self.deal_name,
            'deal_text': self.deal_text,
            'photo_id': self.photo_id
        }

class UserDeal(Base):
    __tablename__ = 'user_redeemed_deals'
    user_id = Column(String(255), ForeignKey('users.id'), primary_key=True)
    deal_id = Column(String(36), ForeignKey('deals.id'), primary_key=True)

class Report(Base):
    __tablename__ = 'reports'
    reporter_id = Column(String(255), ForeignKey('users.id', ondelete="CASCADE"), primary_key=True)
    reportee_id = Column(String(255), ForeignKey('users.id', ondelete="CASCADE"), primary_key=True)
    body = Column(Text())
    def serialize(self):
        return {
            'reporter_id': self.reporter_id,
            'reportee_id': self.reportee_id,
            'body': self.body
        }
