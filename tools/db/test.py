from sqlalchemy.orm import sessionmaker
import database as db




db.session.add_all([
	db.objects.Sensor(name="door IR sensor", gpio_pin=15, description="this is the infrared sensor at the door"),
	db.objects.Sensor(name="door contact sensor", gpio_pin=16, description="this is the contact sensor at the door"),
	db.objects.Sensor(name="window contact sensor", gpio_pin=17, description="this is the contact sensor at the window")
	])


zone_door = db.objects.Zone(name="door")
zone_window = db.objects.Zone(name="windows")

db.session.commit();

doors = db.session.query(db.objects.Sensor).filter(db.objects.Sensor.name.like('%door%')).all()
zone_door.sensors = doors

windows = db.session.query(db.objects.Sensor).filter(db.objects.Sensor.name.like('%window%')).all()
zone_window.sensors = windows

db.session.commit()

set_away = db.objects.Setup(name="away")
set_home = db.objects.Setup(name="at home")

set_away.zones = [zone_door, zone_window]
set_home.zones = [zone_window]

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