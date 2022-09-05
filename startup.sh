#!/bin/bash

# Startup script for SecPi

if [ $# -gt 0 ]
then

	if [ $1 = "manager" ]
	then
		secpi-manager --app-config=etc/development/config-manager.toml

	elif [ $1 = "worker" ]
	then
		secpi-worker --app-config=etc/development/config-worker.toml

	elif [ $1 = "webinterface" ]
	then
		secpi-web --app-config=etc/development/config-web.toml
	else
		echo "Usage: startup.sh <manager|worker|webinterface>"
	fi

else
	echo "Usage: startup.sh <manager|worker|webinterface>"

fi
