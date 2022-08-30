import pathlib
import subprocess

import pytest

from secpi.util.common import setup_logging
from secpi.util.config import ApplicationConfig
from secpi.worker import Worker
from testing.util.service import (
    ManagerServiceWrapper,
    WebinterfaceServiceWrapper,
    WorkerServiceWrapper,
)

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


@pytest.fixture(scope="function", autouse=True)
def drain_amqp():
    """
    Drain relevant AMQP queues to have a fresh environment.
    """

    # Remove all messages from AMQP queues.
    # TODO: Implement more efficiently in pure Python.
    queues = ["secpi-op-1", "secpi-op-m", "secpi-init_config", "secpi-config-1", "secpi-alarm", "secpi-log"]
    for queue in queues:
        command = f"amqp-get --queue={queue} > /dev/null 2>&1"
        process = subprocess.run(command, shell=True)
        if process.returncode not in [1, 2]:
            process.check_returncode()


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
    worker = mocker.patch("secpi.worker.Worker", autospec=True)
    worker_instance = worker.return_value

    app_config = ApplicationConfig()
    worker_instance.config = app_config

    yield worker_instance
