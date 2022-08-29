import pathlib

import pytest

from testing.util.service import ManagerServiceWrapper, WorkerServiceWrapper, WebinterfaceServiceWrapper
from tools.utils import setup_logging


setup_logging()


@pytest.fixture(scope="function", autouse=True)
def reset_database():
    p = pathlib.Path("secpi-database-testing.sqlite")
    try:
        p.unlink(missing_ok=True)

    # Compatibility with Python 3.7.
    except TypeError:
        try:
            p.unlink()
        except:
            pass


@pytest.fixture(scope="function")
def manager_service():

    # Run Manager service.
    service = ManagerServiceWrapper()
    service.run()

    # Hand over to test case.
    yield service

    # Signal the service to shut down.
    service.shutdown(identifier="m")


@pytest.fixture(scope="function")
def worker_service():

    # Run Worker service.
    service = WorkerServiceWrapper()
    service.run()

    # Hand over to test case.
    yield service

    # Signal the service to shut down.
    service.shutdown(identifier="1")


@pytest.fixture(scope="function")
def webinterface_service():

    # Run Worker service.
    service = WebinterfaceServiceWrapper()
    service.run()

    # Hand over to test case.
    yield service

    # Signal the service to shut down.
    service.shutdown()
