import datetime
import typing as t

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, Table, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()

zone_setup_table = Table(
    "zones_setups",
    Base.metadata,
    Column("zone_id", Integer, ForeignKey("zones.id")),
    Column("setup_id", Integer, ForeignKey("setups.id")),
)


class Setup(Base):
    __tablename__ = "setups"
    id = Column(Integer, primary_key=True)  # noqa:A003
    name = Column(Text, nullable=False)
    description = Column(Text)
    active_state = Column(Boolean, nullable=False, default=False)

    zones = relationship("Zone", secondary=zone_setup_table, backref="setups")

    def __repr__(self):
        return f"Setup(id={self.id}, name={self.name}, zones={self.zones})"


class Zone(Base):
    __tablename__ = "zones"
    id = Column(Integer, primary_key=True)  # noqa:A003
    name = Column(Text, nullable=False)
    description = Column(Text)

    sensors = relationship("Sensor", backref="zone")

    def __repr__(self):
        return f"Zone(id={self.id}, name={self.name})"


class Sensor(Base):
    __tablename__ = "sensors"
    id = Column(Integer, primary_key=True)  # noqa:A003
    name = Column(Text, nullable=False)
    description = Column(Text)

    cl = Column(Text, nullable=False)
    module = Column(Text, nullable=False)
    params: t.List["Param"] = relationship(
        "Param", primaryjoin="and_(Param.sensor_id==Sensor.id, Param.object_type=='sensor')", overlaps="params"
    )

    zone_id = Column(Integer, ForeignKey("zones.id"))
    worker_id = Column(Integer, ForeignKey("workers.id"))

    alarms = relationship("Alarm", backref="sensor")

    def __repr__(self):
        return f"Sensor(id={self.id}, name={self.name}, zone={self.zone}, worker={self.worker})"


class Alarm(Base):
    __tablename__ = "alarms"

    id = Column(Integer, primary_key=True)  # noqa:A003
    alarmtime = Column(DateTime, nullable=False, default=datetime.datetime.now)
    ack = Column(Boolean, default=False)
    sensor_id = Column(Integer, ForeignKey("sensors.id"))
    message = Column(Text)

    def __repr__(self):
        return "Alarm@%s for sensor %s (ack: %s): %s" % (
            self.alarmtime.strftime("%Y-%m-%d %H:%M:%S"),
            self.sensor_id,
            self.ack,
            self.message,
        )


class LogEntry(Base):
    __tablename__ = "logs"

    id = Column(Integer, primary_key=True)  # noqa:A003
    logtime = Column(DateTime, nullable=False, default=datetime.datetime.now)
    ack = Column(Boolean, default=False)
    level = Column(Integer, nullable=False)
    sender = Column(Text, nullable=True)
    message = Column(Text, nullable=False)

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

    id = Column(Integer, primary_key=True)  # noqa:A003
    name = Column(Text, nullable=False)
    address = Column(Text, nullable=False)
    description = Column(Text)
    active_state = Column(Boolean, nullable=False, default=True)

    sensors = relationship("Sensor", backref="worker")
    actions = relationship("Action", secondary=worker_action_table, backref="workers")

    def __repr__(self):
        return f"Worker(id={self.id}, name={self.name}, address={self.address})"


class Action(Base):
    __tablename__ = "actions"

    id = Column(Integer, primary_key=True)  # noqa:A003
    name = Column(Text, nullable=False)
    description = Column(Text)
    cl = Column(Text, nullable=False)
    module = Column(Text, nullable=False)
    active_state = Column(Boolean, nullable=False, default=True)

    params: t.List["Param"] = relationship(
        "Param", primaryjoin="and_(Param.action_id==Action.id, Param.object_type=='action')", overlaps="params"
    )

    def __repr__(self):
        return f"Action(id={self.id}, name={self.name}, module={self.module} cl={self.cl})"


class Notifier(Base):
    __tablename__ = "notifiers"

    id = Column(Integer, primary_key=True)  # noqa:A003
    name = Column(Text, nullable=False)
    description = Column(Text)
    cl = Column(Text, nullable=False)
    module = Column(Text, nullable=False)
    active_state = Column(Boolean, nullable=False, default=True)

    params: t.List["Param"] = relationship(
        "Param", primaryjoin="and_(Param.notifier_id == Notifier.id, Param.object_type=='notifier')", overlaps="params"
    )

    def __repr__(self):
        return f"Notifier(id={self.id}, name={self.name}, module={self.module} cl={self.cl})"


class Param(Base):
    __tablename__ = "params"

    id = Column(Integer, primary_key=True)  # noqa:A003
    key = Column(Text, nullable=False)
    value = Column(Text, nullable=False)
    description = Column(Text)
    object_type = Column(Text, nullable=False)

    # object_id = Column(Integer, ForeignKey("actions.id"), ForeignKey("notifiers.id"), ForeignKey("sensors.id"))
    action_id = Column(Integer, ForeignKey("actions.id"))
    sensor_id = Column(Integer, ForeignKey("sensors.id"))
    notifier_id = Column(Integer, ForeignKey("notifiers.id"))

    def __repr__(self):
        object_id = None
        if self.action_id is not None:
            object_id = self.action_id
        if self.notifier_id is not None:
            object_id = self.notifier_id
        if self.sensor_id is not None:
            object_id = self.sensor_id
        return (
            f"Param(id={self.id}, object_type={self.object_type}, object_id={self.object_id}, "
            f"key={self.key}, value={self.value})"
        )


def setup(engine):
    Base.metadata.create_all(engine)
