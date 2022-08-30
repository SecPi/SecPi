import pytest

from secpi.model.action import Action
from secpi.util.common import load_class


@pytest.fixture(scope="function")
def testaction_action(worker_mock) -> Action:
    """
    Provide the test cases with a `TestAction` instance, where its Worker is mocked.
    """

    # Configure action.
    component = load_class("secpi.action.test", "TestAction")
    parameters = {
        "msg": "The message",
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

    # Verify log output matches the expectations.
    setup_messages = [r.getMessage() for r in caplog.get_records(when="setup")]
    assert "Loading class successful: secpi.action.test.TestAction" in setup_messages
    assert "Test Action initialized" in setup_messages
    assert "Executing Test Action" in caplog.messages
    assert "Test Action Message: The message" in caplog.messages
    assert "Test Action Cleanup" in caplog.messages
