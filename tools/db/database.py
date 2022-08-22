from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


from tools import config
from tools.db import objects

session = None
engine = None

def connect(path):
	global session
	global engine
	
	# TODO: think about check_same_thread=False
	engine = create_engine("sqlite:///%s/data.db"%path, connect_args={'check_same_thread':False}, echo = False) # echo = true aktiviert debug logging

	Session = sessionmaker(bind=engine)
	session = Session()

def setup():
	objects.setup(engine)

