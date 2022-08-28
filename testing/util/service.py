import abc
import multiprocessing
import os
import subprocess
import sys
import tempfile
import time
import typing as t

import requests

import manager.manager
import webinterface.main
import worker.worker


class BaseServiceWrapper:
    """
    Run Manager, Worker, or Webinterface service for testing purposes.
    Log output will be saved to a file, so it can be read back later
    for verification.
    """

    def __init__(self):
        # Create temporary log file.
        self.logfile = tempfile.NamedTemporaryFile(delete=False)
        self.process: t.Optional[multiprocessing.Process] = None

    def __del__(self):
        self.logfile.close()
        os.unlink(self.logfile.name)

    @abc.abstractmethod
    def shutdown(self, identifier: str):
        raise NotImplementedError("Please implement `shutdown`")

    def start_process(self, name: str, app_config: str, target: t.Callable):

        sys.argv = [
            name,
            f"--app-config={app_config}",
            "--logging-conf=testing/etc/logging.conf",
            f"--log-file={self.logfile.name}",
        ]

        self.process = multiprocessing.Process(target=target, args=())
        self.process.start()

        # Make sure the service is ready.
        # TODO: How to improve this? Look for a specific marking in the log output?
        time.sleep(0.85)

    def read_log(self):
        self.logfile.seek(0)
        return self.logfile.read().decode("utf-8")

    def wait_for_process(self):
        """
        1. Wait for process to terminate itself.
        """
        self.process.join(timeout=4.2)

    def terminate(self):
        """
        2. Terminate service process.

        In this case, there will be no code coverage information. Because the
        process did not shut down cleanly, it failed to record code coverage.
        """
        self.process.terminate()
        time.sleep(0.05)

        self.process.kill()


class AmqpServiceWrapper(BaseServiceWrapper):

    def shutdown(self, identifier: str):
        """
        Shut down service over AMQP.
        """

        # 1. Send shutdown signal to make the service terminate itself.
        command = """echo '{"action": "shutdown"}' | amqp-publish --routing-key=secpi-op-%s""" % identifier
        subprocess.check_output(command, shell=True)
        self.wait_for_process()

        # 2. Terminate service process.
        # In this case, the process will not record code coverage information.
        self.terminate()


class ManagerServiceWrapper(AmqpServiceWrapper):

    def run(self):
        self.start_process(
            name="secpi-manager",
            app_config="testing/etc/config-manager.json",
            target=manager.manager.main,
        )


class WorkerServiceWrapper(AmqpServiceWrapper):

    def run(self):
        self.start_process(
            name="secpi-worker",
            app_config="testing/etc/config-worker.json",
            target=worker.worker.main,
        )


class WebinterfaceServiceWrapper(BaseServiceWrapper):

    def run(self):
        self.start_process(
            name="secpi-web",
            app_config="testing/etc/config-web.json",
            target=webinterface.main.main,
        )

        # Web server needs a bit longer to start than AMQP-based service.
        time.sleep(0.45)

    def shutdown(self, identifier: t.Optional[str] = None):
        """
        Shut down service over HTTP.
        """

        # 1. Send shutdown signal to make the service terminate itself.
        try:
            requests.post(url="http://localhost:8000/operational", json={"action": "shutdown"})
        except Exception as ex:
            if "Connection aborted" not in str(ex) and "Max retries exceeded" not in str(ex):
                raise
        time.sleep(0.25)
        self.wait_for_process()

        # 2. Terminate service process.
        # In this case, the process will not record code coverage information.
        time.sleep(0.25)
        self.terminate()
