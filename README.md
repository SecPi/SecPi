# SecPi Alarm System

[![Tests](https://img.shields.io/github/workflow/status/isarengineering/SecPi/Tests.svg?style=flat-square&label=Tests)](https://github.com/isarengineering/SecPi/actions/workflows/tests.yml)
[![Test coverage](https://img.shields.io/codecov/c/gh/isarengineering/SecPi.svg?style=flat-square)](https://codecov.io/gh/isarengineering/SecPi/)
[![License](https://img.shields.io/github/license/isarengineering/SecPi.svg?style=flat-square)](https://github.com/isarengineering/SecPi/blob/next/LICENSE) 

## About

SecPi is an open source project which gives people the ability to build their
own inexpensive, expandable and feature-rich alarm system.

We tailored the system to run on the Raspberry Pi but other platforms like the
Banana Pi and any other Linux machines should be capable to run the software too.

With SecPi it is also possible to connect multiple systems via network and have
them work together.

Please visit the [wiki pages](https://github.com/SecPi/SecPi/wiki) for more information.


## Overview

### Features

The major features are:

- Built-in elements for sensors, actions and notifiers
- Modular and extensible architecture for adding more elements
- Support for multiple systems on the network
- Web interface for desktop and mobile devices
- Support for SBC Linux platforms like the Raspberry Pi and Banana Pi


### Architecture

We recommend to make yourself accustomed to the jargon of SecPi. You should know a bit
about the Manager, Worker, and Webinterface/WebUI software components, and how they work
together. A corresponding summary is https://github.com/SecPi/SecPi/wiki/Introduction.


### Technologies

The system is based on Python, AMQP/Pika, RabbitMQ, SQLAlchemy, and CherryPy/Mako.


## Project information

### Contributions

Every kind of contribution, feedback, or patch, is much welcome. [Create an
issue] or submit a patch if you think we should include a new feature, or to
report or fix a bug.


### Development

In order to set up a development environment on your workstation, please head over
to the [development sandbox] documentation. When you see the software tests succeed,
you should be ready to start hacking.


### Resources

- [Source code](https://github.com/isarengineering/SecPi)
- [Documentation](https://github.com/SecPi/SecPi/wiki)


### License

This project is licensed under the GNU General Public License.

You should have received a copy of the GNU General Public License
along with this program. If not, see <http://www.gnu.org/licenses/>.


### Acknowledgements

Many kudos go to the original authors [Philip Wölfel] and [Martin Liebl]
for conceiving and maintaining this program.


### Attributions

#### Fugue Icons

(C) 2012 [Yusuke Kamiyamane]. All rights reserved.
These icons are licensed under a Creative Commons
Attribution 3.0 License.


[Create an issue]: https://github.com/isarengineering/SecPi/issues/new
[development sandbox]: https://github.com/isarengineering/SecPi/blob/next/doc/sandbox.rst
[Martin Liebl]: https://github.com/MartinLiebl
[Philip Wölfel]: https://github.com/phwoelfel
[Yusuke Kamiyamane]: https://github.com/yusukekamiyamane
