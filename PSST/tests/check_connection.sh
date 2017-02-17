#!/bin/bash

# -q: Silence mode; --sipder: don't get, just check page availability
wget -q --spider http://cern.ch
if [ $? -eq 0 ]; then
	echo "Online"
	exit 0
fi

echo -e "GET http://cern.ch HTTP/1.0\n\n" | nc cern.sh 80 > /dev/null 2>&1
if [ $? -eq 0 ]; then
	echo "Online"
else
	echo "Offline"
	exit $ERROR_NO_CONNECTION
fi