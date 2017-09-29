import uuid
from sqlalchemy import Column, String, Boolean, Integer, ForeignKey
from ModelBase import ModelBase

class User(ModelBase):
    __tablename__ = "user"
    id = Column(String(255), primary_key=True)
