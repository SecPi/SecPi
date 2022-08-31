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
CONFIG_PATH="/etc/secpi"
CERT_PATH="/etc/secpi/certs"
RMQ_CONFIG="/etc/rabbitmq/rabbitmq.config"

LOG_PATH="/var/log/secpi"
TMP_PATH="/var/tmp/secpi"

# creates a folder and sets permissions to given user and group
function create_folder(){
	if [ -d $1 ];
	then
		echo "$1 already exists"
		return 0
	fi
	mkdir $1
	if [ $? -ne 0 ];
	then
		echo "Unable to create $1"
		exit 3
	else
		echo "Created $1"
	fi

	chown $2:$3 $1
	if [ $? -ne 0 ];
	then
		echo "Unable to change user and group of $1 to the specified user and group ($2, $3)"
		exit 4
	else
		echo "Changed user and group of $1 to $2 and $3"
	fi
}
# generates and signs a certificate with the passed name
# second parameter is extension (client/server)
function gen_and_sign_cert(){
	# generate key
	openssl genrsa -out $CERT_PATH/$1.key.pem 4096
	# generate csr
	openssl req -config $CERT_PATH/ca/openssl.cnf -new -key $CERT_PATH/$1.key.pem -out $CERT_PATH/$1.req.pem -outform PEM -subj /CN=$1/ -nodes
	# sign cert
	openssl ca -config $CERT_PATH/ca/openssl.cnf -in $CERT_PATH/$1.req.pem -out $CERT_PATH/$1.cert.pem -notext -batch -extensions $2
}

function check_requirements(){
	if ! hash pip 2>/dev/null;
	then
		echo "Dependency pip is missing"
		exit 5
	fi
	
	# manager or complete install only
	if [ $1 -eq 1 ] || [ $1 -eq 2 ]
	then
		if ! hash rabbitmqctl 2>/dev/null;
		then
			echo "Dependency rabbitmq is missing"
			exit 5
		fi
	fi
}


echo "Select installation type: (default: [1] Complete installation)"
echo "[1] Complete installation (manager, webinterface, worker)"
echo "[2] Management installation (manager, webinterface)"
echo "[3] Worker installation (worker only)"
echo "Note: When there is a default option available pressing enter will select it automatically."
read INSTALL_TYPE

if [ -z "$INSTALL_TYPE" ]
then
	INSTALL_TYPE="1"
	echo "Performing complete installation"
fi

check_requirements $INSTALL_TYPE

echo "Please input the user which SecPi should use: (default: secpi)"
read SECPI_USER

if [ -z "$SECPI_USER" ]
then
	SECPI_USER="secpi"
	echo "Setting user to default value"
fi

echo "Please input the group which SecPi should use: (default: secpi)"
read SECPI_GROUP

if [ -z "$SECPI_GROUP" ]
then
	SECPI_GROUP="secpi"
	echo "Setting group to default value"
fi

echo "Enter RabbitMQ Server IP"
read MQ_IP

echo "Enter RabbitMQ Server Port (default: 5672)"
read MQ_PORT

#if [ "$MQ_PORT" = ""]
if [ -z "$MQ_PORT" ]
then
	MQ_PORT="5672"
	echo "Setting port to default value"
fi

echo "Enter RabbitMQ User (default: secpi)"
read MQ_USER

if [ -z "$MQ_USER" ]
then
	MQ_USER="secpi"
	echo "Setting user to default value"
fi

echo "Enter RabbitMQ Password"
read MQ_PWD

if [ $INSTALL_TYPE -ne 3 ]
then
	echo "Generate CA and certificates? [yes/no]"
	read CREATE_CA
fi

if [ "$CREATE_CA" = "yes" ] || [ "$CREATE_CA" = "y" ];
then
	echo "Enter certificate common name for rabbitmq (default: secpi.local)"
	read COMMON_NAME

	#if [ "$COMMON_NAME" = ""]
	if [ -z "$COMMON_NAME" ]
	then
		COMMON_NAME="secpi.local"
		echo "Setting CA domain to default value"
	fi
fi

