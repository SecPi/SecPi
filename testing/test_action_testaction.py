import tempfile
from unittest.mock import call

import pytest

from secpi.model.action import Action
from secpi.util.common import load_class
from testing.util.common import clear_directory

DATA_PATH = tempfile.TemporaryDirectory()


@pytest.fixture(scope="function")
def testaction_action(worker_mock) -> Action:
    """
    Provide the test cases with a `TestAction` instance, where its Worker is mocked.
    """

    clear_directory(DATA_PATH.name)

    # Configure action.
    component = load_class("secpi.action.test", "TestAction")
    parameters = {
        "msg": "Franz jagt im komplett verwahrlosten Taxi quer durch Bayern.",
        "data_path": DATA_PATH.name,
    }

    # Create action instance.
    action: Action = component(id=99, params=parameters, worker=worker_mock)

    yield action


def test_action_testaction(testaction_action, caplog):
    """
    Invoke the `TestAction` and check log output for correctness.
    """

    # Invoke action.
    testaction_action.execute()
    testaction_action.cleanup()

    # Verify the right calls would have been made to the Worker.
    assert testaction_action.worker.mock_calls == [
        call.post_log("Executing Test Action", 50),
        call.post_log("Test Action message: Franz jagt im komplett verwahrlosten Taxi quer durch Bayern.", 50),
    ]

    # Verify log output matches the expectations.
    setup_messages = [r.getMessage() for r in caplog.get_records(when="setup")]
    assert "Loading class successful: secpi.action.test.TestAction" in setup_messages
    assert "Test Action initialized" in setup_messages
    assert "Creating file artefacts at" in caplog.text
    assert "Test Action cleanup" in caplog.messages
