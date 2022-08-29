import pathlib

import pytest

from testing.util.service import ManagerServiceWrapper, WorkerServiceWrapper, WebinterfaceServiceWrapper
from tools.config import ApplicationConfig
from tools.utils import setup_logging
from worker.worker import Worker

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


@pytest.fixture(scope="function")
def worker_mock(mocker) -> Worker:
    """
    Provide the test cases with a mocked SecPi Worker, but using a real `ApplicationConfig` instance.
    """
    worker = mocker.patch("worker.worker.Worker", autospec=True)
    worker_instance = worker.return_value

    app_config = ApplicationConfig()
    worker_instance.config = app_config

    yield worker_instance
