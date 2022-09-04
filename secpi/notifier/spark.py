import logging

import requests
import requests.exceptions

from secpi.model.message import NotificationMessage
from secpi.model.notifier import Notifier

logger = logging.getLogger(__name__)


class SparkNotifier(Notifier):
    def __init__(self, id, params):
        super(SparkNotifier, self).__init__(id, params)
        if not "personal_token" in params or not "room" in params:
            self.corrupted = True
            logger.error("Token or room name missing")
            return

    def notify(self, info: NotificationMessage):
        if not self.corrupted:
            try:
                logger.debug("Sending Cisco Spark notification")

                # Render the notification message.
                info_str = info.render_message()

                room_name = self.params["room"]
                auth_header = {"Authorization": "Bearer %s" % self.params["personal_token"]}

                # get room id
                rooms_req = requests.get("https://api.ciscospark.com/v1/rooms", headers=auth_header)
                rooms_req.raise_for_status()
                rooms = rooms_req.json()
                room = [r for r in rooms["items"] if r["title"] == room_name]

                if len(room) > 0:
                    # we got a room
                    room_id = room[0]["id"]
                    logger.debug("Got existing room")
                else:
                    # if not exists, create it
                    logger.debug("No room found, creating one")
                    new_room_req = requests.post(
                        "https://api.ciscospark.com/v1/rooms", headers=auth_header, data={"title": room_name}
                    )
                    new_room = new_room_req.json()

                    room_id = new_room["id"]

                if room_id != None:
                    logger.debug("Found room: %s" % room_id)
                    noti_req = requests.post(
                        "https://api.ciscospark.com/v1/messages",
                        headers=auth_header,
                        data={"roomId": room_id, "text": info_str},
                    )

                else:
                    logger.error("No room found")
            except requests.RequestException as ce:
                logger.error("Error in Spark Notifier: %s" % ce)
            except KeyError as ke:
                logger.error("Error in Spark Notifier: %s" % ke)

        else:
            logger.error("Cisco Spark Notifier corrupted. No authorization code or room name given as parameter.")

    def cleanup(self):
        logger.debug("Cisco Spark Notifier: No cleanup necessary at the moment.")
