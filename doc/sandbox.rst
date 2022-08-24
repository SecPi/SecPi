#########################
SecPi development sandbox
#########################

*****
Setup
*****
::

    git clone https://github.com/isarengineering/SecPi
    cd SecPi

    python3 -m venv .venv
    source .venv/bin/activate
    pip install -r requirements.txt


*******
Operate
*******

Start::

    docker run -it --rm --publish=5672:5672 rabbitmq:3.9
    ./startup.sh manager
    ./startup.sh worker
    ./startup.sh webinterface
