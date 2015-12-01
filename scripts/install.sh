#!/bin/bash

echo "  _________            __________.__                    
 /   _____/ ____   ____\______   \__|                   
 \_____  \_/ __ \_/ ___\|     ___/  |                   
 /        \  ___/\  \___|    |   |  |                   
/_______  /\___  >\___  >____|   |__|                   
        \/     \/     \/                                
.___                 __         .__  .__                
|   | ____   _______/  |______  |  | |  |   ___________ 
|   |/    \ /  ___/\   __\__  \ |  | |  | _/ __ \_  __ \\
|   |   |  \\\\___ \  |  |  / __ \|  |_|  |_\  ___/|  | \/
|___|___|  /____  > |__| (____  /____/____/\___  >__|   
         \/     \/            \/               \/       "


echo "Please input the user  which SecPi should use:"
read SECPI_USER

echo "Please input the group which SecPi should use:"
read SECPI_GROUP

# create /var/run/secpi and set permissions
mkdir /var/run/secpi
if [ $? -ne 0 ];
then
	echo "Couldn't create /var/run/secpi"
	exit 1
else
	echo "Created /var/run/secpi"
fi

chown $SECPI_USER:$SECPI_GROUP /var/run/secpi
if [ $? -ne 0 ];
then
	echo "Couldn't change user and group of /var/run/secpi to the specified values ($SECPI_USER, $SECPI_GROUP)!"
	exit 2
else
	echo "Changed user and group of /var/run/secpi to $SECPI_USER and $SECPI_GROUP"
fi


mkdir /var/log/secpi
if [ $? -ne 0 ];
then
	echo "Couldn't create /var/log/secpi"
	exit 3
else
	echo "Created /var/log/secpi"
fi

chown $SECPI_USER:$SECPI_GROUP /var/log/secpi
if [ $? -ne 0 ];
then
	echo "Couldn't change user and group of /var/log/secpi to the specified values ($SECPI_USER, $SECPI_GROUP)!"
	exit 4
else
	echo "Changed user and group of /var/log/secpi to $SECPI_USER and $SECPI_GROUP"
fi
