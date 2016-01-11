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


SECPI_PATH="/opt/secpi"
LOG_PATH="/var/log/secpi"
TMP_PATH="/var/tmp/secpi"


function create_folder(){
	if [ -d $1 ];
	then
		echo "$1 exists!"
		return 0
	fi
	mkdir $1
	if [ $? -ne 0 ];
	then
		echo "Couldn't create $1"
		exit 3
	else
		echo "Created $1"
	fi

	chown $2:$3 $1
	if [ $? -ne 0 ];
	then
		echo "Couldn't change user and group of $1 to the specified user and group ($2, $3)!"
		exit 4
	else
		echo "Changed user and group of $1 to $2 and $3"
	fi
}


echo "Please input the user which SecPi should use:"
read SECPI_USER

echo "Please input the group which SecPi should use:"
read SECPI_GROUP

echo "Select installation type:"
echo "[1] Complete installation (manager, webui, worker)"
echo "[2] Management installation (manager, webui)"
echo "[3] Worker installation (worker only)"
read INSTALL_TYPE

echo "Enter RabbitMQ Server IP"
read MQ_IP

echo "Enter RabbitMQ Server Port (default: 5671)"
read MQ_PORT

echo "Enter RabbitMQ User"
read MQ_USER

echo "Enter RabbitMQ Password"
read MQ_PWD

echo "Enter path to CA certificate relative to $SECPI_PATH/certs/"
read CA_CERT_PATH

if [ $INSTALL_TYPE -eq 1 ] || [ $INSTALL_TYPE -eq 2 ]
then
	echo "Enter path to manager client certificate relative to $SECPI_PATH/certs/"
	read MGR_CERT_PATH
	
	echo "Enter path to manager client key relative to $SECPI_PATH/certs/"
	read MGR_KEY_PATH

	echo "Enter path to webinterface client certificate relative to $SECPI_PATH/certs/"
	read WEB_CERT_PATH
	
	echo "Enter path to webinterface client key relative to $SECPI_PATH/certs/"
	read WEB_KEY_PATH
	
	echo "Enter user for webinterface:"
	read WEB_USER
	
	echo "Enter password for webinterface:"
	read WEB_PWD
fi

if [ $INSTALL_TYPE -eq 1 ] || [ $INSTALL_TYPE -eq 3 ]
then
	echo "Enter path to worker client certificate relative to $SECPI_PATH/certs/"
	read WORKER_CERT_PATH
	
	echo "Enter path to worker client key relative to $SECPI_PATH/certs/"
	read WORKER_KEY_PATH
fi



################################################################################################
# create log folder
create_folder $LOG_PATH $SECPI_USER $SECPI_GROUP

################################################################################################
# create secpi folder
create_folder $SECPI_PATH $SECPI_USER $SECPI_GROUP

################################################################################################
# create run folder
# create_folder $SECPI_PATH/run $SECPI_USER $SECPI_GROUP

# create tmp folder
create_folder $TMP_PATH $SECPI_USER $SECPI_GROUP
create_folder $TMP_PATH/worker_data $SECPI_USER $SECPI_GROUP
create_folder $TMP_PATH/alarms $SECPI_USER $SECPI_GROUP


read -d '' JSON_CONFIG << EOF
{
	"rabbitmq":{
		"master_ip": "$MQ_IP",
		"master_port": $MQ_PORT,
		"user": "$MQ_USER",
		"password": "$MQ_PWD",
		"cacert": "$CA_CERT_PATH",
EOF

read -d '' JSON_END << EOF
	}
}
EOF


echo "Current SecPi folder: $PWD"
echo "Copying to $SECPI_PATH..."

# copy tools folder
cp -R tools/ $SECPI_PATH/
cp logging.conf $SECPI_PATH/

# manager or complete install
if [ $INSTALL_TYPE -eq 1 ] || [ $INSTALL_TYPE -eq 2 ]
then
	echo "Copying manager..."
	cp -R manager/ $SECPI_PATH/
	echo "Copying webinterface..."
	cp -R webinterface/ $SECPI_PATH/

	chmod 755 $SECPI_PATH/webinterface/main.py
	chmod 755 $SECPI_PATH/manager/manager.py
	
	echo "Creating config..."
	read -d '' JSON_MGR << EOF
	"certfile": "$MGR_CERT_PATH",
	"keyfile": "$MGR_KEY_PATH"
EOF
	
	read -d '' JSON_WEB << EOF
	"certfile": "$WEB_CERT_PATH",
	"keyfile": "$WEB_KEY_PATH"
EOF

	echo $JSON_CONFIG > $SECPI_PATH/manager/config.json
	echo $JSON_MGR >> $SECPI_PATH/manager/config.json
	echo $JSON_END >> $SECPI_PATH/manager/config.json
	
	echo $JSON_CONFIG > $SECPI_PATH/webinterface/config.json
	echo $JSON_WEB >> $SECPI_PATH/webinterface/config.json
	echo $JSON_END >> $SECPI_PATH/webinterface/config.json

	echo "Creating htdigest file..."
	webinterface/create_htdigest.sh $SECPI_PATH/webinterface/.htdigest $WEB_USER $WEB_PWD
	
	
	echo "Copying startup scripts..."
	
	cp scripts/secpi-manager /etc/init.d/
	sed -i "s/{{DEAMONUSER}}/$SECPI_USER:$SECPI_GROUP/" /etc/init.d/secpi-manager
	update-rc.d secpi-manager defaults
	
	cp scripts/secpi-webinterface /etc/init.d/
	sed -i "s/{{DEAMONUSER}}/$SECPI_USER:$SECPI_GROUP/" /etc/init.d/secpi-webinterface
	update-rc.d secpi-webinterface defaults
fi


# worker or complete install
if [ $INSTALL_TYPE -eq 1 ] || [ $INSTALL_TYPE -eq 3 ]
then
	echo "Copying worker..."
	cp -R worker/ $SECPI_PATH/
	chmod 755 $SECPI_PATH/worker/worker.py
	
	read -d '' JSON_WORKER << EOF
	"certfile": "$WORKER_CERT_PATH",
	"keyfile": "$WORKER_KEY_PATH"
EOF

	echo $JSON_CONFIG > $SECPI_PATH/worker/config.json
	echo $JSON_WORKER >> $SECPI_PATH/worker/config.json
	echo $JSON_END >> $SECPI_PATH/worker/config.json
	
	echo "Copying startup scripts..."
	cp scripts/secpi-worker /etc/init.d/
	sed -i "s/{{DEAMONUSER}}/$SECPI_USER:$SECPI_GROUP/" /etc/init.d/secpi-worker
	update-rc.d secpi-worker defaults
fi



################################################################################################

echo "Installing python requirements..."
pip install -r requirements.txt
if [ $? -ne 0 ];
then
	echo "Error installing requirements!"
	exit 1
fi



echo "SecPi sucessfully installed!"
################
exit 0
################

