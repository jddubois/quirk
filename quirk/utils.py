from uuid import uuid4
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.ext.declarative import declarative_base

# Base Model for Database
Base = declarative_base()

# Database Information
db = None
dbUser = 'root'
dbPassword = 'quirkykidz'
dbHost = 'localhost'
dbPort = '5432'
dbName = 'root'

def dbConnect():
    dbUrl = 'postgresql://{}:{}@{}:{}/{}'
    dbUrl = dbUrl.format(dbUser, dbPassword, dbHost, dbPort, dbName)
    return create_engine(dbUrl, client_encoding='utf8')

def dbGet():
    global db
    if db is None:
        db = dbConnect()
    return db

def dbInitialize():
    from models import User
    Base.metadata.create_all(dbGet())

def dbGetSession():
    dbSession = sessionmaker(autocommit=False, autoflush=False, bind=dbGet())
    return scoped_session(dbSession)
