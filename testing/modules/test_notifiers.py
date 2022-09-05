import datetime
import pathlib
import re
import tempfile
from email.message import Message

import pytest

from secpi.model.message import AlarmMessage, NotificationMessage
from secpi.util.common import load_class

NOTIFICATION_MESSAGE = NotificationMessage(
    sensor_name="sensor-testing",
    worker_name="worker-testing",
    alarm=AlarmMessage(
        sensor_id=1,
        worker_id=1,
        message="Franz jagt im komplett verwahrlosten Taxi quer durch Bayern",
        datetime=datetime.datetime.now(),
    ),
)


def test_notifier_dropbox(caplog):
    """
    Test the Dropbox file drop notifier.
    """

    # Configure notifier.
    component = load_class("secpi.notifier.dropbox", "DropboxFileUpload")
    parameters = {
        "access_token": "foobar-token",
    }

    # Invoke notifier.
    notifier = component(1, parameters)
    notifier.notify(NOTIFICATION_MESSAGE)

    # Verify log output matches the expectations.
    assert "Loading class successful: secpi.notifier.dropbox.DropboxFileUpload" in caplog.messages
    assert "DropboxFileUpload initialized" in caplog.messages
    assert re.match(
        r".*DropboxFileUpload: Uploading file secpi-\d+-\d+.zip to /", caplog.text, re.DOTALL | re.MULTILINE
    )
    assert "Request to files/upload" in caplog.messages

    # It is expected to fail, because we do not have a valid access token.
    # However, it was not expected to receive::
    #
    #   Could not find a suitable TLS CA certificate bundle, invalid path:
    #   /path/to/.venv/lib/python3.9/site-packages/certifi/cacert.pem
    assert "DropboxFileUpload: Uploading file failed" in caplog.text


def test_notifier_mailer(caplog, smtpd):
    """
    Test the SMTP email notifier.
    """

    # Configure notifier.
    component = load_class("secpi.notifier.mailer", "Mailer")
    parameters = {
        "smtp_address": "localhost",
        "smtp_port": "8025",
        "smtp_user": "",
        "smtp_pass": "",
        "smtp_security": "NOAUTH_NOSSL",
        "sender": "secpi@example.org",
        "recipient": "user@example.org",
        "subject": "SecPi Alarm",
        "text": "Your SecPi raised an alarm",
        "unzip_attachments": "1",
    }

    # Invoke notifier.
    notifier = component(1, parameters)
    notifier.notify(NOTIFICATION_MESSAGE)

    # Verify log output matches the expectations.
    assert "Loading class successful: secpi.notifier.mailer.Mailer" in caplog.messages
    assert "Mailer: Notifier initialized" in caplog.messages
    assert "Notifying via SMTP email" in caplog.messages
    assert "Mailer: Decoding zip file as requested" in caplog.messages
    assert "Failed to prepare email attachments" in caplog.messages
    # assert re.match(".*Mailer: Will look into .+ for data.*", caplog.text, re.DOTALL)
    assert "Mailer: Trying to send mail without authentication" in caplog.messages
    assert "Mailer: Establishing connection to SMTP server" in caplog.messages
    assert "Mailer: Mail sent" in caplog.messages

    assert len(smtpd.messages) == 1

    message: Message = smtpd.messages[0]

    assert message.is_multipart()
    assert message.get("From") == "secpi@example.org"
    assert message.get("To") == "user@example.org"
    assert message.get("Subject") == "SecPi Alarm"

    message_part2: Message = message.get_payload()[1]
    message_body2: str = message_part2.get_payload()
    assert (
        "Received alarm on sensor sensor-testing from worker worker-testing: "
        "Franz jagt im komplett verwahrlosten Taxi quer durch Bayern" in message_body2
    )


def test_notifier_sipcall(mocker, caplog):
    """
    Verify the SIP call notifier behaves as expected.
    """

    mocker.patch("pycall.callfile.getpwnam", return_value=(None, None, 999, 999))
    mocker.patch("pycall.callfile.chown")

    callfile_reference = [
        "Channel: SIP/sip-testing/+49-177-1234567\n",
        "WaitTime: 50\n",
        "RetryTime: 120\n",
        "Maxretries: 4\n",
        "Context: alarm_sensor-testing\n",
        "Extension: s\n",
        "Priority: 1",
    ]

    with tempfile.TemporaryDirectory() as tmpdir:
        # Configure notifier.
        component = load_class("secpi.notifier.sipcall", "SipCall")
        parameters = {
            "sip_number": "+49-177-1234567",
            "sip_route": "sip-testing",
            "sip_asterisk_spool_dir": tmpdir,
        }

        # Invoke notifier.
        notifier = component(1, parameters)
        notifier.notify(NOTIFICATION_MESSAGE)

        # Verify the produced call file matches the expectations.
        firstfile = list(pathlib.Path(tmpdir).iterdir())[0]
        callfile_current = open(firstfile, "r").readlines()
        assert callfile_current == callfile_reference

    # Verify log output matches the expectations.
    assert "Loading class successful: secpi.notifier.sipcall.SipCall" in caplog.messages
    assert "SipCall: Notifier initialized" in caplog.messages
    assert "SipCall: Starting call to +49-177-1234567, triggered by sensor sensor-testing" in caplog.messages
    assert "SipCall: Call to +49-177-1234567 submitted successfully" in caplog.messages


