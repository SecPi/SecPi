import datetime

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Table
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import backref, relationship

Base = declarative_base()

zone_setup_table = Table(
    "zones_setups",
    Base.metadata,
    Column("zone_id", Integer, ForeignKey("zones.id")),
    Column("setup_id", Integer, ForeignKey("setups.id")),
)


class Setup(Base):
    __tablename__ = "setups"
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    description = Column(String)
    active_state = Column(Boolean, nullable=False, default=False)

    zones = relationship("Zone", secondary=zone_setup_table, backref="setups")

    def __repr__(self):
        return "Setup: %s" % (self.name)


class Zone(Base):
    __tablename__ = "zones"
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    description = Column(String)

    sensors = relationship("Sensor", backref="zone")

    def __repr__(self):
        return "Zone: %s" % (self.name)


class Sensor(Base):
    __tablename__ = "sensors"
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    description = Column(String)

    cl = Column(String, nullable=False)
    module = Column(String, nullable=False)
    params = relationship("Param", primaryjoin="and_(Param.object_id==Sensor.id, Param.object_type=='sensor')")

    zone_id = Column(Integer, ForeignKey("zones.id"))
    worker_id = Column(Integer, ForeignKey("workers.id"))

    alarms = relationship("Alarm", backref="sensor")

    def __repr__(self):
        return "Sensor: %s in Zone %s on Worker %s" % (self.name, self.zone, self.worker.name)


class Alarm(Base):
    __tablename__ = "alarms"

    id = Column(Integer, primary_key=True)
    alarmtime = Column(DateTime, nullable=False, default=datetime.datetime.now)
    ack = Column(Boolean, default=False)
    sensor_id = Column(Integer, ForeignKey("sensors.id"))
    message = Column(String)

    def __repr__(self):
        return "Alarm@%s for sensor %s (ack: %s): %s" % (
            self.alarmtime.strftime("%Y-%m-%d %H:%M:%S"),
            self.sensor_id,
            self.ack,
            self.message,
        )


class LogEntry(Base):
    __tablename__ = "logs"

    id = Column(Integer, primary_key=True)
    logtime = Column(DateTime, nullable=False, default=datetime.datetime.now)
    ack = Column(Boolean, default=False)
    level = Column(Integer, nullable=False)
    sender = Column(String, nullable=True)
    message = Column(String, nullable=False)

    def __repr__(self):
        return "%s[%i,%s]: %s" % (self.logtime.strftime("%Y-%m-%d %H:%M:%S"), self.level, self.message, self.ack)


worker_action_table = Table(
    "workers_actions",
    Base.metadata,
    Column("worker_id", Integer, ForeignKey("workers.id")),
    Column("action_id", Integer, ForeignKey("actions.id")),
)


class Worker(Base):
    __tablename__ = "workers"

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    address = Column(String, nullable=False)
    description = Column(String)
    active_state = Column(Boolean, nullable=False, default=True)

    sensors = relationship("Sensor", backref="worker")
    actions = relationship("Action", secondary=worker_action_table, backref="workers")

    def __repr__(self):
        return "Worker %s (%i, %s)" % (self.name, self.id, self.address)


class Action(Base):
    __tablename__ = "actions"

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    description = Column(String)
    cl = Column(String, nullable=False)
    module = Column(String, nullable=False)
    active_state = Column(Boolean, nullable=False, default=True)

    params = relationship("Param", primaryjoin="and_(Param.object_id==Action.id, Param.object_type=='action')")

    def __repr__(self):
        return "Action %s with class %s" % (self.name, self.cl)


class Notifier(Base):
    __tablename__ = "notifiers"

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    description = Column(String)
    cl = Column(String, nullable=False)
    module = Column(String, nullable=False)
    active_state = Column(Boolean, nullable=False, default=True)

    params = relationship("Param", primaryjoin="and_(Param.object_id == Notifier.id, Param.object_type=='notifier')")

    def __repr__(self):
        return "Notifier %s with class %s" % (self.name, self.cl)


class Param(Base):
    __tablename__ = "params"

    id = Column(Integer, primary_key=True)
    key = Column(String, nullable=False)
    value = Column(String, nullable=False)
    description = Column(String)
    object_type = Column(String, nullable=False)

    object_id = Column(Integer, ForeignKey("actions.id"), ForeignKey("notifiers.id"), ForeignKey("sensors.id"))

    def __repr__(self):
        return "Param %s:%s" % (self.key, self.value)


def setup(engine):
    Base.metadata.create_all(engine)
