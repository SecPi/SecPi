import logging
import os
import typing as t

import psycopg2
import pymysql
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine, make_url
from sqlalchemy.orm import Session, sessionmaker

from secpi.model import dbmodel

logger = logging.getLogger(__name__)


class DatabaseAdapter:
    """
    Connect to database.
    """

    def __init__(self, uri):
        self.uri = uri

        self.engine: t.Optional[Engine] = None
        self.session: t.Optional[Session] = None

    def connect(self):

        # Feed a newline to the logger when running the test suite.
        if "PYTEST_CURRENT_TEST" in os.environ:
            logger.info("")

        logger.info(f"Connecting to database {self.uri}")

        # `echo = True` activates debug logging.
        self.engine = create_engine(self.uri, echo=False)

        # FIXME: Because there might be stray alarm signals, arriving late, e.g. when the database just has
        #        been freshly re-created already, the test cases will trigger foreign key constraint violations,
        #        when inserting `Alarm` records, because the corresponding `Sensor` entities are missing.
        """
        
        ERROR:
        
          sqlalchemy.exc.IntegrityError: (pymysql.err.IntegrityError)
          (1452, 'Cannot add or update a child row: a foreign key constraint fails
          (`secpi-testdrive`.`alarms`, CONSTRAINT `alarms_ibfk_1` FOREIGN KEY (`sensor_id`) REFERENCES `sensors` (`id`))')
          [SQL: INSERT INTO alarms (alarmtime, ack, sensor_id, message) VALUES (%(alarmtime)s, %(ack)s, %(sensor_id)s, %(message)s)]
          [parameters: {'alarmtime': datetime.datetime(2022, 11, 10, 10, 50, 36, 471869), 'ack': 0, 'sensor_id': 1, 'message': '[LATE] Got TCP connection, raising alarm'}]
        
        SOLUTION / WORKAROUND:
        
          Disable foreign key checks on MySQL/MariaDB, when running the test harness.
        """  # noqa: E501

        if "PYTEST_CURRENT_TEST" in os.environ and self.uri.startswith("mysql"):
            self.engine.execute("SET FOREIGN_KEY_CHECKS = 0;")

        create_session = sessionmaker(bind=self.engine)
        self.session = create_session()

        return self

    def setup(self):
        dbmodel.setup(self.engine)
        return self

    def drop_and_create_database(self):
        if self.uri.startswith("mysql"):
            dbconfig = make_url(self.uri)
            conn = pymysql.connect(host=dbconfig.host, user=dbconfig.username, password=dbconfig.password)
            cursor = conn.cursor()
            logger.info(f"Re-creating database {dbconfig.database}")
            cursor.execute(query=f"DROP DATABASE IF EXISTS `{dbconfig.database}`;")
            cursor.execute(query=f"CREATE DATABASE IF NOT EXISTS `{dbconfig.database}`;")
            cursor.close()
            conn.close()
        elif self.uri.startswith("postgre"):
            logger.info(f"Re-creating database with {self.uri}")
            dbconfig = make_url(self.uri)
            conn = psycopg2.connect(host=dbconfig.host, user=dbconfig.username, password=dbconfig.password)
            conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
            cursor = conn.cursor()
            logger.info(f"Re-creating database {dbconfig.database}")
            cursor.execute(query=f'DROP DATABASE IF EXISTS "{dbconfig.database}";')
            cursor.execute(query=f'CREATE DATABASE "{dbconfig.database}";')
            cursor.close()
            conn.close()
        return self
