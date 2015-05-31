from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Table
from sqlalchemy import Integer, String, DateTime, Boolean
from sqlalchemy import ForeignKey
from sqlalchemy.orm import relationship, backref

import datetime

Base = declarative_base()

zone_setup_table = Table('zones_setups', Base.metadata,
    Column('zone_id', Integer, ForeignKey('zones.id')),
    Column('setup_id', Integer, ForeignKey('setups.id'))
)

class Setup(Base):
	__tablename__ = 'setups'
	id = Column(Integer, primary_key=True)
	name = Column(String, nullable=False)
	description = Column(String)
	active = Column(Boolean)
	
	zones = relationship("Zone", secondary=zone_setup_table, backref="setups")


	def __repr__(self):
		return "Setup: %s" % (self.name)


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
	gpio_pin = Column(Integer, nullable=False)
	
	zone_id = Column(Integer, ForeignKey('zones.id'))
	
	alarms = relationship("Alarm", backref="sensor")


	def __repr__(self):
		return "Sensor: %s (pin: %i) in Zone %s" % (self.name, self.gpio_pin, self.zone)
		

class Alarm(Base):
	__tablename__ = 'alarms'

	id = Column(Integer, primary_key=True)
	alarmtime = Column(DateTime, nullable=False, default=datetime.datetime.now)
	ack = Column(Boolean, default=False)
	sensor_id = Column(Integer, ForeignKey('sensors.id'))

	def __repr__(self):
		return "Alarm@%s for sensor %s (ack: %s)" % (self.alarmtime.strftime("%Y-%m-%d %H:%M:%S"), self.sensor_id, self.ack)


class LogEntry(Base):
	__tablename__ = 'logs'

	id = Column(Integer, primary_key=True)
	time = Column(DateTime, nullable=False, default=datetime.datetime.now)
	ack = Column(Boolean, default=False)
	level = Column(Integer, nullable=False)
	
	message = Column(String, nullable=False)
	

	def __repr__(self):
		return "%s[%i,%s]: %s" %(self.alarmtime.strftime("%Y-%m-%d %H:%M:%S"), self.level, self.message, self.ack)


class Worker(Base):
	__tablename__ = 'workers'

	id = Column(Integer, primary_key=True)
	name = Column(String, nullable=False)
	address = Column(String, nullable=False)
	description = Column(String)
	

	def __repr__(self):
		return "Worker %s (%i, %s)" % (self.name, self.id, self.address)


class Action(Base):
	__tablename__ = 'actions'

	id = Column(Integer, primary_key=True)
	name = Column(String, nullable=False)
	description = Column(String)
	cl = Column(String, nullable=False)
	

	def __repr__(self):
		return "Action %s with class %s" % (self.name, self.cl)



def setup(engine):
	Base.metadata.create_all(engine)
