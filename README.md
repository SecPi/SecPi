# SecPi

## About
SecPi is an open source project which gives people the ability to build their
own inexpensive, expandable and feature-rich alarm system.

We tailored the system to run on the Raspberry Pi but other platforms like the
Banana Pi and any other Linux machine should be capable to run the software too.

With SecPi it's also possible to connect multiple systems via a network
connection and have them work together.

Please visit the [wiki pages](https://github.com/SecPi/SecPi/wiki) for more information.


## Development setup
```shell
git clone https://github.com/isarengineering/SecPi --branch=python3
cd SecPi

python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

docker run -it --rm --publish=5672:5672 rabbitmq:3.9
./startup.sh manager
./startup.sh worker
```


## Attributions

### Fugue Icons
(C) 2012 Yusuke Kamiyamane. All rights reserved.
These icons are licensed under a Creative Commons
Attribution 3.0 License.
<http://creativecommons.org/licenses/by/3.0/>