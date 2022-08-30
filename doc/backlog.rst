#############
SecPi backlog
#############


***********
Iteration 1
***********

Make it work on Python 3. Add adapters for Advantech ADAM 6050 and SIPCall/Asterisk.

- [x] Add compatibility with Python 3. Thanks, @tonkenfo.
- [x] AMQP: refactoring and deduplication.
- [/] AMQP: Upgrade to Pika 1.3. -- https://github.com/isarengineering/SecPi/commit/c21eb4f59f2.
  Cancelled - patch is not ready yet.
- [x] AMQP: Resolve flaws with concurrent access. -- https://github.com/isarengineering/SecPi/issues/5
- [o] ADAM: Summary message should also be submitted on "ACTIVATE".
- [o] ADAM: Summary message should only be a message, not an alarm.


***********
Iteration 2
***********

Many modernizations across the board.

Project and code
================
- [x] Get rid of ``PROJECT_PATH``
- [x] Add ``pyproject.toml`` and command line entrypoints.
- [x] Tests: Add software tests and CI configuration
- [x] Webinterface: Rip out SSL and ``.htdigest`` authentication completely
- [x] Update to SQLAlchemy 1.4 and Pika 1.3
- [x] Pika 0.x & Python 3.10: ``AttributeError: module 'collections' has no attribute 'Callable'``
- [x] Remove dead code
- [x] Remove some features
- [x] Format code
- [o] Refactor to ``secpi`` namespace and rework directory layout
- [o] Webinterface: Start on non-standard port 16677 by default. Don't listen on ``0.0.0.0`` by default.
- [o] Webinterface: Make CherryPy's ``--listen-address`` configurable. What about Unix sockets?
- [o] Dependencies: Make installing ``pygame`` optional
- [o] Remove ``sys.exit(130)`` on ``KeyboardInterrupt``.
- [o] Check RabbitMQ 3.10.7

Bugs
====
- [o] Remove hard-coding of ``/var/tmp/secpi/alarms`` from all plugins
- [o] Webinterface: Croaks right away when navigating to "Alarm Data": ``FileNotFoundError: [Errno 2] No such file or directory: '/var/tmp/secpi/alarms'``

Documentation
=============
- [o] Update/improve https://github.com/isarengineering/SecPi/blob/next/doc/sandbox.rst
- [o] Tutorial I: socat -> TCPListener -> Mailer -> mailserver.py
  while true; do echo hello | socat - tcp:localhost:1234; done
- [o] Improve. "From installation to operation" (e.g. ``journalctl``)
- [o] Database setup. How to run ``DatabaseAdapter.setup()`` once?
- [o] Turn Wiki into dedicated repository. -- https://github.com/SecPi/SecPi/wiki/
- [o] Download Wiki images from imgur

Features
========
- [o] Alarm notifications: We need to have two mails per alarm. One should be emitted
  instantly, and the second one after shoveling all the camera images together.
  Alternatively, think about uploading them to S3 or Nextcloud.
- [o] DO schalten: Als Action.


***********
Iteration 3
***********

Towards 2.0.0.

Project and code
================
- [o] Bring back AMQP SSL connection abilities.
- [o] Add MQTT SSL connection abilities.
- [o] Improve UI
  https://github.com/SecPi/SecPi/issues/101
- [o] Tests: Improve efficiency by implementing ``socat``, ``amqp-publish``, and ``amqp-get`` in pure Python
- [o] More test scenarios and validations, e.g.

  - uninitialized Worker
  - Manager+Mailer
  - Web+Activate
  - AMQP messaging (check receive)
  - Database interaction

- [o] ADAM: Resolve ambiguation with ``mqtt_broker_ip`` vs. "port"
- [o] Webinterface: Bump JavaScript dependencies and rebundle using Yarn and webpack

Deployment and production
=========================
- [o] Improve ``install.sh``.
- [o] Add new systemd unit files, with logging to journald.
- [o] Run CherryPy web server in "production" mode.
- [o] Mount ``/var/tmp`` as tmpfs


***********
Iteration 4
***********

Ideas for the future.

- [o] Naming things: Replace ``Pi`` or ``pi_id`` with something more meaningful
- [o] SQLAlchemy: Resolve flaws with concurrent access.
  https://github.com/isarengineering/SecPi/issues/6
- [o] Webinterface: Optimize (reduce) number of backend requests
- [o] Webinterface: When many entities (Alarm and LogEntry entities) are in the database
  (i.e. millions of records), the frontend becomes completely unresponsive.
  Maybe only fetch the last N entities per request?
- [o] Improve notifications: Discriminate between subject and message.
  Maybe map from subsystem to subject.
- [o] Notifications using Apprise or mqttwarn
