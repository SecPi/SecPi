from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


from tools import config
import objects


engine = create_engine("sqlite:///%s/data.db"%config.get("project_path"), echo = True) # echo = true aktiviert debug logging

Session = sessionmaker(bind=engine)
session = Session()

def setup():
	objects.setup(engine)