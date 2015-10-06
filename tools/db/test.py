from sqlalchemy.orm import sessionmaker

from tools import config

config.load("manager")

import database as db

db.connect()

p_worker = db.objects.Worker(name="Philip's Pi", address="10.0.0.200")
m_worker = db.objects.Worker(name="Martin's Pi", address="192.168.1.2")

cam_params = [
	db.objects.Param(key='path', value='/dev/video0', description='Path to webcam linux device.', object_type="action"),
	db.objects.Param(key='resolution_x', value='640', description='Width of the picture taken.', object_type="action"),
	db.objects.Param(key='resolution_y', value='480', description='Height of the picutre taken.', object_type="action"),
	db.objects.Param(key='count', value='2', description='Number of pictures taken.', object_type="action"),
	db.objects.Param(key='interval', value='1', description='Interval between pictures', object_type="action"),
]

action_pic = db.objects.Action(name="Webcam", cl="Webcam", module="webcam", workers=[m_worker, p_worker], params=cam_params)

db.session.add(p_worker)
db.session.add(m_worker)
db.session.add(action_pic)
db.session.add_all(cam_params)
db.session.add_all([
	db.objects.Sensor(name="door IR sensor", description="this is the infrared sensor at the door", module="gpio_sensor", cl="GPIOSensor", worker=p_worker),
	db.objects.Sensor(name="door contact sensor", description="this is the contact sensor at the door", module="gpio_sensor", cl="GPIOSensor", worker=p_worker),
	db.objects.Sensor(name="window contact sensor", description="this is the contact sensor at the window", module="gpio_sensor", cl="GPIOSensor", worker=p_worker)
	])

db.session.commit()

zone_door = db.objects.Zone(name="door")
zone_window = db.objects.Zone(name="windows")

doors = db.session.query(db.objects.Sensor).filter(db.objects.Sensor.name.like('%door%')).all()
zone_door.sensors = doors

windows = db.session.query(db.objects.Sensor).filter(db.objects.Sensor.name.like('%window%')).all()
zone_window.sensors = windows


set_away = db.objects.Setup(name="away")
set_home = db.objects.Setup(name="at home")

set_away.zones = [zone_door, zone_window]
set_home.zones = [zone_window]



db.session.add(zone_door)
db.session.add(zone_window)
db.session.add(set_away)
db.session.add(set_home)

db.session.commit();



sensors = db.session.query(db.objects.Sensor).all()
print sensors

zones = db.session.query(db.objects.Zone).all()
print zones

sets = db.session.query(db.objects.Setup).all()
print sets

#win_sensor = db.session.query(db.objects.Sensor).get(3)
#print win_sensor
#win_sensor.gpio_pin = 17

#db.session.commit()
