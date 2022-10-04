import logging
import time

from secpi.model import constants
from secpi.model.action import Action, ActionResponse, FileResponse

logger = logging.getLogger(__name__)


class TestAction(Action):
    def __init__(self, identifier, params, worker):
        super(TestAction, self).__init__(identifier, params, worker)

        logger.debug("Test Action initialized")

    def execute(self):
        """
        Execute the action. This is just an example implementation.
        """

        # Decode parameters.
        message_in = self.params.get("msg")

        # Run the main body of the action.
        self.info("Executing Test Action")
        if message_in:
            message_out = f"Test Action message: {message_in}"
            self.info(message_out)
        else:
            self.error("Test Action: No message given")

        # Optionally, add more data in the form of file artefacts.
        try:
            logger.info("Creating file artefacts in memory")
            return self.create_file_artefacts()
        except Exception:
            logger.exception("Failed creating file artefacts")

    def create_file_artefacts(self):
        """
        Create a few files which will be shipped to the worker and finally the notifiers.
        """

        response = ActionResponse()
        response.add(FileResponse(name="index.txt", payload="Alarm report index file"))
        response.add(FileResponse(name="index.json", payload='{"description": "Alarm report index file"}'))
        response.add(FileResponse(name="index.xml", payload="<description>Alarm report index file</description>"))

        for index in range(1, 3):
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            filename = f"{timestamp}_{index}.txt"
            response.add(FileResponse(name=filename, payload=f"File content: {index}"))

        return response

    def info(self, message):
        """
        Submit an INFO log message both to the worker and the log output.
        """
        self.post_log(message, constants.LEVEL_INFO)
        # logger.info(message)

    def error(self, message):
        """
        Submit an ERROR log message both to the worker and the log output.
        """
        self.post_err(message)
        # logger.error(message)

    def cleanup(self):
        """
        Run any procedure needed to tear down the action.
        """
        logger.debug("Test Action cleanup")
