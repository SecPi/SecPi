import dataclasses
import typing as t
from datetime import datetime

from secpi.util.common import DataContainer, check_late_arrival


@dataclasses.dataclass
class AlarmMessage(DataContainer):
    """
    Message used to signal an alarm.
    """

    sensor_id: int
    worker_id: int
    message: str
    datetime: datetime
    holddown: t.Optional[bool] = None
    # alarm_id: str  # Do we need it?

    @property
    def late_arrival(self):
        """
        Whether the alarm is a LATE alarm, which has not been delivered in time.

        # TODO: Memoize?
        """
        return check_late_arrival(self.datetime)

    def get_label(self, with_space=True):
        """
        Produce a label based on `late_arrival` and `holddown` flags.
        """

        labels = []
        if self.holddown:
            labels.append("MUTE")
        if self.late_arrival:
            labels.append("LATE")

        label = "+".join(labels)
        if label:
            label = f"[{label}]"
        if label and with_space:
            label += " "
        return label

    def render_message(self):
        """
        Render amended alarm message based on `late_arrival` and `holddown` flags.
        """
        return f"{self.get_label()}{self.message}"


@dataclasses.dataclass
class NotificationMessage(DataContainer):
    """
    Message used to signal a notification.
    """

    sensor_name: str
    worker_name: str
    alarm: AlarmMessage
    payload: t.Optional[bytearray] = None


@dataclasses.dataclass
class ActionRequestMessage(DataContainer):
    """
    Message used to run an action.
    """

    msg: str
    datetime: datetime
    alarm: AlarmMessage
