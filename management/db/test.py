from sqlalchemy.orm import sessionmaker
import objects

Session = sessionmaker(bind=objects.engine)
session = Session()

'''
session.add_all([
	objects.Sensor(name="door IR sensor", gpio_pin=15, description="this is the infrared sensor at the door"),
	objects.Sensor(name="door contact sensor", gpio_pin=16, description="this is the contact sensor at the door"),
	objects.Sensor(name="window contact sensor", gpio_pin=15, description="this is the contact sensor at the window")
	])

session.commit();
'''

sensors = session.query(objects.Sensor).all()
print sensors

#win_sensor = session.query(objects.Sensor).get(3)
#print win_sensor
#win_sensor.gpio_pin = 17

#session.commit()