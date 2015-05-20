from sqlalchemy.orm import sessionmaker
import objects

Session = sessionmaker(bind=objects.engine)
session = Session()

'''
session.add_all([
	objects.Sensor(name="door IR sensor", gpio_pin=15, description="this is the infrared sensor at the door"),
	objects.Sensor(name="door contact sensor", gpio_pin=16, description="this is the contact sensor at the door"),
	objects.Sensor(name="window contact sensor", gpio_pin=17, description="this is the contact sensor at the window")
	])

zone_door = objects.Zone(name="door")
zone_window = objects.Zone(name="windows")

session.commit();

doors = session.query(objects.Sensor).filter(objects.Sensor.name.like('%door%')).all()
zone_door.sensors = doors

windows = session.query(objects.Sensor).filter(objects.Sensor.name.like('%window%')).all()
zone_window.sensors = windows

session.commit()

set_away = objects.Set(name="away")
set_home = objects.Set(name="at home")

set_away.zones = [zone_door, zone_window]
set_home.zones = [zone_window]

session.commit();
'''

sensors = session.query(objects.Sensor).all()
print sensors

zones = session.query(objects.Zone).all()
print zones

sets = session.query(objects.Set).all()
print sets

#win_sensor = session.query(objects.Sensor).get(3)
#print win_sensor
#win_sensor.gpio_pin = 17

#session.commit()