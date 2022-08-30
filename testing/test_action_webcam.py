from unittest.mock import Mock

import pytest
from surrogate import surrogate

from secpi.model.action import Action
from secpi.util.common import load_class


@pytest.fixture(scope="function")
def webcam_action(mocker, worker_mock) -> Action:
    """
    Provide the test cases with a `Webcam` instance, where its Worker is mocked.
    """

    # Mask OpenCV2 completely.
    # ImportError: libGL.so.1: cannot open shared object file: No such file or directory
    with surrogate("cv2.bootstrap"):
        mocker.patch("pygame._camera_opencv.CameraMac", autospec=True)

        # Configure action.
        component = load_class("worker.webcam", "Webcam")

        parameters = {
            "path": "/dev/to/webcam",
            "data_path": "/path/to/webcam/data",
            "count": "0",
            "interval": "0",
            "resolution_x": "640",
            "resolution_y": "480",
        }

        # Create action instance.
        action: Action = component(id=99, params=parameters, worker=worker_mock)

        yield action


def test_action_webcam(webcam_action, caplog):
    """
    Invoke the `Webcam` and check log output for correctness.
    """

    webcam_action.cam = Mock()

    # Invoke action.
    webcam_action.execute()
    webcam_action.cleanup()

    # Verify log output matches the expectations.
    setup_messages = [r.getMessage() for r in caplog.get_records(when="setup")]
    assert "Loading class successful: worker.webcam.Webcam" in setup_messages
    assert "Webcam: Video device initialized: /dev/to/webcam" in setup_messages
    assert "Webcam: Trying to take pictures" in caplog.messages
    assert "Webcam: Finished taking pictures" in caplog.messages
    assert "Webcam: No cleanup necessary at the moment" in caplog.messages
