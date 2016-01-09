#!/bin/bash
HASH=`echo -n $2:secpi:$3 | md5sum |awk '{print $1}'`
LINE="$2:secpi:$HASH"
echo $LINE > $1