if [ $INSTALL_TYPE -eq 1 ] || [ $INSTALL_TYPE -eq 2 ]
then
	echo "Should we take care of rabbitmq.config file? [yes/no] (default: yes)"
	echo "Select no if you already have an existing rabbitmq setup."
	read CREATE_RMQ_CONFIG

	if [ -z "$CREATE_RMQ_CONFIG" ]
	then
		CREATE_RMQ_CONFIG="yes"
		echo "Creating default rabbitmq configuration file"
	fi

	if [ "$CREATE_RMQ_CONFIG" = "yes" ] || [ "$CREATE_RMQ_CONFIG" = "y" ];
	then
		if [ ! -d /etc/rabbitmq ];
		then
			echo "Error, /etc/rabbitmq/ doesn't exist... is RabbitMQ installed?"
			exit 1
		fi
		echo "Copying rabbitmq.config file..."
		cp scripts/rabbitmq.config $RMQ_CONFIG

		sed -i "s/<port>/$MQ_PORT/" $RMQ_CONFIG
		
		if [ "$CREATE_CA" = "yes" ] || [ "$CREATE_CA" = "y" ];
		then
			sed -i "s/<certfile>/\/etc\/secpi\/certs\/mq-server.cert.pem/" $RMQ_CONFIG
			sed -i "s/<keyfile>/\/etc\/secpi\/certs\/mq-server.key.pem/" $RMQ_CONFIG
		fi
	fi
fi




# create log folder
create_folder $LOG_PATH $SECPI_USER $SECPI_GROUP

# create secpi folder
create_folder $SECPI_PATH $SECPI_USER $SECPI_GROUP

# create tmp folder
create_folder $TMP_PATH $SECPI_USER $SECPI_GROUP
create_folder $TMP_PATH/worker_data $SECPI_USER $SECPI_GROUP
create_folder $TMP_PATH/alarms $SECPI_USER $SECPI_GROUP

# create tls certificate folder
create_folder $CERT_PATH $SECPI_USER $SECPI_GROUP


if [ "$CREATE_CA" = "yes" ] || [ "$CREATE_CA" = "y" ];
then
	# generate certificates for rabbitmq
	create_folder $CERT_PATH/ca $SECPI_USER $SECPI_GROUP
	create_folder $CERT_PATH/ca/private $SECPI_USER $SECPI_GROUP
	create_folder $CERT_PATH/ca/crl $SECPI_USER $SECPI_GROUP
	create_folder $CERT_PATH/ca/newcerts $SECPI_USER $SECPI_GROUP
	create_folder $CERT_PATH/ca/old $SECPI_USER $SECPI_GROUP
	touch $CERT_PATH/ca/index.txt
	echo 1000 > $CERT_PATH/ca/serial
	echo 1000 > $CERT_PATH/ca/crlnumber

	cp scripts/openssl.cnf $CERT_PATH/ca/
	cp scripts/gen_cert.sh $SECPI_PATH
	cp scripts/renew_cert.sh $SECPI_PATH

	# generate ca cert
	openssl req -config $CERT_PATH/ca/openssl.cnf -x509 -newkey rsa:4096 -days 3650 -out $CERT_PATH/ca/cacert.pem -keyout $CERT_PATH/ca/private/cakey.pem -outform PEM -subj /CN=$COMMON_NAME/ -nodes

	# secure ca key
	chmod 600 $CERT_PATH/ca/private

	# generate mq server certificate
	gen_and_sign_cert mq-server server
fi



echo "Current SecPi folder: $PWD"

