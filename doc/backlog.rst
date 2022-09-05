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


***********
Iteration 2
***********

Many modernizations across the board.

Project and code I
==================
- [x] Get rid of ``PROJECT_PATH``
- [x] Add ``pyproject.toml`` and command line entrypoints.
- [x] Tests: Add software tests and CI configuration
- [x] Webinterface: Rip out SSL and ``.htdigest`` authentication completely
- [x] Update to SQLAlchemy 1.4 and Pika 1.3
- [x] Pika 0.x & Python 3.10: ``AttributeError: module 'collections' has no attribute 'Callable'``
- [x] Remove dead code
- [x] Remove some features
- [x] Format code
- [x] Separate configuration directories into {production,development,testing}
- [x] Refactor to ``secpi`` namespace and rework directory layout
- [x] Remove ``sys.exit(130)`` on ``KeyboardInterrupt``.
- [x] Configuration: s/rabbitmq/amqp/
- [x] ``mv .ci .github``
- [x] ``mv scripts stuff contrib``
- [x] Check packaging. -- ``poe build``
- [x] ``mv secpi.web.sites secpi.web.page``
- [x] Add linter

Project and code II
===================
- [x] Put code coverage information into subdirectory
- [x] Refactor test suite
- [x] Use real objects instead of dictionaries for message containers
- [x] Worker/Action: Eradicate writing and reading back data to/from filesystem
  at ``/var/tmp/secpi/worker_data`` and ````/var/tmp/secpi/alarms``.
  Instead, use ``tempfile`` objects all over the place, where applicable, and
  pass all data along with method calls.
- [x] Remove hard-coding of ``/var/tmp/secpi/alarms`` from all plugins
- [x] Use ``AMQP_URL``-style configuration
- [/] Use JSON5 and add comments to configuration files
- [x] Use TOML for configuration files
- [x] Naming things: Replace ``Pi`` or ``pi_id`` with ``worker_id`` across the board.
- [x] Fix ``raise BadZipFile("File is not a zip file")``
- [x] Webinterface: Start on non-standard port 16677 by default. Don't listen on ``0.0.0.0`` by default.
- [x] Webinterface: Make CherryPy's ``--listen-address`` configurable. What about Unix sockets?

Documentation
=============
- [o] Update/improve https://github.com/isarengineering/SecPi/blob/next/doc/sandbox.rst
- [o] Add more comments in configuration files
- [o] Tutorial I: socat -> TCPListener -> Mailer -> mailserver.py
  while true; do echo hello | socat - tcp:localhost:1234; done
- [o] Improve. "From installation to operation" (e.g. ``journalctl``)
- [o] Database setup. How to run ``DatabaseAdapter.setup()`` once?
- [o] Turn Wiki into dedicated repository. -- https://github.com/SecPi/SecPi/wiki/
- [o] Download Wiki images from imgur
- [o] First commit: 14 May 2015. -- https://github.com/SecPi/SecPi/commit/e9d86f31d9
- [o] Other projects

  - https://github.com/nielsfaber/alarmo
  - https://github.com/bkbilly/AlarmPI
  - https://pypi.org/project/automate-home/
  - https://pypi.org/project/home-service/
  - https://pypi.org/project/RPIHomeAlarmSystem/
  - https://projects.privateeyepi.com/

Standalone mode
===============
- [o] Improve generic NoBroker wiring
- [x] Use TOML for configuration?

Features
========
- [o] UI: Facelift with Materialize
- [o] UI: Dropdown boxes providing lists of built-in sensors, notifiers, and actions
- [o] UI: Compound forms with {Action,Notifier} + params
- [o] ADAM: Summary message should also be submitted on "ACTIVATE".
- [o] ADAM: Summary message should only be a message, not an alarm.
- [o] Alarm notifications: We need to have two mails per alarm. One should be emitted
  instantly, and the second one after shoveling all the camera images together.
  Alternatively, think about uploading them to S3 or Nextcloud.
- [o] DO schalten: Als Action.
- [o] SIP: Fritzbox instead of Asterisk?


***********
Iteration 3
***********

Towards 2.0.0.

Project and code
================
- [o] Dependencies: Make installing ``pygame`` optional
- [o] Test _all_ the plugin modules _for-real_ to discover if something went south.
- [o] Bring back AMQP SSL connection abilities.
- [o] Bring back Alarm file storage & Web UI ``/alarmdata`` as "Audit" feature.
- [o] Add MQTT SSL connection abilities.
- [o] Improve UI

  - https://github.com/SecPi/SecPi/issues/101
  - https://github.com/SecPi/SecPi/commit/98926004e
- [o] Tests: Improve efficiency by implementing ``socat``, ``amqp-publish``, and ``amqp-get`` in pure Python
- [o] More test scenarios and validations, e.g.

  - uninitialized Worker
  - Manager+Mailer
  - Web+Activate
  - AMQP messaging (check receive)
  - Database interaction

- [o] ADAM: Resolve ambiguation with ``mqtt_broker_ip`` vs. "port"
- [o] Webinterface: Bump JavaScript dependencies and re-bundle using Yarn and webpack

Deployment and production
=========================
- [o] Improve ``install.sh``.
- [o] Add new systemd unit files, with logging to journald.
- [o] Run CherryPy web server in "production" mode.
- [o] Mount ``/var/tmp`` as tmpfs


***********
Iteration 4
***********

Project and code III
====================
- [o] Check RabbitMQ 3.10.7
- [o] Revisit all ``FIXME`` items
- [o] Add pytest-docker-compose for GarageMQ and Mosquitto
- [o] ``tweepy/auth.py:120: DeprecationWarning: OAuthHandler is deprecated; use OAuth1UserHandler instead.``


Ideas for the future
====================

- [o] SQLAlchemy: Resolve flaws with concurrent access.
  https://github.com/isarengineering/SecPi/issues/6
- [o] Webinterface: Optimize (reduce) number of backend requests
- [o] Webinterface: When many entities (Alarm and LogEntry entities) are in the database
  (i.e. millions of records), the frontend becomes completely unresponsive.
  Maybe only fetch the last N entities per request?
- [o] Improve notifications: Discriminate between subject and message.
  Maybe map from subsystem to subject.
- [o] Notifications using Apprise or mqttwarn
- [o] Command for configuring SecPi, like ``secpictl add sensor foo ...``
- [o] Integration with https://github.com/hostcc/pyg90alarm
- [o] Integrate with Home Assistant
