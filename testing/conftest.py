import sys
import time

import pytest
import worker.worker

from testing.util.process import capturing_run


@pytest.fixture(scope="function")
def worker_daemon(capsys):
    sys.argv = ["secpi-worker", "--app-config=testing/etc/config-worker.json"]
    proc = capturing_run(target=worker.worker.main, args=())
    time.sleep(0.85)
    yield proc
    proc.terminate()