# manager or complete install
if [ $INSTALL_TYPE -eq 1 ] || [ $INSTALL_TYPE -eq 2 ]
then
	
	echo "Creating config..."
	
	sed -i "s/<ip>/$MQ_IP/" $CONFIG_PATH/config-manager.json $CONFIG_PATH/config-web.json
	sed -i "s/<port>/$MQ_PORT/" $CONFIG_PATH/config-manager.json $CONFIG_PATH/config-web.json
	sed -i "s/<user>/$MQ_USER/" $CONFIG_PATH/config-manager.json $CONFIG_PATH/config-web.json
	sed -i "s/<pwd>/$MQ_PWD/" $CONFIG_PATH/config-manager.json $CONFIG_PATH/config-web.json
	
	
	if [ "$CREATE_CA" = "yes" ] || [ "$CREATE_CA" = "y" ];
	then
		sed -i "s/<certfile>/manager.cert.pem/" $CONFIG_PATH/config-manager.json
		sed -i "s/<keyfile>/manager.key.pem/" $CONFIG_PATH/config-manager.json
		
		sed -i "s/<certfile>/webui.cert.pem/" $CONFIG_PATH/config-web.json
		sed -i "s/<keyfile>/webui.key.pem/" $CONFIG_PATH/config-web.json

		echo "Generating rabbitmq certificates..."
		gen_and_sign_cert manager client
		gen_and_sign_cert webui client
	fi

	echo "Copying startup scripts..."
	
	cp packaging/init/secpi-manager /etc/init.d/
	sed -i "s/{{DEAMONUSER}}/$SECPI_USER:$SECPI_GROUP/" /etc/init.d/secpi-manager
	
	cp packaging/init/secpi-manager.service /etc/systemd/system/
	sed -i "s/User=/User=$SECPI_USER/" /etc/systemd/system/secpi-manager.service
	sed -i "s/Group=/Group=$SECPI_GROUP/" /etc/systemd/system/secpi-manager.service
	
	update-rc.d secpi-manager defaults
	update-rc.d secpi-manager enable
	
	
	
	cp packaging/init/secpi-webinterface /etc/init.d/
	sed -i "s/{{DEAMONUSER}}/$SECPI_USER:$SECPI_GROUP/" /etc/init.d/secpi-webinterface
	
	cp packaging/init/secpi-webinterface.service /etc/systemd/system/
	sed -i "s/User=/User=$SECPI_USER/" /etc/systemd/system/secpi-webinterface.service
	sed -i "s/Group=/Group=$SECPI_GROUP/" /etc/systemd/system/secpi-webinterface.service
	
	update-rc.d secpi-webinterface defaults
	update-rc.d secpi-webinterface enable
	
	# add rabbitmq user and set permissions
	rabbitmqctl add_user $MQ_USER $MQ_PWD
	if [ $? -ne 0 ];
	then
		echo "Error adding RabbitMQ user"
	fi
	rabbitmqctl set_permissions $MQ_USER "secpi.*|amq\.gen.*" "secpi.*|amq\.gen.*" "secpi.*|amq\.gen.*"
	if [ $? -ne 0 ];
	then
		echo "Error setting RabbitMQ permissions"
	fi
fi


# worker or complete install
if [ $INSTALL_TYPE -eq 1 ] || [ $INSTALL_TYPE -eq 3 ]
then
	
	sed -i "s/<ip>/$MQ_IP/" $CONFIG_PATH/config-worker.json
	sed -i "s/<port>/$MQ_PORT/" $CONFIG_PATH/config-worker.json
	sed -i "s/<user>/$MQ_USER/" $CONFIG_PATH/config-worker.json
	sed -i "s/<pwd>/$MQ_PWD/" $CONFIG_PATH/config-worker.json
	
	if [ "$CREATE_CA" = "yes" ] || [ "$CREATE_CA" = "y" ];
	then
		sed -i "s/<certfile>/worker1.cert.pem/" $CONFIG_PATH/config-worker.json
		sed -i "s/<keyfile>/worker1.key.pem/" $CONFIG_PATH/config-worker.json
		gen_and_sign_cert worker1 client
	fi
	
	echo "Copying startup scripts..."
	cp packaging/init/secpi-worker /etc/init.d/
	sed -i "s/{{DEAMONUSER}}/$SECPI_USER:$SECPI_GROUP/" /etc/init.d/secpi-worker
	
	cp packaging/init/secpi-worker.service /etc/systemd/system/
	sed -i "s/User=/User=$SECPI_USER/" /etc/systemd/system/secpi-worker.service
	sed -i "s/Group=/Group=$SECPI_GROUP/" /etc/systemd/system/secpi-worker.service
	
	update-rc.d secpi-worker defaults
	update-rc.d secpi-worker enable
	
fi

chown -R $SECPI_USER:$SECPI_GROUP $SECPI_PATH

# reload systemd, but don't write anything if systemctl doesn't exist
systemctl daemon-reload > /dev/null 2>&1




echo "############################"
echo "SecPi successfully installed"
echo "############################"
