import multiprocessing
import os
import subprocess
import sys
import tempfile
import time
import typing as t

import manager.manager
import worker.worker


class ServiceWrapper:
    """
    Run Manager, Worker, or Webinterface service for testing purposes.
    Log output will be saved to a file so it can be read back later for verification.
    """

    def __init__(self):
        # Create temporary log file.
        self.logfile = tempfile.NamedTemporaryFile(delete=False)
        self.process: t.Optional[multiprocessing.Process] = None

    def __del__(self):
        self.logfile.close()
        os.unlink(self.logfile.name)

    def run_manager(self):

        sys.argv = [
            "secpi-manager",
            "--app-config=testing/etc/config-manager.json",
            "--logging-conf=testing/etc/logging.conf",
            f"--log-file={self.logfile.name}",
        ]

        self.process = multiprocessing.Process(target=manager.manager.main, args=())
        self.process.start()

        # Make sure the service is ready.
        # TODO: How to improve this? Look for a specific marking in the log output?
        time.sleep(0.85)

    def run_worker(self):

        sys.argv = [
            "secpi-worker",
            "--app-config=testing/etc/config-worker.json",
            "--logging-conf=testing/etc/logging.conf",
            f"--log-file={self.logfile.name}",
        ]

        self.process = multiprocessing.Process(target=worker.worker.main, args=())
        self.process.start()

        # Make sure the service is ready.
        # TODO: How to improve this? Look for a specific marking in the log output?
        time.sleep(0.85)

    def shutdown(self, identifier: str):
        """
        Send shutdown signal to make the service terminate itself.
        """

        # 1. Send shutdown signal to make the service terminate itself.
        command = """echo '{"action": "shutdown"}' | amqp-publish --routing-key=secpi-op-%s""" % identifier
        subprocess.check_output(command, shell=True)
        time.sleep(0.15)
        self.process.join(timeout=4.2)

        # 2. Terminate service process.
        # In this case, there will be no code coverage information. Because the process did
        # not shut down cleanly, it failed to record it.
        self.process.terminate()
        self.process.kill()

    def read_log(self):
        self.logfile.seek(0)
        return self.logfile.read().decode("utf-8")
