from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


from tools import config
import objects

session = None
engine = None

def connect():
	global session
	global engine
	engine = create_engine("sqlite:///%s/data.db"%PROJECT_PATH, echo = False) # echo = true aktiviert debug logging

	Session = sessionmaker(bind=engine)
	session = Session()

def setup():
	objects.setup(engine)

