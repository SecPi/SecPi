import pytest

from secpi.model.action import Action
from secpi.util.common import load_class


@pytest.fixture(scope="function")
def ffmpegvideo_action(worker_mock) -> Action:
    """
    Provide the test cases with a `FFMPEGVideo` instance, where its Worker is mocked.
    """

    # Configure action.
    component = load_class("secpi.action.ffmpegvideo", "FFMPEGVideo")
    parameters = {
        "url": "https://webcam.example.org/path/to/stream.mp4",
        "count": "0",
        "interval": "0",
    }

    # Create action instance.
    action: Action = component(id=99, params=parameters, worker=worker_mock)

    yield action


def test_action_ffmpegvideo(ffmpegvideo_action, caplog):
    """
    Invoke the `FFMPEGVideo` and check log output for correctness.
    """

    # Invoke action.
    ffmpegvideo_action.execute()
    ffmpegvideo_action.cleanup()

    # Verify log output matches the expectations.
    setup_messages = [r.getMessage() for r in caplog.get_records(when="setup")]
    assert "Loading class successful: secpi.action.ffmpegvideo.FFMPEGVideo" in setup_messages
    assert "FFMPEGVideo: Initializing" in setup_messages
    assert "FFMPEGVideo: Starting to capture images" in caplog.messages
    assert "FFMPEGVideo: Capturing images to" in caplog.text
    assert "FFMPEGVideo: Finished capturing images" in caplog.messages
    assert "FFMPEGVideo: No cleanup necessary at the moment" in caplog.messages
