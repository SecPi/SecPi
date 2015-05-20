from sqlalchemy import create_engine

from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Table
from sqlalchemy import Integer, String, DateTime, Boolean
from sqlalchemy import ForeignKey
from sqlalchemy.orm import relationship, backref


engine = create_engine('sqlite:///data.db') #, echo = True) # echo = true aktiviert debug logging

Base = declarative_base()


zone_set_table = Table('zones_sets', Base.metadata,
    Column('zone_id', Integer, ForeignKey('zones.id')),
    Column('set_id', Integer, ForeignKey('sets.id'))
)

class Set(Base):
	__tablename__ = 'sets'
	id = Column(Integer, primary_key=True)
	name = Column(String, nullable=False)
	description = Column(String)
	
	zones = relationship("Zone", secondary=zone_set_table, backref="sets")


	def __repr__(self):
		return "Set: %s" % (self.name)


class Zone(Base):
	__tablename__ = 'zones'
	id = Column(Integer, primary_key=True)
	name = Column(String, nullable=False)
	description = Column(String)
	
	sensors = relationship("Sensor", backref="zone")


	def __repr__(self):
		return "Zone: %s" % (self.name)


class Sensor(Base):
	__tablename__ = 'sensors'
	id = Column(Integer, primary_key=True)
	name = Column(String, nullable=False)
	description = Column(String)
	gpio_pin = Column(Integer)
	
	zone_id = Column(Integer, ForeignKey('zones.id'))
	
	alarms = relationship("Alarm", backref="sensor")


	def __repr__(self):
		return "Sensor: %s (pin: %i) in Zone %s" % (self.name, self.gpio_pin, self.zone.name)
		

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