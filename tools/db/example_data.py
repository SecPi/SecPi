from sqlalchemy.orm import sessionmaker

from tools import config

config.load("/opt/secpi/manager/config.json")

import database as db

db.connect()

pi_name = raw_input("Enter worker name: ")
pi_ip = raw_input("Enter worker IP: ")

p_worker = db.objects.Worker(name=pi_name, address=pi_ip, active_state=True)

cam_params = [
	db.objects.Param(key='path', value='/dev/video0', description='Path to webcam linux device.', object_type="action"),
	db.objects.Param(key='resolution_x', value='640', description='Width of the picture taken.', object_type="action"),
	db.objects.Param(key='resolution_y', value='480', description='Height of the picutre taken.', object_type="action"),
	db.objects.Param(key='count', value='2', description='Number of pictures taken.', object_type="action"),
	db.objects.Param(key='interval', value='1', description='Interval between pictures', object_type="action"),
	db.objects.Param(key='data_path', value='/var/tmp/secpi/worker_data', description='Path to store the images.', object_type="action"),
]

action_pic = db.objects.Action(name="Webcam", cl="Webcam", module="webcam", workers=[p_worker], params=cam_params)

email_params = [
	db.objects.Param(key='sender', value='alarm@secpi.local', description='Sender of the mail.', object_type="notifier"),
	db.objects.Param(key='recipient', value='alarm@example.com', description='Recipient of the mail.', object_type="notifier"),
	db.objects.Param(key='subject', value='SecPi Alarm', description='Subject of the mail.', object_type="notifier"),
	db.objects.Param(key='text', value='Your SecPi raised an alarm. Please check the attached files.', description='Text for the mail.', object_type="notifier"),
	db.objects.Param(key='data_dir', value='/var/tmp/secpi/alarms', description='Directory to fetch the files from.', object_type="notifier"),
	db.objects.Param(key='smtp_address', value='mail.secpi.local', description='SMTP Server to send mails from.', object_type="notifier"),
	db.objects.Param(key='smtp_port', value='587', description='Port of the SMTP Server.', object_type="notifier"),
	db.objects.Param(key='smtp_user', value='alarm@secpi.local', description='User for the SMTP Server.', object_type="notifier"),
	db.objects.Param(key='smtp_pass', value='TOBESET', description='Password for the SMTP Server.', object_type="notifier"),
	db.objects.Param(key='smtp_security', value='STARTTLS', description='Security setting for SMTP Server (can be STARTTLS, SSL, NOSSL, NOAUTH_NOSSL, NOAUTH_STARTTLS, NOAUTH_SSL).', object_type="notifier")
]

notifier_email = db.objects.Notifier(name="E-Mail", cl="Mailer", module="mailer", params=email_params)

sensor1_params = [
	db.objects.Param(key='gpio', value='15', description='GPIO pin.', object_type="sensor"),
	db.objects.Param(key='bouncetime', value='60000', description='Bouncetime for GPIO pin.', object_type="sensor")
]

sensor2_params = [
	db.objects.Param(key='ip', value=pi_ip, description='TCP Server Listen IP', object_type="sensor"),
	db.objects.Param(key='port', value='1337', description='TCP Server Port.', object_type="sensor")
]

# TODO
sensor3_params = [
	db.objects.Param(key='gpio', value='18', description='GPIO pin.', object_type="sensor"),
	db.objects.Param(key='bouncetime', value='60000', description='Bouncetime for GPIO pin.', object_type="sensor")
]


sensor_gpio = db.objects.Sensor(name="GPIO Sensor", description="This is a simple sensor which reads a GPIO Port", module="gpio_sensor", cl="GPIOSensor", worker=p_worker, params=sensor1_params)
sensor_tcp = db.objects.Sensor(name="TCP Sensor", description="This is a sensor which listens on a TCP port.", module="tcpportlistener", cl="TCPPortListener", worker=p_worker, params=sensor2_params)
sensor_temp = db.objects.Sensor(name="Temperature Sensor", description="A sensor that checks if a temperature is in a defined range.", module="temperature_sensor", cl="TemperatureSensor", worker=p_worker, params=sensor3_params)


db.session.add(p_worker)
db.session.add(m_worker)
db.session.add(action_pic)
db.session.add_all(cam_params)
db.session.add(notifier_email)
db.session.add_all(email_params)
db.session.add(sensor_gpio)
db.session.add(sensor_tcp)
db.session.add(sensor_temp)
db.session.add_all(sensor1_params)
db.session.add_all(sensor2_params)
db.session.add_all(sensor3_params)

db.session.commit()

zone_gpio = db.objects.Zone(name="gpio")
zone_tcp = db.objects.Zone(name="tcp")

zone_gpio.sensors = [sensor_gpio, sensor_temp]
zone_tcp.sensors = [sensor_tcp]


set_gpio = db.objects.Setup(name="gpio set")
set_all = db.objects.Setup(name="tcp set")

set_gpio.zones = [zone_gpio]
set_all.zones = [zone_gpio, zone_tcp]


db.session.add_all([
	db.objects.LogEntry(level=utils.LEVEL_DEBUG, sender="Test", message="Debug test log entry"),
	db.objects.LogEntry(level=utils.LEVEL_INFO, sender="Test", message="Info test log entry"),
	db.objects.LogEntry(level=utils.LEVEL_WARN, sender="Test", message="Warn test log entry"),
	db.objects.LogEntry(level=utils.LEVEL_ERR, sender="Test", message="Error test log entry")
])


db.session.add(zone_gpio)
db.session.add(zone_tcp)
db.session.add(set_all)
db.session.add(set_gpio)

db.session.commit();


#win_sensor = db.session.query(db.objects.Sensor).get(3)
#print win_sensor
#win_sensor.gpio_pin = 17

#db.session.commit()
