import pytest

from secpi.model.action import Action
from secpi.util.common import load_class


@pytest.fixture(scope="function")
def speaker_action(worker_mock) -> Action:
    """
    Provide the test cases with a `Speaker` instance, where its Worker is mocked.
    """

    # Configure action.
    component = load_class("secpi.action.speaker", "Speaker")
    parameters = {
        "path_to_audio": "/path/to/elise.mp3",
        "repetitions": "0",
    }

    # Create action instance.
    action: Action = component(identifier=99, params=parameters, worker=worker_mock)

    yield action


def test_action_speaker(mocker, speaker_action, caplog):
    """
    Invoke the `Speaker` and check log output for correctness.
    """

    # Only pretend.
    mocker.patch("pygame.mixer")

    # Invoke action.
    speaker_action.execute()
    speaker_action.cleanup()

    # Verify log output matches the expectations.
    setup_messages = [r.getMessage() for r in caplog.get_records(when="setup")]
    assert "Loading class successful: secpi.action.speaker.Speaker" in setup_messages
    assert "Speaker: Audio device initialized" in setup_messages
    assert "Speaker: Trying to play audio" in caplog.messages
    assert "Speaker: Finished playing audio" in caplog.messages
