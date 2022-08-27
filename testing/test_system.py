import subprocess
import sys


def test_worker_with_tcplistener(worker_daemon, capsys):

    # Submit a sensor signal.
    command = "echo hello | socat - tcp:localhost:1234"
    print(subprocess.check_output(command, shell=True), file=sys.stderr)

    # Read output of STDERR.
    application_log = capsys.readouterr().err

    # Debug output.
    # print(application_log); assert 1 == 2

    assert "Loading configuration from testing/etc/config-worker.json" in application_log
    assert "Connecting to AMQP broker at localhost:5672" in application_log
    assert "Setting up sensors and actions" in application_log
    assert "Loading class successful: worker.tcpportlistener.TCPPortListener" in application_log
    assert "Start consuming AMQP queue" in application_log
    assert "Sensor with id 1 detected something" in application_log
    assert \
        "Publishing message:" in application_log and \
        '"sensor_id": 1, "message": "Got TCP connection, raising alarm"' in application_log
