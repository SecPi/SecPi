from sqlalchemy import create_engine

from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, DateTime, Boolean
from sqlalchemy import ForeignKey
from sqlalchemy.orm import relationship, backref


engine = create_engine('sqlite:///data.db', echo = True)

Base = declarative_base()


class Sensor(Base):
	__tablename__ = 'sensors'
	id = Column(Integer, primary_key=True)
	name = Column(String, nullable=False)
	description = Column(String)
	gpio_pin = Column(Integer)
	
	alarms = relationship("Alarm", backref="sensor")


	def __repr__(self):
		return "Sensor: %s (pin: %i)" % (self.name, self.gpio_pin)
		

class Alarm(Base):
	__tablename__ = 'alarms'

	id = Column(Integer, primary_key=True)
	alarmtime = Column(DateTime)
	ack = Column(Boolean)
	sensor_id = Column(Integer, ForeignKey('sensors.id'))
	
	
	

	def __repr__(self):
		return "Alarm@%s for sensor %s (ack: %s)" % (self.alarmtime.strftime("%Y-%m-%d %H:%M:%S"), self.sensor_id, self.ack)



		

def setup():
	Base.metadata.create_all(engine)