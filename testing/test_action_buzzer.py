import pytest
from surrogate import surrogate

from tools.action import Action
from tools.utils import load_class


@pytest.fixture(scope="function")
def buzzer_action(worker_mock, mocker) -> Action:
    """
    Provide the test cases with a `Buzzer` instance, where its Worker is mocked.
    """

    # Configure action.
    with surrogate("RPi.GPIO"):
        mocker.patch("RPi.GPIO")
        component = load_class("worker.buzzer", "Buzzer")
    parameters = {
        "gpio_pin": "42",
        "duration": "0",
    }

    # Create action instance.
    action: Action = component(id=99, params=parameters, worker=worker_mock)

    yield action


def test_action_buzzer(buzzer_action, caplog):
    """
    Invoke the `Buzzer` and check log output for correctness.
    """

    # Invoke action.
    buzzer_action.execute()
    buzzer_action.cleanup()

    # Verify log output matches the expectations.
    setup_messages = [r.getMessage() for r in caplog.get_records(when="setup")]
    assert "Loading class successful: worker.buzzer.Buzzer" in setup_messages
    assert "Buzzer: Audio device initialized" in setup_messages
    assert "Buzzer: Trying to make some noise" in caplog.messages
    assert "Buzzer: Finished making noise" in caplog.messages
