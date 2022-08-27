import multiprocessing
import os
import subprocess
import sys
import tempfile
import time
import typing as t

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

    def shutdown(self):
        """
        Send shutdown signal to make the service terminate itself.
        """
        command = """echo '{"action": "shutdown"}' | amqp-publish --routing-key=secpi-op-1"""
        subprocess.check_output(command, shell=True)
        self.process.join(timeout=4.2)

    def read_log(self):
        self.logfile.seek(0)
        return self.logfile.read().decode("utf-8")
