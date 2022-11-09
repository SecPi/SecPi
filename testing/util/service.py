import abc
import multiprocessing
import subprocess
import tempfile
import time
import typing as t
from pathlib import Path

import requests

import secpi.manager
import secpi.webinterface
import secpi.worker
from secpi.model.settings import StartupOptions
from secpi.util.database import DatabaseAdapter


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
        Path(self.logfile.name).unlink(missing_ok=True)

    @abc.abstractmethod
    def shutdown(self, identifier: str):
        raise NotImplementedError("Please implement `shutdown`")

    def start_process(self, name: str, app_config: str, target: t.Callable):

        options = StartupOptions(
            app_config=app_config, logging_config="etc/testing/logging.conf", log_file=self.logfile.name
        )

        self.process = multiprocessing.Process(target=target, kwargs={"options": options})
        self.process.start()

        # Make sure the service is ready.
        # TODO: How to improve this? Look for a specific marking in the log output?
        time.sleep(0.75)

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

        # TODO: Read database URI from application configuration file.
        #       Otherwise, pass "create_schema=True" through `start_process` or app config.
        #       However, this might be dangerous?
        # DatabaseAdapter(uri="sqlite:///secpi-database-testing.sqlite").connect().setup()
        DatabaseAdapter(uri="mysql+pymysql://secpi:secret@localhost/secpi-testdrive").connect().setup()
        self.start_process(
            name="secpi-manager",
            app_config="etc/testing/config-manager.toml",
            target=secpi.manager.main,
        )
        # Manager needs a bit longer to start?
        # time.sleep(0.25)


class WorkerServiceWrapper(AmqpServiceWrapper):
    def run(self):
        self.start_process(
            name="secpi-worker",
            app_config="etc/testing/config-worker.toml",
            target=secpi.worker.main,
        )
        # time.sleep(0.25)


class WebinterfaceServiceWrapper(BaseServiceWrapper):

    BASEURL = "http://localhost:16677"

    def run(self):
        self.start_process(
            name="secpi-web",
            app_config="etc/testing/config-web.toml",
            target=secpi.webinterface.main,
        )

        # Web server needs a bit longer to start than AMQP-based service.
        time.sleep(0.50)

    def shutdown(self, identifier: t.Optional[str] = None):
        """
        Shut down service over HTTP.
        """

        # 1. Send shutdown signal to make the service terminate itself.
        try:
            requests.post(url=f"{self.BASEURL}/operational", json={"action": "shutdown"})
        except Exception as ex:
            if "Connection aborted" not in str(ex) and "Max retries exceeded" not in str(ex):
                raise
        time.sleep(0.25)
        self.wait_for_process()

        # 2. Terminate service process.
        # In this case, the process will not record code coverage information.
        time.sleep(0.25)
        self.terminate()
