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
CERT_PATH="$SECPI_PATH/certs"
RMQ_CONFIG="/etc/rabbitmq/rabbitmq.config"

# creates a folder and sets permissions to given user and group
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
# generates and signs a certificate with the passed name
# second parameter is extension (client/server)
function gen_and_sign_cert(){
	# generate key
	openssl genrsa -out $CERT_PATH/$1.key.pem 2048
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

# got at least two arguments
# --update <worker|manager|webinterface|all>
# -u <worker|manager|webinterface|all>
if [ $# -ge 2 ]
then
	if [ $1 = "-u" ] || [ $1 = "--update" ]
	then
		# copy tools folder
		find tools/ -name '*.py' | cpio -updm $SECPI_PATH
		
		# copy other stuff
		cp logging.conf $SECPI_PATH/
		
		if [ $2 = "worker" ] || [ $2 = "all" ]
		then
			/etc/init.d/secpi-worker stop
			find worker/ -name '*.py' | cpio -updm $SECPI_PATH
			chmod 755 $SECPI_PATH/worker/worker.py
			/etc/init.d/secpi-worker start
			echo "Updated worker files..."
		fi
		
		if [ $2 = "manager" ] || [ $2 = "all" ]
		then
			/etc/init.d/secpi-manager stop
			find manager/ -name '*.py' | cpio -updm $SECPI_PATH
			chmod 755 $SECPI_PATH/manager/manager.py
			/etc/init.d/secpi-manager start
			echo "Updated manager files..."
		fi
		
		if [ $2 = "webinterface" ] || [ $2 = "all" ]
		then
			/etc/init.d/secpi-webinterface stop
			find webinterface/ -name '*.py' | cpio -updm $SECPI_PATH
			find webinterface/ -name '*.sh' | cpio -updm $SECPI_PATH
			find webinterface/ -name '*.css' | cpio -updm $SECPI_PATH
			find webinterface/ -name '*.js' | cpio -updm $SECPI_PATH
			find webinterface/ -name '*.mako' | cpio -updm $SECPI_PATH
			find webinterface/ -name '*.html' | cpio -updm $SECPI_PATH
			find webinterface/ -name '*.png' | cpio -updm $SECPI_PATH
			find webinterface/ -name '*.jpg' | cpio -updm $SECPI_PATH
			find webinterface/ -name '*.gif' | cpio -updm $SECPI_PATH
			chmod 755 $SECPI_PATH/webinterface/main.py
			/etc/init.d/secpi-webinterface start
			echo "Updated webinterface files..."
		fi
		
		echo "Installing python requirements..."
		pip install -r requirements.txt

		echo "Finished update process!"
		# only copy files in update mode
		exit 0
	fi
fi

echo "Select installation type:"
echo "[1] Complete installation (manager, webinterface, worker)"
echo "[2] Management installation (manager, webinterface)"
echo "[3] Worker installation (worker only)"
read INSTALL_TYPE


check_requirements $INSTALL_TYPE

echo "Please input the user which SecPi should use: (default: root)"
read SECPI_USER

if [ -z "$SECPI_USER" ]
then
	SECPI_USER="root"
	echo "Setting user to default value"
fi

echo "Please input the group which SecPi should use: (default: root)"
read SECPI_GROUP

if [ -z "$SECPI_GROUP" ]
then
	SECPI_GROUP="root"
	echo "Setting group to default value"
fi

echo "Enter RabbitMQ Server IP"
read MQ_IP

echo "Enter RabbitMQ Server Port (default: 5671)"
read MQ_PORT

#if [ "$MQ_PORT" = ""]
if [ -z "$MQ_PORT" ]
then
	MQ_PORT="5671"
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
	echo "Enter certificate authority domain (for rabbitmq and webserver, default: secpi.local)"
	read CA_DOMAIN

	#if [ "$CA_DOMAIN" = ""]
	if [ -z "$CA_DOMAIN" ]
	then
		CA_DOMAIN="secpi.local"
		echo "Setting CA domain to default value"
	fi
fi

if [ $INSTALL_TYPE -eq 1 ] || [ $INSTALL_TYPE -eq 2 ]
then
	if [ "$CREATE_CA" = "yes" ] || [ "$CREATE_CA" = "y" ];
	then
		echo "Enter name for webserver certificate (excluding $CA_DOMAIN; The names 'manager', 'webui', 'mq-server' and 'worker1' are already reserved for RabbitMQ certificates)"
		read WEB_CERT_NAME
	fi
		
	echo "Enter user for webinterface: (default: admin)"
	read WEB_USER

	if [ -z "$WEB_USER" ]
	then
		WEB_USER="admin"
		echo "Setting user to default value"
	fi
	
	echo "Enter password for webinterface: (default: admin)"
	read WEB_PWD

	if [ -z "$WEB_PWD" ]
	then
		WEB_PWD="admin"
		echo "Setting password to default value"
	fi

	echo "Should we take care of rabbitmq.config file? [yes/no]"
	echo "Select no if you already have an existing rabbitmq setup."
	read CREATE_RMQ_CONFIG

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
			sed -i "s/<certfile>/\/opt\/secpi\/certs\/mq-server.$CA_DOMAIN.cert.pem/" $RMQ_CONFIG
			sed -i "s/<keyfile>/\/opt\/secpi\/certs\/mq-server.$CA_DOMAIN.key.pem/" $RMQ_CONFIG
		fi
	fi
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
	openssl req -config $CERT_PATH/ca/openssl.cnf -x509 -newkey rsa:2048 -days 365 -out $CERT_PATH/ca/cacert.pem -keyout $CERT_PATH/ca/private/cakey.pem -outform PEM -subj /CN=$CA_DOMAIN/ -nodes

	# secure ca key
	chmod 600 $CERT_PATH/ca/private

	# generate mq server certificate
	gen_and_sign_cert mq-server.$CA_DOMAIN server
fi



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
	
	echo "Creating config..."
	
	sed -i "s/<ip>/$MQ_IP/" $SECPI_PATH/manager/config.json $SECPI_PATH/webinterface/config.json
	sed -i "s/<port>/$MQ_PORT/" $SECPI_PATH/manager/config.json $SECPI_PATH/webinterface/config.json
	sed -i "s/<user>/$MQ_USER/" $SECPI_PATH/manager/config.json $SECPI_PATH/webinterface/config.json
	sed -i "s/<pwd>/$MQ_PWD/" $SECPI_PATH/manager/config.json $SECPI_PATH/webinterface/config.json
	
	
	if [ "$CREATE_CA" = "yes" ] || [ "$CREATE_CA" = "y" ];
	then
		sed -i "s/<certfile>/manager.$CA_DOMAIN.cert.pem/" $SECPI_PATH/manager/config.json
		sed -i "s/<keyfile>/manager.$CA_DOMAIN.key.pem/" $SECPI_PATH/manager/config.json
		
		sed -i "s/<certfile>/webui.$CA_DOMAIN.cert.pem/" $SECPI_PATH/webinterface/config.json
		sed -i "s/<keyfile>/webui.$CA_DOMAIN.key.pem/" $SECPI_PATH/webinterface/config.json
		sed -i "s/<server_cert>/$WEB_CERT_NAME.$CA_DOMAIN.cert.pem/" $SECPI_PATH/webinterface/config.json
		sed -i "s/<server_key>/$WEB_CERT_NAME.$CA_DOMAIN.key.pem/" $SECPI_PATH/webinterface/config.json
	
		echo "Generating rabbitmq certificates..."
		gen_and_sign_cert manager.$CA_DOMAIN client
		gen_and_sign_cert webui.$CA_DOMAIN client
		
		echo "Generating webserver certificate..."
		gen_and_sign_cert $WEB_CERT_NAME.$CA_DOMAIN server
	fi

	echo "Creating htdigest file..."
	webinterface/create_htdigest.sh $SECPI_PATH/webinterface/.htdigest $WEB_USER $WEB_PWD
	
	
	echo "Copying startup scripts..."
	
	cp scripts/secpi-manager /etc/init.d/
	sed -i "s/{{DEAMONUSER}}/$SECPI_USER:$SECPI_GROUP/" /etc/init.d/secpi-manager
	
	cp scripts/secpi-manager.service /etc/systemd/system/
	sed -i "s/User=/User=$SECPI_USER/" /etc/systemd/system/secpi-manager.service
	sed -i "s/Group=/Group=$SECPI_GROUP/" /etc/systemd/system/secpi-manager.service
	
	update-rc.d secpi-manager defaults
	update-rc.d secpi-manager enable
	
	
	
	cp scripts/secpi-webinterface /etc/init.d/
	sed -i "s/{{DEAMONUSER}}/$SECPI_USER:$SECPI_GROUP/" /etc/init.d/secpi-webinterface
	
	cp scripts/secpi-webinterface.service /etc/systemd/system/
	sed -i "s/User=/User=$SECPI_USER/" /etc/systemd/system/secpi-webinterface.service
	sed -i "s/Group=/Group=$SECPI_GROUP/" /etc/systemd/system/secpi-webinterface.service
	
	update-rc.d secpi-webinterface defaults
	update-rc.d secpi-webinterface enable
	
	# set permissions
	chmod 755 $SECPI_PATH/webinterface/main.py
	chmod 755 $SECPI_PATH/manager/manager.py
	
	# add rabbitmq user and set permissions
	rabbitmqctl add_user $MQ_USER $MQ_PWD
	if [ $? -ne 0 ];
	then
		echo "Error adding RabbitMQ user!"
	fi
	rabbitmqctl set_permissions $MQ_USER "secpi.*|amq\.gen.*" "secpi.*|amq\.gen.*" "secpi.*|amq\.gen.*"
	if [ $? -ne 0 ];
	then
		echo "Error setting RabbitMQ permissions!"
	fi
fi


# worker or complete install
if [ $INSTALL_TYPE -eq 1 ] || [ $INSTALL_TYPE -eq 3 ]
then
	echo "Copying worker..."
	cp -R worker/ $SECPI_PATH/
	
	sed -i "s/<ip>/$MQ_IP/" $SECPI_PATH/worker/config.json
	sed -i "s/<port>/$MQ_PORT/" $SECPI_PATH/worker/config.json
	sed -i "s/<user>/$MQ_USER/" $SECPI_PATH/worker/config.json
	sed -i "s/<pwd>/$MQ_PWD/" $SECPI_PATH/worker/config.json
	
	if [ "$CREATE_CA" = "yes" ] || [ "$CREATE_CA" = "y" ];
	then
		sed -i "s/<certfile>/worker1.$CA_DOMAIN.cert.pem/" $SECPI_PATH/worker/config.json
		sed -i "s/<keyfile>/worker1.$CA_DOMAIN.key.pem/" $SECPI_PATH/worker/config.json
		gen_and_sign_cert worker1.$CA_DOMAIN client
	fi
	
	echo "Copying startup scripts..."
	cp scripts/secpi-worker /etc/init.d/
	sed -i "s/{{DEAMONUSER}}/$SECPI_USER:$SECPI_GROUP/" /etc/init.d/secpi-worker
	
	cp scripts/secpi-worker.service /etc/systemd/system/
	sed -i "s/User=/User=$SECPI_USER/" /etc/systemd/system/secpi-worker.service
	sed -i "s/Group=/Group=$SECPI_GROUP/" /etc/systemd/system/secpi-worker.service
	
	update-rc.d secpi-worker defaults
	update-rc.d secpi-worker enable
	
	
	# set permissions
	chmod 755 $SECPI_PATH/worker/worker.py
fi

chown -R $SECPI_USER:$SECPI_GROUP $SECPI_PATH

# reload systemd, but don't write anything if systemctl doesn't exist
systemctl daemon-reload > /dev/null 2>&1


################################################################################################

echo "Installing python requirements..."
pip install -r requirements.txt
if [ $? -ne 0 ];
then
	echo "Error installing requirements!"
	exit 1
fi


echo "#####################################################"
echo "SecPi sucessfully installed!"
echo "#####################################################"
################
exit 0
################