def test_notifier_slack(caplog):
    """
    Verify the Slack notifier behaves as expected.
    """
    import slacker

    # Configure notifier.
    component = load_class("secpi.notifier.slack", "SlackNotifier")
    parameters = {
        "channel": "secpi-testing",
        "bot_token": "foobar-token",
    }

    # Invoke notifier.
    # It is expected to fail, probably because of an invalid token?
    notifier = component(1, parameters)
    with pytest.raises(slacker.Error) as ex:
        notifier.notify(NOTIFICATION_MESSAGE)
    assert ex.match("unknown_method")

    # Verify log output matches the expectations.
    assert "Loading class successful: secpi.notifier.slack.SlackNotifier" in caplog.messages
    assert "Sending Slack notification" in caplog.messages
    assert "Starting new HTTPS connection (1): slack.com:443" in caplog.messages
    assert (
        'https://slack.com:443 "GET /api/groups.list?exclude_archived=1&token=foobar-token HTTP/1.1" 200 77'
        in caplog.messages
    )


def test_notifier_sms(mocker, caplog):
    """
    Verify the SMS notifier behaves as expected.
    """

    mocker.patch("gsmmodem.GsmModem", create=True)

    # Configure notifier.
    component = load_class("secpi.notifier.sms", "Sms")
    parameters = {
        "port": "/dev/ttyUSB-testing",
        "recipients": "alice,bob",
    }

    # Invoke notifier.
    # It is expected to fail, probably because of an invalid token?
    notifier = component(1, parameters)
    notifier.notify(NOTIFICATION_MESSAGE)

    # Verify log output matches the expectations.
    assert "Loading class successful: secpi.notifier.sms.Sms" in caplog.messages
    assert "Sms: Notifier initialized" in caplog.messages
    assert "Sms: Sending message to alice" in caplog.messages
    assert "Sms: Message to alice was sent successfully" in caplog.messages
    assert "Sms: Sending message to bob" in caplog.messages
    assert "Sms: Message to bob was sent successfully" in caplog.messages


def test_notifier_spark(caplog):
    """
    Verify the Cisco Spark notifier behaves as expected.
    """

    # Configure notifier.
    component = load_class("secpi.notifier.spark", "SparkNotifier")
    parameters = {
        "personal_token": "foobar-token",
        "room": "room-42",
    }

    # Invoke notifier.
    # It is expected to fail, probably because of an invalid token?
    notifier = component(1, parameters)
    notifier.notify(NOTIFICATION_MESSAGE)

    # Verify log output matches the expectations.
    assert "Loading class successful: secpi.notifier.spark.SparkNotifier" in caplog.messages
    assert "Sending Cisco Spark notification" in caplog.messages
    assert "Starting new HTTPS connection (1): api.ciscospark.com:443" in caplog.messages

    # It is expected to fail, because invalid token.
    assert 'https://api.ciscospark.com:443 "GET /v1/rooms HTTP/1.1" 401' in caplog.text
    assert (
        "Error in Spark Notifier: 401 Client Error: Unauthorized for url: https://api.ciscospark.com/v1/rooms"
        in caplog.messages
    )


def test_notifier_twitter(caplog):
    """
    Verify the Twitter notifier behaves as expected.
    """

    # Configure notifier.
    component = load_class("secpi.notifier.twitter", "Twitter")
    parameters = {
        "consumer_key": "foobar-key",
        "consumer_secret": "foobar-secret",
        "access_token": "foobar-token",
        "access_token_secret": "foobar-token-secret",
        "recipients": "alice,bob",
    }

    # Invoke notifier.
    # It is expected to fail, probably because of an invalid token?
    notifier = component(1, parameters)
    notifier.notify(NOTIFICATION_MESSAGE)

    # Verify log output matches the expectations.
    assert "Loading class successful: secpi.notifier.twitter.Twitter" in caplog.messages
    assert "Twitter: Notifier initialized" in caplog.messages
    assert "Starting new HTTPS connection (1): api.twitter.com:443" in caplog.messages

    # It is expected to fail, because invalid token.
    assert 'https://api.twitter.com:443 "POST /1.1/direct_messages/events/new.json HTTP/1.1" 401 87' in caplog.messages
    assert "Twitter: Sending message to alice failed" in caplog.messages
    assert "tweepy.errors.Unauthorized: 401 Unauthorized" in caplog.text
    assert "89 - Invalid or expired token" in caplog.text
