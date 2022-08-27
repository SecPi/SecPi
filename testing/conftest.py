import subprocess
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

    # 1. Send shutdown signal to make the service terminate itself.
    command = """echo '{"action": "shutdown"}' | amqp-publish --routing-key=secpi-op-1"""
    print(subprocess.check_output(command, shell=True), file=sys.stderr)
    time.sleep(0.75)

    # 2. Terminate service process.
    # In this case, there will be no code coverage information. Because the process did
    # not shut down cleanly, it failed to record it.
    proc.terminate()