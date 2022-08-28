import pytest

from testing.util.service import ServiceWrapper
from tools.utils import setup_logging


setup_logging()


@pytest.fixture(scope="function")
def manager_service():

    # Run Manager service.
    service = ServiceWrapper()
    service.run_manager()

    # Hand over to test case.
    yield service

    # Signal the service to shut down.
    service.shutdown(identifier="m")


@pytest.fixture(scope="function")
def worker_service():

    # Run Worker service.
    service = ServiceWrapper()
    service.run_worker()

    # Hand over to test case.
    yield service

    # Signal the service to shut down.
    service.shutdown(identifier="1")
