from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from models import Base

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

def getDb():
    global db
    if db is None:
        db = dbConnect()
    return db

def dbInitialize():
    from models import User
    Base.metadata.create_all(getDb())

dbSession = scoped_session(sessionmaker(autocommit=False, autoflush=False, bind=getDb()))
