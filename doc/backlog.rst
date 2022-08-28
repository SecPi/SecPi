#############
SecPi backlog
#############


***********
Iteration 1
***********
- [x] AMQP: refactoring and deduplication.
- [o] AMQP: Upgrade to Pika 1.3.0 again.
  See https://github.com/isarengineering/SecPi/commit/c21eb4f59f2.
- [x] AMQP: Resolve flaws with concurrent access.
  https://github.com/isarengineering/SecPi/issues/5
- [o] ADAM: Summary message should also be submitted on "ACTIVATE".
- [o] ADAM: Summary message should only be a message, not an alarm.


***********
Iteration 2
***********
- [o] Get rid of ``PROJECT_PATH``
- [o] Overhaul directory layout. Add setup.py and command line entrypoints.
- [o] Add software tests and CI configuration
- [o] Naming things: Replace ``Pi`` or ``pi_id`` with something more meaningful
- [o] Improve ``install.sh``.
- [o] Deployment: Add new systemd unit files, with logging to journald.
- [o] Tutorial I: socat -> TCPListener -> Mailer -> mailserver.py
  while true; do echo hello | socat - tcp:localhost:1234; done
- [o] Mount ``/var/tmp`` as tmpfs
- [o] Tests: Replace ``socat`` with Python routine
- [o] CI: Improve efficiency by implementing ``socat`` and ``amqp-publish`` in Python
- [o] More test scenarios, e.g. uninitialized Worker, Manager+Mailer, Web+Activate
- [o] Remove dead code
- [o] Namespace refactoring
- [o] Improve docs; from installation to operation (e.g. ``journalctl``)
- [o] Webinterface: Shouldn't it better be implemented using a real web server?

  - Rip out SSL completely?
  - Rip out ``.htdigest`` authentication completely?
- [o] Test and use ``speaker.py``
- [o] Bump JavaScript dependencies and rebundle using Yarn and webpack.


***********
Iteration 3
***********
- [o] SQLAlchemy: Resolve flaws with concurrent access.
  https://github.com/isarengineering/SecPi/issues/6
- [o] Webinterface: Optimize (reduce) number backend requests
- [o] Webinterface: When many entities (Alarm and LogEntry entities) are in the database
  (i.e. millions of records), the frontend becomes completely unresponsive.
  Maybe only fetch the last N entities per request?
- [o] Improve notifications: Discriminate between subject and message.
  Maybe map from subsystem to subject.
- [o] Bring back AMQP SSL connection abilities.
- [o] Add MQTT SSL connection abilities.
- [o] Notifications using Apprise or mqttwarn
- [o] Improve UI
  https://github.com/SecPi/SecPi/issues/101
- [o] Add documentation from Wiki
- [o] Turn Wiki into dedicated repository
  https://github.com/SecPi/SecPi/wiki/
- [o] Download Wiki images from imgur.
