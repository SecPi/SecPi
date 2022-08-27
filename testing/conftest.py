import time

import pytest

from testing.util.service import ServiceWrapper
from tools.utils import setup_logging


setup_logging()


@pytest.fixture(scope="function")
def worker_service():

    service = ServiceWrapper()
    service.run_worker()

    yield service

    # 1. Send shutdown signal to make the service terminate itself.
    service.shutdown()

    # 2. Terminate service process.
    # In this case, there will be no code coverage information. Because the process did
    # not shut down cleanly, it failed to record it.
    service.process.terminate()
