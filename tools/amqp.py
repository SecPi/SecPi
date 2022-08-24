import logging
import time
import typing as t

import pika


class AMQPAdapter:
    """
    Connect to AMQP broker and start consuming messages, with reconnect.
    """

    # TODO: Implement exponential backoff.
    CONVERSATION_DELAY = 4.2

    def __init__(self, hostname: str, port: int, username: str, password: str):
        self.hostname = hostname
        self.port = port
        self.username = username
        self.password = password

        self.connection: pika.BaseConnection = None
        self.channel: pika.channel.Channel = None

    def connect(self, retries=None):
        credentials = pika.PlainCredentials(self.username, self.password)
        parameters = pika.ConnectionParameters(
            credentials=credentials,
            host=self.hostname,
            port=self.port,
            socket_timeout=10,
            # ssl=True,
            # ssl_options = {
            # 	"ca_certs":PROJECT_PATH+"/certs/"+config.get('rabbitmq')['cacert'],
            # 	"certfile":PROJECT_PATH+"/certs/"+config.get('rabbitmq')['certfile'],
            # 	"keyfile":PROJECT_PATH+"/certs/"+config.get('rabbitmq')['keyfile']
            # }
        )

        connected = False
        while not connected:
            try:
                logging.info(f"Connecting to AMQP broker at {self.hostname}:{self.port}")
                self.connection = pika.BlockingConnection(parameters=parameters)
                self.channel = self.connection.channel()
                connected = True
                logging.info("Connecting to AMQP broker successful")
            except Exception:
                retry_label = "forever"
                if retries is not None:
                    retry_label = f"for {retries} more times"
                logging.exception(f"Connecting to AMQP broker failed temporarily, retrying {retry_label}")
                time.sleep(self.CONVERSATION_DELAY)

            if retries is not None:
                retries -= 1
                if retries <= 0:
                    raise ConnectionError("Connecting to AMQP broker failed permanently, giving up")

        return connected

    @property
    def available(self):
        return self.connection.is_open

    def disconnect(self):
        try:
            self.channel.close()
        except:
            pass
        try:
            self.connection.close()
        except:
            pass

        self.channel = None
        self.connection = None

    def subscribe_forever(self, on_error: t.Optional[t.Callable] = None):
        good = False
        while True:
            logging.info("Start consuming AMQP queue")
            try:
                # Blocking call.
                if self.available:
                    good = True
                    self.channel.start_consuming()
                else:
                    good = False

            # Connection is lost, e.g. RabbitMQ not running.
            except Exception:
                if good:
                    logging.exception("Lost connection to AMQP broker")
                good = False

            time.sleep(self.CONVERSATION_DELAY)

            if not good:
                if callable(on_error):
                    on_error()