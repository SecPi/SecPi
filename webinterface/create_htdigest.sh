#!/bin/bash
HASH=`echo -n $2:secpi:$3 | md5sum |awk '{print $1}'`
LINE="$2:secpi:$HASH"
# file already exists, do some magic
if [ -f $1 ]
then
	# check if name already in file
	if grep $2:secpi $1 > /dev/null 2>&1
	then
		sed -i "s/$2:secpi:.*/$2:secpi:$HASH/" "$1"
	else
		# else append to file
		echo $LINE >> $1
	fi
else
	echo $LINE > $1
fi
