if [ $# -lt 2 ]
then
	echo "Usage: renew_cert.sh <name> <extension>"
	exit 1
fi

CERT_PATH="/etc/secpi/certs"

# revoke old cert
openssl ca -config $CERT_PATH/ca/openssl.cnf -revoke $1.cert.pem

# generate crl
openssl ca -gencrl -config $CERT_PATH/ca/openssl.cnf -out $CERT_PATH/ca/crl/secpi-ca.crl

# move old cert
CURTIME=`date +%F_%H%M%S`
mv $CERT_PATH/$1.cert.pem $CERT_PATH/old/$CURTIME-$1.cert.pem
mv $CERT_PATH/$1.req.pem $CERT_PATH/old/$CURTIME-$1.req.pem

# generate csr
openssl req -config $CERT_PATH/ca/openssl.cnf -new -key $CERT_PATH/$1.key.pem -out $CERT_PATH/$1.req.pem -outform PEM -subj /CN=$1/ -nodes
# sign cert
openssl ca -config $CERT_PATH/ca/openssl.cnf -in $CERT_PATH/$1.req.pem -out $CERT_PATH/$1.cert.pem -notext -batch -extensions $2


