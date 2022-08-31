#!/bin/bash

# Startup script for SecPi

if [ $# -gt 0 ]
then

	if [ $1 = "manager" ]
	then
		secpi-manager --app-config=etc/development/config-manager.json

	elif [ $1 = "worker" ]
	then
		secpi-worker --app-config=etc/development/config-worker.json

	elif [ $1 = "webinterface" ]
	then
		secpi-web --app-config=etc/development/config-web.json
	else
		echo "Usage: startup.sh <manager|worker|webinterface>"
	fi

else
	echo "Usage: startup.sh <manager|worker|webinterface>"

fi
