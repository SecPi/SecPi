import logging
import functools
import time
import typing as t

import pika

logger = logging.getLogger(__name__)


class AMQPAdapter:
    """
    Connect to AMQP broker and start consuming messages, with reconnect, and buffering.
    """

    # TODO: Implement exponential backoff.
    CONVERSATION_DELAY = 4.2

    def __init__(self, hostname: str, port: int, username: str, password: str, buffer_undelivered=False):
        self.hostname = hostname
        self.port = port
        self.username = username
        self.password = password
        self.buffer_undelivered = buffer_undelivered

        self.connection: pika.BlockingConnection = None
        self.channel: pika.channel.Channel = None

        # List of undelivered messages.
        self.undelivered_messages = []

    def connect(self, retries=None):
        credentials = pika.PlainCredentials(self.username, self.password)
        parameters = pika.ConnectionParameters(
            credentials=credentials,
            host=self.hostname,
            port=self.port,
            heartbeat=360,
            socket_timeout=10,
            # blocked_connection_timeout=300,
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
                logger.info(f"Connecting to AMQP broker at {self.hostname}:{self.port}")
                self.connection = pika.BlockingConnection(parameters=parameters)
                self.channel = self.connection.channel()
                connected = True
                logger.info("Connecting to AMQP broker successful")
            except Exception:
                retry_label = "forever"
                if retries is not None:
                    retry_label = f"for {retries} more times"
                logger.exception(f"Connecting to AMQP broker failed temporarily, retrying {retry_label}")
                self.sleep(self.CONVERSATION_DELAY)

            if retries is not None:
                retries -= 1
                if retries <= 0:
                    raise ConnectionError("Connecting to AMQP broker failed permanently, giving up")

        return connected

    @property
    def available(self):
        return self.connection and self.connection.is_open

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

    def publish(self, **kwargs):
        """
        Publish message to AMQP broker.

        - Optionally buffer messages when bus unavailable.
        - Invokes `publish_threadsafe`.
        """
        if self.available:
            try:
                logger.debug(f"Publishing message: {kwargs}")
                self.publish_threadsafe(**kwargs)
                return True
            except Exception:
                logger.exception("Publishing message failed")
                return False
        else:
            logger.error("Not connected to bus, unable to publish message")

            if self.buffer_undelivered:
                message = kwargs

                if message not in self.undelivered_messages:
                    logger.debug("Storing message to undelivered queue")
                    self.undelivered_messages.append(message)

                # Could happen if we have another disconnect while processing
                # undelivered messages.
                else:
                    logger.debug("Message already in undelivered queue")

            return False

    def publish_threadsafe(self, **kwargs):
        """
        Publish message to bus from multithreaded application.

        This is necessary for multithreaded apps since Pika is not thread safe.
        We must use `add_callback_threadsafe` anytime we want to perform a network action
        on a different thread than the main connection thread.

        - https://brandthill.com/blog/pika.html
        - https://github.com/pika/pika/blob/0.13.1/examples/basic_consumer_threaded.py
        """
        func = functools.partial(self.channel.basic_publish, **kwargs)
        self.connection.add_callback_threadsafe(func)

    def subscribe_forever(self, on_error: t.Optional[t.Callable] = None):
        good = False
        while True:
            logger.info("Start consuming AMQP queue")
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
                    logger.exception("Lost connection to AMQP broker")
                good = False

            self.sleep(self.CONVERSATION_DELAY)

            if not good:
                if callable(on_error):
                    on_error()

    def process_undelivered_messages(self, delay=None):
        """
        Re-submit messages which could not be sent beforehand.
        """
        logger.info("Processing undelivered messages")

        if not self.undelivered_messages:
            logger.info("No undelivered messages found")
            return

        # When processing undelivered messages, make sure to wait a bit, in order to give the
        # manager a chance to be ready beforehand. This easily happens when both daemons are
        # either starting up side by side, or when both regain connection to the AMQP broker
        # at the same time.
        if delay is not None:
            logger.info(f"Delaying undelivered message processing by {delay} seconds")
            self.sleep(self.CONVERSATION_DELAY)

        for message in self.undelivered_messages.copy():
            if self.publish(**message):
                self.undelivered_messages.remove(message)
            else:
                logger.warning("Failed processing undelivered message")

        if not self.undelivered_messages:
            logger.info("Undelivered messages processed completely")
        else:
            logger.warning("Undelivered message processing incomplete")

    def sleep(self, duration):
        """
        `pika.BlockingConnection.sleep` is a safer way to sleep than calling `time.sleep()`
        directly that would keep the adapter from ignoring frames sent from the broker.
        The connection will "sleep" or block the number of seconds specified in duration
        in small intervals.

        https://pika.readthedocs.io/en/stable/modules/adapters/blocking.html#pika.adapters.blocking_connection.BlockingConnection.sleep
        """
        if self.connection is not None and self.connection.is_open:
            self.connection.sleep(duration)
        else:
            time.sleep(duration)
