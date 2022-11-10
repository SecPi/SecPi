import logging
import os
import typing as t

import pymysql
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

        # FIXME: The current data model is not 100% compatible with SQLAlchemy SQLite+MySQL,
        #        because it violates foreign key constraints on the relationship between
        #        {`Action`, `Notifier`, `Sensor`} and `Param` entities.
        #        See also: https://github.com/isarengineering/SecPi/issues/37
        #
        # ERROR:
        #
        #   sqlalchemy.exc.IntegrityError: (pymysql.err.IntegrityError)
        #   Cannot add or update a child row: a foreign key constraint fails (1452)
        #   `params` CONSTRAINT `lalala` FOREIGN KEY (`object_id`) REFERENCES `{actions,sensors,notifiers}` (`id`))'
        #
        # SOLUTION / WORKAROUND:
        #
        #   Disable foreign key checks on MySQL/MariaDB.

        if self.uri.startswith("mysql"):
            self.engine.execute("SET FOREIGN_KEY_CHECKS = 0;")

        create_session = sessionmaker(bind=self.engine)
        self.session = create_session()

        return self

    def setup(self):
        dbmodel.setup(self.engine)
        return self

    def create_database(self):
        if self.uri.startswith("mysql"):
            dbconfig = make_url(self.uri)
            conn = pymysql.connect(host=dbconfig.host, user=dbconfig.username, password=dbconfig.password)
            cursor = conn.cursor()
            cursor.execute(query=f"DROP DATABASE IF EXISTS `{dbconfig.database}`;")
            cursor.execute(query=f"CREATE DATABASE IF NOT EXISTS `{dbconfig.database}`;")
            cursor.execute(
                query=f"GRANT ALL PRIVILEGES ON `{dbconfig.database}`.* "
                f"TO 'secpi'@'localhost' IDENTIFIED BY 'secret';"
            )
            cursor.execute(
                query=f"GRANT ALL PRIVILEGES ON `{dbconfig.database}`.* " f"TO 'secpi'@'%' IDENTIFIED BY 'secret';"
            )
            cursor.close()
            conn.close()
        return self
