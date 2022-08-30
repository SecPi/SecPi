import logging
import typing as t

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from tools.db import objects

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
        logger.info(f"Connecting to database {self.uri}")
        # `echo = True` activates debug logging.
        # TODO: think about `check_same_thread=False`
        self.engine = create_engine(self.uri, connect_args={"check_same_thread": False}, echo=False)

        create_session = sessionmaker(bind=self.engine)
        self.session = create_session()

        return self

    def setup(self):
        objects.setup(self.engine)
        return self
