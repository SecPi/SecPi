from sqlalchemy.orm import sessionmaker

from tools import config

config.load("manager")

import database as db

db.connect()

p_worker = db.objects.Worker(name="Philip's Pi", address="10.0.0.200", active_state=True)
m_worker = db.objects.Worker(name="Martin's Pi", address="192.168.1.2", active_state=False)

cam_params = [
	db.objects.Param(key='path', value='/dev/video0', description='Path to webcam linux device.', object_type="action"),
	db.objects.Param(key='resolution_x', value='640', description='Width of the picture taken.', object_type="action"),
	db.objects.Param(key='resolution_y', value='480', description='Height of the picutre taken.', object_type="action"),
	db.objects.Param(key='count', value='2', description='Number of pictures taken.', object_type="action"),
	db.objects.Param(key='interval', value='1', description='Interval between pictures', object_type="action"),
	db.objects.Param(key='data_path', value='/tmp/secpi/worker', description='Path to store the images.', object_type="action"),
]

action_pic = db.objects.Action(name="Webcam", cl="Webcam", module="webcam", workers=[m_worker, p_worker], params=cam_params)

email_params = [
	db.objects.Param(key='sender', value='secpi@gmx.at', description='Sender of the mail.', object_type="notifier"),
	db.objects.Param(key='recipient', value='martin.liebl@hotmail.com', description='Recipient of the mail.', object_type="notifier"),
	db.objects.Param(key='subject', value='SecPi Alarm', description='Subject of the mail.', object_type="notifier"),
	db.objects.Param(key='text', value='Your SecPi raised an alarm. Please check the attached files.', description='Text for the mail.', object_type="notifier"),
	db.objects.Param(key='data_dir', value='/var/tmp/manager', description='Directory to fetch the files from.', object_type="notifier"),
	db.objects.Param(key='smtp_address', value='mail.gmx.com', description='SMTP Server to send mails from.', object_type="notifier"),
	db.objects.Param(key='smtp_port', value='587', description='Port of the SMTP Server.', object_type="notifier"),
	db.objects.Param(key='smtp_user', value='secpi@gmx.at', description='User for the SMTP Server.', object_type="notifier"),
	db.objects.Param(key='smtp_pass', value='TOBESET', description='Password for the SMTP Server.', object_type="notifier"),
	db.objects.Param(key='smtp_security', value='STARTTLS', description='Security setting for SMTP Server (can be STARTTLS, SSL, NOSSL, NOAUTH).', object_type="notifier")
]

notifier_email = db.objects.Notifier(name="E-Mail", cl="Mailer", module="mailer", params=email_params)

sensor1_params = [
	db.objects.Param(key='gpio', value='15', description='GPIO pin.', object_type="sensor"),
	db.objects.Param(key='bouncetime', value='60000', description='Bouncetime for GPIO pin.', object_type="sensor")
]

sensor2_params = [
	db.objects.Param(key='gpio', value='17', description='GPIO pin.', object_type="sensor"),
	db.objects.Param(key='bouncetime', value='60000', description='Bouncetime for GPIO pin.', object_type="sensor")
]

sensor3_params = [
	db.objects.Param(key='gpio', value='18', description='GPIO pin.', object_type="sensor"),
	db.objects.Param(key='bouncetime', value='60000', description='Bouncetime for GPIO pin.', object_type="sensor")
]


sensors = [
	db.objects.Sensor(name="door IR sensor", description="this is the infrared sensor at the door", module="gpio_sensor", cl="GPIOSensor", worker=p_worker, params=sensor1_params),
	db.objects.Sensor(name="door contact sensor", description="this is the contact sensor at the door", module="gpio_sensor", cl="GPIOSensor", worker=p_worker, params=sensor2_params),
	db.objects.Sensor(name="window contact sensor", description="this is the contact sensor at the window", module="gpio_sensor", cl="GPIOSensor", worker=p_worker, params=sensor3_params)
]


db.session.add(p_worker)
db.session.add(m_worker)
db.session.add(action_pic)
db.session.add_all(cam_params)
db.session.add(notifier_email)
db.session.add_all(email_params)
db.session.add_all(sensors)
db.session.add_all(sensor1_params)
db.session.add_all(sensor2_params)
db.session.add_all(sensor3_params)

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
