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

def dbGetURI():
    dbUrl = 'postgresql://{}:{}@{}:{}/{}'
    return dbUrl.format(dbUser, dbPassword, dbHost, dbPort, dbName)

def dbConnect():
    return create_engine(dbGetURI(), client_encoding='utf8')

def dbGet():
    global db
    if db is None:
        db = dbConnect()
    return db

def dbInitialize():
    from models import *
    Base.metadata.create_all(dbGet())

def dbGetSession():
    dbSession = sessionmaker(expire_on_commit=False, autocommit=False, autoflush=False, bind=dbGet())
    return scoped_session(dbSession)
