import typing as t
from enum import Enum

import pymysql
import pytest
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session

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
from secpi.util.database import DatabaseAdapter


class SqlAlchemyWrapper:
    """
    Database wrapper for test infrastructure.
    Provides database and SQLAlchemy session to the test cases.
    """

    def __init__(self, uri: str):
        self.uri: str = uri
        self.engine: t.Optional[Engine] = None
        self.session: t.Optional[Session] = None
        self.setup()

    def setup(self):
        if self.uri.startswith("mysql"):
            # FIXME: Use `host`, `user`, `password`, and `dbname` from DB URI.
            dbname = "secpi_testdrive"
            conn = pymysql.connect(host="localhost", user="root", password="secret")
            cursor = conn.cursor()
            cursor.execute(query=f"DROP DATABASE IF EXISTS `{dbname}`;")
            cursor.execute(query=f"CREATE DATABASE IF NOT EXISTS `{dbname}`;")
            cursor.execute(query="grant all privileges on"
                                 " secpi_testdrive.* TO 'secpi'@'localhost' identified by 'secret';")
            cursor.execute(query="grant all privileges on secpi_testdrive.* TO 'secpi'@'%' identified by 'secret';")
            cursor.close()
            conn.close()
        self.session: Session = self.session_factory()

    def session_factory(self) -> Session:
        """
        Create the SQLAlchemy session.
        """
        dba = DatabaseAdapter(uri=self.uri)
        dba.connect()
        self.engine = dba.engine
        self.session = dba.session
        Base.metadata.create_all(self.engine)
        return self.session

    def commit_and_flush(self):
        """
        Shortcut function to commit, flush, and expire/expunge objects to/from the SQLAlchemy session.
        """
        self.session.commit()
        self.session.flush()
        self.session.expire_all()
        self.session.expunge_all()
        self.session.close()

    @staticmethod
    def mysql_drop_all_tables(dbname):
        """
        Drop all tables in MySQL/MariaDB database.
        """

        # Connect to database.
        conn = pymysql.connect(host="localhost", user="secpi", password="secret")
        conn.select_db(dbname)

        # Inquire database schema for table names.
        cursor = conn.cursor()
        cursor.execute(
            query=f"""
        SELECT concat('DROP TABLE IF EXISTS `', table_name, '`;')
        FROM information_schema.tables
        WHERE table_schema = '{dbname}';
                """
        )

        # Build statements for dropping all tables.
        statements = []
        statements += ["SET FOREIGN_KEY_CHECKS = 0;"]
        statements += [item[0] for item in cursor.fetchall()]
        # statements += ["SET FOREIGN_KEY_CHECKS = 1;"]

        # Run all drop table statements.
        for statement in statements:
            conn.query(sql=statement)

        conn.close()

    def __del__(self):
        """
        Close and dispose SQLAlchemy session and engine.
        """
        if self.session is not None:
            self.session.close()
        if self.engine is not None:
            self.engine.dispose()


class DbType(Enum):
    """
    Database URIs to enumerate for all the test cases.
    """

    SQLITE = "sqlite:///:memory:"
    MYSQL = "mysql+pymysql://secpi:secret@localhost/secpi_testdrive"


@pytest.fixture(params=(DbType.SQLITE, DbType.MYSQL))
def db(request):
    """
    Provide the database wrapper to the test cases.
    """
    uri = request.param.value
    try:
        return SqlAlchemyWrapper(uri=uri)
    except Exception as ex:
        raise pytest.skip(f"Skipping tests for MySQL/MariaDB. Server not running. Reason: {ex}")


def test_dbmodel_setup_zone_worker_sensor(db):
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
    db.session.add_all([setup, zone, worker, sensor])
    db.commit_and_flush()

    # Query database and verify outcome.
    assert (
        str(db.session.query(Setup).first())
        == "Setup(id=1000, name=testdrive-setup, zones=[Zone(id=2000, name=testdrive-zone)])"
    )

    assert (
        str(db.session.query(Sensor).first())
        == "Sensor(id=4000, name=testdrive-sensor-4000, zone=Zone(id=2000, name=testdrive-zone), "
        "worker=Worker(id=3000, name=testdrive-worker, address=127.0.0.1))"
    )


def test_dbmodel_sensor_parameters(db):
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
    db.session.add(sensor)
    db.commit_and_flush()

    # Query database and verify outcome.
    sensor = db.session.query(Sensor).first()
    assert str(sensor) == "Sensor(id=4001, name=testdrive-sensor-4001, zone=None, worker=None)"

    assert list(map(str, sensor.params)) == [
        "Param(id=1, object_type=sensor, object_id=4001, key=foo, value=bar)",
        "Param(id=2, object_type=sensor, object_id=4001, key=baz, value=qux)",
    ]


def test_dbmodel_action_notifier_parameters(db):
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
    db.session.add_all([action, notifier])
    db.commit_and_flush()

    # Query database and verify outcome.

    action = db.session.query(Action).first()
    assert str(action) == "Action(id=5000, name=testdrive-action-5000, module=test_module cl=TestAction)"
    assert list(map(str, action.params)) == [
        "Param(id=1, object_type=action, object_id=5000, key=action-foo, value=action-bar)",
        "Param(id=2, object_type=action, object_id=5000, key=action-baz, value=action-qux)",
    ]

    notifier = db.session.query(Notifier).first()
    assert str(notifier) == "Notifier(id=6000, name=testdrive-notifier-6000, module=test_module cl=TestNotifier)"
    assert list(map(str, notifier.params)) == [
        "Param(id=3, object_type=notifier, object_id=6000, key=notifier-foo, value=notifier-bar)",
        "Param(id=4, object_type=notifier, object_id=6000, key=notifier-baz, value=notifier-qux)",
    ]
