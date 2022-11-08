import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from secpi.model.dbmodel import (
    Action,
    Base,
    Notifier,
    Param,
    Sensor,
    Setup,
    Worker,
    Zone,
)


@pytest.fixture
def dbsession() -> Session:
    """
    Provide an SQLAlchemy session to the test cases.
    """
    uri = "sqlite:///:memory:"
    engine = create_engine(uri)
    session = sessionmaker(bind=engine)()
    Base.metadata.create_all(engine)
    return session


def commit_and_flush(dbsession):
    """
    Shortcut function to commit, flush, and expire/expunge objects to/from the SQLAlchemy session.
    """
    dbsession.commit()
    dbsession.flush()
    dbsession.expire_all()
    dbsession.expunge_all()
    dbsession.close()


def test_dbmodel_setup_zone_worker_sensor(dbsession):
    """
    Verify adding `Setup`, `Zone`, `Worker`, and `Sensor` entities.
    """

    # Add some entities.
    setup = Setup(id=1000, name="testdrive-setup", description="Testdrive Setup", active_state=True)
    zone = Zone(id=2000, name="testdrive-zone", description="Testdrive Zone", setups=[setup])
    worker = Worker(
        id=3000, name="testdrive-worker", description="Testdrive Worker", active_state=True, address="127.0.0.1"
    )
    sensor = Sensor(
        id=4000,
        name="testdrive-sensor-4000",
        description="Testdrive Sensor 4000",
        cl="TestSensor",
        module="test_module",
        zone=zone,
        worker=worker,
    )

    # Store to database and flush session.
    dbsession.add_all([setup, zone, worker, sensor])
    commit_and_flush(dbsession)

    # Query database and verify outcome.
    assert (
        str(dbsession.query(Setup).first())
        == "Setup(id=1000, name=testdrive-setup, zones=[Zone(id=2000, name=testdrive-zone)])"
    )

    assert (
        str(dbsession.query(Sensor).first())
        == "Sensor(id=4000, name=testdrive-sensor-4000, zone=Zone(id=2000, name=testdrive-zone), "
        "worker=Worker(id=3000, name=testdrive-worker, address=127.0.0.1))"
    )


def test_dbmodel_sensor_parameters(dbsession):
    """
    Verify adding `Param` items to a `Sensor` entity.
    """

    # Add a `Sensor` entity.
    sensor = Sensor(
        id=4001,
        name="testdrive-sensor-4001",
        description="Testdrive Sensor 4001",
        cl="TestSensor",
        module="test_module",
    )

    # Add some parameters.
    param_foo = Param(object_type="sensor", key="foo", value="bar")
    param_baz = Param(object_type="sensor", key="baz", value="qux")
    sensor.params.append(param_foo)
    sensor.params.append(param_baz)

    # Store to database and flush session.
    dbsession.add(sensor)
    commit_and_flush(dbsession)

    # Query database and verify outcome.
    sensor = dbsession.query(Sensor).first()
    assert str(sensor) == "Sensor(id=4001, name=testdrive-sensor-4001, zone=None, worker=None)"

    assert list(map(str, sensor.params)) == [
        "Param(id=1, object_type=sensor, object_id=4001, key=foo, value=bar)",
        "Param(id=2, object_type=sensor, object_id=4001, key=baz, value=qux)",
    ]


def test_dbmodel_action_notifier_parameters(dbsession):
    """
    Verify adding `Param` items to `Action` and `Notifier` entities.
    """

    def mkparam(object_type, key, value):
        return Param(object_type=object_type, key=f"{object_type}-{key}", value=f"{object_type}-{value}")

    # Add an `Action` entity, with parameters.
    action = Action(
        id=5000,
        name="testdrive-action-5000",
        description="Testdrive Action 5000",
        cl="TestAction",
        module="test_module",
        active_state=True,
        params=[
            mkparam("action", "foo", "bar"),
            mkparam("action", "baz", "qux"),
        ],
    )

    # Add a `Notifier` entity, with parameters.
    notifier = Notifier(
        id=6000,
        name="testdrive-notifier-6000",
        description="Testdrive Notifier 6000",
        cl="TestNotifier",
        module="test_module",
        active_state=True,
        params=[
            mkparam("notifier", "foo", "bar"),
            mkparam("notifier", "baz", "qux"),
        ],
    )

    # Store to database and flush session.
    dbsession.add_all([action, notifier])
    commit_and_flush(dbsession)

    # Query database and verify outcome.

    action = dbsession.query(Action).first()
    assert str(action) == "Action(id=5000, name=testdrive-action-5000, module=test_module cl=TestAction)"
    assert list(map(str, action.params)) == [
        "Param(id=1, object_type=action, object_id=5000, key=action-foo, value=action-bar)",
        "Param(id=2, object_type=action, object_id=5000, key=action-baz, value=action-qux)",
    ]

    notifier = dbsession.query(Notifier).first()
    assert str(notifier) == "Notifier(id=6000, name=testdrive-notifier-6000, module=test_module cl=TestNotifier)"
    assert list(map(str, notifier.params)) == [
        "Param(id=3, object_type=notifier, object_id=6000, key=notifier-foo, value=notifier-bar)",
        "Param(id=4, object_type=notifier, object_id=6000, key=notifier-baz, value=notifier-qux)",
    ]
