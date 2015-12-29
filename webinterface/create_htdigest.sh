#!/bin/bash
HASH=`echo -n $1:secpi:$2 | md5sum |awk '{print $1}'`
LINE="$1:secpi:$HASH"
echo $LINE > .htdigest