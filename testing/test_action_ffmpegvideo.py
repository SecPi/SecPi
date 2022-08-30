import pytest

from tools.action import Action
from tools.utils import load_class


@pytest.fixture(scope="function")
def ffmpegvideo_action(fs, worker_mock) -> Action:
    """
    Provide the test cases with a `FFMPEGVideo` instance, where its Worker is mocked.
    """

    fs.create_dir("/path/to/ffmpeg/spool")

    # Configure action.
    component = load_class("worker.ffmpegvideo", "FFMPEGVideo")
    parameters = {
        "url": "https://webcam.example.org/path/to/stream.mp4",
        "data_path": "/path/to/ffmpeg/spool",
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
    assert "Loading class successful: worker.ffmpegvideo.FFMPEGVideo" in setup_messages
    assert "FFMPEGVideo: Starting" in setup_messages
    assert "FFMPEGVideo: Trying to take pictures" in caplog.messages
    assert "FFMPEGVideo: Finished taking pictures" in caplog.messages
    assert "FFMPEGVideo: No cleanup necessary at the moment" in caplog.messages
